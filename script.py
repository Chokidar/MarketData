import sqlite3
import secrets
import bcrypt
import re
import logging
from contextlib import contextmanager

# Set up secure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='user_database.log'
)
logger = logging.getLogger('user_database')

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
        # Validate username
        if not username or not isinstance(username, str) or len(username) < 3:
            raise ValueError("Username must be a string of at least 3 characters")
        
        # More robust email validation with regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not email or not isinstance(email, str) or not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        return True
    
    def add_user(self, username, password, email):
        try:
            # Validate inputs
            self.validate_input(username, email)
            
            if not password or not isinstance(password, str) or len(password) < 8:
                raise ValueError("Password must be a string of at least 8 characters")
            
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
                logger.info(f"User created: {username}")
                return True
        except sqlite3.IntegrityError:
            # Handle duplicate username without exposing details
            logger.warning(f"Failed to create user: integrity constraint violated")
            raise ValueError("Username already exists")
        except Exception as e:
            # Log the error securely without exposing internals
            logger.error(f"Error in add_user: {type(e).__name__}")
            raise RuntimeError("Failed to create user") from e
    
    def authenticate(self, username, password):
        try:
            if not username or not password:
                return None
                
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, password FROM users WHERE username = ?",
                    (username,)
                )
                user = cursor.fetchone()
                
                if user and bcrypt.checkpw(password.encode(), user[1]):
                    # Return only the user ID, not the full record
                    logger.info(f"Successful authentication for user ID: {user[0]}")
                    return user[0]
                
                logger.warning(f"Failed authentication attempt for username: {username}")
                return None
        except Exception as e:
            # Log the error securely
            logger.error(f"Authentication error: {type(e).__name__}")
            raise RuntimeError("Authentication failed") from e
    
    def get_user_by_id(self, user_id):
        try:
            # Ensure user_id is an integer
            if not isinstance(user_id, int):
                user_id = int(user_id)  # Try to convert, will raise ValueError if not possible
                
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, username, email FROM users WHERE id = ?", 
                    (user_id,)
                )
                result = cursor.fetchone()
                if not result:
                    logger.info(f"No user found with ID: {user_id}")
                return result
        except ValueError:
            logger.error(f"Invalid user ID format: {user_id}")
            raise ValueError("User ID must be a valid integer")
        except Exception as e:
            logger.error(f"Error retrieving user: {type(e).__name__}")
            raise RuntimeError(f"Failed to retrieve user") from e
    
    def update_email(self, user_id, current_user_id, new_email):
        try:
            # Ensure IDs are integers for comparison
            user_id = int(user_id) if not isinstance(user_id, int) else user_id
            current_user_id = int(current_user_id) if not isinstance(current_user_id, int) else current_user_id
            
            # Authorization check
            if user_id != current_user_id:
                logger.warning(f"Unauthorized email update attempt: User {current_user_id} tried to update User {user_id}")
                raise PermissionError("Not authorized to update this user's email")
                
            # Email validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not new_email or not isinstance(new_email, str) or not re.match(email_pattern, new_email):
                raise ValueError("Invalid email format")
                
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET email = ? WHERE id = ?",
                    (new_email, user_id)
                )
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Email updated for user ID: {user_id}")
                    return True
                else:
                    logger.warning(f"No email updated for user ID: {user_id} - user not found")
                    return False
        except Exception as e:
            logger.error(f"Error updating email: {type(e).__name__}")
            raise RuntimeError("Failed to update email") from e

# For demonstration purposes only
if __name__ == "__main__":
    try:
        # In a real application, these would come from environment variables or a secure config
        # import os
        # test_user = os.environ.get("TEST_USER")
        # test_password = os.environ.get("TEST_PASSWORD")
        # test_email = os.environ.get("TEST_EMAIL")
        
        # This is commented out to prevent execution with hardcoded credentials
        '''
        db = UserDatabase()
        user_created = db.add_user("testuser", "securePassword123!", "test@example.com")
        if user_created:
            user_id = db.authenticate("testuser", "securePassword123!")
            if user_id:
                user_data = db.get_user_by_id(user_id)
                if user_data:
                    print(f"User found with ID: {user_data[0]}")
                email_updated = db.update_email(user_id, user_id, "updated@example.com")
                if email_updated:
                    print("Email updated successfully")
        '''
        print("To use this module, import it and create instances programmatically.")
        print("Do not use the example code in production environments.")
    except Exception as e:
        logger.critical(f"Critical error in main execution: {e}")
