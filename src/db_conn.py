from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config.setup_config import logging_setup, AppConfig

logger=logging_setup(AppConfig.LOG_PATH, __name__)

CHUNK_SIZE = 1000

# Create database engine
try:
    logger.info("====== BEGIN EMAIL AUTOMATION SCRIPT ======")
    engine = create_engine(AppConfig.DB_CREDENTIALS, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise


def fetch_users_in_batches(email_frequency, batch_size=CHUNK_SIZE):
    """
    Fetch users in batches from database.
    """
    total_fetched = 0
    
    with Session() as session:
        while True:
            try:
                query = text("""
                    SELECT user_id, first_name, email_address
                    FROM users
                    WHERE subscription_status = 'active'
                        AND email_frequency = :frequency
                        AND (last_email_sent_at < CURRENT_DATE OR last_email_sent_at IS NULL)
                    ORDER BY user_id ASC
                    LIMIT :limit;
                """)
                    
                result = session.execute(query, {"frequency": email_frequency, "limit": batch_size})
                    
                batch = [dict(row) for row in result.mappings()]
                
                if not batch:
                    # No more records
                    logger.info("Daily automation: All users have been processed for today.")
                    break

                yield batch   

                batch_ids = [u['user_id'] for u in batch]
                session.execute(
                    text("UPDATE users SET last_email_sent_at = CURRENT_TIMESTAMP WHERE user_id IN :ids"),
                    {"now": datetime.now(), "ids": tuple(batch_ids)}
                )
                session.commit()

                total_fetched += len(batch)
                logger.info(f"Processed and updated {len(batch)} {email_frequency} users (Total so far: {total_fetched})")
                    
            except Exception as e:
                session.rollback() # undo changes if update fails
                logger.error(f"Error in daily batch: {e}", exc_info=True)
                raise
