import json
import time
from config.setup_config import logging_setup, AppConfig
from src.email_utils import send_email_config, RATE_LIMIT_DELAY

logger = logging_setup(AppConfig.LOG_PATH, __name__)

def get_quote(filename):
    """Load quote from JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            quote = json.load(file)
            return quote['quote'], quote['author']
    except Exception as e:
        logger.error(f"Could not read quote file {filename}: {e}")
        return None, None


def process_user_batch(batch, quote, author, stats):
    """Processes a batch of users and updates stats."""
    for user in batch:
        name = user['first_name']
        email = user['email_address']

        stats['records_processed'] += 1

        try: 
            success = send_email_config(name, email, quote, author)
            if success:
                stats['emails_sent'] += 1
            else:
                stats['failed'] += 1           
           
        except Exception as e:
            stats['failed'] += 1 
            logger.error(f"Failed to send email to {name} ({email}): {e}")
            
     # Update every 100 emails progress
        if stats['records_processed'] % 100 == 0:
            logger.info(f"Progress: {stats['records_processed']} emails attempted.")
        
        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)   

