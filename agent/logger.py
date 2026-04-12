import logging
import os
import re
from logging.handlers import RotatingFileHandler

# Filter to mask API keys and sensitive data
class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        msg = str(record.msg)
        # Mask Groq keys (gsk_...)
        msg = re.sub(r'gsk_[a-zA-Z0-9]{30,}', '***GROQ_KEY_MASKED***', msg)
        # Mask Tavily keys (tvly-...)
        msg = re.sub(r'tvly-[a-zA-Z0-9]{20,}', '***TAVILY_KEY_MASKED***', msg)
        record.msg = msg
        return True

# Ensure logs directory exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "agent.log")

# Setup logger
logger = logging.getLogger("CompanyResearchAgent")
logger.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Rotating File Handler (5 MB max per file, keep 3 backups)
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3)
file_handler.setFormatter(formatter)
file_handler.addFilter(SensitiveDataFilter())

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.addFilter(SensitiveDataFilter())

if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
