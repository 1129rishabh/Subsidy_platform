import os
import uuid
import logging
from werkzeug.utils import secure_filename
from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS
from database.models import Document


class DocumentManager:
    @staticmethod
    def allowed_file(filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @staticmethod
    def save_file(file, application_id, document_type):
        """Save uploaded file to disk and create document record"""
        try:
            if not file:
                return None, "No file provided"

            if not DocumentManager.allowed_file(file.filename):
                return None, f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"

            # Create upload directory if it doesn't exist
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            # Generate unique filename
            original_filename = secure_filename(file.filename)
            file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}" if file_extension else f"{uuid.uuid4().hex}"

            # Create application-specific subfolder
            app_folder = os.path.join(UPLOAD_FOLDER, f"application_{application_id}")
            os.makedirs(app_folder, exist_ok=True)

            # Save file
            file_path = os.path.join(app_folder, unique_filename)
            file.save(file_path)

            # Create document record in database
            document_id = Document.create(
                application_id=application_id,
                document_type=document_type,
                file_path=file_path,
                notes=f"Original filename: {original_filename}"
            )

            if document_id:
                return document_id, "Document uploaded successfully"
            return None, "Failed to create document record"

        except Exception as e:
            logging.error(f"Error saving document: {e}")
            return None, f"Error saving document: {str(e)}"

    @staticmethod
    def get_document_file(document_id):
        """Get file path for a document"""
        try:
            from database.db_manager import DatabaseManager
            # noinspection SqlNoDataSourceInspection
            query = "SELECT file_path FROM documents WHERE id = %s"
            result = DatabaseManager.execute_query(query, (document_id,))

            if not result:
                return None, "Document not found"

            file_path = result[0]['file_path']
            if not os.path.exists(file_path):
                return None, "Document file not found on disk"

            return file_path, "Document found"

        except Exception as e:
            logging.error(f"Error retrieving document: {e}")
            return None, f"Error retrieving document: {str(e)}"

    @staticmethod
    def delete_document(document_id):
        """Delete a document and its file"""
        try:
            # Get file path
            file_path, message = DocumentManager.get_document_file(document_id)
            if not file_path:
                return False, message

            # Delete file from disk
            try:
                os.remove(file_path)
            except OSError as e:
                logging.warning(f"Error deleting file {file_path}: {e}")

            # Delete document record from database
            from database.db_manager import DatabaseManager
            # noinspection SqlNoDataSourceInspection
            query = "DELETE FROM documents WHERE id = %s RETURNING id"
            result = DatabaseManager.execute_query(query, (document_id,))

            if result:
                return True, "Document deleted successfully"
            return False, "Failed to delete document record"

        except Exception as e:
            logging.error(f"Error deleting document: {e}")
            return False, f"Error deleting document: {str(e)}"

    @staticmethod
    def get_required_documents(subsidy_id):
        """Get list of required documents for a subsidy"""
        try:
            from database.models import Subsidy
            subsidy = Subsidy.get_by_id(subsidy_id)

            if not subsidy:
                return [], "Subsidy not found"

            # Parse required documents
            try:
                import json
                required_documents = json.loads(subsidy['required_documents'])
            except (json.JSONDecodeError, TypeError):
                # Fallback to simple text parsing if JSON parsing fails
                required_documents = []
                for line in subsidy['required_documents'].split('\n'):
                    doc = line.strip()
                    if doc and not doc.startswith('#'):
                        required_documents.append(doc)

            return required_documents, "Required documents retrieved successfully"

        except Exception as e:
            logging.error(f"Error retrieving required documents: {e}")
            return [], f"Error retrieving required documents: {str(e)}"

    @staticmethod
    def check_missing_documents(application_id):
        """Check which required documents are missing for an application"""
        try:
            from database.db_manager import DatabaseManager

            # Get application details
            # noinspection SqlNoDataSourceInspection
            query = "SELECT subsidy_id FROM applications WHERE id = %s"
            result = DatabaseManager.execute_query(query, (application_id,))

            if not result:
                return [], "Application not found"

            subsidy_id = result[0]['subsidy_id']

            # Get required documents for this subsidy
            required_docs, _ = DocumentManager.get_required_documents(subsidy_id)

            # Get submitted documents
            # noinspection SqlNoDataSourceInspection
            query = "SELECT document_type FROM documents WHERE application_id = %s"
            submitted_docs_result = DatabaseManager.execute_query(query, (application_id,))
            submitted_docs = [doc['document_type'] for doc in submitted_docs_result]

            # Find missing documents
            missing_docs = [doc for doc in required_docs if doc not in submitted_docs]

            return missing_docs, "Missing documents check completed"

        except Exception as e:
            logging.error(f"Error checking missing documents: {e}")
            return [], f"Error checking missing documents: {str(e)}"
