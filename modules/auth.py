from datetime import datetime, timezone

import jwt
import bcrypt
import datetime
from config import SECRET_KEY
from database.models import User
import logging


class Auth:
    @staticmethod
    def hash_password(password):
        """Hash a password for storing."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(stored_password, provided_password):
        """Verify a stored password against one provided by user"""
        return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

    @staticmethod
    def generate_token(user_id):
        """Generate JWT token for authentication"""
        payload = {
            'user_id': user_id,
            'exp': datetime.now(timezone.utc) + datetime.timedelta(days=1),
            'iat': datetime.now(timezone.utc)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    @staticmethod
    def verify_token(token):
        """Verify JWT token and return user_id if valid"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            return payload['user_id']
        except jwt.ExpiredSignatureError:
            logging.warning("Expired token attempted to be used")
            return None
        except jwt.InvalidTokenError:
            logging.warning("Invalid token attempted to be used")
            return None

    @staticmethod
    def register_user(username, email, password, first_name, last_name, national_id, date_of_birth, address,
                      phone=None):
        """Register a new user"""
        # Check if user already exists
        if User.get_by_username(username) or User.get_by_email(email):
            return None, "Username or email already exists"

        # Hash password and create user
        password_hash = Auth.hash_password(password)
        user_id = User.create(
            username, email, password_hash, first_name, last_name,
            national_id, date_of_birth, address, phone
        )

        if user_id:
            return user_id, "User registered successfully"
        return None, "Failed to register user"

    @staticmethod
    def login(username, password):
        """Authenticate a user and return a token"""
        user = User.get_by_username(username)
        if not user:
            return None, "Invalid username or password"

        if Auth.verify_password(user['password_hash'], password):
            token = Auth.generate_token(user['id'])
            return token, "Login successful"

        return None, "Invalid username or password"
