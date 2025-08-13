"""Payment system configuration."""

import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field


class PaymentSettings(BaseSettings):
    """Payment system configuration settings."""
    
    # Database settings
    database_url: str = Field(
        default="postgresql://user:password@localhost/payments",
        env="PAYMENT_DATABASE_URL"
    )
    
    # Stripe settings
    stripe_secret_key: Optional[str] = Field(
        default=None,
        env="STRIPE_SECRET_KEY"
    )
    stripe_publishable_key: Optional[str] = Field(
        default=None,
        env="STRIPE_PUBLISHABLE_KEY"
    )
    stripe_webhook_secret: Optional[str] = Field(
        default=None,
        env="STRIPE_WEBHOOK_SECRET"
    )
    stripe_api_version: str = Field(
        default="2023-10-16",
        env="STRIPE_API_VERSION"
    )
    
    # Adyen settings
    adyen_api_key: str = Field(
        default="",
        env="ADYEN_API_KEY"
    )
    adyen_merchant_account: str = Field(
        default="",
        env="ADYEN_MERCHANT_ACCOUNT"
    )
    adyen_environment: str = Field(
        default="test",
        env="ADYEN_ENVIRONMENT"
    )
    
    # PayPal settings
    paypal_client_id: Optional[str] = Field(
        default=None,
        env="PAYPAL_CLIENT_ID"
    )
    paypal_client_secret: Optional[str] = Field(
        default=None,
        env="PAYPAL_CLIENT_SECRET"
    )
    paypal_webhook_secret: Optional[str] = Field(
        default=None,
        env="PAYPAL_WEBHOOK_SECRET"
    )
    paypal_base_url: str = Field(
        default="https://api-m.sandbox.paypal.com",  # Use production URL in production
        env="PAYPAL_BASE_URL"
    )
    paypal_mode: str = Field(
        default="sandbox",  # Use "live" in production
        env="PAYPAL_MODE"
    )
    
    # General payment settings
    default_currency: str = Field(
        default="USD",
        env="DEFAULT_CURRENCY"
    )
    supported_currencies: list = Field(
        default=["USD", "EUR", "GBP", "CAD", "AUD", "JPY"],
        env="SUPPORTED_CURRENCIES"
    )
    
    # Gateway selection settings
    gateway_priority: Dict[str, list] = Field(
        default={
            "US": ["stripe", "paypal"],
            "CA": ["stripe", "paypal"],
            "GB": ["stripe", "paypal"],
            "DE": ["stripe", "paypal"],
            "FR": ["stripe", "paypal"],
            "AU": ["stripe", "paypal"],
            "JP": ["stripe", "paypal"],
            "default": ["stripe", "paypal"]
        }
    )
    
    # Payment method settings
    payment_method_limits: Dict[str, Dict[str, Any]] = Field(
        default={
            "card": {
                "min_amount": 50,  # 50 cents
                "max_amount": 99999999,  # $999,999.99
                "supported_currencies": ["USD", "EUR", "GBP", "CAD", "AUD", "JPY"]
            },
            "sepa_debit": {
                "min_amount": 100,  # 1 EUR
                "max_amount": 99999999,  # 999,999.99 EUR
                "supported_currencies": ["EUR"],
                "supported_countries": ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"]
            },
            "ach_debit": {
                "min_amount": 100,  # $1.00
                "max_amount": 99999999,  # $999,999.99
                "supported_currencies": ["USD"],
                "supported_countries": ["US"]
            }
        }
    )
    
    # Security settings
    webhook_timeout: int = Field(
        default=30,
        env="WEBHOOK_TIMEOUT"
    )
    max_webhook_retries: int = Field(
        default=3,
        env="MAX_WEBHOOK_RETRIES"
    )
    
    # Logging settings
    log_level: str = Field(
        default="INFO",
        env="PAYMENT_LOG_LEVEL"
    )
    log_format: str = Field(
        default="json",
        env="PAYMENT_LOG_FORMAT"
    )
    
    # Monitoring settings
    health_check_interval: int = Field(
        default=300,  # 5 minutes
        env="HEALTH_CHECK_INTERVAL"
    )
    metrics_enabled: bool = Field(
        default=True,
        env="PAYMENT_METRICS_ENABLED"
    )
    
    # Idempotency settings
    idempotency_key_header: str = Field(
        default="Idempotency-Key",
        env="IDEMPOTENCY_KEY_HEADER"
    )
    idempotency_cache_ttl: int = Field(
        default=86400,  # 24 hours
        env="IDEMPOTENCY_CACHE_TTL"
    )
    
    # Rate limiting
    rate_limit_requests: int = Field(
        default=100,
        env="RATE_LIMIT_REQUESTS"
    )
    rate_limit_window: int = Field(
        default=60,  # 1 minute
        env="RATE_LIMIT_WINDOW"
    )
    
    # Feature flags
    features: Dict[str, bool] = Field(
        default={
            "subscriptions": True,
            "invoices": True,
            "refunds": True,
            "disputes": True,
            "webhooks": True,
            "3ds": True,
            "saved_payment_methods": True,
            "recurring_payments": True
        }
    )
    
    # Testing settings
    test_mode: bool = Field(
        default=False,
        env="PAYMENT_TEST_MODE"
    )
    mock_gateway_enabled: bool = Field(
        default=False,
        env="MOCK_GATEWAY_ENABLED"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
_settings: Optional[PaymentSettings] = None


def get_settings() -> PaymentSettings:
    """Get payment settings instance."""
    global _settings
    if _settings is None:
        _settings = PaymentSettings()
    return _settings


def update_settings(**kwargs) -> None:
    """Update payment settings."""
    global _settings
    if _settings is None:
        _settings = PaymentSettings()
    
    for key, value in kwargs.items():
        if hasattr(_settings, key):
            setattr(_settings, key, value)


def reset_settings() -> None:
    """Reset payment settings to defaults."""
    global _settings
    _settings = None


# Environment-specific configurations
def get_development_settings() -> PaymentSettings:
    """Get development environment settings."""
    return PaymentSettings(
        test_mode=True,
        mock_gateway_enabled=True,
        log_level="DEBUG",
        paypal_mode="sandbox"
    )


def get_production_settings() -> PaymentSettings:
    """Get production environment settings."""
    return PaymentSettings(
        test_mode=False,
        mock_gateway_enabled=False,
        log_level="WARNING",
        paypal_mode="live"
    )


def get_test_settings() -> PaymentSettings:
    """Get test environment settings."""
    return PaymentSettings(
        test_mode=True,
        mock_gateway_enabled=True,
        log_level="DEBUG",
        database_url="postgresql://test:test@localhost/test_payments",
        paypal_mode="sandbox"
    )


# Configuration validation
def validate_settings() -> Dict[str, Any]:
    """Validate payment settings and return validation results."""
    settings = get_settings()
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "gateways": {}
    }
    
    # Validate Stripe configuration
    if settings.stripe_secret_key:
        validation_results["gateways"]["stripe"] = {
            "configured": True,
            "api_version": settings.stripe_api_version,
            "webhook_secret": bool(settings.stripe_webhook_secret)
        }
    else:
        validation_results["gateways"]["stripe"] = {
            "configured": False,
            "error": "Missing STRIPE_SECRET_KEY"
        }
        validation_results["warnings"].append("Stripe gateway not configured")
    
    # Validate PayPal configuration
    if settings.paypal_client_id and settings.paypal_client_secret:
        validation_results["gateways"]["paypal"] = {
            "configured": True,
            "mode": settings.paypal_mode,
            "base_url": settings.paypal_base_url,
            "webhook_secret": bool(settings.paypal_webhook_secret)
        }
    else:
        validation_results["gateways"]["paypal"] = {
            "configured": False,
            "error": "Missing PayPal credentials"
        }
        validation_results["warnings"].append("PayPal gateway not configured")
    
    # Validate database configuration
    if not settings.database_url:
        validation_results["valid"] = False
        validation_results["errors"].append("Missing database URL")
    
    # Validate currency configuration
    if settings.default_currency not in settings.supported_currencies:
        validation_results["warnings"].append(
            f"Default currency {settings.default_currency} not in supported currencies"
        )
    
    # Check if at least one gateway is configured
    configured_gateways = [
        gateway for gateway in validation_results["gateways"].values()
        if gateway.get("configured", False)
    ]
    
    if not configured_gateways:
        validation_results["valid"] = False
        validation_results["errors"].append("No payment gateways configured")
    
    return validation_results


