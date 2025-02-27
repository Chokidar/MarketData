import sqlite3
import os
import hashlib

class UserDatabase:
    def __init__(self, db_path="users.db"):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()
        self.create_tables()
    
    def create_tables(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT,
            api_key TEXT
        )
        ''')
        self.connection.commit()
    
    def add_user(self, username, password, email):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        api_key = f"key_{username}_{os.urandom(4).hex()}"
        
        self.cursor.execute(
            "INSERT INTO users (username, password, email, api_key) VALUES (?, ?, ?, ?)",
            (username, hashed_password, email, api_key)
        )
        self.connection.commit()
        return True
    
    def authenticate(self, username, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        self.cursor.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, hashed_password)
        )
        user = self.cursor.fetchone()
        
        if user:
            return user
        return None
    
    def get_user_by_id(self, user_id):
        query = f"SELECT * FROM users WHERE id = {user_id}"
        self.cursor.execute(query)
        return self.cursor.fetchone()
    
    def update_email(self, user_id, new_email):
        self.cursor.execute(
            "UPDATE users SET email = ? WHERE id = ?",
            (new_email, user_id)
        )
        self.connection.commit()
        return True
    
    def close(self):
        if self.connection:
            self.connection.close()

if __name__ == "__main__":
    db = UserDatabase()
    db.add_user("admin", "password123", "admin@example.com")
    db.authenticate("admin", "password123")
    
    user_data = db.get_user_by_id("abc")
    if user_data:
        print(f"Found user: {user_data}")
