import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Setup directories and file paths
LOG_DIR = "logs"
OUTPUT_DIR = "api_data"

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

API_LOG_PATH = os.path.join(LOG_DIR, "api_ingest.log")
MAIN_LOG_PATH = os.path.join(LOG_DIR, "process.log")
SUMMARY_LOG_PATH = os.path.join(LOG_DIR, "summary.log")

OUTPUT_PATH = os.path.join(OUTPUT_DIR, "quote_data.json")


class EmailConfig:
    # SMTP credentials
    SENDER_EMAIL = os.getenv('SENDER_EMAIL')
    SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_TIMEOUT = int(os.getenv('SMTP_TIMEOUT'))


class AppConfig:  
    DB_CREDENTIALS = os.getenv('DB_CREDENTIALS')  # DB credentials
    FILE_PATH = os.getenv('FILE_PATH') # Path to quotes file
    CHECKPOINT_FILE = "api_data/pipeline_checkpoint.json"

    # process, main script and summary log file path
    LOG_PATH = MAIN_LOG_PATH 
    SUMMARY_LOG_PATH = SUMMARY_LOG_PATH
    
    # Alert email configuration
    SENDER_EMAIL = os.getenv('ALERT')
    ALERT_EMAIL = os.getenv('ALERT_EMAIL') 
    SEND_ALERTS = os.getenv('SEND_ALERTS').lower() == 'true'


def api_dirs():
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def logging_setup(log_path, module_name):
    logger = logging.getLogger(module_name)
    
    # Only add handler if logger doesn't already have one
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create file handler
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(file_handler)
        
        # Prevent propagation to root logger 
        logger.propagate = False

    return logger

