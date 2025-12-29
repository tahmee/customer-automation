import logging
import os
from dotenv import load_dotenv

# Load environment variables from a .env file into the system environment
load_dotenv()

# Global directory setup
LOG_DIR = "logs"
OUTPUT_DIR = "api_data"

# Ensure essential directories exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Define specific log file destinations
API_LOG_PATH = os.path.join(LOG_DIR, "api_ingest.log")
MAIN_LOG_PATH = os.path.join(LOG_DIR, "process.log")
SUMMARY_LOG_PATH = os.path.join(LOG_DIR, "summary.log")

# Define the primary output data file path
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "quote_data.json")


class EmailConfig:
    """
    Configuration settings for SMTP email communication.
    
    Attributes:
        SENDER_EMAIL (str): The email address used to send notifications.
        SENDER_PASSWORD (str): The authentication password for the sender email.
        SMTP_SERVER (str): The host address of the SMTP provider.
        SMTP_PORT (int): The connection port (defaults to 587 for TLS).
        SMTP_TIMEOUT (int): Time in seconds to wait for a server response.
    """
    SENDER_EMAIL = os.getenv('SENDER_EMAIL')
    SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_TIMEOUT = int(os.getenv('SMTP_TIMEOUT'))


class AppConfig:  
    """
    Centralised application settings including database credentials and alert toggle.
    
    Attributes:
        DB_CREDENTIALS (str): Connection string for the database.
        FILE_PATH (str): Path to the source quotes file.
        CHECKPOINT_FILE (str): Path to the JSON file tracking pipeline progress.
        LOG_PATH (str): Path for general process logging.
        SUMMARY_LOG_PATH (str): Path for pipeline execution summary.
        SEND_ALERTS (bool): Toggle for enabling/disabling email notifications.
    """
    DB_CREDENTIALS = os.getenv('DB_CREDENTIALS') 
    FILE_PATH = os.getenv('FILE_PATH') 
    CHECKPOINT_FILE = "api_data/pipeline_checkpoint.json"

    LOG_PATH = MAIN_LOG_PATH 
    SUMMARY_LOG_PATH = SUMMARY_LOG_PATH
    
    # Alert email configuration
    SENDER_EMAIL = os.getenv('ALERT')
    ALERT_EMAIL = os.getenv('ALERT_EMAIL') 
    SEND_ALERTS = os.getenv('SEND_ALERTS').lower() == 'true'


def api_dirs():
    """
    Creates the necessary directory structure for the application.
    
    This function ensures that the 'logs' and 'api_data' folders exist 
    to prevent FileNotFoundError.
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def logging_setup(log_path, module_name):
    """
    Initializes and configures a logger instance for a specific module.

    Args:
        log_path (str): The file path where logs will be written.
        module_name (str): The name of the module to identify log sources.

    Returns:
        logging.Logger: A configured logger instance with a FileHandler and specific formatting.
    """
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
        
        # Prevent logs from being passed up to the root logger to avoid double logging in console
        logger.propagate = False

    return logger

