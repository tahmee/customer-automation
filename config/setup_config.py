import logging
import os


# Setup api_ingest directories
LOG_DIR = "logs"
LOG_FILE = "api_ingest.log"
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE)
OUTPUT_DIR = "api_data"
OUTPUT_FILE = "quote_data.json"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, OUTPUT_FILE)



# Setup log path and directory
MAIN_LOG_FILE = "process.log"
SUMMARY_LOG_FILE = "summary.log"
M_LOG_PATH = os.path.join(LOG_DIR, MAIN_LOG_FILE)
SUMMARY_LOG_PATH = os.path.join(LOG_DIR, SUMMARY_LOG_FILE)

class EmailConfig:
    # SMTP credentials/ DB config
    SENDER_EMAIL = os.getenv('SENDER_EMAIL')
    SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT'))
    SMTP_TIMEOUT = int(os.getenv('SMTP_TIMEOUT'))


class AppConfig   
    # Set database credentials and file path
    DB_CREDENTIALS = os.getenv('DB_CREDENTIALS')
    FILE_PATH = os.getenv('FILE_PATH') # Path to quotes file

    # Alert email configuration
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
        
        # Prevent propagation to root logger (avoids duplicate logs)
        logger.propagate = False

    return logger

