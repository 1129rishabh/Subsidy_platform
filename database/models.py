from database.db_manager import DatabaseManager


class User:
    @staticmethod
    def create_table():
        # noinspection SqlNoDataSourceInspection
        query = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            national_id VARCHAR(20) UNIQUE NOT NULL,
            date_of_birth DATE NOT NULL,
            address TEXT NOT NULL,
            phone VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        DatabaseManager.execute_query(query)

    @staticmethod
    def create(username, email, password_hash, first_name, last_name, national_id, date_of_birth, address, phone=None):
        # noinspection SqlNoDataSourceInspection
        query = """
        INSERT INTO users (username, email, password_hash, first_name, last_name, national_id, date_of_birth, address, phone)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        params = (username, email, password_hash, first_name, last_name, national_id, date_of_birth, address, phone)
        result = DatabaseManager.execute_query(query, params)
        return result[0]['id'] if result else None

    @staticmethod
    def get_by_id(user_id):
        # noinspection SqlNoDataSourceInspection
        query = "SELECT * FROM users WHERE id = %s"
        result = DatabaseManager.execute_query(query, (user_id,))
        return result[0] if result else None

    @staticmethod
    def get_by_username(username):
        # noinspection SqlNoDataSourceInspection
        query = "SELECT * FROM users WHERE username = %s"
        result = DatabaseManager.execute_query(query, (username,))
        return result[0] if result else None

    @staticmethod
    def get_by_email(email):
        # noinspection SqlNoDataSourceInspection
        query = "SELECT * FROM users WHERE email = %s"
        result = DatabaseManager.execute_query(query, (email,))
        return result[0] if result else None

    @staticmethod
    def update(user_id, **kwargs):
        allowed_fields = ['email', 'first_name', 'last_name', 'address', 'phone']
        updates = []
        params = []

        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = %s")
                params.append(value)

        if not updates:
            return False

        updates.append("updated_at = CURRENT_TIMESTAMP")
        # noinspection SqlNoDataSourceInspection
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
        params.append(user_id)

        DatabaseManager.execute_query(query, tuple(params))
        return True


class Subsidy:
    @staticmethod
    def create_table():
        # noinspection SqlNoDataSourceInspection
        query = """
        CREATE TABLE IF NOT EXISTS subsidies (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,
            agency VARCHAR(100) NOT NULL,
            amount_min DECIMAL(10, 2),
            amount_max DECIMAL(10, 2),
            start_date DATE NOT NULL,
            end_date DATE,
            eligibility_criteria TEXT NOT NULL,
            required_documents TEXT NOT NULL,
            application_process TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        DatabaseManager.execute_query(query)

    @staticmethod
    def create(name, description, agency, eligibility_criteria, required_documents,
               application_process, start_date, end_date=None, amount_min=None, amount_max=None):
        # noinspection SqlNoDataSourceInspection
        query = """
        INSERT INTO subsidies (name, description, agency, eligibility_criteria, required_documents, 
                              application_process, start_date, end_date, amount_min, amount_max)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        params = (name, description, agency, eligibility_criteria, required_documents,
                  application_process, start_date, end_date, amount_min, amount_max)
        result = DatabaseManager.execute_query(query, params)
        return result[0]['id'] if result else None

    @staticmethod
    def get_all(active_only=True):
        # noinspection SqlNoDataSourceInspection
        query = "SELECT * FROM subsidies"
        if active_only:
            query += " WHERE status = 'active' AND (end_date IS NULL OR end_date >= CURRENT_DATE)"
        query += " ORDER BY created_at DESC"
        return DatabaseManager.execute_query(query)

    @staticmethod
    def get_by_id(subsidy_id):
        # noinspection SqlNoDataSourceInspection
        query = "SELECT * FROM subsidies WHERE id = %s"
        result = DatabaseManager.execute_query(query, (subsidy_id,))
        return result[0] if result else None

    @staticmethod
    def update(subsidy_id, **kwargs):
        allowed_fields = ['name', 'description', 'agency', 'amount_min', 'amount_max',
                          'start_date', 'end_date', 'eligibility_criteria',
                          'required_documents', 'application_process', 'status']
        updates = []
        params = []

        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = %s")
                params.append(value)

        if not updates:
            return False

        updates.append("updated_at = CURRENT_TIMESTAMP")
        # noinspection SqlNoDataSourceInspection
        query = f"UPDATE subsidies SET {', '.join(updates)} WHERE id = %s"
        params.append(subsidy_id)

        DatabaseManager.execute_query(query, tuple(params))
        return True


class Application:
    @staticmethod
    def create_table():
        # noinspection SqlNoDataSourceInspection
        query = """
        CREATE TABLE IF NOT EXISTS applications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            subsidy_id INTEGER NOT NULL REFERENCES subsidies(id),
            status VARCHAR(20) DEFAULT 'pending',
            submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            decision_date TIMESTAMP,
            amount_granted DECIMAL(10, 2),
            rejection_reason TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, subsidy_id)
        )
        """
        DatabaseManager.execute_query(query)

    @staticmethod
    def create(user_id, subsidy_id, notes=None):
        # noinspection SqlNoDataSourceInspection
        query = """
        INSERT INTO applications (user_id, subsidy_id, notes)
        VALUES (%s, %s, %s)
        RETURNING id
        """
        params = (user_id, subsidy_id, notes)
        result = DatabaseManager.execute_query(query, params)
        return result[0]['id'] if result else None

    @staticmethod
    def get_by_id(application_id):
        # noinspection SqlNoDataSourceInspection
        query = """
        SELECT a.*, u.first_name, u.last_name, u.email, s.name as subsidy_name
        FROM applications a
        JOIN users u ON a.user_id = u.id
        JOIN subsidies s ON a.subsidy_id = s.id
        WHERE a.id = %s
        """
        result = DatabaseManager.execute_query(query, (application_id,))
        return result[0] if result else None

    @staticmethod
    def get_by_user(user_id):
        # noinspection SqlNoDataSourceInspection
        query = """
        SELECT a.*, s.name as subsidy_name, s.agency
        FROM applications a
        JOIN subsidies s ON a.subsidy_id = s.id
        WHERE a.user_id = %s
        ORDER BY a.submission_date DESC
        """
        return DatabaseManager.execute_query(query, (user_id,))

    @staticmethod
    def update_status(application_id, status, decision_date=None, amount_granted=None, rejection_reason=None):
        # noinspection SqlNoDataSourceInspection
        query = """
        UPDATE applications 
        SET status = %s, decision_date = %s, amount_granted = %s, rejection_reason = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        params = (status, decision_date, amount_granted, rejection_reason, application_id)
        DatabaseManager.execute_query(query, params)
        return True


