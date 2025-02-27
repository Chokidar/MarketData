import sqlite3
import secrets
import bcrypt
from contextlib import contextmanager

class UserDatabase:
    def __init__(self, db_path="users.db"):
        self.db_path = db_path
        self.connection = None
        self.create_tables()
    
    @contextmanager
    def get_connection(self):
        try:
            connection = sqlite3.connect(self.db_path)
            yield connection
        finally:
            if connection:
                connection.close()
    
    def create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT,
                email TEXT,
                api_key TEXT UNIQUE
            )
            ''')
            conn.commit()
    
    def validate_input(self, username, email):
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters")
        
        if not email or '@' not in email or '.' not in email:
            raise ValueError("Invalid email format")
        
        return True
    
    def add_user(self, username, password, email):
        try:
            # Validate inputs
            self.validate_input(username, email)
            
            # Strong password hashing with bcrypt
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password.encode(), salt)
            
            # Secure API key generation
            api_key = secrets.token_hex(16)  # 32 character hex string (16 bytes)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password, email, api_key) VALUES (?, ?, ?, ?)",
                    (username, hashed_password, email, api_key)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            # Handle duplicate username
            return False
        except Exception as e:
            # Log the error securely
            print(f"Error adding user: {type(e).__name__}")
            return False
    
    def authenticate(self, username, password):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, password FROM users WHERE username = ?",
                    (username,)
                )
                user = cursor.fetchone()
                
                if user and bcrypt.checkpw(password.encode(), user[1]):
                    # Return only the user ID, not the full record
                    return user[0]
                return None
        except Exception as e:
            # Log the error securely
            print(f"Authentication error: {type(e).__name__}")
            return None
    
    def get_user_by_id(self, user_id):
        try:
            if not isinstance(user_id, int):
                raise TypeError("User ID must be an integer")
                
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, username, email FROM users WHERE id = ?", 
                    (user_id,)
                )
                return cursor.fetchone()
        except Exception as e:
            print(f"Error retrieving user: {type(e).__name__}")
            return None
    
    def update_email(self, user_id, current_user_id, new_email):
        try:
            # Authorization check
            if user_id != current_user_id:
                raise PermissionError("Not authorized to update this user's email")
                
            if not new_email or '@' not in new_email or '.' not in new_email:
                raise ValueError("Invalid email format")
                
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET email = ? WHERE id = ?",
                    (new_email, user_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating email: {type(e).__name__}")
            return False

if __name__ == "__main__":
    # Example usage for testing - would not be in production code
    db = UserDatabase()
    
    # Register a test user - in production, get inputs from a secure form
    try:
        user_created = db.add_user("testuser", "securePassword123!", "test@example.com")
        if user_created:
            # Authenticate
            user_id = db.authenticate("testuser", "securePassword123!")
            if user_id:
                # Retrieve user data
                user_data = db.get_user_by_id(user_id)
                if user_data:
                    print(f"User found with ID: {user_data[0]}")
                
                # Update email with proper authorization
                email_updated = db.update_email(user_id, user_id, "updated@example.com")
                if email_updated:
                    print("Email updated successfully")
    except Exception as e:
        print(f"An error occurred: {e}")
