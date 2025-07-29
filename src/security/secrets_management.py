"""
Advanced Secrets Management System

Provides comprehensive secrets management with:
- Hierarchical secret organization
- Version control and rollback
- Secret rotation and lifecycle management
- Integration with external secret stores (HashiCorp Vault, AWS Secrets Manager)
- Audit logging for all secret operations
- Dynamic secret generation
- Secret sharing with time-limited access
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, Union, Protocol, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import secrets
import hashlib
import base64
from urllib.parse import urlparse

import aiohttp
import jwt
from cryptography.fernet import Fernet
from pydantic import BaseModel, Field, SecretStr, validator
import hvac  # HashiCorp Vault client
import boto3
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

from ..common.redis_client import RedisClient
from .encryption import EncryptionService, EncryptionKey, KeyType
from .audit_logging import AuditLogger, AuditEventType, AuditEventSeverity

logger = logging.getLogger(__name__)


class SecretType(str, Enum):
    """Types of secrets managed by the system"""
    API_KEY = "api_key"
    DATABASE_PASSWORD = "database_password"
    JWT_SECRET = "jwt_secret"
    ENCRYPTION_KEY = "encryption_key"
    CERTIFICATE = "certificate"
    SSH_KEY = "ssh_key"
    OAUTH_TOKEN = "oauth_token"
    WEBHOOK_SECRET = "webhook_secret"
    SERVICE_ACCOUNT = "service_account"
    CUSTOM = "custom"


class SecretProvider(str, Enum):
    """Supported secret storage providers"""
    LOCAL = "local"
    HASHICORP_VAULT = "hashicorp_vault"
    AWS_SECRETS_MANAGER = "aws_secrets_manager"
    AZURE_KEY_VAULT = "azure_key_vault"
    GOOGLE_SECRET_MANAGER = "google_secret_manager"
    KUBERNETES_SECRETS = "kubernetes_secrets"


class SecretAccessLevel(str, Enum):
    """Access levels for secrets"""
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"


@dataclass
class SecretMetadata:
    """Metadata for a secret"""
    secret_id: str
    name: str
    secret_type: SecretType
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    last_modified: datetime = field(default_factory=datetime.utcnow)
    modified_by: Optional[str] = None
    expires_at: Optional[datetime] = None
    rotation_interval_days: Optional[int] = None
    last_rotated: Optional[datetime] = None
    version: int = 1
    is_active: bool = True
    access_count: int = 0
    last_accessed: Optional[datetime] = None


@dataclass
class SecretVersion:
    """Version of a secret"""
    version: int
    value: SecretStr
    created_at: datetime
    created_by: Optional[str] = None
    change_description: Optional[str] = None
    is_active: bool = True


@dataclass
class SecretAccessGrant:
    """Access grant for a secret"""
    grant_id: str
    secret_id: str
    principal: str  # User ID, service account, etc.
    access_level: SecretAccessLevel
    granted_by: str
    granted_at: datetime
    expires_at: Optional[datetime] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True


class SecretStoreProvider(Protocol):
    """Protocol for secret storage providers"""
    async def store_secret(self, secret_id: str, value: str, metadata: SecretMetadata) -> bool:
        ...
    
    async def retrieve_secret(self, secret_id: str) -> Optional[str]:
        ...
    
    async def delete_secret(self, secret_id: str) -> bool:
        ...
    
    async def list_secrets(self, path_prefix: str = "") -> List[str]:
        ...


class LocalSecretProvider:
    """Local encrypted secret storage"""
    
    def __init__(self, encryption_service: EncryptionService, redis_client: Optional[RedisClient] = None):
        self.encryption_service = encryption_service
        self.redis_client = redis_client
        self.local_storage: Dict[str, str] = {}
    
    async def store_secret(self, secret_id: str, value: str, metadata: SecretMetadata) -> bool:
        """Store secret locally with encryption"""
        try:
            # Encrypt the secret value
            encrypted_value = await self.encryption_service.encrypt_field(value, f"secret_{secret_id}")
            
            if self.redis_client:
                await self.redis_client.client.set(f"secret:{secret_id}", encrypted_value)
                if metadata.expires_at:
                    ttl = int((metadata.expires_at - datetime.utcnow()).total_seconds())
                    await self.redis_client.client.expire(f"secret:{secret_id}", ttl)
            else:
                self.local_storage[secret_id] = encrypted_value
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store secret {secret_id}: {e}")
            return False
    
    async def retrieve_secret(self, secret_id: str) -> Optional[str]:
        """Retrieve and decrypt secret"""
        try:
            encrypted_value = None
            
            if self.redis_client:
                encrypted_value = await self.redis_client.client.get(f"secret:{secret_id}")
                if encrypted_value:
                    encrypted_value = encrypted_value.decode()
            else:
                encrypted_value = self.local_storage.get(secret_id)
            
            if encrypted_value:
                decrypted_bytes = await self.encryption_service.decrypt_field(encrypted_value)
                return decrypted_bytes.decode('utf-8')
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_id}: {e}")
            return None
    
    async def delete_secret(self, secret_id: str) -> bool:
        """Delete secret"""
        try:
            if self.redis_client:
                result = await self.redis_client.client.delete(f"secret:{secret_id}")
                return result > 0
            else:
                return self.local_storage.pop(secret_id, None) is not None
        except Exception as e:
            logger.error(f"Failed to delete secret {secret_id}: {e}")
            return False
    
    async def list_secrets(self, path_prefix: str = "") -> List[str]:
        """List secrets with optional path prefix"""
        try:
            if self.redis_client:
                pattern = f"secret:{path_prefix}*"
                keys = await self.redis_client.client.keys(pattern)
                return [key.decode().replace("secret:", "") for key in keys]
            else:
                return [key for key in self.local_storage.keys() if key.startswith(path_prefix)]
        except Exception as e:
            logger.error(f"Failed to list secrets: {e}")
            return []


class HashiCorpVaultProvider:
    """HashiCorp Vault secret storage provider"""
    
    def __init__(self, vault_url: str, vault_token: Optional[str] = None, vault_role_id: Optional[str] = None, vault_secret_id: Optional[str] = None):
        self.vault_url = vault_url
        self.client = hvac.Client(url=vault_url)
        
        # Authenticate with Vault
        if vault_token:
            self.client.token = vault_token
        elif vault_role_id and vault_secret_id:
            auth_response = self.client.auth.approle.login(vault_role_id, vault_secret_id)
            self.client.token = auth_response['auth']['client_token']
        else:
            raise ValueError("Vault authentication credentials required")
    
    async def store_secret(self, secret_id: str, value: str, metadata: SecretMetadata) -> bool:
        """Store secret in Vault"""
        try:
            path = f"secret/{secret_id}"
            secret_data = {
                "value": value,
                "metadata": {
                    "type": metadata.secret_type.value,
                    "description": metadata.description,
                    "tags": metadata.tags,
                    "created_at": metadata.created_at.isoformat(),
                    "expires_at": metadata.expires_at.isoformat() if metadata.expires_at else None
                }
            }
            
            self.client.secrets.kv.v2.create_or_update_secret(
                path=secret_id,
                secret=secret_data
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store secret in Vault {secret_id}: {e}")
            return False
    
    async def retrieve_secret(self, secret_id: str) -> Optional[str]:
        """Retrieve secret from Vault"""
        try:
            response = self.client.secrets.kv.v2.read_secret_version(path=secret_id)
            return response['data']['data'].get('value')
        except Exception as e:
            logger.error(f"Failed to retrieve secret from Vault {secret_id}: {e}")
            return None
    
    async def delete_secret(self, secret_id: str) -> bool:
        """Delete secret from Vault"""
        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(path=secret_id)
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret from Vault {secret_id}: {e}")
            return False
    
    async def list_secrets(self, path_prefix: str = "") -> List[str]:
        """List secrets from Vault"""
        try:
            response = self.client.secrets.kv.v2.list_secrets(path=path_prefix or "/")
            return response['data']['keys']
        except Exception as e:
            logger.error(f"Failed to list secrets from Vault: {e}")
            return []


class AWSSecretsManagerProvider:
    """AWS Secrets Manager provider"""
    
    def __init__(self, region_name: str = "us-east-1"):
        self.client = boto3.client('secretsmanager', region_name=region_name)
    
    async def store_secret(self, secret_id: str, value: str, metadata: SecretMetadata) -> bool:
        """Store secret in AWS Secrets Manager"""
        try:
            secret_data = {
                "value": value,
                "metadata": {
                    "type": metadata.secret_type.value,
                    "description": metadata.description,
                    "tags": metadata.tags
                }
            }
            
            try:
                # Try to update existing secret
                self.client.update_secret(
                    SecretId=secret_id,
                    SecretString=json.dumps(secret_data)
                )
            except self.client.exceptions.ResourceNotFoundException:
                # Create new secret
                self.client.create_secret(
                    Name=secret_id,
                    SecretString=json.dumps(secret_data),
                    Description=metadata.description or f"Secret of type {metadata.secret_type.value}"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store secret in AWS Secrets Manager {secret_id}: {e}")
            return False
    
    async def retrieve_secret(self, secret_id: str) -> Optional[str]:
        """Retrieve secret from AWS Secrets Manager"""
        try:
            response = self.client.get_secret_value(SecretId=secret_id)
            secret_data = json.loads(response['SecretString'])
            return secret_data.get('value')
        except Exception as e:
            logger.error(f"Failed to retrieve secret from AWS Secrets Manager {secret_id}: {e}")
            return None
    
    async def delete_secret(self, secret_id: str) -> bool:
        """Delete secret from AWS Secrets Manager"""
        try:
            self.client.delete_secret(
                SecretId=secret_id,
                ForceDeleteWithoutRecovery=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret from AWS Secrets Manager {secret_id}: {e}")
            return False
    
    async def list_secrets(self, path_prefix: str = "") -> List[str]:
        """List secrets from AWS Secrets Manager"""
        try:
            paginator = self.client.get_paginator('list_secrets')
            secrets = []
            
            for page in paginator.paginate():
                for secret in page['SecretList']:
                    name = secret['Name']
                    if name.startswith(path_prefix):
                        secrets.append(name)
            
            return secrets
        except Exception as e:
            logger.error(f"Failed to list secrets from AWS Secrets Manager: {e}")
            return []


class SecretsManager:
    """Main secrets management service"""
    
    def __init__(self, 
                 provider: SecretStoreProvider,
                 encryption_service: EncryptionService,
                 audit_logger: AuditLogger,
                 redis_client: Optional[RedisClient] = None):
        self.provider = provider
        self.encryption_service = encryption_service
        self.audit_logger = audit_logger
        self.redis_client = redis_client
        
        # In-memory caches
        self.metadata_cache: Dict[str, SecretMetadata] = {}
        self.version_cache: Dict[str, List[SecretVersion]] = {}
        self.access_grants: Dict[str, List[SecretAccessGrant]] = {}
        
        # Secret generators
        self.generators: Dict[SecretType, Callable[[], str]] = {
            SecretType.API_KEY: self._generate_api_key,
            SecretType.JWT_SECRET: self._generate_jwt_secret,
            SecretType.WEBHOOK_SECRET: self._generate_webhook_secret,
        }
    
    async def create_secret(self, 
                          name: str,
                          value: str,
                          secret_type: SecretType,
                          description: Optional[str] = None,
                          tags: Optional[List[str]] = None,
                          expires_at: Optional[datetime] = None,
                          rotation_interval_days: Optional[int] = None,
                          created_by: Optional[str] = None) -> str:
        """Create a new secret"""
        
        secret_id = self._generate_secret_id(name)
        
        metadata = SecretMetadata(
            secret_id=secret_id,
            name=name,
            secret_type=secret_type,
            description=description,
            tags=tags or [],
            expires_at=expires_at,
            rotation_interval_days=rotation_interval_days,
            created_by=created_by
        )
        
        # Store secret
        success = await self.provider.store_secret(secret_id, value, metadata)
        if not success:
            raise ValueError(f"Failed to store secret: {name}")
        
        # Store metadata
        await self._store_metadata(metadata)
        
        # Create first version
        version = SecretVersion(
            version=1,
            value=SecretStr(value),
            created_at=datetime.utcnow(),
            created_by=created_by,
            change_description="Initial version"
        )
        await self._store_version(secret_id, version)
        
        # Audit log
        self.audit_logger.log_event(
            AuditEventType.ADMIN_ACTION,
            f"Secret created: {name}",
            user_id=created_by,
            resource=secret_id,
            action="create_secret",
            details={
                "secret_type": secret_type.value,
                "has_expires": expires_at is not None,
                "has_rotation": rotation_interval_days is not None
            }
        )
        
        logger.info(f"Created secret: {name} ({secret_id})")
        return secret_id
    
    async def get_secret(self, secret_id: str, version: Optional[int] = None, requesting_user: Optional[str] = None) -> Optional[str]:
        """Retrieve a secret value"""
        
        # Check access permissions
        if not await self._check_access(secret_id, requesting_user, SecretAccessLevel.READ_ONLY):
            self.audit_logger.log_event(
                AuditEventType.ACCESS_DENIED,
                f"Secret access denied: {secret_id}",
                user_id=requesting_user,
                resource=secret_id,
                action="get_secret",
                severity=AuditEventSeverity.HIGH
            )
            raise PermissionError(f"Access denied to secret: {secret_id}")
        
        # Get specific version if requested
        if version:
            versions = await self._get_versions(secret_id)
            for v in versions:
                if v.version == version:
                    value = v.value.get_secret_value()
                    break
            else:
                return None
        else:
            # Get current version
            value = await self.provider.retrieve_secret(secret_id)
        
        if value:
            # Update access tracking
            await self._update_access_tracking(secret_id, requesting_user)
            
            # Audit log
            self.audit_logger.log_event(
                AuditEventType.DATA_READ,
                f"Secret accessed: {secret_id}",
                user_id=requesting_user,
                resource=secret_id,
                action="get_secret",
                details={"version": version} if version else {}
            )
        
        return value
    
    async def update_secret(self, secret_id: str, new_value: str, change_description: Optional[str] = None, updated_by: Optional[str] = None) -> int:
        """Update a secret value and create new version"""
        
        # Check access permissions
        if not await self._check_access(secret_id, updated_by, SecretAccessLevel.READ_WRITE):
            raise PermissionError(f"Access denied to update secret: {secret_id}")
        
        # Get current metadata
        metadata = await self._get_metadata(secret_id)
        if not metadata:
            raise ValueError(f"Secret not found: {secret_id}")
        
        # Store new value
        success = await self.provider.store_secret(secret_id, new_value, metadata)
        if not success:
            raise ValueError(f"Failed to update secret: {secret_id}")
        
        # Create new version
        versions = await self._get_versions(secret_id)
        new_version_number = max([v.version for v in versions], default=0) + 1
        
        version = SecretVersion(
            version=new_version_number,
            value=SecretStr(new_value),
            created_at=datetime.utcnow(),
            created_by=updated_by,
            change_description=change_description
        )
        await self._store_version(secret_id, version)
        
        # Update metadata
        metadata.last_modified = datetime.utcnow()
        metadata.modified_by = updated_by
        metadata.version = new_version_number
        await self._store_metadata(metadata)
        
        # Audit log
        self.audit_logger.log_event(
            AuditEventType.DATA_UPDATE,
            f"Secret updated: {secret_id}",
            user_id=updated_by,
            resource=secret_id,
            action="update_secret",
            details={
                "new_version": new_version_number,
                "change_description": change_description
            }
        )
        
        logger.info(f"Updated secret: {secret_id} to version {new_version_number}")
        return new_version_number
    
    async def rotate_secret(self, secret_id: str, rotated_by: Optional[str] = None) -> str:
        """Rotate a secret (generate new value)"""
        
        metadata = await self._get_metadata(secret_id)
        if not metadata:
            raise ValueError(f"Secret not found: {secret_id}")
        
        # Generate new value based on secret type
        generator = self.generators.get(metadata.secret_type)
        if not generator:
            raise ValueError(f"Cannot auto-rotate secret of type: {metadata.secret_type}")
        
        new_value = generator()
        
        # Update secret
        await self.update_secret(secret_id, new_value, "Automatic rotation", rotated_by)
        
        # Update rotation tracking
        metadata.last_rotated = datetime.utcnow()
        await self._store_metadata(metadata)
        
        # Audit log
        self.audit_logger.log_event(
            AuditEventType.ADMIN_ACTION,
            f"Secret rotated: {secret_id}",
            user_id=rotated_by,
            resource=secret_id,
            action="rotate_secret",
            severity=AuditEventSeverity.MEDIUM
        )
        
        return new_value
    
    async def delete_secret(self, secret_id: str, deleted_by: Optional[str] = None) -> bool:
        """Delete a secret"""
        
        # Check access permissions
        if not await self._check_access(secret_id, deleted_by, SecretAccessLevel.ADMIN):
            raise PermissionError(f"Access denied to delete secret: {secret_id}")
        
        # Delete from provider
        success = await self.provider.delete_secret(secret_id)
        if not success:
            return False
        
        # Clean up metadata and versions
        await self._delete_metadata(secret_id)
        await self._delete_versions(secret_id)
        
        # Audit log
        self.audit_logger.log_event(
            AuditEventType.DATA_DELETE,
            f"Secret deleted: {secret_id}",
            user_id=deleted_by,
            resource=secret_id,
            action="delete_secret",
            severity=AuditEventSeverity.HIGH
        )
        
        logger.warning(f"Deleted secret: {secret_id}")
        return True
    
    async def grant_access(self, 
                         secret_id: str,
                         principal: str,
                         access_level: SecretAccessLevel,
                         granted_by: str,
                         expires_at: Optional[datetime] = None,
                         conditions: Optional[Dict[str, Any]] = None) -> str:
        """Grant access to a secret"""
        
        grant_id = f"grant_{secrets.token_hex(16)}"
        grant = SecretAccessGrant(
            grant_id=grant_id,
            secret_id=secret_id,
            principal=principal,
            access_level=access_level,
            granted_by=granted_by,
            granted_at=datetime.utcnow(),
            expires_at=expires_at,
            conditions=conditions or {}
        )
        
        # Store grant
        if secret_id not in self.access_grants:
            self.access_grants[secret_id] = []
        self.access_grants[secret_id].append(grant)
        
        # Store in Redis if available
        if self.redis_client:
            grant_data = {
                "grant_id": grant_id,
                "secret_id": secret_id,
                "principal": principal,
                "access_level": access_level.value,
                "granted_by": granted_by,
                "granted_at": grant.granted_at.isoformat(),
                "expires_at": grant.expires_at.isoformat() if grant.expires_at else None,
                "conditions": grant.conditions
            }
            await self.redis_client.client.set(f"secret_grant:{grant_id}", json.dumps(grant_data))
            
            if expires_at:
                ttl = int((expires_at - datetime.utcnow()).total_seconds())
                await self.redis_client.client.expire(f"secret_grant:{grant_id}", ttl)
        
        # Audit log
        self.audit_logger.log_event(
            AuditEventType.ADMIN_ACTION,
            f"Secret access granted: {secret_id} to {principal}",
            user_id=granted_by,
            resource=secret_id,
            action="grant_access",
            details={
                "principal": principal,
                "access_level": access_level.value,
                "expires_at": expires_at.isoformat() if expires_at else None
            }
        )
        
        return grant_id
    
    async def list_secrets(self, 
                         path_prefix: str = "",
                         secret_type: Optional[SecretType] = None,
                         tags: Optional[List[str]] = None,
                         requesting_user: Optional[str] = None) -> List[SecretMetadata]:
        """List secrets with optional filtering"""
        
        # Get all secret IDs
        secret_ids = await self.provider.list_secrets(path_prefix)
        
        # Filter and collect metadata
        results = []
        for secret_id in secret_ids:
            # Check access
            if not await self._check_access(secret_id, requesting_user, SecretAccessLevel.READ_ONLY):
                continue
            
            metadata = await self._get_metadata(secret_id)
            if not metadata:
                continue
            
            # Apply filters
            if secret_type and metadata.secret_type != secret_type:
                continue
            
            if tags and not any(tag in metadata.tags for tag in tags):
                continue
            
            results.append(metadata)
        
        return results
    
    @asynccontextmanager
    async def temporary_secret(self, value: str, ttl_seconds: int = 3600):
        """Create a temporary secret that auto-expires"""
        temp_id = f"temp_{secrets.token_hex(16)}"
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        
        secret_id = await self.create_secret(
            name=temp_id,
            value=value,
            secret_type=SecretType.CUSTOM,
            description="Temporary secret",
            expires_at=expires_at
        )
        
        try:
            yield secret_id
        finally:
            # Clean up
            await self.delete_secret(secret_id)
    
    # Private helper methods
    
    def _generate_secret_id(self, name: str) -> str:
        """Generate unique secret ID"""
        timestamp = int(datetime.utcnow().timestamp())
        name_hash = hashlib.sha256(name.encode()).hexdigest()[:8]
        return f"secret_{timestamp}_{name_hash}"
    
    def _generate_api_key(self) -> str:
        """Generate API key"""
        return f"ak_{secrets.token_urlsafe(32)}"
    
    def _generate_jwt_secret(self) -> str:
        """Generate JWT secret"""
        return secrets.token_urlsafe(64)
    
    def _generate_webhook_secret(self) -> str:
        """Generate webhook secret"""
        return secrets.token_hex(32)
    
    async def _check_access(self, secret_id: str, user_id: Optional[str], required_level: SecretAccessLevel) -> bool:
        """Check if user has required access to secret"""
        if not user_id:
            return False
        
        # Get access grants for this secret
        grants = self.access_grants.get(secret_id, [])
        
        # Load from Redis if available
        if self.redis_client:
            grant_keys = await self.redis_client.client.keys(f"secret_grant:*")
            for key in grant_keys:
                grant_data = await self.redis_client.client.get(key)
                if grant_data:
                    grant_info = json.loads(grant_data)
                    if grant_info["secret_id"] == secret_id:
                        grant = SecretAccessGrant(
                            grant_id=grant_info["grant_id"],
                            secret_id=grant_info["secret_id"],
                            principal=grant_info["principal"],
                            access_level=SecretAccessLevel(grant_info["access_level"]),
                            granted_by=grant_info["granted_by"],
                            granted_at=datetime.fromisoformat(grant_info["granted_at"]),
                            expires_at=datetime.fromisoformat(grant_info["expires_at"]) if grant_info.get("expires_at") else None,
                            conditions=grant_info.get("conditions", {})
                        )
                        grants.append(grant)
        
        # Check grants
        for grant in grants:
            if not grant.is_active:
                continue
            
            if grant.expires_at and grant.expires_at < datetime.utcnow():
                continue
            
            if grant.principal == user_id:
                # Check access level hierarchy
                levels = [SecretAccessLevel.READ_ONLY, SecretAccessLevel.READ_WRITE, SecretAccessLevel.ADMIN]
                if levels.index(grant.access_level) >= levels.index(required_level):
                    return True
        
        return False
    
    async def _store_metadata(self, metadata: SecretMetadata):
        """Store secret metadata"""
        self.metadata_cache[metadata.secret_id] = metadata
        
        if self.redis_client:
            metadata_dict = {
                "secret_id": metadata.secret_id,
                "name": metadata.name,
                "secret_type": metadata.secret_type.value,
                "description": metadata.description,
                "tags": metadata.tags,
                "created_at": metadata.created_at.isoformat(),
                "created_by": metadata.created_by,
                "last_modified": metadata.last_modified.isoformat(),
                "modified_by": metadata.modified_by,
                "expires_at": metadata.expires_at.isoformat() if metadata.expires_at else None,
                "rotation_interval_days": metadata.rotation_interval_days,
                "last_rotated": metadata.last_rotated.isoformat() if metadata.last_rotated else None,
                "version": metadata.version,
                "is_active": metadata.is_active,
                "access_count": metadata.access_count,
                "last_accessed": metadata.last_accessed.isoformat() if metadata.last_accessed else None
            }
            await self.redis_client.client.set(f"secret_metadata:{metadata.secret_id}", json.dumps(metadata_dict))
    
    async def _get_metadata(self, secret_id: str) -> Optional[SecretMetadata]:
        """Get secret metadata"""
        # Check cache first
        if secret_id in self.metadata_cache:
            return self.metadata_cache[secret_id]
        
        # Load from Redis
        if self.redis_client:
            metadata_data = await self.redis_client.client.get(f"secret_metadata:{secret_id}")
            if metadata_data:
                data = json.loads(metadata_data)
                metadata = SecretMetadata(
                    secret_id=data["secret_id"],
                    name=data["name"],
                    secret_type=SecretType(data["secret_type"]),
                    description=data.get("description"),
                    tags=data.get("tags", []),
                    created_at=datetime.fromisoformat(data["created_at"]),
                    created_by=data.get("created_by"),
                    last_modified=datetime.fromisoformat(data["last_modified"]),
                    modified_by=data.get("modified_by"),
                    expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
                    rotation_interval_days=data.get("rotation_interval_days"),
                    last_rotated=datetime.fromisoformat(data["last_rotated"]) if data.get("last_rotated") else None,
                    version=data.get("version", 1),
                    is_active=data.get("is_active", True),
                    access_count=data.get("access_count", 0),
                    last_accessed=datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None
                )
                self.metadata_cache[secret_id] = metadata
                return metadata
        
        return None
    
    async def _store_version(self, secret_id: str, version: SecretVersion):
        """Store secret version"""
        if secret_id not in self.version_cache:
            self.version_cache[secret_id] = []
        self.version_cache[secret_id].append(version)
        
        if self.redis_client:
            version_data = {
                "version": version.version,
                "value": version.value.get_secret_value(),
                "created_at": version.created_at.isoformat(),
                "created_by": version.created_by,
                "change_description": version.change_description,
                "is_active": version.is_active
            }
            await self.redis_client.client.hset(
                f"secret_versions:{secret_id}",
                str(version.version),
                json.dumps(version_data)
            )
    
    async def _get_versions(self, secret_id: str) -> List[SecretVersion]:
        """Get all versions of a secret"""
        # Check cache first
        if secret_id in self.version_cache:
            return self.version_cache[secret_id]
        
        versions = []
        
        if self.redis_client:
            version_data = await self.redis_client.client.hgetall(f"secret_versions:{secret_id}")
            for version_num, data in version_data.items():
                data_dict = json.loads(data)
                version = SecretVersion(
                    version=int(version_num),
                    value=SecretStr(data_dict["value"]),
                    created_at=datetime.fromisoformat(data_dict["created_at"]),
                    created_by=data_dict.get("created_by"),
                    change_description=data_dict.get("change_description"),
                    is_active=data_dict.get("is_active", True)
                )
                versions.append(version)
        
        # Sort by version number
        versions.sort(key=lambda v: v.version)
        self.version_cache[secret_id] = versions
        return versions
    
    async def _update_access_tracking(self, secret_id: str, user_id: Optional[str]):
        """Update access tracking for a secret"""
        metadata = await self._get_metadata(secret_id)
        if metadata:
            metadata.access_count += 1
            metadata.last_accessed = datetime.utcnow()
            await self._store_metadata(metadata)
    
    async def _delete_metadata(self, secret_id: str):
        """Delete secret metadata"""
        self.metadata_cache.pop(secret_id, None)
        
        if self.redis_client:
            await self.redis_client.client.delete(f"secret_metadata:{secret_id}")
    
    async def _delete_versions(self, secret_id: str):
        """Delete secret versions"""
        self.version_cache.pop(secret_id, None)
        
        if self.redis_client:
            await self.redis_client.client.delete(f"secret_versions:{secret_id}")


# Factory functions

async def create_secrets_manager(
    provider_type: SecretProvider,
    encryption_service: EncryptionService,
    audit_logger: AuditLogger,
    redis_client: Optional[RedisClient] = None,
    **provider_kwargs
) -> SecretsManager:
    """Create secrets manager with specified provider"""
    
    if provider_type == SecretProvider.LOCAL:
        provider = LocalSecretProvider(encryption_service, redis_client)
    elif provider_type == SecretProvider.HASHICORP_VAULT:
        provider = HashiCorpVaultProvider(**provider_kwargs)
    elif provider_type == SecretProvider.AWS_SECRETS_MANAGER:
        provider = AWSSecretsManagerProvider(**provider_kwargs)
    else:
        raise ValueError(f"Unsupported provider type: {provider_type}")
    
    return SecretsManager(provider, encryption_service, audit_logger, redis_client)


# Utility functions for common secret operations

async def generate_database_password(secrets_manager: SecretsManager, db_name: str, length: int = 32) -> str:
    """Generate and store a database password"""
    import string
    
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(chars) for _ in range(length))
    
    secret_id = await secrets_manager.create_secret(
        name=f"db_password_{db_name}",
        value=password,
        secret_type=SecretType.DATABASE_PASSWORD,
        description=f"Database password for {db_name}",
        rotation_interval_days=90
    )
    
    return secret_id


async def create_service_api_key(secrets_manager: SecretsManager, service_name: str) -> str:
    """Create API key for a service"""
    api_key = f"sk_{secrets.token_urlsafe(32)}"
    
    secret_id = await secrets_manager.create_secret(
        name=f"api_key_{service_name}",
        value=api_key,
        secret_type=SecretType.API_KEY,
        description=f"API key for {service_name}",
        tags=["api", "service", service_name]
    )
    
    return secret_id