# Configuration helpers
def is_gateway_enabled(gateway_name: str) -> bool:
    """Check if a specific gateway is enabled."""
    settings = get_settings()
    
    if gateway_name == "stripe":
        return bool(settings.stripe_secret_key)
    elif gateway_name == "paypal":
        return bool(settings.paypal_client_id and settings.paypal_client_secret)
    elif gateway_name == "mock":
        return settings.mock_gateway_enabled
    else:
        return False


def get_gateway_config(gateway_name: str) -> Dict[str, Any]:
    """Get configuration for a specific gateway."""
    settings = get_settings()
    
    if gateway_name == "stripe":
        return {
            "secret_key": settings.stripe_secret_key,
            "publishable_key": settings.stripe_publishable_key,
            "webhook_secret": settings.stripe_webhook_secret,
            "api_version": settings.stripe_api_version
        }
    elif gateway_name == "paypal":
        return {
            "client_id": settings.paypal_client_id,
            "client_secret": settings.paypal_client_secret,
            "webhook_secret": settings.paypal_webhook_secret,
            "base_url": settings.paypal_base_url,
            "mode": settings.paypal_mode
        }
    else:
        return {}


def get_supported_countries_for_gateway(gateway_name: str) -> list:
    """Get list of supported countries for a gateway."""
    settings = get_settings()
    
    if gateway_name == "stripe":
        # Stripe supports most countries
        return ["US", "CA", "GB", "DE", "FR", "AU", "JP", "SG", "HK", "IN", "BR", "MX"]
    elif gateway_name == "paypal":
        # PayPal has extensive global coverage
        return ["US", "CA", "GB", "DE", "FR", "AU", "JP", "SG", "HK", "IN", "BR", "MX", "IT", "ES", "NL", "SE", "NO", "DK", "FI", "CH", "AT", "BE", "IE", "PT", "GR", "PL", "CZ", "HU", "RO", "BG", "HR", "SK", "SI", "LT", "LV", "EE", "CY", "LU", "MT"]
    else:
        return []


