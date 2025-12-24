import json
import time
import smtplib
from sqlalchemy import text
from config.setup_config import logging_setup, AppConfig, EmailConfig
from src.email_utils import send_email
from src.db_conn import save_checkpoint

logger = logging_setup(AppConfig.LOG_PATH, __name__)

RATE_LIMIT_DELAY = 0.1  # seconds between emails (10 emails/second)

def get_quote(filename):
    """Load quote from JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            quote = json.load(file)
            return quote['quote'], quote['author']
    except Exception as e:
        logger.error(f"Could not read quote file {filename}: {e}")
        return None, None


def process_user_batch(batch, quote, author, stats, session):
    """Processes a batch of users and updates stats."""
    successful_ids = []
    try:
        with smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT, timeout=EmailConfig.SMTP_TIMEOUT) as server:
            server.starttls()
            server.login(EmailConfig.SENDER_EMAIL, EmailConfig.SENDER_PASSWORD)

            for user in batch:
                name = user['first_name']
                email = user['email_address']

                stats['records_processed'] += 1

                try: 
                    success = send_email(server, name, email, quote, author)
                    if success:
                        stats['emails_sent'] += 1
                        successful_ids.append(user['user_id'])
                    else:
                        stats['failed'] += 1
                        logger.warning(f"Failed to send email to {user['email_address']}. Check logs.")           
                
                except Exception as e:
                    stats['failed'] += 1 
                    logger.warning(f"Failed to send email to {email}: {e}")

            time.sleep(RATE_LIMIT_DELAY)

        if successful_ids:
            try:
                session.execute(
                    text("UPDATE users SET last_email_sent_at = CURRENT_TIMESTAMP WHERE user_id IN :ids"),
                    {"ids": tuple(successful_ids)}
                )
                session.commit() # Save the changes

                # Save checkpoint after successful DB update
                save_checkpoint(successful_ids[-1])
                logger.info(f"Batch complete. Updated {len(successful_ids)} records in DB.")

            except Exception as e:
                session.rollback() # <--- CRITICAL: Undo changes if the update fails
                logger.error(f"Database update failed. Rolling back transaction: {e}")
                raise # Re-raise to stop the pipeline

       
    except Exception as e:
        # If the SMTP connection or anything else breaks, we ensure the session is clean
        session.rollback() 
        logger.error(f"Batch processing aborted:: {e}")
        raise  

