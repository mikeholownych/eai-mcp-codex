#!/usr/bin/env python3
"""
Payment Service Startup Script

This script starts the payment service with proper configuration,
environment setup, and error handling.
"""

import os
import sys
import logging
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from payments.config import PaymentSettings
from payments.database import init_db, check_db_health
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('payment_service.log')
    ]
)

logger = logging.getLogger(__name__)

def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        'STRIPE_SECRET_KEY',
        'DATABASE_URL',
        'REDIS_URL',
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your environment or .env file")
        return False
    
    return True

def check_database():
    """Check database connectivity and health."""
    try:
        logger.info("Checking database connectivity...")
        health = check_db_health()
        if health['status'] == 'healthy':
            logger.info("Database connection successful")
            return True
        else:
            logger.error(f"Database health check failed: {health}")
            return False
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def main():
    """Main startup function."""
    logger.info("Starting Payment Service...")
    
    # Check environment
    if not check_environment():
        logger.error("Environment check failed. Exiting.")
        sys.exit(1)
    
    # Check database
    if not check_database():
        logger.error("Database check failed. Exiting.")
        sys.exit(1)
    
    # Initialize database
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)
    
    # Load settings
    try:
        settings = PaymentSettings()
        logger.info(f"Payment service configured for environment: {settings.environment}")
        logger.info(f"Supported currencies: {', '.join(settings.supported_currencies)}")
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        sys.exit(1)
    
    # Start the server
    logger.info("Starting uvicorn server...")
    try:
        uvicorn.run(
            "payments.app:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True,
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
