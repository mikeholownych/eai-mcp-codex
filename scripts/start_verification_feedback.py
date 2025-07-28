from uvicorn import run

from src.verification_feedback.app import app
from src.verification_feedback.config import SERVICE_PORT

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=SERVICE_PORT)
