from uvicorn import run

from src.model_router.app import app
from src.model_router.config import SERVICE_PORT

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=SERVICE_PORT)
