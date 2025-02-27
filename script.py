import requests
import sqlite3
import re

def get_current_price(symbol):
    """
    Get the current price for a stock symbol from the API.
    Includes error handling for API requests.
    """
    if not is_valid_symbol(symbol):
        raise ValueError(f"Invalid stock symbol: {symbol}")

    try:
        response = requests.get(f'https://api.example.com/v1/prices/{symbol}', timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()['price']
    except requests.exceptions.RequestException as e:
        # Handle network errors, timeouts, and HTTP errors
        print(f"API request failed: {e}")
        raise
    except (KeyError, ValueError) as e:
        # Handle JSON parsing errors or missing 'price' key
        print(f"Error parsing API response: {e}")
        raise

def is_valid_symbol(symbol):
    """
    Validate that the symbol follows a typical stock symbol pattern.
    """
    if not symbol:
        return False
    # Basic pattern: 1-5 uppercase letters
    pattern = re.compile(r'^[A-Z]{1,5}$')
    return bool(pattern.match(symbol))

def log_price(symbol, price):
    """
    Log the price to the database using parameterized queries to prevent SQL injection.
    Includes error handling for database operations.
    """
    conn = None
    try:
        conn = sqlite3.connect('prices.db')
        cur = conn.cursor()
        # Use parameterized query to prevent SQL injection
        cur.execute("INSERT INTO prices (symbol, price) VALUES (?, ?)", (symbol, price))
        conn.commit()
    except sqlite3.Error as e:
        # Roll back any changes if something goes wrong
        if conn:
            conn.rollback()
        print(f"Database error: {e}")
        raise
    finally:
        # Ensure connection is closed even if an exception occurs
        if conn:
            conn.close()

def main():
    try:
        symbol = 'AAPL'
        price = get_current_price(symbol)
        log_price(symbol, price)
        print(f"{symbol}: ${price}")
    except Exception as e:
        print(f"Error in main function: {e}")
        return 1  # Return error code
    return 0  # Return success code

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
