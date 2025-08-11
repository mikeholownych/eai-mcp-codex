"""Payment system exceptions."""


class PaymentError(Exception):
    """Base exception for payment system errors."""
    pass


class PaymentGatewayError(PaymentError):
    """Raised when there's an error with payment gateway operations."""
    pass


class PaymentValidationError(PaymentError):
    """Raised when payment data validation fails."""
    pass


class PaymentProcessingError(PaymentError):
    """Raised when payment processing fails."""
    pass


class CustomerError(PaymentError):
    """Raised when there's an error with customer operations."""
    pass


class PaymentMethodError(PaymentError):
    """Raised when there's an error with payment method operations."""
    pass


class RefundError(PaymentError):
    """Raised when there's an error with refund operations."""
    pass


class WebhookError(PaymentError):
    """Raised when there's an error with webhook processing."""
    pass


class SubscriptionError(PaymentError):
    """Raised when there's an error with subscription operations."""
    pass


class BillingError(PaymentError):
    """Raised when there's an error with billing operations."""
    pass


class InvoiceError(PaymentError):
    """Raised when there's an error with invoice operations."""
    pass


class PlanError(PaymentError):
    """Raised when there's an error with subscription plan operations."""
    pass


class AnalyticsError(PaymentError):
    """Raised when there's an error with analytics operations."""
    pass


class ReconciliationError(PaymentError):
    """Raised when there's an error with reconciliation operations."""
    pass


class DisputeError(PaymentError):
    """Raised when there's an error with dispute operations."""
    pass


class MandateError(PaymentError):
    """Raised when there's an error with mandate operations."""
    pass

