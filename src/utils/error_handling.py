"""
Error handling utilities for the Monday Uploader application.
"""

import logging
import traceback
from typing import Any, Dict, List, Optional, Callable, TypeVar, Union
from functools import wraps

import requests
from PySide6.QtWidgets import QMessageBox, QWidget, QDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QStyle

# Get logger
logger = logging.getLogger("monday_uploader.error_handling")

# Type variable for generic return types
T = TypeVar('T')

class ErrorCodes:
    """Error codes for the application"""
    # API Errors (2000-2999)
    API_UNKNOWN_ERROR = 2000
    API_AUTHENTICATION_ERROR = 2001
    API_RATE_LIMIT_EXCEEDED = 2002
    API_PERMISSION_DENIED = 2003
    API_RESOURCE_NOT_FOUND = 2004
    API_REQUEST_INVALID = 2005
    API_SERVER_ERROR = 2006
    
    # Network Errors (3000-3999)
    NETWORK_ERROR = 3000
    NETWORK_UNAVAILABLE = 3001
    CONNECTION_TIMEOUT = 3002
    
    # Database Errors (4000-4999)
    DB_CONNECTION_ERROR = 4000
    DB_QUERY_ERROR = 4001
    DB_INTEGRITY_ERROR = 4002
    
    # File Errors (5000-5999)
    FILE_NOT_FOUND = 5000
    FILE_PERMISSION_DENIED = 5001
    FILE_FORMAT_INVALID = 5002
    
    # Calendar Errors (6000-6999)
    CALENDAR_INIT_ERROR = 6000
    CALENDAR_VIEW_ERROR = 6001
    CALENDAR_EVENT_ERROR = 6002
    CALENDAR_SYNC_ERROR = 6003
    
    # Application Errors (9000-9999)
    APP_UNEXPECTED_ERROR = 9000
    APP_CONFIG_ERROR = 9001
    APP_STARTUP_ERROR = 9002

