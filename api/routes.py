from flask import Blueprint, request, jsonify, g
import time
# import datetime
from functools import wraps

from modules.auth import Auth
from modules.user import UserManager
from modules.subsidy import SubsidyManager
from modules.application import ApplicationManager
from modules.eligibility import EligibilityChecker
from modules.notification import NotificationManager
from modules.document import DocumentManager
from utils.logger import Logger
from utils.validators import Validators

# Create blueprint
api = Blueprint('api', __name__)


# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'message': 'Authentication token is missing!'}), 401

        # Verify token
        user_id = Auth.verify_token(token)
        if not user_id:
            return jsonify({'message': 'Invalid or expired token!'}), 401

        # Store user_id in Flask's g object for use in the route function
        g.user_id = user_id
        return f(*args, **kwargs)

    return decorated


# Request timing middleware
@api.before_request
def start_timer():
    g.start_time = time.time()


@api.after_request
def log_request(response):
    if hasattr(g, 'start_time'):
        response_time = (time.time() - g.start_time) * 1000  # Convert to milliseconds
        Logger.log_api_request(request, response.status_code, response_time)
    return response


# Authentication routes
@api.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()

    # Validate required fields
    required_fields = ['username', 'email', 'password', 'first_name', 'last_name',
                       'national_id', 'date_of_birth', 'address']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400

    # Validate email format
    is_valid, message = Validators.validate_email(data['email'])
    if not is_valid:
        return jsonify({'message': message}), 400

    # Validate password strength
    is_valid, message = Validators.validate_password(data['password'])
    if not is_valid:
        return jsonify({'message': message}), 400

    # Validate date format
    is_valid, message = Validators.validate_date(data['date_of_birth'])
    if not is_valid:
        return jsonify({'message': message}), 400

    # Register user
    user_id, message = Auth.register_user(
        data['username'],
        data['email'],
        data['password'],
        data['first_name'],
        data['last_name'],
        data['national_id'],
        data['date_of_birth'],
        data['address'],
        data.get('phone')
    )

    if user_id:
        return jsonify({
            'message': message,
            'user_id': user_id
        }), 201
    else:
        return jsonify({'message': message}), 400


@api.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()

    # Validate required fields
    if 'username' not in data or 'password' not in data:
        return jsonify({'message': 'Username and password are required'}), 400

    # Authenticate user
    token, message = Auth.login(data['username'], data['password'])

    if token:
        return jsonify({
            'message': message,
            'token': token
        }), 200
    else:
        return jsonify({'message': message}), 401


# User routes
@api.route('/user/profile', methods=['GET'])
@token_required
def get_profile():
    user_profile, message = UserManager.get_user_profile(g.user_id)

    if user_profile:
        return jsonify({
            'message': message,
            'profile': user_profile
        }), 200
    else:
        return jsonify({'message': message}), 404


@api.route('/user/profile', methods=['PUT'])
@token_required
def update_profile():
    data = request.get_json()

    # Validate email if provided
    if 'email' in data:
        is_valid, message = Validators.validate_email(data['email'])
        if not is_valid:
            return jsonify({'message': message}), 400

    # Update profile
    success, message = UserManager.update_user_profile(g.user_id, **data)

    if success:
        return jsonify({'message': message}), 200
    else:
        return jsonify({'message': message}), 400


# Subsidy routes
@api.route('/subsidies', methods=['GET'])
def get_subsidies():
    # Get query parameters
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    search_query = request.args.get('search', '')

    if search_query:
        subsidies, message = SubsidyManager.search_subsidies(search_query)
    else:
        subsidies, message = SubsidyManager.get_all_subsidies(active_only)

    return jsonify({
        'message': message,
        'subsidies': subsidies
    }), 200


@api.route('/subsidies/<int:subsidy_id>', methods=['GET'])
def get_subsidy(subsidy_id):
    subsidy, message = SubsidyManager.get_subsidy_details(subsidy_id)

    if subsidy:
        return jsonify({
            'message': message,
            'subsidy': subsidy
        }), 200
    else:
        return jsonify({'message': message}), 404


@api.route('/subsidies', methods=['POST'])
@token_required
def create_subsidy():
    # This would typically be restricted to admin users
    data = request.get_json()

    # Validate required fields
    required_fields = ['name', 'description', 'agency', 'eligibility_criteria',
                       'required_documents', 'application_process', 'start_date']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400

    # Create subsidy
    subsidy_id, message = SubsidyManager.create_subsidy(
        data['name'],
        data['description'],
        data['agency'],
        data['eligibility_criteria'],
        data['required_documents'],
        data['application_process'],
        data['start_date'],
        data.get('end_date'),
        data.get('amount_min'),
        data.get('amount_max')
    )

    if subsidy_id:
        return jsonify({
            'message': message,
            'subsidy_id': subsidy_id
        }), 201
    else:
        return jsonify({'message': message}), 400


@api.route('/subsidies/<int:subsidy_id>', methods=['PUT'])
@token_required
def update_subsidy(subsidy_id):
    # This would typically be restricted to admin users
    data = request.get_json()

    # Update subsidy
    success, message = SubsidyManager.update_subsidy(subsidy_id, **data)

    if success:
        return jsonify({'message': message}), 200
    else:
        return jsonify({'message': message}), 400


