import json
import logging
from database.models import User, Subsidy


class EligibilityChecker:
    @staticmethod
    def check_eligibility(user_id, subsidy_id):
        """
        Check if a user is eligible for a specific subsidy
        Returns a tuple (is_eligible, reasons, missing_documents)
        """
        try:
            # Get user and subsidy information
            user = User.get_by_id(user_id)
            subsidy = Subsidy.get_by_id(subsidy_id)

            if not user or not subsidy:
                return False, ["User or subsidy not found"], []

            # Parse eligibility criteria from subsidy
            # Assuming criteria is stored as JSON or structured text
            try:
                criteria = json.loads(subsidy['eligibility_criteria'])
            except (json.JSONDecodeError, TypeError):
                # Fallback to simple text parsing if JSON parsing fails
                criteria = EligibilityChecker._parse_criteria_text(subsidy['eligibility_criteria'])

            # Parse required documents
            try:
                required_documents = json.loads(subsidy['required_documents'])
            except (json.JSONDecodeError, TypeError):
                required_documents = EligibilityChecker._parse_documents_text(subsidy['required_documents'])

            # Check each criterion
            is_eligible = True
            reasons = []

            # Example criteria checks (would be more complex in a real system)
            if 'age_min' in criteria and EligibilityChecker._calculate_age(user['date_of_birth']) < criteria['age_min']:
                is_eligible = False
                reasons.append(f"Age below minimum requirement of {criteria['age_min']} years")

            if 'age_max' in criteria and EligibilityChecker._calculate_age(user['date_of_birth']) > criteria['age_max']:
                is_eligible = False
                reasons.append(f"Age above maximum requirement of {criteria['age_max']} years")

            # More criteria checks would be implemented here based on the specific subsidy requirements

            return is_eligible, reasons, required_documents

        except Exception as e:
            logging.error(f"Error checking eligibility: {e}")
            return False, [f"Error checking eligibility: {str(e)}"], []

    @staticmethod
    def _calculate_age(birth_date):
        """Calculate age from birth date"""
        from datetime import date
        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    @staticmethod
    def _parse_criteria_text(criteria_text):
        """Parse eligibility criteria from text format"""
        criteria = {}
        lines = criteria_text.split('\n')

        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()

                # Try to convert to appropriate type
                try:
                    if value.isdigit():
                        value = int(value)
                    elif value.replace('.', '', 1).isdigit():
                        value = float(value)
                except ValueError:
                    pass

                criteria[key] = value

        return criteria

    @staticmethod
    def _parse_documents_text(documents_text):
        """Parse required documents from text format"""
        documents = []
        lines = documents_text.split('\n')

        for line in lines:
            doc = line.strip()
            if doc and not doc.startswith('#'):
                documents.append(doc)

        return documents

    @staticmethod
    def get_recommended_subsidies(user_id):
        """Get recommended subsidies for a user based on their profile"""
        try:
            user = User.get_by_id(user_id)
            if not user:
                return [], "User not found"

            # Get all active subsidies
            subsidies = Subsidy.get_all(active_only=True)

            # Check eligibility for each subsidy
            recommended = []
            for subsidy in subsidies:
                is_eligible, reasons, _ = EligibilityChecker.check_eligibility(user_id, subsidy['id'])
                if is_eligible:
                    recommended.append({
                        'subsidy': subsidy,
                        'match_score': 100  # In a real system, this would be a calculated score
                    })
                elif len(reasons) <= 2:  # If close to being eligible
                    recommended.append({
                        'subsidy': subsidy,
                        'match_score': 70 - (len(reasons) * 20),  # Lower score based on number of ineligibility reasons
                        'ineligibility_reasons': reasons
                    })

            # Sort by match score
            recommended.sort(key=lambda x: x['match_score'], reverse=True)

            return recommended, "Recommendations generated successfully"
        except Exception as e:
            logging.error(f"Error generating recommendations: {e}")
            return [], f"Error generating recommendations: {str(e)}"
