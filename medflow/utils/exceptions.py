"""Custom exception classes for MedFlow application."""


class MedFlowError(Exception):
    """Base exception for all MedFlow errors."""
    pass


class DatabaseError(MedFlowError):
    """Exception raised for database-related errors."""
    pass


class ValidationError(MedFlowError):
    """Exception raised for input validation errors."""
    pass


class FileNotFoundError(MedFlowError):
    """Exception raised when a required file is not found."""
    pass


class ConfigurationError(MedFlowError):
    """Exception raised for configuration-related errors."""
    pass


class MigrationError(MedFlowError):
    """Exception raised for database migration errors."""
    pass