# Eligibility routes
@api.route('/subsidies/<int:subsidy_id>/check-eligibility', methods=['GET'])
@token_required
def check_eligibility(subsidy_id):
    is_eligible, reasons, required_documents = EligibilityChecker.check_eligibility(g.user_id, subsidy_id)

    return jsonify({
        'eligible': is_eligible,
        'reasons': reasons,
        'required_documents': required_documents
    }), 200


@api.route('/recommendations', methods=['GET'])
@token_required
def get_recommendations():
    recommendations, message = EligibilityChecker.get_recommended_subsidies(g.user_id)

    return jsonify({
        'message': message,
        'recommendations': recommendations
    }), 200


# Application routes
@api.route('/applications', methods=['POST'])
@token_required
def submit_application():
    data = request.get_json()

    # Validate required fields
    if 'subsidy_id' not in data:
        return jsonify({'message': 'Subsidy ID is required'}), 400

    # Submit application
    application_id, message = ApplicationManager.submit_application(
        g.user_id,
        data['subsidy_id'],
        data.get('notes')
    )

    if application_id:
        return jsonify({
            'message': message,
            'application_id': application_id
        }), 201
    else:
        return jsonify({'message': message}), 400


@api.route('/applications', methods=['GET'])
@token_required
def get_user_applications():
    applications, message = ApplicationManager.get_user_applications(g.user_id)

    return jsonify({
        'message': message,
        'applications': applications
    }), 200


@api.route('/applications/<int:application_id>', methods=['GET'])
@token_required
def get_application(application_id):
    application, message = ApplicationManager.get_application_details(application_id, g.user_id)

    if application:
        return jsonify({
            'message': message,
            'application': application
        }), 200
    else:
        return jsonify({'message': message}), 404


@api.route('/applications/<int:application_id>/status', methods=['PUT'])
@token_required
def update_application_status(application_id):
    # This would typically be restricted to admin users
    data = request.get_json()

    if 'status' not in data:
        return jsonify({'message': 'Status is required'}), 400

    # Update application status
    success, message = ApplicationManager.update_application_status(
        application_id,
        data['status'],
        data.get('amount_granted'),
        data.get('rejection_reason')
    )

    if success:
        # Send notification about status change
        NotificationManager.notify_application_status_change(application_id)
        return jsonify({'message': message}), 200
    else:
        return jsonify({'message': message}), 400


# Document routes
@api.route('/applications/<int:application_id>/documents', methods=['POST'])
@token_required
def upload_document(application_id):
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400

    file = request.files['file']
    document_type = request.form.get('document_type')
    notes = request.form.get('notes')

    if not document_type:
        return jsonify({'message': 'Document type is required'}), 400

    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    # Verify the application belongs to the user
    application, _ = ApplicationManager.get_application_details(application_id, g.user_id)
    if not application:
        return jsonify({'message': 'Application not found or access denied'}), 404

    # Upload document
    document_id, message = DocumentManager.save_file(file, application_id, document_type)

    if document_id:
        return jsonify({
            'message': message,
            'document_id': document_id
        }), 201
    else:
        return jsonify({'message': message}), 400


@api.route('/applications/<int:application_id>/documents', methods=['GET'])
@token_required
def get_application_documents(application_id):
    # Verify the application belongs to the user
    application, _ = ApplicationManager.get_application_details(application_id, g.user_id)
    if not application:
        return jsonify({'message': 'Application not found or access denied'}), 404

    # Get documents
    documents = application.get('documents', [])

    return jsonify({
        'message': 'Documents retrieved successfully',
        'documents': documents
    }), 200


@api.route('/applications/<int:application_id>/missing-documents', methods=['GET'])
@token_required
def get_missing_documents(application_id):
    # Verify the application belongs to the user
    application, _ = ApplicationManager.get_application_details(application_id, g.user_id)
    if not application:
        return jsonify({'message': 'Application not found or access denied'}), 404

    # Get missing documents
    missing_docs, message = DocumentManager.check_missing_documents(application_id)

    return jsonify({
        'message': message,
        'missing_documents': missing_docs
    }), 200


@api.route('/documents/<int:document_id>/verify', methods=['PUT'])
@token_required
def verify_document(document_id):
    # This would typically be restricted to admin users
    data = request.get_json()

    if 'status' not in data:
        return jsonify({'message': 'Status is required'}), 400

    # Verify document
    success, message = DocumentManager.verify_document(
        document_id,
        data['status'],
        data.get('notes')
    )

    if success:
        # Send notification about document verification
        NotificationManager.notify_document_verification(document_id)
        return jsonify({'message': message}), 200
    else:
        return jsonify({'message': message}), 400


# Notification routes
@api.route('/applications/<int:application_id>/send-reminder', methods=['POST'])
@token_required
def send_reminder(application_id):
    # This would typically be restricted to admin users
    data = request.get_json()

    if 'reminder_type' not in data:
        return jsonify({'message': 'Reminder type is required'}), 400

    # Send reminder
    success, message = NotificationManager.send_reminder(
        application_id,
        data['reminder_type']
    )

    if success:
        return jsonify({'message': message}), 200
    else:
        return jsonify({'message': message}), 400


# Error handlers
@api.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404


@api.errorhandler(500)
def internal_server_error(error):
    Logger.log_error(error)
    return jsonify({'message': 'Internal server error'}), 500