def get_supported_currencies_for_gateway(gateway_name: str) -> list:
    """Get list of supported currencies for a gateway."""
    settings = get_settings()
    
    if gateway_name == "stripe":
        # Stripe supports 135+ currencies
        return ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF", "SEK", "NOK", "DKK", "PLN", "CZK", "HUF", "RON", "BGN", "HRK", "RUB", "TRY", "BRL", "MXN", "ARS", "CLP", "COP", "PEN", "UYU", "VND", "THB", "MYR", "SGD", "HKD", "TWD", "KRW", "INR", "PKR", "BDT", "LKR", "NPR", "MMK", "KHR", "LAK", "MNT"]
    elif gateway_name == "paypal":
        # PayPal supports 25+ currencies
        return ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF", "SEK", "NOK", "DKK", "PLN", "CZK", "HUF", "RON", "BGN", "HRK", "RUB", "TRY", "BRL", "MXN", "ARS", "CLP", "COP", "PEN", "UYU", "VND", "THB", "MYR", "SGD", "HKD", "TWD", "KRW", "INR", "PKR", "BDT", "LKR", "NPR", "MMK", "KHR", "LAK", "MNT"]
    else:
        return settings.supported_currencies


def get_payment_method_limits(payment_method_type: str) -> Dict[str, Any]:
    """Get limits for a specific payment method type."""
    settings = get_settings()
    return settings.payment_method_limits.get(payment_method_type, {})
