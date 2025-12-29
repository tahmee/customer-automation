import sys
import time
from datetime import datetime
from config.setup_config import logging_setup, AppConfig, api_dirs
from src.process import get_quote, process_user_batch
from src.db_conn import fetch_users_in_batches, Session
from src.summary_log import generate_summary, log_final_summary
from src.alerts import send_alert_email

# Setup specialised loggers
logger = logging_setup(AppConfig.LOG_PATH, "ORCHESTRATOR")

def main():
    """
    The main execution entry point for the MindFuel Email Automation system.
    
    This function coordinates the end-to-end workflow:
    1. Validates environment and loads the daily quote.
    2. Iterates through subscribers in batches.
    3. Conditionally processes weekly subscribers (Mondays only).
    4. Calculates performance metrics and sends a summary alert to the admin.
    5. Handles critical failures by sending an emergency notification.
    """
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
        # Load the quote
        quote, author = get_quote(AppConfig.FILE_PATH)
        
        if not quote:
            logger.critical("Aborting Run: Quote file missing or empty. Run fetch_quote.py first.")
            return
        else:
            logger.info(f"Quote loaded successfully: '{quote[:30]}...' by {author}")

        # Database Session Management   
        with Session() as session:
        # Process Daily Subscribers
            logger.info("Attempting to fetch daily subscribers")
            for batch in fetch_users_in_batches('daily'):
                process_user_batch(batch, quote, author, stats, session)
                stats['daily'] += len(batch)
            logger.info(f"Completed daily subscribers: {stats['daily']} users processed.")

        # Process Weekly Subscribers (only if today is Monday)
        if day_name == "Monday":
            logger.info("It's Monday: Attempting to fetch weekly subscribers")
            for batch in fetch_users_in_batches('weekly'):
                process_user_batch(batch, quote, author, stats, session)
                stats['weekly'] += len(batch)
            logger.info(f"Completed weekly subscribers: {stats['weekly']} users processed")
        else:
            logger.info(f"Skipping weekly subscribers (Today is {day_name}).")

        # Finalise statistics and performance
        duration = time.time() - start_time
        
        # Log detailed stats to summary log file
        log_final_summary(stats, day_name, duration)

        # Generate and send email alert to admin
        summary_text = generate_summary(stats, day_name, duration, success=True)
        send_alert_email(summary_text, subject=f"MindFuel Report: {day_name}")

        logger.info(f"====== AUTOMATION COMPLETED IN {duration:.2f}s ======")

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"CRITICAL SYSTEM FAILURE: {e}", exc_info=True)
        
        # Send pipeline failure alert
        summary_text = generate_summary(stats, day_name, duration, success=False)
        send_alert_email(summary_text, subject=f"CRITICAL FAILURE: MindFuel {day_name}")
        
        # Exit with a failure code for cron job monitoring
        sys.exit(1)

if __name__ == "__main__":
    main()