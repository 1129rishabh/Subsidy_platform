import re
import datetime
from dateutil.relativedelta import relativedelta


class Validators:
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email):
            return True, "Valid email"
        return False, "Invalid email format"

    @staticmethod
    def validate_password(password):
        """
        Validate password strength
        - At least 8 characters
        - Contains at least one digit
        - Contains at least one uppercase letter
        - Contains at least one lowercase letter
        - Contains at least one special character
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"

        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"

        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"

        return True, "Valid password"

    @staticmethod
    def validate_national_id(national_id, country_code='default'):
        """Validate national ID format based on country"""
        # This is a simplified validation - in a real system, you'd have specific
        # validation rules for each country's ID format

        if country_code == 'US':
            # US SSN format: XXX-XX-XXXX
            pattern = r'^\d{3}-\d{2}-\d{4}$'
        elif country_code == 'UK':
            # UK National Insurance Number: 2 letters, 6 numbers, 1 letter
            pattern = r'^[A-Z]{2}\d{6}[A-Z]$'
        else:
            # Default: alphanumeric, 5-20 characters
            pattern = r'^[a-zA-Z0-9]{5,20}$'

        if re.match(pattern, national_id):
            return True, "Valid national ID"
        return False, "Invalid national ID format"

    @staticmethod
    def validate_phone(phone, country_code='default'):
        """Validate phone number format based on country"""
        # This is a simplified validation

        if country_code == 'US':
            # US format: +1 XXX-XXX-XXXX or (XXX) XXX-XXXX
            pattern = r'^(\+1\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$'
        elif country_code == 'UK':
            # UK format: +44 XXXX XXXXXX
            pattern = r'^(\+44\s?)?\d{4}\s?\d{6}$'
        else:
            # Default: allow +, spaces, dashes, parentheses, 8-15 digits
            pattern = r'^[+]?[\s()0-9-]{8,20}$'

        if re.match(pattern, phone):
            return True, "Valid phone number"
        return False, "Invalid phone number format"

    @staticmethod
    def validate_date(date_str, format='%Y-%m-%d'):
        """Validate date format and check if it's a valid date"""
        try:
            datetime.datetime.strptime(date_str, format)
            return True, "Valid date"
        except ValueError:
            return False, "Invalid date format. Expected format: YYYY-MM-DD"

    @staticmethod
    def validate_age(birth_date, min_age=18):
        """Validate if person is at least the minimum age"""
        if isinstance(birth_date, str):
            try:
                birth_date = datetime.datetime.strptime(birth_date, '%Y-%m-%d').date()
            except ValueError:
                return False, "Invalid date format. Expected format: YYYY-MM-DD"

        today = datetime.date.today()
        age = relativedelta(today, birth_date).years

        if age >= min_age:
            return True, f"Person is {age} years old"
        return False, f"Person must be at least {min_age} years old (currently {age})"

    @staticmethod
    def validate_amount(amount, min_value=0, max_value=None):
        """Validate if amount is within acceptable range"""
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return False, "Amount must be a number"

        if amount < min_value:
            return False, f"Amount must be at least {min_value}"

        if max_value is not None and amount > max_value:
            return False, f"Amount cannot exceed {max_value}"

        return True, "Valid amount"
