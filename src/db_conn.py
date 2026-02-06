import json
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config.setup_config import logging_setup, AppConfig

# Logging config
logger=logging_setup(AppConfig.LOG_PATH, __name__)

# Determines how many user records are pulled into memory at once
CHUNK_SIZE = 1000

# Global placeholders for database engine and session
engine = None
Session = sessionmaker()


def initialize_engine():
    """
    Creates the database engine and configures the Session.
    
    Raises:
        Exception: If the database connection cannot be established.
    """
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
    """
    Retrieves the last user ID processed from the last successful run.
    
    This function ensures that if the script crashes, it can resume exactly where 
    it left off by reading from the checkpoint file.

    Returns:
        int: The last processed user_id, or 0 if no checkpoint exists or is invalid.
    """
    if os.path.exists(AppConfig.CHECKPOINT_FILE):
        try:
            with open(AppConfig.CHECKPOINT_FILE, 'r') as f:
                # Retrieve the persistent user_id required to continue the pipeline
                return json.load(f).get('max_id', 0)
        except Exception: return 0
    return 0


def save_checkpoint(last_id):
    """
    Persists the current progress by saving the last processed ID to a JSON file.
    
    Args:
        last_id (int): The user_id of the final record in the most recent successful batch.
    """
    with open(AppConfig.CHECKPOINT_FILE, 'w') as f:
        # Store both the ID and a timestamp
        json.dump({'max_id': last_id, 'updated_at': str(datetime.now())}, f)


def fetch_users_in_batches(email_frequency, batch_size=CHUNK_SIZE):
    """
    A generator that yields retrieved batch of 'active' users for processing.

    This function uses uses the database connection to retrieve subscribed users from the database is batches.

    Args:
        email_frequency (str): Filter for user preference (e.g. 'daily', 'weekly').
        batch_size (int, optional): Number of records per batch. Defaults to CHUNK_SIZE.

    Yields:
        list[dict]: A batch of user records (user_id, first_name, email_address).

    Raises:
        Exception: If a database error occurs during query execution.
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
                        
                    # Execute the query and map rows to dictionaries for easy access    
                    result = session.execute(query, {"frequency": email_frequency, "limit": batch_size, "last_id": last_id})
                        
                    batch = [dict(row) for row in result.mappings()]
                    
                    if not batch:
                        # End of the table reached: Reset checkpoint for the next full run cycle
                        logger.info(f"All {email_frequency} users have been processed for today.")
                        save_checkpoint(0)
                        break
                    
                    # Update local tracking to the last user in the current batch
                    last_id = batch[-1]['user_id']

                    # Return the batch to the caller, then resume here for the next iteration
                    yield batch

    except Exception as e:
        logger.error(f"Database Fetch Error: Failed to retrieve batch after ID {last_id}. Error: {e}", exc_info=True)
        raise

# Automatically initialize connection when the module is imported
initialize_engine()