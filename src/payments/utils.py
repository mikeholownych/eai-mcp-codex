"""Utility functions for payment processing."""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)


def generate_invoice_number() -> str:
    """Generate a unique invoice number."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_suffix = str(hash(str(datetime.utcnow().microsecond)))[-4:]
    return f"INV-{timestamp}-{random_suffix}"


def calculate_proration(
    current_amount: int,
    new_amount: int,
    current_period_start: datetime,
    current_period_end: datetime,
    change_date: datetime
) -> Dict[str, int]:
    """
    Calculate proration amounts when changing subscription plans.
    
    Returns:
        Dict with 'credit_amount' and 'charge_amount' in cents
    """
    if change_date < current_period_start or change_date > current_period_end:
        raise ValueError("Change date must be within current billing period")
    
    # Calculate remaining time in current period
    remaining_duration = current_period_end - change_date
    total_duration = current_period_end - current_period_start
    
    if total_duration.total_seconds() <= 0:
        return {"credit_amount": 0, "charge_amount": 0}
    
    # Calculate proportional amounts
    remaining_ratio = remaining_duration.total_seconds() / total_duration.total_seconds()
    
    # Credit for unused portion of current plan
    credit_amount = int(current_amount * remaining_ratio)
    
    # Charge for remaining portion of new plan
    charge_amount = int(new_amount * remaining_ratio)
    
    return {
        "credit_amount": credit_amount,
        "charge_amount": charge_amount
    }


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
    tolerance: int = 300
) -> bool:
    """
    Verify webhook signature from payment gateway.
    
    Args:
        payload: Raw webhook payload
        signature: Signature header from webhook
        secret: Webhook secret key
        tolerance: Time tolerance in seconds for timestamp validation
    
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Parse signature header (format: t=timestamp,v1=signature)
        signature_parts = signature.split(',')
        timestamp = None
        signature_value = None
        
        for part in signature_parts:
            if part.startswith('t='):
                timestamp = int(part[2:])
            elif part.startswith('v1='):
                signature_value = part[3:]
        
        if not timestamp or not signature_value:
            logger.warning("Invalid signature header format")
            return False
        
        # Check timestamp tolerance
        current_time = int(datetime.utcnow().timestamp())
        if abs(current_time - timestamp) > tolerance:
            logger.warning(f"Webhook timestamp too old: {timestamp}")
            return False
        
        # Calculate expected signature
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            f"{timestamp}.{payload.decode('utf-8')}".encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(signature_value, expected_signature)
        
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False


def parse_webhook_payload(payload: bytes) -> Dict[str, Any]:
    """Parse webhook payload and return structured data."""
    try:
        if isinstance(payload, bytes):
            payload_str = payload.decode('utf-8')
        else:
            payload_str = payload
        
        # Try JSON first
        try:
            return json.loads(payload_str)
        except json.JSONDecodeError:
            pass
        
        # Try form-encoded data
        try:
            parsed = parse_qs(payload_str)
            # Convert single-item lists to single values
            result = {}
            for key, value in parsed.items():
                if len(value) == 1:
                    result[key] = value[0]
                else:
                    result[key] = value
            return result
        except Exception:
            pass
        
        # Return as string if all else fails
        return {"raw_payload": payload_str}
        
    except Exception as e:
        logger.error(f"Error parsing webhook payload: {e}")
        return {"error": str(e), "raw_payload": str(payload)}


def format_currency(amount: int, currency: str) -> str:
    """Format amount in cents to human-readable currency string."""
    currency_symbols = {
        "usd": "$",
        "eur": "€",
        "gbp": "£",
        "jpy": "¥",
        "cad": "C$",
        "aud": "A$"
    }
    
    symbol = currency_symbols.get(currency.lower(), currency.upper())
    dollars = amount / 100
    
    if currency.lower() == "jpy":
        return f"{symbol}{amount}"
    else:
        return f"{symbol}{dollars:.2f}"


def calculate_tax_amount(
    subtotal: int,
    tax_rate: float,
    currency: str = "usd"
) -> int:
    """Calculate tax amount based on subtotal and tax rate."""
    tax_amount = int(subtotal * tax_rate)
    
    # Round to nearest cent for USD
    if currency.lower() == "usd":
        tax_amount = round(tax_amount / 100) * 100
    
    return tax_amount


def validate_card_number(card_number: str) -> bool:
    """Basic Luhn algorithm validation for card numbers."""
    if not card_number or not card_number.isdigit():
        return False
    
    # Remove spaces and dashes
    card_number = card_number.replace(" ", "").replace("-", "")
    
    if len(card_number) < 13 or len(card_number) > 19:
        return False
    
    # Luhn algorithm
    sum_digits = 0
    is_even = False
    
    for digit in reversed(card_number):
        d = int(digit)
        if is_even:
            d *= 2
            if d > 9:
                d -= 9
        sum_digits += d
        is_even = not is_even
    
    return sum_digits % 10 == 0


def mask_card_number(card_number: str, mask_char: str = "*") -> str:
    """Mask a card number for display (e.g., **** **** **** 1234)."""
    if not card_number or len(card_number) < 4:
        return card_number
    
    # Remove spaces and dashes
    card_number = card_number.replace(" ", "").replace("-", "")
    
    if len(card_number) <= 4:
        return card_number
    
    masked = mask_char * (len(card_number) - 4) + card_number[-4:]
    
    # Add spaces every 4 characters
    formatted = ""
    for i in range(0, len(masked), 4):
        formatted += masked[i:i+4] + " "
    
    return formatted.strip()


def generate_payment_token() -> str:
    """Generate a secure payment token."""
    import secrets
    return secrets.token_urlsafe(32)


def validate_expiry_date(month: int, year: int) -> bool:
    """Validate card expiry date."""
    current_date = datetime.utcnow()
    current_year = current_date.year
    current_month = current_date.month
    
    # Check if year is in the past
    if year < current_year:
        return False
    
    # Check if month is valid
    if month < 1 or month > 12:
        return False
    
    # Check if card is expired this month
    if year == current_year and month < current_month:
        return False
    
    return True


def calculate_installment_amount(
    total_amount: int,
    num_installments: int,
    interest_rate: float = 0.0
) -> int:
    """Calculate installment amount with optional interest."""
    if num_installments <= 0:
        raise ValueError("Number of installments must be positive")
    
    if interest_rate < 0:
        raise ValueError("Interest rate cannot be negative")
    
    if interest_rate == 0:
        return total_amount // num_installments
    
    # Simple interest calculation
    total_with_interest = total_amount * (1 + interest_rate)
    return int(total_with_interest / num_installments)
