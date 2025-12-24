import sys
import time
from datetime import datetime
from config.setup_config import logging_setup, AppConfig, api_dirs
from src.process import get_quote, process_user_batch
from src.db_conn import fetch_users_in_batches, Session
from src.summary_log import generate_summary, log_final_summary
from src.alerts import send_alert_email

# 1. Setup specialized loggers
logger = logging_setup(AppConfig.LOG_PATH, "ORCHESTRATOR")

def main():
    # Ensure directories exist
    api_dirs()
    
    start_time = time.time()
    day_name = datetime.now().strftime("%A")
    
    # Initialize run statistics
    stats = {
        'records_processed': 0,
        'emails_sent': 0,
        'failed': 0,
        'daily': 0,
        'weekly': 0
        }

    try:
        quote, author = get_quote(AppConfig.FILE_PATH)
        
        if not quote:
            logger.critical("Aborting Run: Quote file missing or empty. Run fetch_quote.py first.")
            return
        else:
            logger.info(f"Quote loaded successfully: '{quote[:30]}...' by {author}")
            
        with Session() as session:
        # Process Daily Subscribers
            logger.info("Attempting to fetch daily subscribers")
            for batch in fetch_users_in_batches('daily'):
                process_user_batch(batch, quote, author, stats, session)
                stats['daily'] += len(batch)
            logger.info(f"Completed daily subscribers: {stats['daily']} users processed.")

        # Process Weekly Subscribers (Only if today is Monday)
        if day_name == "Monday":
            logger.info("It's Monday: Attempting to fetch weekly subscribers")
            for batch in fetch_users_in_batches('weekly'):
                process_user_batch(batch, quote, author, stats, session)
                stats['weekly'] += len(batch)
            logger.info(f"Completed weekly subscribers: {stats['weekly']} users processed")
        else:
            logger.info(f"Skipping weekly subscribers (Today is {day_name}).")

        # Finalize Statistics and Performance
        duration = time.time() - start_time
        
        # Log to summary.log using your logic in summary_log.py
        log_final_summary(stats, day_name, duration)

        # Generate and Send HTML Alert to Admin
        summary_text = generate_summary(stats, day_name, duration, success=True)
        send_alert_email(summary_text, subject=f"MindFuel Report: {day_name}")

        logger.info(f"====== AUTOMATION COMPLETED IN {duration:.2f}s ======")

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"CRITICAL SYSTEM FAILURE: {e}", exc_info=True)
        
        # Send failure alert
        summary_text = generate_summary(stats, day_name, duration, success=False)
        send_alert_email(summary_text, subject=f"CRITICAL FAILURE: MindFuel {day_name}")
        
        sys.exit(1)

if __name__ == "__main__":
    main()