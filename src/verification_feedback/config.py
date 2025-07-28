"""Verification Feedback configuration."""

import os

SERVICE_NAME = "verification-feedback"
SERVICE_PORT = int(os.getenv("VERIFICATION_FEEDBACK_PORT", 8005))
