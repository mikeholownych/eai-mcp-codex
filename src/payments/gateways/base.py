"""Abstract base payment gateway interface."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime


class PaymentMethod:
    """Payment method data structure."""
    
    def __init__(
        self,
        id: str,
        brand: str,
        last4: str,
        exp_month: int,
        exp_year: int,
        customer_id: str,
        mandate_id: Optional[str] = None
    ):
        self.id = id
        self.brand = brand
        self.last4 = last4
        self.exp_month = exp_month
        self.exp_year = exp_year
        self.customer_id = customer_id
        self.mandate_id = mandate_id


class PaymentIntent:
    """Payment intent data structure."""
    
    def __init__(
        self,
        id: str,
        amount_minor: int,
        currency: str,
        status: str,
        client_secret: str,
        capture_method: str = "automatic",
        confirmation_method: str = "automatic",
        three_ds_status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.amount_minor = amount_minor
        self.currency = currency
        self.status = status
        self.client_secret = client_secret
        self.capture_method = capture_method
        self.confirmation_method = confirmation_method
        self.three_ds_status = three_ds_status
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.utcnow()


class Charge:
    """Charge data structure."""
    
    def __init__(
        self,
        id: str,
        amount_minor: int,
        currency: str,
        status: str,
        receipt_url: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.amount_minor = amount_minor
        self.currency = currency
        self.status = status
        self.receipt_url = receipt_url
        self.created_at = created_at or datetime.utcnow()


class Refund:
    """Refund data structure."""
    
    def __init__(
        self,
        id: str,
        amount_minor: int,
        currency: str,
        status: str,
        reason: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.amount_minor = amount_minor
        self.currency = currency
        self.status = status
        self.reason = reason
        self.created_at = created_at or datetime.utcnow()


class Mandate:
    """Mandate data structure."""
    
    def __init__(
        self,
        id: str,
        scheme: str,
        status: str,
        text_version: str,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.scheme = scheme
        self.status = status
        self.text_version = text_version
        self.created_at = created_at or datetime.utcnow()


class PaymentGatewayError(Exception):
    """Base exception for payment gateway errors."""
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class PaymentGateway(ABC):
    """Abstract base class for payment gateways."""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the payment provider."""
        pass
    
    @abstractmethod
    async def create_customer(self, email: str, country: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a customer in the payment provider.
        
        Args:
            email: Customer email address
            country: Customer country code (ISO 3166-1 alpha-2)
            metadata: Additional customer metadata
            
        Returns:
            Customer ID from the payment provider
            
        Raises:
            PaymentGatewayError: If customer creation fails
        """
        pass
    
    @abstractmethod
    async def create_payment_intent(
        self,
        amount_minor: int,
        currency: str,
        customer_id: str,
        capture_method: str = "automatic",
        confirmation_method: str = "automatic",
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> PaymentIntent:
        """
        Create a payment intent.
        
        Args:
            amount_minor: Amount in minor units (e.g., cents for USD)
            currency: Currency code (ISO 4217)
            customer_id: Customer ID from the payment provider
            capture_method: When to capture the payment (automatic/manual)
            confirmation_method: How to confirm the payment (automatic/manual)
            metadata: Additional payment metadata
            idempotency_key: Idempotency key for duplicate request prevention
            
        Returns:
            PaymentIntent object with client secret
            
        Raises:
            PaymentGatewayError: If payment intent creation fails
        """
        pass
    
    @abstractmethod
    async def confirm_payment_intent(
        self,
        payment_intent_id: str,
        payment_method_id: str,
        idempotency_key: Optional[str] = None
    ) -> PaymentIntent:
        """
        Confirm a payment intent with a payment method.
        
        Args:
            payment_intent_id: Payment intent ID
            payment_method_id: Payment method ID
            idempotency_key: Idempotency key for duplicate request prevention
            
        Returns:
            Updated PaymentIntent object
            
        Raises:
            PaymentGatewayError: If confirmation fails
        """
        pass
    
    @abstractmethod
    async def capture_payment_intent(
        self,
        payment_intent_id: str,
        amount_minor: Optional[int] = None,
        idempotency_key: Optional[str] = None
    ) -> Charge:
        """
        Capture a payment intent (for manual capture).
        
        Args:
            payment_intent_id: Payment intent ID
            amount_minor: Amount to capture (if partial capture)
            idempotency_key: Idempotency key for duplicate request prevention
            
        Returns:
            Charge object
            
        Raises:
            PaymentGatewayError: If capture fails
        """
        pass
    
    @abstractmethod
    async def create_refund(
        self,
        charge_id: str,
        amount_minor: Optional[int] = None,
        reason: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Refund:
        """
        Create a refund for a charge.
        
        Args:
            charge_id: Charge ID to refund
            amount_minor: Amount to refund (if partial refund)
            reason: Reason for refund
            idempotency_key: Idempotency key for duplicate request prevention
            
        Returns:
            Refund object
            
        Raises:
            PaymentGatewayError: If refund creation fails
        """
        pass
    
    @abstractmethod
    async def get_payment_intent(self, payment_intent_id: str) -> PaymentIntent:
        """
        Retrieve a payment intent.
        
        Args:
            payment_intent_id: Payment intent ID
            
        Returns:
            PaymentIntent object
            
        Raises:
            PaymentGatewayError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_charge(self, charge_id: str) -> Charge:
        """
        Retrieve a charge.
        
        Args:
            charge_id: Charge ID
            
        Returns:
            Charge object
            
        Raises:
            PaymentGatewayError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def create_setup_intent(
        self,
        customer_id: str,
        payment_method_types: List[str],
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> str:
        """
        Create a setup intent for saving payment methods.
        
        Args:
            customer_id: Customer ID
            payment_method_types: List of payment method types
            metadata: Additional metadata
            idempotency_key: Idempotency key for duplicate request prevention
            
        Returns:
            Setup intent ID
            
        Raises:
            PaymentGatewayError: If setup intent creation fails
        """
        pass
    
    @abstractmethod
    async def create_mandate(
        self,
        customer_id: str,
        scheme: str,
        text_version: str,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> Mandate:
        """
        Create a mandate for recurring payments.
        
        Args:
            customer_id: Customer ID
            scheme: Mandate scheme (sepa, ach, etc.)
            text_version: Version of mandate text
            metadata: Additional metadata
            idempotency_key: Idempotency key for duplicate request prevention
            
        Returns:
            Mandate object
            
        Raises:
            PaymentGatewayError: If mandate creation fails
        """
        pass
    
    @abstractmethod
    async def get_payment_method_eligibility(
        self,
        payment_method_type: str,
        amount_minor: int,
        currency: str,
        country: str
    ) -> Dict[str, Any]:
        """
        Check if a payment method is eligible for a transaction.
        
        Args:
            payment_method_type: Type of payment method (apple_pay, google_pay, etc.)
            amount_minor: Transaction amount in minor units
            currency: Transaction currency
            country: Customer country
            
        Returns:
            Eligibility information including is_eligible flag
            
        Raises:
            PaymentGatewayError: If eligibility check fails
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of the payment gateway.
        
        Returns:
            Health status information
        """
        pass

    @abstractmethod
    async def create_payment_method(
        self,
        customer_id: str,
        payment_method_type: str,
        payment_method_data: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> PaymentMethod:
        """
        Create a new payment method for a customer.
        
        Args:
            customer_id: Customer ID
            payment_method_type: Type of payment method (card, sepa_debit, etc.)
            payment_method_data: Payment method specific data
            idempotency_key: Idempotency key for the request
            
        Returns:
            PaymentMethod object with the created payment method details
        """
        pass

    @abstractmethod
    async def delete_payment_method(self, payment_method_id: str) -> bool:
        """
        Delete a payment method.
        
        Args:
            payment_method_id: ID of the payment method to delete
            
        Returns:
            True if deletion was successful
        """
        pass
