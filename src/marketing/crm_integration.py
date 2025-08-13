"""
CRM integration system for marketing and sales funnel.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from uuid import uuid4
import json
import aiohttp
from abc import ABC, abstractmethod
from enum import Enum

from ..common.redis_client import RedisClient

logger = logging.getLogger(__name__)


class CRMProvider(str, Enum):
    """CRM provider values"""
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    PIPEDRIVE = "pipedrive"
    ZOHO = "zoho"
    HUBSPOT_CRM = "hubspot_crm"
    CUSTOM = "custom"


@dataclass
class CRMContact:
    """CRM contact information"""
    id: str = ""
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    company: str = ""
    job_title: str = ""
    phone: str = ""
    website: str = ""
    industry: str = ""
    company_size: str = ""
    annual_revenue: str = ""
    lead_source: str = ""
    lead_score: int = 0
    stage: str = ""
    assigned_to: str = ""
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    last_contact: Optional[datetime] = None
    next_follow_up: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class CRMOpportunity:
    """CRM opportunity information"""
    id: str = ""
    name: str = ""
    contact_id: str = ""
    company: str = ""
    amount: float = 0.0
    stage: str = ""
    probability: float = 0.0
    close_date: Optional[datetime] = None
    assigned_to: str = ""
    description: str = ""
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class CRMSyncResult:
    """CRM synchronization result"""
    success: bool = True
    contacts_synced: int = 0
    opportunities_synced: int = 0
    errors: List[str] = field(default_factory=list)
    sync_timestamp: datetime = field(default_factory=datetime.utcnow)


class BaseCRMIntegration(ABC):
    """Base class for CRM integrations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get("api_key", "")
        self.api_url = config.get("api_url", "")
        self.timeout = config.get("timeout", 30)
        
        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Rate limiting
        self.rate_limit_delay = config.get("rate_limit_delay", 0.1)
        self.last_request_time = 0
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self):
        """Apply rate limiting"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        
        self.last_request_time = asyncio.get_event_loop().time()
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with CRM"""
        pass
    
    @abstractmethod
    async def create_contact(self, contact_data: Dict[str, Any]) -> Optional[CRMContact]:
        """Create contact in CRM"""
        pass
    
    @abstractmethod
    async def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> Optional[CRMContact]:
        """Update contact in CRM"""
        pass
    
    @abstractmethod
    async def get_contact(self, contact_id: str) -> Optional[CRMContact]:
        """Get contact from CRM"""
        pass
    
    @abstractmethod
    async def search_contacts(self, filters: Dict[str, Any] = None) -> List[CRMContact]:
        """Search contacts in CRM"""
        pass
    
    @abstractmethod
    async def create_opportunity(self, opportunity_data: Dict[str, Any]) -> Optional[CRMOpportunity]:
        """Create opportunity in CRM"""
        pass
    
    @abstractmethod
    async def update_opportunity(self, opportunity_id: str, updates: Dict[str, Any]) -> Optional[CRMOpportunity]:
        """Update opportunity in CRM"""
        pass
    
    @abstractmethod
    async def get_opportunity(self, opportunity_id: str) -> Optional[CRMOpportunity]:
        """Get opportunity from CRM"""
        pass


