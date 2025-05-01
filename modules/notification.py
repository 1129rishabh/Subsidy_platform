import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from config import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_SENDER
from database.models import User, Application, Subsidy


class NotificationManager:
    @staticmethod
    def send_email(recipient_email, subject, message_html, message_text=None):
        """Send an email notification"""
        if not message_text:
            message_text = message_html.replace('<br>', '\n').replace('<p>', '').replace('</p>', '\n\n')
            # Remove other HTML tags
            import re
            message_text = re.sub('<[^<]+?>', '', message_text)

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = EMAIL_SENDER
            msg['To'] = recipient_email

            # Attach parts
            part1 = MIMEText(message_text, 'plain')
            part2 = MIMEText(message_html, 'html')
            msg.attach(part1)
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                if SMTP_USERNAME and SMTP_PASSWORD:
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)

            logging.info(f"Email sent to {recipient_email}: {subject}")
            return True, "Email sent successfully"
        except Exception as e:
            logging.error(f"Error sending email: {e}")
            return False, f"Error sending email: {str(e)}"

    @staticmethod
    def notify_application_status_change(application_id):
        """Notify user about application status change"""
        try:
            # Get application details
            application = Application.get_by_id(application_id)
            if not application:
                return False, "Application not found"

            # Get user and subsidy details
            user = User.get_by_id(application['user_id'])
            subsidy = Subsidy.get_by_id(application['subsidy_id'])

            if not user or not subsidy:
                return False, "User or subsidy not found"

            # Prepare email content based on application status
            subject = f"Update on your {subsidy['name']} subsidy application"

            if application['status'] == 'approved':
                message_html = f"""
                <p>Dear {user['first_name']},</p>
                <p>Congratulations! Your application for the <b>{subsidy['name']}</b> subsidy has been approved.</p>
                <p>Amount granted: {application['amount_granted'] if application['amount_granted'] else 'To be determined'}</p>
                <p>Please log in to your account for more details and next steps.</p>
                <p>Thank you for using our platform.</p>
                <p>Best regards,<br>The Subsidy Platform Team</p>
                """
            elif application['status'] == 'rejected':
                message_html = f"""
                <p>Dear {user['first_name']},</p>
                <p>We regret to inform you that your application for the <b>{subsidy['name']}</b> subsidy has been rejected.</p>
                <p>Reason: {application['rejection_reason'] if application['rejection_reason'] else 'Not specified'}</p>
                <p>If you believe this decision was made in error, you may appeal by contacting the agency directly.</p>
                <p>Thank you for using our platform.</p>
                <p>Best regards,<br>The Subsidy Platform Team</p>
                """
            elif application['status'] == 'in_review':
                message_html = f"""
                <p>Dear {user['first_name']},</p>
                <p>Your application for the <b>{subsidy['name']}</b> subsidy is now being reviewed.</p>
                <p>We will notify you once a decision has been made.</p>
                <p>Thank you for your patience.</p>
                <p>Best regards,<br>The Subsidy Platform Team</p>
                """
            else:
                message_html = f"""
                <p>Dear {user['first_name']},</p>
                <p>The status of your application for the <b>{subsidy['name']}</b> subsidy has been updated to: {application['status']}</p>
                <p>Please log in to your account for more details.</p>
                <p>Thank you for using our platform.</p>
                <p>Best regards,<br>The Subsidy Platform Team</p>
                """

            # Send email notification
            return NotificationManager.send_email(user['email'], subject, message_html)

        except Exception as e:
            logging.error(f"Error sending application status notification: {e}")
            return False, f"Error sending notification: {str(e)}"

    @staticmethod
    def notify_document_verification(document_id):
        """Notify user about document verification status"""
        try:
            from database.db_manager import DatabaseManager

            # Get document details with application and user info
            # noinspection SqlNoDataSourceInspection
            query = """
            SELECT d.*, a.user_id, a.subsidy_id, u.email, u.first_name, s.name as subsidy_name
            FROM documents d
            JOIN applications a ON d.application_id = a.id
            JOIN users u ON a.user_id = u.id
            JOIN subsidies s ON a.subsidy_id = s.id
            WHERE d.id = %s
            """
            result = DatabaseManager.execute_query(query, (document_id,))

            if not result:
                return False, "Document not found"

            document = result[0]

            # Prepare email content based on document status
            subject = f"Document verification update - {document['subsidy_name']} application"

            if document['status'] == 'approved':
                message_html = f"""
                <p>Dear {document['first_name']},</p>
                <p>Your document ({document['document_type']}) for the <b>{document['subsidy_name']}</b> subsidy application has been verified and approved.</p>
                <p>Your application is progressing well.</p>
                <p>Thank you for using our platform.</p>
                <p>Best regards,<br>The Subsidy Platform Team</p>
                """
            elif document['status'] == 'rejected':
                message_html = f"""
                <p>Dear {document['first_name']},</p>
                <p>Your document ({document['document_type']}) for the <b>{document['subsidy_name']}</b> subsidy application has been rejected.</p>
                <p>Reason: {document['notes'] if document['notes'] else 'Not specified'}</p>
                <p>Please log in to your account to upload a corrected document.</p>
                <p>Thank you for using our platform.</p>
                <p>Best regards,<br>The Subsidy Platform Team</p>
                """
            else:
                return True, "No notification needed for this status"

            # Send email notification
            return NotificationManager.send_email(document['email'], subject, message_html)

        except Exception as e:
            logging.error(f"Error sending document verification notification: {e}")
            return False, f"Error sending notification: {str(e)}"

    @staticmethod
    def send_reminder(application_id, reminder_type):
        """Send reminder notifications to users"""
        try:
            # Get application details
            application = Application.get_by_id(application_id)
            if not application:
                return False, "Application not found"

            # Get user and subsidy details
            user = User.get_by_id(application['user_id'])
            subsidy = Subsidy.get_by_id(application['subsidy_id'])

            if not user or not subsidy:
                return False, "User or subsidy not found"

            # Prepare email content based on reminder type
            subject = f"Reminder: {subsidy['name']} subsidy application"

            if reminder_type == 'document_missing':
                # Get missing documents
                from database.db_manager import DatabaseManager
                # noinspection SqlNoDataSourceInspection
                query = """
                SELECT document_type FROM documents 
                WHERE application_id = %s AND status = 'pending'
                """
                missing_docs = DatabaseManager.execute_query(query, (application_id,))

                if not missing_docs:
                    return False, "No missing documents found"

                doc_list = "".join([f"<li>{doc['document_type']}</li>" for doc in missing_docs])

                message_html = f"""
                <p>Dear {user['first_name']},</p>
                <p>This is a reminder that your application for the <b>{subsidy['name']}</b> subsidy is missing the following documents:</p>
                <ul>
                {doc_list}
                </ul>
                <p>Please log in to your account to upload these documents as soon as possible to avoid delays in processing your application.</p>
                <p>Thank you for using our platform.</p>
                <p>Best regards,<br>The Subsidy Platform Team</p>
                """
            elif reminder_type == 'deadline_approaching':
                message_html = f"""
                <p>Dear {user['first_name']},</p>
                <p>This is a reminder that the deadline for the <b>{subsidy['name']}</b> subsidy is approaching.</p>
                <p>Please ensure that all required documents are submitted and your application is complete.</p>
                <p>Thank you for using our platform.</p>
                <p>Best regards,<br>The Subsidy Platform Team</p>
                """
            else:
                message_html = f"""
                <p>Dear {user['first_name']},</p>
                <p>This is a reminder about your application for the <b>{subsidy['name']}</b> subsidy.</p>
                <p>Please log in to your account to check the status and ensure all requirements are met.</p>
                <p>Thank you for using our platform.</p>
                <p>Best regards,<br>The Subsidy Platform Team</p>
                """

            # Send email notification
            return NotificationManager.send_email(user['email'], subject, message_html)

        except Exception as e:
            logging.error(f"Error sending reminder notification: {e}")
            return False, f"Error sending reminder: {str(e)}"
