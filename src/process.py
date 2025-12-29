import json
import time
import smtplib
from sqlalchemy import text
from config.setup_config import logging_setup, AppConfig, EmailConfig
from src.email_utils import send_email
from src.db_conn import save_checkpoint

# Logging config
logger = logging_setup(AppConfig.LOG_PATH, __name__)

# RATE_LIMIT_DELAY prevents being flagged as spam by the SMTP provider
RATE_LIMIT_DELAY = 0.1  # seconds between emails (10 emails per second maximum throughput)


def get_quote(filename):
    """
    Reads and parses the formatted quote data from the local JSON cache.

    Args:
        filename (str): Path to the quote JSON file.

    Returns:
        tuple (str, str) | (None, None): (quote, author) if successful, 
                                        otherwise (None, None).
    """
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            quote = json.load(file)
            return quote['quote'], quote['author']
    except Exception as e:
        logger.error(f"Could not read quote file {filename}: {e}")
        return None, None


def process_user_batch(batch, quote, author, stats, session):
    """
    Coordinates the sending of emails and the updating of database records for a single batch.

    This function opens a persistent SMTP connection for the duration of the batch, 
    sends individual emails, and then performs a bulk database update to mark 
    those users as "processed" for today.

    Args:
        batch (list[dict]): A list of user dictionaries from the database.
        quote (str): The quote of the day.
        author (str): The author of the quote.
        stats (dict): A mutable dictionary tracking 'records_processed', 'emails_sent', and 'failed'.
        session (sqlalchemy.orm.Session): The active database session for updates.

    Raises:
        Exception: Re-raises critical exceptions (SMTP failures or DB errors) to signal 
                   the main script to stop processing.
    """
    successful_ids = []
    try:
        # Establish a single SMTP session for the entire batch
        with smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT, timeout=EmailConfig.SMTP_TIMEOUT) as server:
            server.starttls()
            server.login(EmailConfig.SENDER_EMAIL, EmailConfig.SENDER_PASSWORD)

            for user in batch:
                name = user['first_name']
                email = user['email_address']

                stats['records_processed'] += 1

                try: 
                    # Attempt to send the personalised email
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

            # Minor sleep to adhere SMTP rate limits
            time.sleep(RATE_LIMIT_DELAY)

        # Database Update: Only update records for users who successfully received the email
        if successful_ids:
            try:
                # Bulk update last_email_sent_at to prevent duplicate emails today
                session.execute(
                    text("UPDATE users SET last_email_sent_at = CURRENT_TIMESTAMP WHERE user_id IN :ids"),
                    {"ids": tuple(successful_ids)}
                )
                session.commit() # Save the final changes to the database.

                # Update the max_id checkpoint after successful database update so as to resume from if the NEXT batch fails
                save_checkpoint(successful_ids[-1])
                logger.info(f"Batch complete. Updated {len(successful_ids)} records in DB.")

            except Exception as e:
                # CRITICAL: If the database update fails, undo the transaction to ensure data consistency
                session.rollback() 
                logger.error(f"Database update failed. Rolling back transaction: {e}")
                raise # Re-raise to stop the pipeline

       
    except Exception as e:
        # General catch-all for SMTP session failures or script interruptions
        session.rollback() 
        logger.error(f"Batch processing aborted:: {e}")
        raise  