class Document:
    @staticmethod
    def create_table():
        # noinspection SqlNoDataSourceInspection
        query = """
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            application_id INTEGER NOT NULL REFERENCES applications(id),
            document_type VARCHAR(50) NOT NULL,
            file_path VARCHAR(255) NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'pending',
            verification_date TIMESTAMP,
            notes TEXT
        )
        """
        DatabaseManager.execute_query(query)

    @staticmethod
    def create(application_id, document_type, file_path, notes=None):
        # noinspection SqlNoDataSourceInspection
        query = """
        INSERT INTO documents (application_id, document_type, file_path, notes)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """
        params = (application_id, document_type, file_path, notes)
        result = DatabaseManager.execute_query(query, params)
        return result[0]['id'] if result else None

    @staticmethod
    def get_by_application(application_id):
        # noinspection SqlNoDataSourceInspection
        query = "SELECT * FROM documents WHERE application_id = %s ORDER BY upload_date"
        return DatabaseManager.execute_query(query, (application_id,))

    @staticmethod
    def update_status(document_id, status, verification_date=None, notes=None):
        # noinspection SqlNoDataSourceInspection
        query = """
        UPDATE documents 
        SET status = %s, verification_date = %s, notes = %s
        WHERE id = %s
        """
        params = (status, verification_date, notes, document_id)
        DatabaseManager.execute_query(query, params)
        return True


def initialize_database():
    """Create all tables if they don't exist"""
    User.create_table()
    Subsidy.create_table()
    Application.create_table()
    Document.create_table()
