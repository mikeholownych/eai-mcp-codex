"""Payment service for high-level payment operations."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from uuid import uuid4

from .gateways.factory import PaymentGatewayFactory, get_best_gateway
from .gateways.base import PaymentGateway, PaymentIntent, Charge, Refund, Mandate, PaymentMethod
from .models import Customer, PaymentIntent as DBPaymentIntent, Charge as DBCharge, Refund as DBRefund
from .database import get_db_session
from .utils import create_audit_log

logger = logging.getLogger(__name__)


class PaymentService:
    """High-level payment service for managing payment operations."""
    
    def __init__(self):
        self.gateway_factory = PaymentGatewayFactory()
    
    async def create_customer(
        self,
        email: str,
        country: str,
        metadata: Optional[Dict[str, Any]] = None,
        preferred_gateway: Optional[str] = None
    ) -> Tuple[str, str]:
        """Create a customer in the payment system and gateway."""
        try:
            # Create customer in database
            db_session = get_db_session()
            
            # Check if customer already exists
            existing_customer = db_session.query(Customer).filter(
                Customer.email == email
            ).first()
            
            if existing_customer:
                logger.info("Customer already exists: %s", existing_customer.id)
                return str(existing_customer.id), existing_customer.external_id
            
            # Create customer in payment gateway
            if preferred_gateway:
                gateway = self.gateway_factory.get_gateway(preferred_gateway)
            else:
                # Use best gateway based on country
                gateway = get_best_gateway(country, 0, "USD")
            
            external_id = await gateway.create_customer(email, country, metadata)
            
            # Create customer in database
            customer = Customer(
                external_id=external_id,
                email=email,
                country=country
            )
            
            db_session.add(customer)
            db_session.commit()
            
            # Create audit log
            await create_audit_log(
                db_session,
                actor="system",
                action="customer_created",
                resource_type="customer",
                resource_id=customer.id,
                metadata={"gateway": gateway.provider_name, "external_id": external_id}
            )
            
            logger.info("Created customer %s with external ID %s", customer.id, external_id)
            return str(customer.id), external_id
            
        except Exception as e:
            logger.error("Failed to create customer: %s", str(e))
            raise
    
    async def create_payment_intent(
        self,
        customer_id: str,
        amount_minor: int,
        currency: str,
        capture_method: str = "automatic",
        confirmation_method: str = "automatic",
        metadata: Optional[Dict[str, Any]] = None,
        preferred_gateway: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Tuple[PaymentIntent, str]:
        """Create a payment intent."""
        try:
            db_session = get_db_session()
            
            # Get customer
            customer = db_session.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                raise ValueError(f"Customer not found: {customer_id}")
            
            # Generate idempotency key if not provided
            if not idempotency_key:
                idempotency_key = str(uuid4())
            
            # Check for existing payment intent with same idempotency key
            existing_intent = db_session.query(DBPaymentIntent).filter(
                DBPaymentIntent.idempotency_key == idempotency_key
            ).first()
            
            if existing_intent:
                logger.info("Payment intent already exists with idempotency key: %s", idempotency_key)
                # Return existing intent
                gateway = self.gateway_factory.get_gateway_by_provider(existing_intent.provider)
                return await gateway.get_payment_intent(existing_intent.provider_id), existing_intent.id
            
            # Get best gateway
            if preferred_gateway:
                gateway = self.gateway_factory.get_gateway(preferred_gateway)
            else:
                gateway = get_best_gateway(customer.country, amount_minor, currency)
            
            # Create payment intent in gateway
            payment_intent = await gateway.create_payment_intent(
                amount_minor=amount_minor,
                currency=currency,
                customer_id=customer.external_id,
                capture_method=capture_method,
                confirmation_method=confirmation_method,
                metadata=metadata,
                idempotency_key=idempotency_key
            )
            
            # Create payment intent in database
            db_payment_intent = DBPaymentIntent(
                provider_id=payment_intent.id,
                customer_id=customer_id,
                amount_minor=amount_minor,
                currency=currency,
                status=payment_intent.status,
                capture_method=capture_method,
                confirmation_method=confirmation_method,
                three_ds_status=payment_intent.three_ds_status,
                idempotency_key=idempotency_key,
                metadata=metadata or {},
                provider=gateway.provider_name
            )
            
            db_session.add(db_payment_intent)
            db_session.commit()
            
            # Create audit log
            await create_audit_log(
                db_session,
                actor="system",
                action="payment_intent_created",
                resource_type="payment_intent",
                resource_id=db_payment_intent.id,
                metadata={
                    "gateway": gateway.provider_name,
                    "amount": amount_minor,
                    "currency": currency
                }
            )
            
            logger.info("Created payment intent %s via %s", db_payment_intent.id, gateway.provider_name)
            return payment_intent, str(db_payment_intent.id)
            
        except Exception as e:
            logger.error("Failed to create payment intent: %s", str(e))
            raise
    
    async def confirm_payment_intent(
        self,
        payment_intent_id: str,
        payment_method_id: str,
        idempotency_key: Optional[str] = None
    ) -> PaymentIntent:
        """Confirm a payment intent."""
        try:
            db_session = get_db_session()
            
            # Get payment intent from database
            db_payment_intent = db_session.query(DBPaymentIntent).filter(
                DBPaymentIntent.id == payment_intent_id
            ).first()
            
            if not db_payment_intent:
                raise ValueError(f"Payment intent not found: {payment_intent_id}")
            
            # Get gateway
            gateway = self.gateway_factory.get_gateway_by_provider(db_payment_intent.provider)
            
            # Confirm payment intent
            payment_intent = await gateway.confirm_payment_intent(
                db_payment_intent.provider_id,
                payment_method_id,
                idempotency_key
            )
            
            # Update database
            db_payment_intent.status = payment_intent.status
            db_payment_intent.three_ds_status = payment_intent.three_ds_status
            db_payment_intent.updated_at = datetime.utcnow()
            
            db_session.commit()
            
            # Create audit log
            await create_audit_log(
                db_session,
                actor="system",
                action="payment_intent_confirmed",
                resource_type="payment_intent",
                resource_id=payment_intent_id,
                metadata={"payment_method_id": payment_method_id}
            )
            
            logger.info("Confirmed payment intent %s", payment_intent_id)
            return payment_intent
            
        except Exception as e:
            logger.error("Failed to confirm payment intent %s: %s", payment_intent_id, str(e))
            raise
    
    async def capture_payment_intent(
        self,
        payment_intent_id: str,
        amount_minor: Optional[int] = None,
        idempotency_key: Optional[str] = None
    ) -> Tuple[Charge, str]:
        """Capture a payment intent."""
        try:
            db_session = get_db_session()
            
            # Get payment intent from database
            db_payment_intent = db_session.query(DBPaymentIntent).filter(
                DBPaymentIntent.id == payment_intent_id
            ).first()
            
            if not db_payment_intent:
                raise ValueError(f"Payment intent not found: {payment_intent_id}")
            
            # Get gateway
            gateway = self.gateway_factory.get_gateway_by_provider(db_payment_intent.provider)
            
            # Capture payment intent
            charge = await gateway.capture_payment_intent(
                db_payment_intent.provider_id,
                amount_minor,
                idempotency_key
            )
            
            # Create charge in database
            db_charge = DBCharge(
                payment_intent_id=payment_intent_id,
                provider_charge_id=charge.id,
                status=charge.status,
                receipt_url=charge.receipt_url
            )
            
            db_session.add(db_charge)
            
            # Update payment intent status
            db_payment_intent.status = "succeeded"
            db_payment_intent.updated_at = datetime.utcnow()
            
            db_session.commit()
            
            # Create audit log
            await create_audit_log(
                db_session,
                actor="system",
                action="payment_intent_captured",
                resource_type="payment_intent",
                resource_id=payment_intent_id,
                metadata={
                    "charge_id": charge.id,
                    "amount": charge.amount_minor,
                    "currency": charge.currency
                }
            )
            
            logger.info("Captured payment intent %s, charge %s", payment_intent_id, charge.id)
            return charge, str(db_charge.id)
            
        except Exception as e:
            logger.error("Failed to capture payment intent %s: %s", payment_intent_id, str(e))
            raise
    
    async def create_refund(
        self,
        charge_id: str,
        amount_minor: Optional[int] = None,
        reason: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Tuple[Refund, str]:
        """Create a refund for a charge."""
        try:
            db_session = get_db_session()
            
            # Get charge from database
            db_charge = db_session.query(DBCharge).filter(
                DBCharge.id == charge_id
            ).first()
            
            if not db_charge:
                raise ValueError(f"Charge not found: {charge_id}")
            
            # Get payment intent to determine gateway
            db_payment_intent = db_session.query(DBPaymentIntent).filter(
                DBPaymentIntent.id == db_charge.payment_intent_id
            ).first()
            
            if not db_payment_intent:
                raise ValueError(f"Payment intent not found for charge: {charge_id}")
            
            # Get gateway
            gateway = self.gateway_factory.get_gateway_by_provider(db_payment_intent.provider)
            
            # Create refund
            refund = await gateway.create_refund(
                db_charge.provider_charge_id,
                amount_minor,
                reason,
                idempotency_key
            )
            
            # Create refund in database
            db_refund = DBRefund(
                charge_id=charge_id,
                provider_refund_id=refund.id,
                amount_minor=refund.amount_minor,
                status=refund.status,
                reason=refund.reason
            )
            
            db_session.add(db_refund)
            db_session.commit()
            
            # Create audit log
            await create_audit_log(
                db_session,
                actor="system",
                action="refund_created",
                resource_type="charge",
                resource_id=charge_id,
                metadata={
                    "refund_id": refund.id,
                    "amount": refund.amount_minor,
                    "reason": refund.reason
                }
            )
            
            logger.info("Created refund %s for charge %s", refund.id, charge_id)
            return refund, str(db_refund.id)
            
        except Exception as e:
            logger.error("Failed to create refund for charge %s: %s", charge_id, str(e))
            raise
    
    async def get_payment_intent(self, payment_intent_id: str) -> PaymentIntent:
        """Get a payment intent."""
        try:
            db_session = get_db_session()
            
            # Get payment intent from database
            db_payment_intent = db_session.query(DBPaymentIntent).filter(
                DBPaymentIntent.id == payment_intent_id
            ).first()
            
            if not db_payment_intent:
                raise ValueError(f"Payment intent not found: {payment_intent_id}")
            
            # Get gateway
            gateway = self.gateway_factory.get_gateway_by_provider(db_payment_intent.provider)
            
            # Get payment intent from gateway
            return await gateway.get_payment_intent(db_payment_intent.provider_id)
            
        except Exception as e:
            logger.error("Failed to get payment intent %s: %s", payment_intent_id, str(e))
            raise
    
    async def get_charge(self, charge_id: str) -> Charge:
        """Get a charge."""
        try:
            db_session = get_db_session()
            
            # Get charge from database
            db_charge = db_session.query(DBCharge).filter(
                DBCharge.id == charge_id
            ).first()
            
            if not db_charge:
                raise ValueError(f"Charge not found: {charge_id}")
            
            # Get payment intent to determine gateway
            db_payment_intent = db_session.query(DBPaymentIntent).filter(
                DBPaymentIntent.id == db_charge.payment_intent_id
            ).first()
            
            if not db_payment_intent:
                raise ValueError(f"Payment intent not found for charge: {charge_id}")
            
            # Get gateway
            gateway = self.gateway_factory.get_gateway_by_provider(db_payment_intent.provider)
            
            # Get charge from gateway
            return await gateway.get_charge(db_charge.provider_charge_id)
            
        except Exception as e:
            logger.error("Failed to get charge %s: %s", charge_id, str(e))
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all payment gateways."""
        try:
            health_status = await self.gateway_factory.health_check_all()
            
            overall_status = "healthy"
            if any(status["status"] != "healthy" for status in health_status.values()):
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "gateways": health_status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Health check failed: %s", str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_payment_method_eligibility(
        self,
        payment_method_type: str,
        amount_minor: int,
        currency: str,
        country: str
    ) -> Dict[str, Any]:
        """Check payment method eligibility across all gateways."""
        try:
            # Get best gateway for this payment method
            gateway = self.gateway_factory.get_gateway_by_payment_method(
                payment_method_type, country
            )
            
            if not gateway:
                return {
                    "is_eligible": False,
                    "requirements": [],
                    "restrictions": [f"No gateway supports {payment_method_type} in {country}"]
                }
            
            # Check eligibility
            return await gateway.get_payment_method_eligibility(
                payment_method_type, amount_minor, currency, country
            )
            
        except Exception as e:
            logger.error("Failed to check payment method eligibility: %s", str(e))
            return {
                "is_eligible": False,
                "requirements": [],
                "restrictions": [f"Eligibility check failed: {str(e)}"]
            }

    async def create_setup_intent(
        self,
        customer_id: str,
        payment_method_types: List[str],
        metadata: Optional[Dict[str, Any]] = None,
        preferred_gateway: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Tuple[str, str]:
        """Create a setup intent for saving payment methods."""
        try:
            db_session = get_db_session()
            
            # Get customer
            customer = db_session.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                raise ValueError(f"Customer not found: {customer_id}")
            
            # Generate idempotency key if not provided
            if not idempotency_key:
                idempotency_key = str(uuid4())
            
            # Get best gateway
            if preferred_gateway:
                gateway = self.gateway_factory.get_gateway(preferred_gateway)
            else:
                gateway = get_best_gateway(customer.country, 0, "USD")
            
            # Create setup intent in gateway
            setup_intent_id = await gateway.create_setup_intent(
                customer_id=customer.external_id,
                payment_method_types=payment_method_types,
                metadata=metadata,
                idempotency_key=idempotency_key
            )
            
            # Create setup intent in database
            from .models import SetupIntent
            db_setup_intent = SetupIntent(
                provider_id=setup_intent_id,
                customer_id=customer_id,
                status="requires_payment_method",
                client_secret=setup_intent_id,  # Gateway will provide actual client secret
                payment_method_types=payment_method_types,
                metadata=metadata or {}
            )
            
            db_session.add(db_setup_intent)
            db_session.commit()
            
            # Create audit log
            await create_audit_log(
                db_session,
                actor="system",
                action="setup_intent_created",
                resource_type="setup_intent",
                resource_id=db_setup_intent.id,
                metadata={
                    "gateway": gateway.provider_name,
                    "payment_method_types": payment_method_types
                }
            )
            
            logger.info("Created setup intent %s via %s", db_setup_intent.id, gateway.provider_name)
            return setup_intent_id, str(db_setup_intent.id)
            
        except Exception as e:
            logger.error("Failed to create setup intent: %s", str(e))
            raise

    async def create_payment_method(
        self,
        customer_id: str,
        payment_method_type: str,
        payment_method_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        preferred_gateway: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Tuple[str, str]:
        """Create a payment method for a customer."""
        try:
            db_session = get_db_session()
            
            # Get customer
            customer = db_session.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                raise ValueError(f"Customer not found: {customer_id}")
            
            # Generate idempotency key if not provided
            if not idempotency_key:
                idempotency_key = str(uuid4())
            
            # Get best gateway
            if preferred_gateway:
                gateway = self.gateway_factory.get_gateway(preferred_gateway)
            else:
                gateway = get_best_gateway(customer.country, 0, "USD")
            
            # Create payment method in gateway
            payment_method = await gateway.create_payment_method(
                customer_id=customer.external_id,
                payment_method_type=payment_method_type,
                payment_method_data=payment_method_data,
                idempotency_key=idempotency_key
            )
            
            # Create payment method in database
            from .models import PaymentMethod as DBPaymentMethod
            db_payment_method = DBPaymentMethod(
                provider=gateway.provider_name,
                pm_token=payment_method.id,
                brand=payment_method.brand,
                last4=payment_method.last4,
                exp_month=payment_method.exp_month,
                exp_year=payment_method.exp_year,
                customer_id=customer_id,
                mandate_id=payment_method.mandate_id,
                is_default=False,
                metadata=metadata or {}
            )
            
            db_session.add(db_payment_method)
            db_session.commit()
            
            # Create audit log
            await create_audit_log(
                db_session,
                actor="system",
                action="payment_method_created",
                resource_type="payment_method",
                resource_id=db_payment_method.id,
                metadata={
                    "gateway": gateway.provider_name,
                    "payment_method_type": payment_method_type,
                    "brand": payment_method.brand
                }
            )
            
            logger.info("Created payment method %s via %s", db_payment_method.id, gateway.provider_name)
            return payment_method.id, str(db_payment_method.id)
            
        except Exception as e:
            logger.error("Failed to create payment method: %s", str(e))
            raise

    async def delete_payment_method(
        self,
        payment_method_id: str
    ) -> bool:
        """Delete a payment method."""
        try:
            db_session = get_db_session()
            
            # Get payment method from database
            from .models import PaymentMethod as DBPaymentMethod
            db_payment_method = db_session.query(DBPaymentMethod).filter(
                DBPaymentMethod.id == payment_method_id
            ).first()
            
            if not db_payment_method:
                raise ValueError(f"Payment method not found: {payment_method_id}")
            
            # Get gateway
            gateway = self.gateway_factory.get_gateway_by_provider(db_payment_method.provider)
            
            # Delete payment method in gateway
            success = await gateway.delete_payment_method(db_payment_method.pm_token)
            
            if success:
                # Delete from database
                db_session.delete(db_payment_method)
                db_session.commit()
                
                # Create audit log
                await create_audit_log(
                    db_session,
                    actor="system",
                    action="payment_method_deleted",
                    resource_type="payment_method",
                    resource_id=payment_method_id,
                    metadata={"gateway": db_payment_method.provider}
                )
                
                logger.info("Deleted payment method %s", payment_method_id)
                return True
            else:
                logger.warning("Failed to delete payment method %s in gateway", payment_method_id)
                return False
                
        except Exception as e:
            logger.error("Failed to delete payment method %s: %s", payment_method_id, str(e))
            raise

    async def create_subscription(
        self,
        customer_id: str,
        plan_id: str,
        plan_name: str,
        amount_minor: int,
        currency: str,
        interval: str = "month",
        interval_count: int = 1,
        trial_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        preferred_gateway: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Tuple[str, str]:
        """Create a subscription for recurring payments."""
        try:
            db_session = get_db_session()
            
            # Get customer
            customer = db_session.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                raise ValueError(f"Customer not found: {customer_id}")
            
            # Generate idempotency key if not provided
            if not idempotency_key:
                idempotency_key = str(uuid4())
            
            # Get best gateway
            if preferred_gateway:
                gateway = self.gateway_factory.get_gateway(preferred_gateway)
            else:
                gateway = get_best_gateway(customer.country, amount_minor, currency)
            
            # Create subscription in gateway (this would need to be implemented in gateway)
            # For now, we'll create a placeholder
            subscription_id = f"sub_{idempotency_key}"
            
            # Calculate trial dates
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            current_period_start = now
            current_period_end = now + timedelta(days=30 * interval_count)  # Simplified
            
            trial_start = None
            trial_end = None
            if trial_days:
                trial_start = now
                trial_end = now + timedelta(days=trial_days)
                current_period_start = trial_end
                current_period_end = current_period_start + timedelta(days=30 * interval_count)
            
            # Create subscription in database
            from .models import Subscription
            db_subscription = Subscription(
                provider_id=subscription_id,
                customer_id=customer_id,
                status="active",
                plan_id=plan_id,
                plan_name=plan_name,
                interval=interval,
                interval_count=interval_count,
                amount_minor=amount_minor,
                currency=currency,
                current_period_start=current_period_start,
                current_period_end=current_period_end,
                trial_start=trial_start,
                trial_end=trial_end,
                metadata=metadata or {}
            )
            
            db_session.add(db_subscription)
            db_session.commit()
            
            # Create audit log
            await create_audit_log(
                db_session,
                actor="system",
                action="subscription_created",
                resource_type="subscription",
                resource_id=db_subscription.id,
                metadata={
                    "gateway": gateway.provider_name,
                    "plan_id": plan_id,
                    "amount": amount_minor,
                    "currency": currency
                }
            )
            
            logger.info("Created subscription %s via %s", db_subscription.id, gateway.provider_name)
            return subscription_id, str(db_subscription.id)
            
        except Exception as e:
            logger.error("Failed to create subscription: %s", str(e))
            raise

    async def cancel_subscription(
        self,
        subscription_id: str,
        cancel_at_period_end: bool = True
    ) -> bool:
        """Cancel a subscription."""
        try:
            db_session = get_db_session()
            
            # Get subscription from database
            from .models import Subscription
            db_subscription = db_session.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not db_subscription:
                raise ValueError(f"Subscription not found: {subscription_id}")
            
            # Get gateway
            gateway = self.gateway_factory.get_gateway_by_provider(db_subscription.provider)
            
            # Cancel subscription in gateway (this would need to be implemented in gateway)
            # For now, we'll just update the database
            if cancel_at_period_end:
                db_subscription.cancel_at_period_end = True
            else:
                db_subscription.status = "canceled"
                db_subscription.canceled_at = datetime.utcnow()
                db_subscription.ended_at = datetime.utcnow()
            
            db_session.commit()
            
            # Create audit log
            await create_audit_log(
                db_session,
                actor="system",
                action="subscription_canceled",
                resource_type="subscription",
                resource_id=subscription_id,
                metadata={
                    "cancel_at_period_end": cancel_at_period_end,
                    "gateway": db_subscription.provider
                }
            )
            
            logger.info("Canceled subscription %s", subscription_id)
            return True
                
        except Exception as e:
            logger.error("Failed to cancel subscription %s: %s", subscription_id, str(e))
            raise

    async def create_invoice(
        self,
        customer_id: str,
        amount_minor: int,
        currency: str,
        description: Optional[str] = None,
        subscription_id: Optional[str] = None,
        due_date: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> Tuple[str, str]:
        """Create an invoice for billing."""
        try:
            db_session = get_db_session()
            
            # Get customer
            customer = db_session.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                raise ValueError(f"Customer not found: {customer_id}")
            
            # Generate idempotency key if not provided
            if not idempotency_key:
                idempotency_key = str(uuid4())
            
            # Generate invoice number
            invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{idempotency_key[:8]}"
            
            # Create invoice in database
            from .models import Invoice
            db_invoice = Invoice(
                provider_id=invoice_number,  # Using invoice number as provider ID for now
                customer_id=customer_id,
                subscription_id=subscription_id,
                number=invoice_number,
                status="draft",
                amount_minor=amount_minor,
                currency=currency,
                amount_paid_minor=0,
                amount_due_minor=amount_minor,
                due_date=due_date,
                description=description,
                metadata=metadata or {}
            )
            
            db_session.add(db_invoice)
            db_session.commit()
            
            # Create audit log
            await create_audit_log(
                db_session,
                actor="system",
                action="invoice_created",
                resource_type="invoice",
                resource_id=db_invoice.id,
                metadata={
                    "invoice_number": invoice_number,
                    "amount": amount_minor,
                    "currency": currency
                }
            )
            
            logger.info("Created invoice %s", db_invoice.id)
            return invoice_number, str(db_invoice.id)
            
        except Exception as e:
            logger.error("Failed to create invoice: %s", str(e))
            raise

    async def get_customer_payment_methods(
        self,
        customer_id: str
    ) -> List[Dict[str, Any]]:
        """Get all payment methods for a customer."""
        try:
            db_session = get_db_session()
            
            # Get customer
            customer = db_session.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                raise ValueError(f"Customer not found: {customer_id}")
            
            # Get payment methods from database
            from .models import PaymentMethod as DBPaymentMethod
            db_payment_methods = db_session.query(DBPaymentMethod).filter(
                DBPaymentMethod.customer_id == customer_id,
                DBPaymentMethod.is_enabled == True
            ).all()
            
            payment_methods = []
            for pm in db_payment_methods:
                payment_methods.append({
                    "id": str(pm.id),
                    "brand": pm.brand,
                    "last4": pm.last4,
                    "exp_month": pm.exp_month,
                    "exp_year": pm.exp_year,
                    "is_default": pm.is_default,
                    "created_at": pm.created_at.isoformat() if pm.created_at else None
                })
            
            return payment_methods
                
        except Exception as e:
            logger.error("Failed to get payment methods for customer %s: %s", customer_id, str(e))
            raise

    async def set_default_payment_method(
        self,
        customer_id: str,
        payment_method_id: str
    ) -> bool:
        """Set a payment method as default for a customer."""
        try:
            db_session = get_db_session()
            
            # Get customer
            customer = db_session.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                raise ValueError(f"Customer not found: {customer_id}")
            
            # Get payment method
            from .models import PaymentMethod as DBPaymentMethod
            db_payment_method = db_session.query(DBPaymentMethod).filter(
                DBPaymentMethod.id == payment_method_id,
                DBPaymentMethod.customer_id == customer_id
            ).first()
            
            if not db_payment_method:
                raise ValueError(f"Payment method not found: {payment_method_id}")
            
            # Remove default from all other payment methods
            db_session.query(DBPaymentMethod).filter(
                DBPaymentMethod.customer_id == customer_id
            ).update({"is_default": False})
            
            # Set this payment method as default
            db_payment_method.is_default = True
            db_session.commit()
            
            # Create audit log
            await create_audit_log(
                db_session,
                actor="system",
                action="default_payment_method_set",
                resource_type="payment_method",
                resource_id=payment_method_id,
                metadata={"customer_id": customer_id}
            )
            
            logger.info("Set payment method %s as default for customer %s", payment_method_id, customer_id)
            return True
                
        except Exception as e:
            logger.error("Failed to set default payment method: %s", str(e))
            raise