class SalesforceIntegration(BaseCRMIntegration):
    """Salesforce CRM integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.instance_url = config.get("instance_url", "")
        self.username = config.get("username", "")
        self.password = config.get("password", "")
        self.security_token = config.get("security_token", "")
        self.access_token = ""
        self.refresh_token = ""
    
    async def authenticate(self) -> bool:
        """Authenticate with Salesforce using OAuth"""
        try:
            # OAuth 2.0 authentication
            auth_url = "https://login.salesforce.com/services/oauth2/token"
            auth_data = {
                "grant_type": "password",
                "username": self.username,
                "password": self.password + self.security_token,
                "client_id": self.config.get("client_id", ""),
                "client_secret": self.config.get("client_secret", "")
            }
            
            await self._rate_limit()
            
            async with self.session.post(auth_url, data=auth_data) as response:
                if response.status == 200:
                    auth_result = await response.json()
                    self.access_token = auth_result["access_token"]
                    self.refresh_token = auth_result.get("refresh_token", "")
                    
                    # Set authorization header
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.access_token}"
                    })
                    
                    logger.info("Salesforce authentication successful")
                    return True
                else:
                    logger.error(f"Salesforce authentication failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Salesforce authentication error: {e}")
            return False
    
    async def create_contact(self, contact_data: Dict[str, Any]) -> Optional[CRMContact]:
        """Create contact in Salesforce"""
        try:
            # Map contact data to Salesforce fields
            sf_contact = self._map_contact_to_salesforce(contact_data)
            
            await self._rate_limit()
            
            url = f"{self.instance_url}/services/data/v58.0/sobjects/Contact"
            async with self.session.post(url, json=sf_contact) as response:
                if response.status == 201:
                    result = await response.json()
                    contact_id = result["id"]
                    
                    # Get created contact
                    return await self.get_contact(contact_id)
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to create Salesforce contact: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating Salesforce contact: {e}")
            return None
    
    async def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> Optional[CRMContact]:
        """Update contact in Salesforce"""
        try:
            # Map updates to Salesforce fields
            sf_updates = self._map_contact_to_salesforce(updates)
            
            await self._rate_limit()
            
            url = f"{self.instance_url}/services/data/v58.0/sobjects/Contact/{contact_id}"
            async with self.session.patch(url, json=sf_updates) as response:
                if response.status == 204:
                    # Get updated contact
                    return await self.get_contact(contact_id)
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to update Salesforce contact: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error updating Salesforce contact: {e}")
            return None
    
    async def get_contact(self, contact_id: str) -> Optional[CRMContact]:
        """Get contact from Salesforce"""
        try:
            await self._rate_limit()
            
            url = f"{self.instance_url}/services/data/v58.0/sobjects/Contact/{contact_id}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    sf_contact = await response.json()
                    return self._map_salesforce_to_contact(sf_contact)
                else:
                    logger.error(f"Failed to get Salesforce contact: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting Salesforce contact: {e}")
            return None
    
    async def search_contacts(self, filters: Dict[str, Any] = None) -> List[CRMContact]:
        """Search contacts in Salesforce using SOQL"""
        try:
            # Build SOQL query
            soql = "SELECT Id, Email, FirstName, LastName, Company, Title, Phone, Website, " \
                   "Industry, Company_Size__c, Annual_Revenue__c, LeadSource, " \
                   "Lead_Score__c, Stage__c, OwnerId, Description, CreatedDate, LastModifiedDate " \
                   "FROM Contact"
            
            if filters:
                where_clauses = []
                for key, value in filters.items():
                    if key == "email":
                        where_clauses.append(f"Email = '{value}'")
                    elif key == "company":
                        where_clauses.append(f"Company LIKE '%{value}%'")
                    elif key == "industry":
                        where_clauses.append(f"Industry = '{value}'")
                
                if where_clauses:
                    soql += " WHERE " + " AND ".join(where_clauses)
            
            soql += " ORDER BY LastModifiedDate DESC LIMIT 200"
            
            await self._rate_limit()
            
            url = f"{self.instance_url}/services/data/v58.0/query?q={soql}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    contacts = []
                    
                    for record in result.get("records", []):
                        contact = self._map_salesforce_to_contact(record)
                        if contact:
                            contacts.append(contact)
                    
                    return contacts
                else:
                    logger.error(f"Failed to search Salesforce contacts: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching Salesforce contacts: {e}")
            return []
    
    async def create_opportunity(self, opportunity_data: Dict[str, Any]) -> Optional[CRMOpportunity]:
        """Create opportunity in Salesforce"""
        try:
            # Map opportunity data to Salesforce fields
            sf_opportunity = self._map_opportunity_to_salesforce(opportunity_data)
            
            await self._rate_limit()
            
            url = f"{self.instance_url}/services/data/v58.0/sobjects/Opportunity"
            async with self.session.post(url, json=sf_opportunity) as response:
                if response.status == 201:
                    result = await response.json()
                    opportunity_id = result["id"]
                    
                    # Get created opportunity
                    return await self.get_opportunity(opportunity_id)
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to create Salesforce opportunity: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating Salesforce opportunity: {e}")
            return None
    
    async def update_opportunity(self, opportunity_id: str, updates: Dict[str, Any]) -> Optional[CRMOpportunity]:
        """Update opportunity in Salesforce"""
        try:
            # Map updates to Salesforce fields
            sf_updates = self._map_opportunity_to_salesforce(updates)
            
            await self._rate_limit()
            
            url = f"{self.instance_url}/services/data/v58.0/sobjects/Opportunity/{opportunity_id}"
            async with self.session.patch(url, json=sf_updates) as response:
                if response.status == 204:
                    # Get updated opportunity
                    return await self.get_opportunity(opportunity_id)
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to update Salesforce opportunity: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error updating Salesforce opportunity: {e}")
            return None
    
    async def get_opportunity(self, opportunity_id: str) -> Optional[CRMOpportunity]:
        """Get opportunity from Salesforce"""
        try:
            await self._rate_limit()
            
            url = f"{self.instance_url}/services/data/v58.0/sobjects/Opportunity/{opportunity_id}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    sf_opportunity = await response.json()
                    return self._map_salesforce_to_opportunity(sf_opportunity)
                else:
                    logger.error(f"Failed to get Salesforce opportunity: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting Salesforce opportunity: {e}")
            return None
    
    def _map_contact_to_salesforce(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map contact data to Salesforce fields"""
        mapping = {
            "Email": contact_data.get("email", ""),
            "FirstName": contact_data.get("first_name", ""),
            "LastName": contact_data.get("last_name", ""),
            "Company": contact_data.get("company", ""),
            "Title": contact_data.get("job_title", ""),
            "Phone": contact_data.get("phone", ""),
            "Website": contact_data.get("website", ""),
            "Industry": contact_data.get("industry", ""),
            "Company_Size__c": contact_data.get("company_size", ""),
            "Annual_Revenue__c": contact_data.get("annual_revenue", ""),
            "LeadSource": contact_data.get("lead_source", ""),
            "Lead_Score__c": contact_data.get("lead_score", 0),
            "Stage__c": contact_data.get("stage", ""),
            "Description": contact_data.get("notes", "")
        }
        
        # Remove empty values
        return {k: v for k, v in mapping.items() if v}
    
    def _map_salesforce_to_contact(self, sf_contact: Dict[str, Any]) -> CRMContact:
        """Map Salesforce contact to CRMContact"""
        return CRMContact(
            id=sf_contact.get("Id", ""),
            email=sf_contact.get("Email", ""),
            first_name=sf_contact.get("FirstName", ""),
            last_name=sf_contact.get("LastName", ""),
            company=sf_contact.get("Company", ""),
            job_title=sf_contact.get("Title", ""),
            phone=sf_contact.get("Phone", ""),
            website=sf_contact.get("Website", ""),
            industry=sf_contact.get("Industry", ""),
            company_size=sf_contact.get("Company_Size__c", ""),
            annual_revenue=sf_contact.get("Annual_Revenue__c", ""),
            lead_source=sf_contact.get("LeadSource", ""),
            lead_score=sf_contact.get("Lead_Score__c", 0),
            stage=sf_contact.get("Stage__c", ""),
            notes=sf_contact.get("Description", ""),
            created_at=self._parse_salesforce_date(sf_contact.get("CreatedDate")),
            updated_at=self._parse_salesforce_date(sf_contact.get("LastModifiedDate"))
        )
    
    def _map_opportunity_to_salesforce(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map opportunity data to Salesforce fields"""
        mapping = {
            "Name": opportunity_data.get("name", ""),
            "ContactId": opportunity_data.get("contact_id", ""),
            "Company__c": opportunity_data.get("company", ""),
            "Amount": opportunity_data.get("amount", 0.0),
            "StageName": opportunity_data.get("stage", ""),
            "Probability": opportunity_data.get("probability", 0.0),
            "CloseDate": opportunity_data.get("close_date", ""),
            "Description": opportunity_data.get("description", "")
        }
        
        # Remove empty values
        return {k: v for k, v in mapping.items() if v}
    
    def _map_salesforce_to_opportunity(self, sf_opportunity: Dict[str, Any]) -> CRMOpportunity:
        """Map Salesforce opportunity to CRMOpportunity"""
        return CRMOpportunity(
            id=sf_opportunity.get("Id", ""),
            name=sf_opportunity.get("Name", ""),
            contact_id=sf_opportunity.get("ContactId", ""),
            company=sf_opportunity.get("Company__c", ""),
            amount=sf_opportunity.get("Amount", 0.0),
            stage=sf_opportunity.get("StageName", ""),
            probability=sf_opportunity.get("Probability", 0.0),
            close_date=self._parse_salesforce_date(sf_opportunity.get("CloseDate")),
            description=sf_opportunity.get("Description", ""),
            created_at=self._parse_salesforce_date(sf_opportunity.get("CreatedDate")),
            updated_at=self._parse_salesforce_date(sf_opportunity.get("LastModifiedDate"))
        )
    
    def _parse_salesforce_date(self, date_str: str) -> Optional[datetime]:
        """Parse Salesforce date string"""
        if not date_str:
            return None
        
        try:
            # Salesforce uses ISO 8601 format
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            return None


class HubSpotIntegration(BaseCRMIntegration):
    """HubSpot CRM integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key", "")
        self.base_url = "https://api.hubapi.com"
        
        # Set authorization header
        if self.session:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}"
            })
    
    async def authenticate(self) -> bool:
        """Authenticate with HubSpot (API key based)"""
        try:
            # Test API key by making a simple request
            await self._rate_limit()
            
            url = f"{self.base_url}/crm/v3/objects/contacts"
            params = {"limit": 1}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    logger.info("HubSpot authentication successful")
                    return True
                else:
                    logger.error(f"HubSpot authentication failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"HubSpot authentication error: {e}")
            return False
    
    async def create_contact(self, contact_data: Dict[str, Any]) -> Optional[CRMContact]:
        """Create contact in HubSpot"""
        try:
            # Map contact data to HubSpot properties
            hs_properties = self._map_contact_to_hubspot(contact_data)
            
            await self._rate_limit()
            
            url = f"{self.base_url}/crm/v3/objects/contacts"
            payload = {"properties": hs_properties}
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 201:
                    result = await response.json()
                    contact_id = result["id"]
                    
                    # Get created contact
                    return await self.get_contact(contact_id)
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to create HubSpot contact: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating HubSpot contact: {e}")
            return None
    
    async def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> Optional[CRMContact]:
        """Update contact in HubSpot"""
        try:
            # Map updates to HubSpot properties
            hs_properties = self._map_contact_to_hubspot(updates)
            
            await self._rate_limit()
            
            url = f"{self.base_url}/crm/v3/objects/contacts/{contact_id}"
            payload = {"properties": hs_properties}
            
            async with self.session.patch(url, json=payload) as response:
                if response.status == 200:
                    # Get updated contact
                    return await self.get_contact(contact_id)
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to update HubSpot contact: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error updating HubSpot contact: {e}")
            return None
    
    async def get_contact(self, contact_id: str) -> Optional[CRMContact]:
        """Get contact from HubSpot"""
        try:
            await self._rate_limit()
            
            url = f"{self.base_url}/crm/v3/objects/contacts/{contact_id}"
            params = {"properties": "email,firstname,lastname,company,title,phone,website,industry,company_size,annual_revenue,lead_source,lead_score,stage,notes"}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    hs_contact = await response.json()
                    return self._map_hubspot_to_contact(hs_contact)
                else:
                    logger.error(f"Failed to get HubSpot contact: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting HubSpot contact: {e}")
            return None
    
    async def search_contacts(self, filters: Dict[str, Any] = None) -> List[CRMContact]:
        """Search contacts in HubSpot"""
        try:
            # Build search query
            search_payload = {
                "filterGroups": [],
                "properties": ["email", "firstname", "lastname", "company", "title", "phone", "website", "industry", "company_size", "annual_revenue", "lead_source", "lead_score", "stage", "notes"],
                "limit": 100
            }
            
            if filters:
                filter_group = {"filters": []}
                for key, value in filters.items():
                    if key == "email":
                        filter_group["filters"].append({
                            "propertyName": "email",
                            "operator": "EQ",
                            "value": value
                        })
                    elif key == "company":
                        filter_group["filters"].append({
                            "propertyName": "company",
                            "operator": "CONTAINS_TOKEN",
                            "value": value
                        })
                
                if filter_group["filters"]:
                    search_payload["filterGroups"].append(filter_group)
            
            await self._rate_limit()
            
            url = f"{self.base_url}/crm/v3/objects/contacts/search"
            async with self.session.post(url, json=search_payload) as response:
                if response.status == 200:
                    result = await response.json()
                    contacts = []
                    
                    for record in result.get("results", []):
                        contact = self._map_hubspot_to_contact(record)
                        if contact:
                            contacts.append(contact)
                    
                    return contacts
                else:
                    logger.error(f"Failed to search HubSpot contacts: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching HubSpot contacts: {e}")
            return []
    
    async def create_opportunity(self, opportunity_data: Dict[str, Any]) -> Optional[CRMOpportunity]:
        """Create opportunity in HubSpot (Deal)"""
        try:
            # Map opportunity data to HubSpot deal properties
            hs_properties = self._map_opportunity_to_hubspot(opportunity_data)
            
            await self._rate_limit()
            
            url = f"{self.base_url}/crm/v3/objects/deals"
            payload = {"properties": hs_properties}
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 201:
                    result = await response.json()
                    opportunity_id = result["id"]
                    
                    # Get created opportunity
                    return await self.get_opportunity(opportunity_id)
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to create HubSpot deal: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating HubSpot deal: {e}")
            return None
    
    async def update_opportunity(self, opportunity_id: str, updates: Dict[str, Any]) -> Optional[CRMOpportunity]:
        """Update opportunity in HubSpot (Deal)"""
        try:
            # Map updates to HubSpot deal properties
            hs_properties = self._map_opportunity_to_hubspot(updates)
            
            await self._rate_limit()
            
            url = f"{self.base_url}/crm/v3/objects/deals/{opportunity_id}"
            payload = {"properties": hs_properties}
            
            async with self.session.patch(url, json=payload) as response:
                if response.status == 200:
                    # Get updated opportunity
                    return await self.get_opportunity(opportunity_id)
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to update HubSpot deal: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error updating HubSpot deal: {e}")
            return None
    
    async def get_opportunity(self, opportunity_id: str) -> Optional[CRMOpportunity]:
        """Get opportunity from HubSpot (Deal)"""
        try:
            await self._rate_limit()
            
            url = f"{self.base_url}/crm/v3/objects/deals/{opportunity_id}"
            params = {"properties": "dealname,amount,dealstage,closedate,description"}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    hs_deal = await response.json()
                    return self._map_hubspot_to_opportunity(hs_deal)
                else:
                    logger.error(f"Failed to get HubSpot deal: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting HubSpot deal: {e}")
            return None
    
    def _map_contact_to_hubspot(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map contact data to HubSpot properties"""
        mapping = {
            "email": contact_data.get("email", ""),
            "firstname": contact_data.get("first_name", ""),
            "lastname": contact_data.get("last_name", ""),
            "company": contact_data.get("company", ""),
            "title": contact_data.get("job_title", ""),
            "phone": contact_data.get("phone", ""),
            "website": contact_data.get("website", ""),
            "industry": contact_data.get("industry", ""),
            "company_size": contact_data.get("company_size", ""),
            "annual_revenue": contact_data.get("annual_revenue", ""),
            "lead_source": contact_data.get("lead_source", ""),
            "lead_score": contact_data.get("lead_score", 0),
            "stage": contact_data.get("stage", ""),
            "notes": contact_data.get("notes", "")
        }
        
        # Remove empty values
        return {k: v for k, v in mapping.items() if v}
    
    def _map_hubspot_to_contact(self, hs_contact: Dict[str, Any]) -> CRMContact:
        """Map HubSpot contact to CRMContact"""
        properties = hs_contact.get("properties", {})
        
        return CRMContact(
            id=hs_contact.get("id", ""),
            email=properties.get("email", ""),
            first_name=properties.get("firstname", ""),
            last_name=properties.get("lastname", ""),
            company=properties.get("company", ""),
            job_title=properties.get("title", ""),
            phone=properties.get("phone", ""),
            website=properties.get("website", ""),
            industry=properties.get("industry", ""),
            company_size=properties.get("company_size", ""),
            annual_revenue=properties.get("annual_revenue", ""),
            lead_source=properties.get("lead_source", ""),
            lead_score=int(properties.get("lead_score", 0)),
            stage=properties.get("stage", ""),
            notes=properties.get("notes", ""),
            created_at=self._parse_hubspot_date(hs_contact.get("createdAt")),
            updated_at=self._parse_hubspot_date(hs_contact.get("updatedAt"))
        )
    
    def _map_opportunity_to_hubspot(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map opportunity data to HubSpot deal properties"""
        mapping = {
            "dealname": opportunity_data.get("name", ""),
            "amount": opportunity_data.get("amount", 0.0),
            "dealstage": opportunity_data.get("stage", ""),
            "closedate": opportunity_data.get("close_date", ""),
            "description": opportunity_data.get("description", "")
        }
        
        # Remove empty values
        return {k: v for k, v in mapping.items() if v}
    
    def _map_hubspot_to_opportunity(self, hs_deal: Dict[str, Any]) -> CRMOpportunity:
        """Map HubSpot deal to CRMOpportunity"""
        properties = hs_deal.get("properties", {})
        
        return CRMOpportunity(
            id=hs_deal.get("id", ""),
            name=properties.get("dealname", ""),
            amount=float(properties.get("amount", 0.0)),
            stage=properties.get("dealstage", ""),
            close_date=self._parse_hubspot_date(properties.get("closedate")),
            description=properties.get("description", ""),
            created_at=self._parse_hubspot_date(hs_deal.get("createdAt")),
            updated_at=self._parse_hubspot_date(hs_deal.get("updatedAt"))
        )
    
    def _parse_hubspot_date(self, date_str: str) -> Optional[datetime]:
        """Parse HubSpot date string"""
        if not date_str:
            return None
        
        try:
            # HubSpot uses ISO 8601 format
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            return None


class CRMIntegration:
    """Main CRM integration manager"""
    
    def __init__(self, redis_client: RedisClient, config: Dict[str, Any]):
        self.redis_client = redis_client
        self.config = config
        
        # CRM provider instances
        self.providers: Dict[str, BaseCRMIntegration] = {}
        
        # Initialize CRM providers
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize CRM provider instances"""
        for provider_name, provider_config in self.config.get("providers", {}).items():
            if provider_name == "salesforce":
                self.providers[provider_name] = SalesforceIntegration(provider_config)
            elif provider_name == "hubspot":
                self.providers[provider_name] = HubSpotIntegration(provider_config)
            # Add more providers as needed
    
    async def get_provider(self, provider_name: str) -> Optional[BaseCRMIntegration]:
        """Get CRM provider instance"""
        return self.providers.get(provider_name)
    
    async def sync_contacts(self, provider_name: str, contacts: List[Dict[str, Any]]) -> CRMSyncResult:
        """Sync contacts with CRM"""
        provider = await self.get_provider(provider_name)
        if not provider:
            return CRMSyncResult(success=False, errors=[f"Provider {provider_name} not found"])
        
        result = CRMSyncResult()
        
        try:
            # Authenticate with CRM
            if not await provider.authenticate():
                result.success = False
                result.errors.append("Authentication failed")
                return result
            
            # Sync contacts
            for contact_data in contacts:
                try:
                    # Check if contact exists
                    existing_contacts = await provider.search_contacts({"email": contact_data["email"]})
                    
                    if existing_contacts:
                        # Update existing contact
                        contact_id = existing_contacts[0].id
                        await provider.update_contact(contact_id, contact_data)
                    else:
                        # Create new contact
                        await provider.create_contact(contact_data)
                    
                    result.contacts_synced += 1
                    
                except Exception as e:
                    result.errors.append(f"Failed to sync contact {contact_data.get('email', 'unknown')}: {e}")
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Sync failed: {e}")
        
        return result
    
    async def sync_opportunities(self, provider_name: str, opportunities: List[Dict[str, Any]]) -> CRMSyncResult:
        """Sync opportunities with CRM"""
        provider = await self.get_provider(provider_name)
        if not provider:
            return CRMSyncResult(success=False, errors=[f"Provider {provider_name} not found"])
        
        result = CRMSyncResult()
        
        try:
            # Authenticate with CRM
            if not await provider.authenticate():
                result.success = False
                result.errors.append("Authentication failed")
                return result
            
            # Sync opportunities
            for opportunity_data in opportunities:
                try:
                    # Create or update opportunity
                    if "id" in opportunity_data:
                        await provider.update_opportunity(opportunity_data["id"], opportunity_data)
                    else:
                        await provider.create_opportunity(opportunity_data)
                    
                    result.opportunities_synced += 1
                    
                except Exception as e:
                    result.errors.append(f"Failed to sync opportunity {opportunity_data.get('name', 'unknown')}: {e}")
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Sync failed: {e}")
        
        return result
    
    async def get_contact_from_crm(self, provider_name: str, contact_id: str) -> Optional[CRMContact]:
        """Get contact from CRM"""
        provider = await self.get_provider(provider_name)
        if not provider:
            return None
        
        try:
            if await provider.authenticate():
                return await provider.get_contact(contact_id)
        except Exception as e:
            logger.error(f"Error getting contact from CRM: {e}")
        
        return None
    
    async def search_contacts_in_crm(self, provider_name: str, filters: Dict[str, Any] = None) -> List[CRMContact]:
        """Search contacts in CRM"""
        provider = await self.get_provider(provider_name)
        if not provider:
            return []
        
        try:
            if await provider.authenticate():
                return await provider.search_contacts(filters)
        except Exception as e:
            logger.error(f"Error searching contacts in CRM: {e}")
        
        return []
