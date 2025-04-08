import logging
from logging.handlers import RotatingFileHandler
import os

# Create a logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)
LOG_FILE = "logs/app.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3),
        logging.StreamHandler()  # Also log to console
    ]
)

logger = logging.getLogger("app_logger")
