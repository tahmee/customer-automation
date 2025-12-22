import requests
import json
import os
from dotenv import load_dotenv 
from datetime import datetime
from config.setup_config import logging_setup, API_LOG_PATH, OUTPUT_PATH

# logging config
logger = logging_setup(API_LOG_PATH, __name__)

load_dotenv()

zq_today_api = os.getenv("API_URL")


def fetch_api_data(url=zq_today_api, api_timeout=10):
    """
    Fetches quote data from ZenQuotes API.
    
    Args:
        url (str, optional): API endpoint URL. Defaults to zq_today_api.
        api_timeout (int, optional): Request timeout in seconds. Defaults to 10.
    
    Returns:
        dict | None: First quote object from API response containing 'q' (quote) 
                     and 'a' (author) keys, or None if request fails.
    
    Note:
        ZenQuotes API returns an array with a single quote object. This function
        extracts and returns only the first element.
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
                return None
            
            logger.info("Data successfully retrieved and parsed")


            if data and len(data) > 0:
                quote_data = data[0]
                return quote_data
            else:
                logger.error(f"API returned invalid/empty data.")
                return None
        else:
            logger.error(f"Failed to retrieve data. Status code: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return None

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
    Validates, formats, and saves quote data to JSON file.
    
    Args:
        data (dict): Raw quote data from API with 'q' (quote) and 'a' (author) keys.
        filename (str, optional): Output file path. Defaults to OUTPUT_PATH.
    
    Returns:
        bool: True if save successful, False otherwise.
    
    Note:
        Transforms API keys ('q', 'a') to readable format ('quote', 'author') and
        adds date/timestamp metadata before saving.
    """
    try:
        logger.info(f"Attempting to save quote to {filename.split('/')[1]}")

        # Extract and validate values
        quote = data.get('q')
        author = data.get('a')

        # Check for missing keys or empty values (malformed data)
        if not quote or not author:
            logger.error(
                f"Malformed quote data: 'q' or 'a' key missing or value is empty. "
                f"Keys received: {list(data.keys())}"
            )
            return None
            
        # Data formatting (only if validation passes)
        now = datetime.now()
        formatted_quote = {
            'quote': quote,
            'author': author,
            'date': now.strftime('%Y-%m-%d'),
            'fetched_at': now.isoformat()
        }

        logger.info(f"Today's quote: '{quote[:50]}...' by {author}")
        
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
    Loads cached quote from file if it exists and is from today.
    
    Args:
        filename (str, optional): Path to cached quote file. Defaults to OUTPUT_PATH.
    
    Returns:
        dict | None: Quote data with 'quote', 'author', 'date', and 'fetched_at' keys
                     if valid cache exists and is from today, otherwise None.
    
    Note:
        Cache is considered invalid if file is missing, corrupted, from a different
        date, or missing required keys.
    """
    try:
        if not os.path.exists(filename):
            logger.debug("No cached quote file found")
            return None
            
        with open(filename, 'r') as file:
            cached_data = json.load(file)

        # Validate cache structure
        required_keys = {'quote', 'author', 'date', 'fetched_at'}
        if not all(key in cached_data for key in required_keys):
            missing = required_keys - set(cached_data.keys())
            logger.warning(f"Cached file missing required keys: {missing}")
            return None
        
        # Check if cache is from today
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
