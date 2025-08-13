"""Basic test to verify payment system structure."""

import pytest
from unittest.mock import Mock, patch

def test_basic_import():
    """Test that basic imports work."""
    # Test that we can import the base classes
    from src.payments.gateways.base import PaymentGateway, PaymentIntent, Charge, Refund
    
    # Test that PaymentGateway is abstract
    with pytest.raises(TypeError):
        PaymentGateway()
    
    # Test that we can create basic objects
    payment_intent = PaymentIntent(
        id="pi_test123",
        amount_minor=1000,
        currency="USD",
        status="requires_payment_method",
        client_secret="pi_test123_secret"
    )
    
    assert payment_intent.id == "pi_test123"
    assert payment_intent.amount_minor == 1000
    assert payment_intent.currency == "USD"

def test_gateway_factory():
    """Test gateway factory basic functionality."""
    with patch('src.payments.gateways.factory.get_settings') as mock_settings:
        mock_settings.return_value = Mock()
        
        from src.payments.gateways.factory import PaymentGatewayFactory
        
        factory = PaymentGatewayFactory()
        
        # Test that factory can be created
        assert factory is not None
        assert hasattr(factory, '_gateways')
        
        # Test that we can get gateways
        assert "stripe" in factory._gateways
        assert "paypal" in factory._gateways
        assert "adyen" in factory._gateways

def test_config():
    """Test configuration loading."""
    from src.payments.config import get_settings
    
    settings = get_settings()
    
    # Test that settings can be loaded
    assert settings is not None
    assert hasattr(settings, 'database_url')
    assert hasattr(settings, 'stripe_secret_key')
    assert hasattr(settings, 'db_pool_size')

if __name__ == "__main__":
    pytest.main([__file__])
