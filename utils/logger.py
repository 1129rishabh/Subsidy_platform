import logging
import os
from logging.handlers import RotatingFileHandler
import datetime
from config import DEBUG


class Logger:
    _logger = None

    @classmethod
    def setup_logger(cls, name='subsidy_platform', log_dir='logs'):
        """Set up and configure logger"""
        if cls._logger is not None:
            return cls._logger

        # Create logs directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)

        # Set up logger
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # File handler for all logs
        log_file = os.path.join(log_dir, f"{name}.log")
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Error log file handler
        error_log_file = os.path.join(log_dir, f"{name}_error.log")
        error_file_handler = RotatingFileHandler(
            error_log_file, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(formatter)
        logger.addHandler(error_file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)
        logger.addHandler(console_handler)

        cls._logger = logger
        return logger

    @classmethod
    def get_logger(cls):
        """Get the configured logger instance"""
        if cls._logger is None:
            return cls.setup_logger()
        return cls._logger

    @staticmethod
    def log_api_request(request, response_status, response_time):
        """Log API request details"""
        logger = Logger.get_logger()

        log_data = {
            'timestamp': datetime.datetime.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'status': response_status,
            'response_time_ms': response_time,
            'ip': request.remote_addr,
            'user_agent': request.user_agent.string if hasattr(request, 'user_agent') else 'Unknown'
        }

        if response_status >= 400:
            logger.warning(f"API Request: {log_data}")
        else:
            logger.info(f"API Request: {log_data}")

    @staticmethod
    def log_error(error, context=None):
        """Log error with context"""
        logger = Logger.get_logger()
        if context:
            logger.error(f"Error: {error}, Context: {context}")
        else:
            logger.error(f"Error: {error}")

    @staticmethod
    def log_security_event(event_type, details, severity='info'):
        """Log security-related events"""
        logger = Logger.get_logger()
        log_data = {
            'timestamp': datetime.datetime.now().isoformat(),
            'event_type': event_type,
            'details': details,
            'severity': severity
        }

        if severity == 'critical':
            logger.critical(f"Security Event: {log_data}")
        elif severity == 'error':
            logger.error(f"Security Event: {log_data}")
        elif severity == 'warning':
            logger.warning(f"Security Event: {log_data}")
        else:
            logger.info(f"Security Event: {log_data}")