class MondayError(Exception):
    """
    Base exception class for Monday.com application
    """
    def __init__(
        self, 
        message: str, 
        error_code: int = ErrorCodes.APP_UNEXPECTED_ERROR,
        original_exception: Optional[Exception] = None,
        recovery_options: Optional[List[str]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.original_exception = original_exception
        self.recovery_options = recovery_options or []
        super().__init__(message)
        
    def __str__(self) -> str:
        return f"[Error {self.error_code}] {self.message}"
        
    def log_error(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log the error with detailed information
        """
        error_info = {
            "error_code": self.error_code,
            "message": self.message,
            "original_exception": repr(self.original_exception) if self.original_exception else None,
            "recovery_options": self.recovery_options,
            "context": context or {}
        }
        
        logger.error(f"Error occurred: {self.message}", extra={"error_info": error_info})
        
        # Log the stack trace of the original exception
        if self.original_exception:
            logger.error(f"Original exception: {traceback.format_exc()}")

class NetworkError(MondayError):
    """
    Network-related errors
    """
    def __init__(
        self, 
        message: str, 
        error_code: int = ErrorCodes.NETWORK_UNAVAILABLE,
        original_exception: Optional[Exception] = None
    ):
        recovery_options = [
            "Check your internet connection",
            "Try again later",
            "Check if Monday.com is experiencing issues"
        ]
        super().__init__(message, error_code, original_exception, recovery_options)

class APIError(MondayError):
    """
    Monday.com API-related errors
    """
    def __init__(
        self, 
        message: str, 
        error_code: int = ErrorCodes.API_SERVER_ERROR,
        original_exception: Optional[Exception] = None,
        http_status: Optional[int] = None,
        response_body: Optional[str] = None
    ):
        self.http_status = http_status
        self.response_body = response_body
        
        recovery_options = []
        
        # Add recovery options based on error code
        if error_code == ErrorCodes.API_AUTHENTICATION_ERROR:
            recovery_options = [
                "Check your API key in Settings",
                "Ensure your account has permission for these operations"
            ]
        elif error_code == ErrorCodes.API_RATE_LIMIT_EXCEEDED:
            recovery_options = [
                "Wait before trying again",
                "Reduce the frequency of API calls",
                "Use local data if available"
            ]
        elif error_code == ErrorCodes.API_PERMISSION_DENIED:
            recovery_options = [
                "Check your account permissions on Monday.com",
                "Contact your Monday.com administrator"
            ]
        else:
            recovery_options = [
                "Try again later",
                "Use local data if available",
                "Check if Monday.com is experiencing issues"
            ]
            
        super().__init__(message, error_code, original_exception, recovery_options)
        
    def log_error(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log API error with additional details
        """
        context = context or {}
        context.update({
            "http_status": self.http_status,
            "response_body": self.response_body
        })
        super().log_error(context)

class DatabaseError(MondayError):
    """
    Database-related errors
    """
    def __init__(
        self, 
        message: str, 
        error_code: int = ErrorCodes.DB_CONNECTION_ERROR,
        original_exception: Optional[Exception] = None,
        query: Optional[str] = None
    ):
        self.query = query
        
        recovery_options = [
            "Restart the application",
            "Check database file permissions",
            "Use online data instead"
        ]
        
        super().__init__(message, error_code, original_exception, recovery_options)
        
    def log_error(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log database error with additional details
        """
        context = context or {}
        if self.query:
            # Sanitize query to remove sensitive information
            context["query"] = self.query
        super().log_error(context)

class FileError(MondayError):
    """
    File-related errors
    """
    def __init__(
        self, 
        message: str, 
        error_code: int = ErrorCodes.FILE_NOT_FOUND,
        original_exception: Optional[Exception] = None,
        file_path: Optional[str] = None
    ):
        self.file_path = file_path
        
        recovery_options = [
            "Check if the file exists and has correct permissions",
            "Use a different file"
        ]
        
        super().__init__(message, error_code, original_exception, recovery_options)
        
    def log_error(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log file error with additional details
        """
        context = context or {}
        if self.file_path:
            context["file_path"] = self.file_path
        super().log_error(context)

class ErrorDialog(QDialog):
    """
    Error dialog for displaying errors to the user with recovery options
    """
    def __init__(
        self, 
        parent: Optional[QWidget], 
        title: str, 
        message: str, 
        error_code: int, 
        recovery_options: List[str] = None,
        callback: Optional[Callable[[str], None]] = None
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setWindowModality(Qt.WindowModal)
        
        self.recovery_options = recovery_options or []
        self.callback = callback
        
        # Create error dialog UI
        from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton
        
        layout = QVBoxLayout(self)
        
        # Error icon and message
        message_layout = QHBoxLayout()
        error_icon = QLabel()
        error_icon.setPixmap(self.style().standardIcon(QStyle.SP_MessageBoxCritical).pixmap(32, 32))
        message_layout.addWidget(error_icon, 0, Qt.AlignTop)
        
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_font = QFont()
        message_font.setPointSize(10)
        message_label.setFont(message_font)
        message_layout.addWidget(message_label, 1)
        
        layout.addLayout(message_layout)
        
        # Error code
        error_code_label = QLabel(f"Error Code: {error_code}")
        error_code_label.setStyleSheet("color: gray;")
        layout.addWidget(error_code_label)
        
        # Recovery options
        if self.recovery_options:
            from PySide6.QtWidgets import QGroupBox
            
            options_group = QGroupBox("Options to resolve this error")
            options_layout = QVBoxLayout(options_group)
            
            for option in self.recovery_options:
                option_button = QPushButton(option)
                option_button.clicked.connect(lambda checked, opt=option: self._select_option(opt))
                options_layout.addWidget(option_button)
            
            layout.addWidget(options_group)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Copy details button
        copy_button = QPushButton("Copy Details")
        copy_button.clicked.connect(lambda: self._copy_to_clipboard(f"Error [{error_code}]: {message}"))
        buttons_layout.addWidget(copy_button)
        
        buttons_layout.addStretch(1)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(close_button)
        
        layout.addLayout(buttons_layout)
        
    def _select_option(self, option: str) -> None:
        """Handle recovery option selection"""
        if self.callback:
            self.callback(option)
        self.accept()
        
    def _copy_to_clipboard(self, text: str) -> None:
        """Copy text to clipboard"""
        from PySide6.QtGui import QGuiApplication
        
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        
        from PySide6.QtWidgets import QToolTip
        QToolTip.showText(self.mapToGlobal(self.rect().center()), "Copied to clipboard", self, self.rect(), 2000)

def handle_error(
    exception: Exception, 
    parent: Optional[QWidget] = None, 
    context: Optional[Dict[str, Any]] = None,
    title: Optional[str] = None,
    message: Optional[str] = None,
    callback: Optional[Callable[[str], None]] = None
) -> None:
    """
    Handle an error by displaying an error dialog and logging the error.
    
    Args:
        exception: The exception that occurred
        parent: Parent widget for the error dialog
        context: Additional context information
        title: Custom error dialog title
        message: Custom error message
        callback: Optional callback function to handle user response
    """
    # Log the error
    if isinstance(exception, MondayError):
        exception.log_error(context)
    else:
        logger.error(f"Error occurred: {str(exception)}")
        logger.error(f"Original exception: {traceback.format_exc()}")
    
    # Check if QApplication exists
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        logger.error("Cannot show error dialog: QApplication not initialized")
        return
    
    # Create error dialog
    if isinstance(exception, MondayError):
        dialog = ErrorDialog(
            parent=parent if isinstance(parent, QWidget) else None,
            title=title or "Error",
            message=message or str(exception),
            error_code=exception.error_code,
            recovery_options=exception.recovery_options,
            callback=callback
        )
    else:
        # Use QMessageBox for non-MondayError exceptions
        dialog = QMessageBox()
        dialog.setIcon(QMessageBox.Critical)
        dialog.setWindowTitle(title or "Error")
        dialog.setText(message or str(exception))
        dialog.setStandardButtons(QMessageBox.Ok)
        if isinstance(parent, QWidget):
            dialog.setParent(parent)
    
    # Show dialog
    dialog.exec()

def retry(
    max_retries: int = 3, 
    retry_delay: float = 1.0, 
    backoff_factor: float = 2.0,
    retry_on_exceptions: tuple = (requests.RequestException,),
    retry_on_status_codes: tuple = (429, 500, 502, 503, 504)
):
    """
    Decorator for retrying functions that might fail due to temporary issues.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay between retries
        retry_on_exceptions: Exceptions to retry on
        retry_on_status_codes: HTTP status codes to retry on
    
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            retries = 0
            delay = retry_delay
            
            while True:
                try:
                    return func(*args, **kwargs)
                except retry_on_exceptions as e:
                    if isinstance(e, requests.HTTPError):
                        status_code = e.response.status_code if hasattr(e, 'response') else None
                        if status_code not in retry_on_status_codes:
                            # Don't retry for non-retryable status codes
                            raise
                            
                    retries += 1
                    if retries > max_retries:
                        # We've exceeded the maximum retries, so re-raise the exception
                        raise
                        
                    # Log retry attempt
                    func_name = getattr(func, '__name__', str(func))
                    logger.warning(
                        f"Retry {retries}/{max_retries} for {func_name} after error: {str(e)}"
                    )
                    
                    # Wait before retrying with exponential backoff
                    time.sleep(delay)
                    delay *= backoff_factor
                    
        return wrapper
    return decorator 