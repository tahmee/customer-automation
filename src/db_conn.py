import json
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config.setup_config import logging_setup, AppConfig


logger=logging_setup(AppConfig.LOG_PATH, __name__)
CHUNK_SIZE = 1000


engine = None
Session = sessionmaker()


def initialize_engine():
    # Create database engine
    global engine, Session
    try:
        logger.info(f"=== INITIALIZING DATABASE ENGINE ===")
        engine = create_engine(AppConfig.DB_CREDENTIALS, pool_pre_ping=True)
        Session.configure(bind=engine)
        logger.info("Database engine created successfully")
    except Exception as e:
        logger.critical(f"Failed: Could not establish database connection: {e}")
        raise 


def get_last_processed_id():
    if os.path.exists(AppConfig.CHECKPOINT_FILE):
        try:
            with open(AppConfig.CHECKPOINT_FILE, 'r') as f:
                return json.load(f).get('max_id', 0)
        except Exception: return 0
    return 0


def save_checkpoint(last_id):
    with open(AppConfig.CHECKPOINT_FILE, 'w') as f:
        json.dump({'max_id': last_id, 'updated_at': str(datetime.now())}, f)


def fetch_users_in_batches(email_frequency, batch_size=CHUNK_SIZE):
    """
    Fetch users in batches from database.
    """
    last_id = get_last_processed_id()
    
    try:
        with Session() as session:
            while True:
                    query = text("""
                        SELECT user_id, first_name, email_address
                        FROM users
                        WHERE subscription_status = 'active'
                            AND email_frequency = :frequency
                            AND user_id > :last_id
                            AND (last_email_sent_at < CURRENT_DATE OR last_email_sent_at IS NULL)
                        ORDER BY user_id ASC
                        LIMIT :limit;
                    """)
                        
                    # Execute the query    
                    result = session.execute(query, {"frequency": email_frequency, "limit": batch_size, "last_id": last_id})
                        
                    batch = [dict(row) for row in result.mappings()]
                    
                    if not batch:
                        # No more records
                        logger.info(f"All {email_frequency} users have been processed for today.")
                        save_checkpoint(0)
                        break
                    
                    last_id = batch[-1]['user_id']

                    yield batch

    except Exception as e:
        logger.error(f"Database Fetch Error: Failed to retrieve batch after ID {last_id}. Error: {e}", exc_info=True)
        raise







initialize_engine()