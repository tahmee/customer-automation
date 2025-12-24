import sys
import time
from config.setup_config import logging_setup, API_LOG_PATH, api_dirs
from src.api_ingest import fetch_api_data, cache_quote, save_api_data        


logger = logging_setup(API_LOG_PATH, __name__)
#api_dirs()
MAX_RETRIES=3


def main():
    api_dirs()
    try:
        logger.info("==Starting daily quote fetch ==")

        # Check if there's today's quote cached
        cached_quote = cache_quote()

        if cached_quote:
            logger.info(f"Quote '{cached_quote['quote'][:20]}...' already cached for today.")
            return

        api_data = None
        for attempt in range(MAX_RETRIES + 1):
            api_data = fetch_api_data()
            if api_data:
                break

            if attempt < MAX_RETRIES:
                wait = 2 ** attempt 
                logger.warning(f"Attempt {attempt + 1} retrying...")
                time.sleep(wait)
                
        if not api_data:  # Check AFTER retry loop
            logger.error(f"Failed to fetch data after {MAX_RETRIES} retries")
            raise RuntimeError("API fetch failed")

        if not save_api_data(api_data): 
            logger.error("Failed to save quote data to file")
            raise RuntimeError("Failed to save quote")
            
    except Exception as e:
        print(f"Critical error. Check logs: {API_LOG_PATH}")
        logger.critical(f"Script failed; Unexpected error: {e}", exc_info=True)
        sys.exit(1)
       

if __name__ == "__main__":
    main()


