from database.models import Application, Document
import datetime
import logging


class ApplicationManager:
    @staticmethod
    def submit_application(user_id, subsidy_id, notes=None):
        """Submit a new subsidy application"""
        try:
            # Check if user already has an application for this subsidy
            existing_applications = Application.get_by_user(user_id)
            for app in existing_applications:
                if app['subsidy_id'] == subsidy_id and app['status'] in ['pending', 'approved', 'in_review']:
                    return None, "You already have an active application for this subsidy"

            # Create new application
            application_id = Application.create(user_id, subsidy_id, notes)
            if application_id:
                return application_id, "Application submitted successfully"
            return None, "Failed to submit application"
        except Exception as e:
            logging.error(f"Error submitting application: {e}")
            return None, f"Error submitting application: {str(e)}"

    @staticmethod
    def get_user_applications(user_id):
        """Get all applications for a specific user"""
        try:
            applications = Application.get_by_user(user_id)
            return applications, "Applications retrieved successfully"
        except Exception as e:
            logging.error(f"Error retrieving user applications: {e}")
            return [], "Error retrieving applications"

    @staticmethod
    def get_application_details(application_id, user_id=None):
        """Get detailed information about a specific application"""
        try:
            application = Application.get_by_id(application_id)
            if not application:
                return None, "Application not found"

            # If user_id is provided, verify the application belongs to this user
            if user_id and application['user_id'] != user_id:
                return None, "You don't have permission to view this application"

            # Get documents associated with this application
            documents = Document.get_by_application(application_id)
            application['documents'] = documents

            return application, "Application details retrieved successfully"
        except Exception as e:
            logging.error(f"Error retrieving application details: {e}")
            return None, f"Error retrieving application details: {str(e)}"

    @staticmethod
    def update_application_status(application_id, status, amount_granted=None, rejection_reason=None):
        """Update the status of an application"""
        try:
            # Verify application exists
            application = Application.get_by_id(application_id)
            if not application:
                return False, "Application not found"

            # Update application status
            decision_date = datetime.datetime.now() if status in ['approved', 'rejected'] else None
            success = Application.update_status(
                application_id, status, decision_date, amount_granted, rejection_reason
            )

            if success:
                return True, f"Application status updated to {status}"
            return False, "Failed to update application status"
        except Exception as e:
            logging.error(f"Error updating application status: {e}")
            return False, f"Error updating application status: {str(e)}"

    @staticmethod
    def upload_document(application_id, document_type, file_path, notes=None):
        """Upload a document for an application"""
        try:
            # Verify application exists
            application = Application.get_by_id(application_id)
            if not application:
                return None, "Application not found"

            # Create document record
            document_id = Document.create(application_id, document_type, file_path, notes)
            if document_id:
                return document_id, "Document uploaded successfully"
            return None, "Failed to upload document"
        except Exception as e:
            logging.error(f"Error uploading document: {e}")
            return None, f"Error uploading document: {str(e)}"

    @staticmethod
    def verify_document(document_id, status, notes=None):
        """Verify a document (approve or reject)"""
        try:
            verification_date = datetime.datetime.now()
            success = Document.update_status(document_id, status, verification_date, notes)
            if success:
                return True, f"Document marked as {status}"
            return False, "Failed to update document status"
        except Exception as e:
            logging.error(f"Error verifying document: {e}")
            return False, f"Error verifying document: {str(e)}"
