#!/usr/bin/env python3
"""Start the Staff Management service."""

import os
import sys
from pathlib import Path
import uvicorn

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))  # noqa: E402

from src.staff.app import app  # noqa: E402
from src.staff.config import settings  # noqa: E402
from src.common.logging import get_logger  # noqa: E402

logger = get_logger("staff_service_start")


def main():
    """Start the Staff Management service."""
    logger.info(f"Starting Staff Management service on port {settings.service_port}")

    # Set environment variables if not already set
    os.environ.setdefault("STAFF_SERVICE_PORT", str(settings.service_port))

    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=settings.service_port,
            log_level="info",
            access_log=True,
            reload=False,  # Set to True for development
        )
    except Exception as e:
        logger.error(f"Failed to start Staff Management service: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
