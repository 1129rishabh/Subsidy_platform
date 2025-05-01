from database.models import User
import logging


class UserManager:
    @staticmethod
    def get_user_profile(user_id):
        """Get user profile information"""
        user = User.get_by_id(user_id)
        if not user:
            return None, "User not found"

        # Remove sensitive information
        if 'password_hash' in user:
            del user['password_hash']

        return user, "User profile retrieved successfully"

    @staticmethod
    def update_user_profile(user_id, **kwargs):
        """Update user profile information"""
        # Verify user exists
        user = User.get_by_id(user_id)
        if not user:
            return False, "User not found"

        # Update user information
        success = User.update(user_id, **kwargs)
        if success:
            return True, "Profile updated successfully"
        return False, "Failed to update profile"

    @staticmethod
    def search_users(query, limit=10):
        """Search for users by name or email"""
        # noinspection SqlNoDataSourceInspection
        search_query = f"""
        SELECT id, username, email, first_name, last_name 
        FROM users 
        WHERE username ILIKE %s OR email ILIKE %s OR first_name ILIKE %s OR last_name ILIKE %s
        LIMIT %s
        """
        search_term = f"%{query}%"
        params = (search_term, search_term, search_term, search_term, limit)

        try:
            from database.db_manager import DatabaseManager
            results = DatabaseManager.execute_query(search_query, params)
            return results, "Search completed successfully"
        except Exception as e:
            logging.error(f"Error searching users: {e}")
            return [], "Error performing search"
