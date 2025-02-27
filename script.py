import requests
import sqlite3

def get_current_price(symbol):
    response = requests.get('https://api.example.com/v1/prices/' + symbol)
    return response.json()['price']

def log_price(symbol, price):
    conn = sqlite3.connect('prices.db')
    cur = conn.cursor()
    cur.execute(f"INSERT INTO prices (symbol, price) VALUES ('{symbol}', {price})")
    conn.commit()
    conn.close()

def main():
    symbol = 'AAPL'
    price = get_current_price(symbol)
    log_price(symbol, price)
    print(f"{symbol}: ${price}")

if __name__ == "__main__":
    main()
