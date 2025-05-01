import datetime
import json
import re
import uuid
import hashlib


class Helpers:
    @staticmethod
    def generate_reference_number():
        """Generate a unique reference number for applications"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        random_part = uuid.uuid4().hex[:8]
        return f"SUB-{timestamp}-{random_part}"

    @staticmethod
    def format_currency(amount, currency='$'):
        """Format amount as currency"""
        if amount is None:
            return "N/A"
        return f"{currency}{amount:,.2f}"

    @staticmethod
    def format_date(date_obj, format_str='%Y-%m-%d'):
        """Format date object as string"""
        if not date_obj:
            return "N/A"
        return date_obj.strftime(format_str)

    @staticmethod
    def parse_json_field(json_str, default=None):
        """Safely parse JSON string"""
        if not json_str:
            return default
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return default

    @staticmethod
    def sanitize_html(html_content):
        """Remove potentially dangerous HTML tags"""
        if not html_content:
            return ""

        # Remove script tags and their content
        clean = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)

        # Remove on* attributes (onclick, onload, etc.)
        clean = re.sub(r'\son\w+="[^"]*"', '', clean)

        # Remove iframe tags
        clean = re.sub(r'<iframe[^>]*>.*?</iframe>', '', clean, flags=re.DOTALL)

        return clean

    @staticmethod
    def truncate_text(text, max_length=100, suffix='...'):
        """Truncate text to specified length"""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length].rstrip() + suffix

    @staticmethod
    def calculate_hash(data):
        """Calculate SHA-256 hash of data"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def get_file_extension(filename):
        """Get file extension from filename"""
        if '.' not in filename:
            return ""
        return filename.rsplit('.', 1)[1].lower()

    @staticmethod
    def format_phone_number(phone):
        """Format phone number consistently"""
        if not phone:
            return ""

        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)

        # Format based on length
        if len(digits) == 10:  # US format
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':  # US with country code
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            # Just add spaces for readability for other formats
            return ' '.join([digits[i:i + 4] for i in range(0, len(digits), 4)])

    @staticmethod
    def calculate_age(birth_date):
        """Calculate age from birthdate"""
        today = datetime.date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    @staticmethod
    def get_status_display(status_code):
        """Convert status codes to display-friendly text"""
        status_map = {
            'pending': 'Pending Review',
            'in_review': 'In Review',
            'approved': 'Approved',
            'rejected': 'Rejected',
            'incomplete': 'Incomplete',
            'withdrawn': 'Withdrawn',
            'expired': 'Expired'
        }
        return status_map.get(status_code, status_code.replace('_', ' ').title())
