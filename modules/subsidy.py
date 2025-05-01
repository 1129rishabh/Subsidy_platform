from database.models import Subsidy
import logging


class SubsidyManager:
    @staticmethod
    def get_all_subsidies(active_only=True):
        """Get all available subsidies"""
        try:
            subsidies = Subsidy.get_all(active_only)
            return subsidies, "Subsidies retrieved successfully"
        except Exception as e:
            logging.error(f"Error retrieving subsidies: {e}")
            return [], "Error retrieving subsidies"

    @staticmethod
    def get_subsidy_details(subsidy_id):
        """Get detailed information about a specific subsidy"""
        subsidy = Subsidy.get_by_id(subsidy_id)
        if not subsidy:
            return None, "Subsidy not found"
        return subsidy, "Subsidy details retrieved successfully"

    @staticmethod
    def create_subsidy(name, description, agency, eligibility_criteria, required_documents,
                       application_process, start_date, end_date=None, amount_min=None, amount_max=None):
        """Create a new subsidy program"""
        try:
            subsidy_id = Subsidy.create(
                name, description, agency, eligibility_criteria, required_documents,
                application_process, start_date, end_date, amount_min, amount_max
            )
            if subsidy_id:
                return subsidy_id, "Subsidy created successfully"
            return None, "Failed to create subsidy"
        except Exception as e:
            logging.error(f"Error creating subsidy: {e}")
            return None, f"Error creating subsidy: {str(e)}"

    @staticmethod
    def update_subsidy(subsidy_id, **kwargs):
        """Update subsidy information"""
        # Verify subsidy exists
        subsidy = Subsidy.get_by_id(subsidy_id)
        if not subsidy:
            return False, "Subsidy not found"

        # Update subsidy information
        try:
            success = Subsidy.update(subsidy_id, **kwargs)
            if success:
                return True, "Subsidy updated successfully"
            return False, "No changes made to subsidy"
        except Exception as e:
            logging.error(f"Error updating subsidy: {e}")
            return False, f"Error updating subsidy: {str(e)}"

    @staticmethod
    def search_subsidies(query, limit=20):
        """Search for subsidies by name, description, or agency"""
        # noinspection SqlNoDataSourceInspection
        search_query = f"""
        SELECT * FROM subsidies 
        WHERE name ILIKE %s OR description ILIKE %s OR agency ILIKE %s
        AND (status = 'active' AND (end_date IS NULL OR end_date >= CURRENT_DATE))
        LIMIT %s
        """
        search_term = f"%{query}%"
        params = (search_term, search_term, search_term, limit)

        try:
            from database.db_manager import DatabaseManager
            results = DatabaseManager.execute_query(search_query, params)
            return results, "Search completed successfully"
        except Exception as e:
            logging.error(f"Error searching subsidies: {e}")
            return [], "Error performing search"
