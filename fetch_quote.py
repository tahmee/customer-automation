import time

# configuration imports
from config.setup_config import logging_setup, LOG_PATH, api_dirs

# API processing imports
from src.api_ingest import fetch_api_data, cache_quote, save_api_data        

# logging and directories setup
logger = logging_setup(LOG_PATH, __name__)
api_dirs()

MAX_RETRIES=3


def main():
    """
    Main entry point for daily quote fetcher.

    Workflow:
        1. Check if today's quote is already cached
        2. If cached, display it to user
        3. If not cached, fetch from ZenQuotes API
        4. Save fetched quote and display success message

    Raises:
        RuntimeError: If API fetch fails or file save fails
    """
    try:
        logger.info("========== Starting daily quote fetch ==========")

        # Check if there's today's quote cached
        cached_quote = cache_quote()

        if not cached_quote:
            api_data = fetch_api_data() 
            if not api_data:
                retries = 0
                logger.warning("Initial fetch failed, retrying...")
                while retries < MAX_RETRIES + 1:
                        time.sleep(2 ** retries)  # Exponential backoff
                        api_data = fetch_api_data()
                        retries += 1
                        if api_data:
                            logger.info(f"Retry {retries + 1} succeeded")
                            break
                
                if not api_data:  # Check AFTER retry loop
                    logger.error(f"Failed to fetch data after {MAX_RETRIES} retries")
                    raise RuntimeError("API fetch failed")

            if not save_api_data(api_data): 
                logger.error("Failed to save quote data to file")
                raise RuntimeError("Failed to save quote")
            
        else: 
            logger.info(f"Quote '{cached_quote['quote'][:20]}...' already cached for the day")   

    except Exception as e:
        print(f"Critical error. Check logs: {LOG_PATH}")
        logger.critical(f"Script failed; Unexpected error: {e}", exc_info=True)
        raise
       


if __name__ == "__main__":
    main()


