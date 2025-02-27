import requests
import sqlite3
import os
import sys
import logging
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='stock_price.log'
)
logger = logging.getLogger(__name__)

def get_current_price(symbol, api_key):
    """Get the current price of a stock symbol from the API.
    
    Args:
        symbol (str): The stock symbol to look up
        api_key (str): API key for authentication
        
    Returns:
        float: The current price of the stock
        
    Raises:
        RequestException: If there is a network error
        ValueError: If the API returns invalid data
    """
    try:
        # Include API key in headers for authentication
        headers = {'Authorization': f'Bearer {api_key}'}
        response = requests.get(
            f'https://api.example.com/v1/prices/{symbol}', 
            headers=headers
        )
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        data = response.json()
        if 'price' not in data:
            raise ValueError(f"API response missing 'price' field")
        return data['price']
    except RequestException as e:
        # Log the error without potentially exposing sensitive info
        logger.error(f"Network error when fetching price for {symbol}")
        logger.debug(f"Details: {str(e)}")
        raise

def ensure_db_setup():
    """Ensure the database and required tables exist."""
    conn = None
    try:
        conn = sqlite3.connect('prices.db')
        cur = conn.cursor()
        # Create table if it doesn't exist
        cur.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database setup error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def log_price(symbol, price):
    """Log a stock price to the database.
    
    Args:
        symbol (str): The stock symbol
        price (float): The current price
    """
    conn = None
    try:
        conn = sqlite3.connect('prices.db')
        cur = conn.cursor()
        # Use parameterized query to prevent SQL injection
        cur.execute(
            "INSERT INTO prices (symbol, price) VALUES (?, ?)",
            (symbol, price)
        )
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database error when logging price for {symbol}")
        logger.debug(f"Details: {str(e)}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def main():
    """Main function to retrieve and log a stock price."""
    try:
        # Get API key from environment variable instead of hardcoding
        api_key = os.environ.get('API_KEY')
        if not api_key:
            raise ValueError("API_KEY environment variable not set")
            
        # Ensure database is set up before proceeding
        ensure_db_setup()
        
        symbol = 'AAPL'
        price = get_current_price(symbol, api_key)
        log_price(symbol, price)
        logger.info(f"{symbol}: ${price}")
        print(f"{symbol}: ${price}")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        # Non-zero exit code to indicate failure to calling process
        sys.exit(1)

if __name__ == "__main__":
    main()
