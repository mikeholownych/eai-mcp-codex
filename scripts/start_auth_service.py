import sys
import os

sys.path.insert(0, os.getcwd())

from uvicorn import run

from src.auth_service.app import app

if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", "8007"))
    host = os.getenv("SERVICE_HOST", "0.0.0.0")
    
    run(app, host=host, port=port)