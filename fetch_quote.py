import sys
import time
from config.setup_config import logging_setup, API_LOG_PATH, api_dirs
from src.api_ingest import fetch_api_data, cache_quote, save_api_data        

# Logging config
logger = logging_setup(API_LOG_PATH, __name__)

# Number of times to re-attempt the API call before giving up
MAX_RETRIES=3


def main():
    """
    Orchestrates the daily quote retrieval process.
    
    The workflow follows these steps:
    1. Ensures required directories exist.
    2. Checks the local cache to avoid redundant API calls.
    3. Attempts to fetch a new quote with a retry mechanism (exponential backoff).
    4. Saves the successful response to a JSON file for the email pipeline.
    
    Raises:
        RuntimeError: If data cannot be fetched or saved after all attempts.
    """
    # Ensure logs and data directories are initialised
    api_dirs()

    try:
        logger.info("==Starting daily quote fetch ==")

        # Check if a valid quote for today is already stored locally
        cached_quote = cache_quote()

        if cached_quote:
            logger.info(f"Quote '{cached_quote['quote'][:20]}...' already cached for today.")
            return  # Exit cache_quote function if no new fetch is needed

        # API Fetch Logic with exponential backoff
        api_data = None
        for attempt in range(MAX_RETRIES + 1):
            api_data = fetch_api_data()
            if api_data:
                # Successfully retrieved data, break the retry loop
                break

            if attempt < MAX_RETRIES:
                wait = 2 ** attempt 
                logger.warning(f"Attempt {attempt + 1} retrying...")
                time.sleep(wait)
                
        # Post-fetch Validation
        if not api_data: 
            logger.error(f"Failed to fetch data after {MAX_RETRIES} retries")
            raise RuntimeError("API fetch failed")

        # Persist the data
        if not save_api_data(api_data): 
            logger.error("Failed to save quote data to file")
            raise RuntimeError("Failed to save quote")
        
        logger.info("== Daily quote fetch completed successfully ==")
            
    except Exception as e:
        print(f"Critical error. Check logs: {API_LOG_PATH}")
        logger.critical(f"Script failed; Unexpected error: {e}", exc_info=True)
        sys.exit(1)
       

if __name__ == "__main__":
    main()


