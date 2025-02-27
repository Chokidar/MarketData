import requests
import sqlite3
import os
from requests.exceptions import RequestException

def get_current_price(symbol):
    """Get the current price of a stock symbol from the API.
    
    Args:
        symbol (str): The stock symbol to look up
        
    Returns:
        float: The current price of the stock
        
    Raises:
        RequestException: If there is a network error
        ValueError: If the API returns invalid data
    """
    try:
        response = requests.get(f'https://api.example.com/v1/prices/{symbol}')
        response.raise_for_status()  # Raise exception for 4XX/5XX responses

        data = response.json()
        if 'price' not in data:
            raise ValueError(f"API response missing 'price' field: {data}")

        return data['price']
    except RequestException as e:
        # Log the error and re-raise or handle appropriately
        print(f"Network error when fetching price for {symbol}: {e}")
        raise

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
        print(f"Database error: {e}")
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

        symbol = 'AAPL'
        price = get_current_price(symbol)
        log_price(symbol, price)
        print(f"{symbol}: ${price}")
    except Exception as e:
        print(f"Error in main: {e}")
        # Non-zero exit code to indicate failure to calling process
        exit(1)

if __name__ == "__main__":
    main()
