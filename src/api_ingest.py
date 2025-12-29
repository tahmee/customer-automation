import requests
import json
import os
from dotenv import load_dotenv 
from datetime import datetime
from config.setup_config import logging_setup, API_LOG_PATH, OUTPUT_PATH

# Load environment variables
load_dotenv()

# logging config
logger = logging_setup(API_LOG_PATH, __name__)

# Assign API url
zq_today_api = os.getenv("API_URL")


def fetch_api_data(url=zq_today_api, api_timeout=10):
    """
    Fetches quote data from ZenQuotes API.
    
    Args:
        url (str, optional): The API endpoint. Defaults to zq_today_api.
        api_timeout (int, optional): Seconds to wait before timing out. Defaults to 10.
    
    Returns:
        dict | None: The raw dictionary for the first quote in the list if successful, 
                     otherwise None if a network or parsing error occurs.
    """
    try:
        logger.info(f"Fetch attempt from {url.split('/')[2]}")
        response = requests.get(url, timeout=api_timeout)
        logger.info(f"Response status code: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()
            except ValueError as e:
                logger.error(f"Failed to parse JSON: {e}")
                logger.error(f"Raw response: {response.text[:200]}")
                raise
            
            logger.info("Data successfully retrieved and parsed")

            # Confirm data returned is not empty and return the first item.
            if data and len(data) > 0:
                quote_data = data[0]
                return quote_data
            else:
                logger.error(f"API returned invalid/empty data.")
                return None
        else:
            logger.error(f"Failed to retrieve data. Status code: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            response.raise_for_status()

    except requests.exceptions.Timeout:
        logger.error(f"Request timed out.")
        return None
        
    except requests.exceptions.ConnectionError:
        logger.error(f"A connection error occurred for {url.split('/')[2]}")
        return None
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        return None
        

def save_api_data(data, filename=OUTPUT_PATH):
    """
    Validates, transforms, and persists quote data to a local JSON file.
    
    The function converts shorthand API keys (q, a) into more descriptive 
    ones (quote, author) and appends execution metadata.
    
     Args:
        data (dict): The raw dictionary returned by the ZenQuotes API.
        filename (str, optional): Path where the JSON file will be stored. 
                                  Defaults to OUTPUT_PATH.
    
    Returns:
        bool: True if file write was successful, False if validation or process failed.
    """
    try:
        logger.info(f"Attempting to save quote to {filename.split('/')[1]}")

        # Extract values using API keys: 'q' = quote, 'a' = author
        quote = data.get('q')
        author = data.get('a')

        # Emsure partly missing or malformed data is not saved
        if not quote or not author:
            logger.error(
                f"Malformed quote data: 'q' or 'a' key missing or value is empty. "
                f"Keys received: {list(data.keys())}"
            )
            return None
            
        # Data transformation: map to readable keys and add time metadata
        now = datetime.now()
        formatted_quote = {
            'quote': quote,
            'author': author,
            'date': now.strftime('%Y-%m-%d'),
            'fetched_at': now.isoformat()
        }

        # Log a snippet of the quote for verification
        logger.info(f"Today's quote: '{quote[:50]}...' by {author}")
        
        # Save to local disk with indentation for readability
        with open(filename, 'w') as file:
            json.dump(formatted_quote, file, indent=2, ensure_ascii=False)
            logger.info(f"Quote successfully saved to {filename.split('/')[1]}")
            return True

    except PermissionError:
        logger.error(f"Permission denied: Cannot write to {filename.split('/')[1]}")
        return False
    except OSError as e:
        logger.error(f"OS error while saving file: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while trying to save to file: {e}", exc_info=True)
        return False  
    

def cache_quote(filename=OUTPUT_PATH):
    """
    Checks if a valid, up-to-date quote already exists on disk.
    
    This function helps avoid unnecessary API calls (rate limiting) if the script 
    is run multiple times on the same day.

    Args:
        filename (str, optional): Path to the JSON file to check. 
                                  Defaults to OUTPUT_PATH.
    
    Returns:
        dict | None: The cached quote if it matches today's date, 
                     otherwise None if the cache is old, missing, or corrupt.
    """
    try:
        # Check if the file exists before attempting to open
        if not os.path.exists(filename):
            logger.debug("No cached quote file found")
            return None
            
        with open(filename, 'r') as file:
            cached_data = json.load(file)

        # Structure Validation: Ensure all expected keys exist in the dict
        required_keys = {'quote', 'author', 'date', 'fetched_at'}
        if not all(key in cached_data for key in required_keys):
            missing = required_keys - set(cached_data.keys())
            logger.warning(f"Cached file missing required keys: {missing}")
            return None
        
        # Freshness Check: Checks if the quote is from today
        today = datetime.now().strftime('%Y-%m-%d')
        if cached_data.get('date') == today:
            logger.info(f"Quote for today: ({today}) already cached")
            return cached_data
        else:
            logger.info(f"Cached quote is old (from {cached_data.get('date')}), fetching new one")
            return None

    except FileNotFoundError:
        logger.debug("No cached quote file found")
        return None
    
    except json.JSONDecodeError as e:
        logger.warning(f"Cached quote file corrupted: {e}")
        return None

    except Exception as e:
        logger.warning(f"Could not load cached quote: {e}")
        return None
