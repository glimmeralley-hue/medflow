"""Input validation and sanitization functions."""

import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
from .exceptions import ValidationError


def sanitize_string(input_string: str, max_length: int = 1000) -> str:
    """
    Sanitize a string input by removing potentially harmful characters.
    
    Args:
        input_string: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
        
    Raises:
        ValidationError: If string is too long or contains invalid characters
    """
    if not isinstance(input_string, str):
        raise ValidationError("Input must be a string")
    
    if len(input_string) > max_length:
        raise ValidationError(f"String exceeds maximum length of {max_length}")
    
    # Remove null bytes and control characters (except newline, tab, carriage return)
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', input_string)
    
    # Strip leading/trailing whitespace
    sanitized = sanitized.strip()
    
    return sanitized


def validate_date(date_string: str, date_format: str = "%Y-%m-%d") -> datetime:
    """
    Validate and parse a date string.
    
    Args:
        date_string: Date string to validate
        date_format: Expected date format
        
    Returns:
        Parsed datetime object
        
    Raises:
        ValidationError: If date is invalid
    """
    try:
        return datetime.strptime(date_string, date_format)
    except ValueError as e:
        raise ValidationError(f"Invalid date format: {date_string}. Expected format: {date_format}") from e


def validate_time(time_string: str, time_format: str = "%H:%M") -> datetime:
    """
    Validate and parse a time string.
    
    Args:
        time_string: Time string to validate
        time_format: Expected time format
        
    Returns:
        Parsed datetime object
        
    Raises:
        ValidationError: If time is invalid
    """
    try:
        return datetime.strptime(time_string, time_format)
    except ValueError as e:
        raise ValidationError(f"Invalid time format: {time_string}. Expected format: {time_format}") from e


def validate_time_range(start_time: str, end_time: str, time_format: str = "%H:%M") -> Tuple[datetime, datetime]:
    """
    Validate that end time is after start time.
    
    Args:
        start_time: Start time string
        end_time: End time string
        time_format: Expected time format
        
    Returns:
        Tuple of (start_datetime, end_datetime)
        
    Raises:
        ValidationError: If time range is invalid
    """
    start = validate_time(start_time, time_format)
    end = validate_time(end_time, time_format)
    
    if end <= start:
        raise ValidationError("End time must be after start time")
    
    return start, end


def validate_score(score: float, min_score: float = 0.0, max_score: float = 100.0) -> float:
    """
    Validate a score is within acceptable range.
    
    Args:
        score: Score to validate
        min_score: Minimum acceptable score
        max_score: Maximum acceptable score
        
    Returns:
        Validated score
        
    Raises:
        ValidationError: If score is out of range
    """
    try:
        score_float = float(score)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"Invalid score: {score}. Must be a number") from e
    
    if not (min_score <= score_float <= max_score):
        raise ValidationError(f"Score must be between {min_score} and {max_score}")
    
    return score_float


def validate_file_path(file_path: str, must_exist: bool = False, allowed_extensions: Optional[list] = None) -> Path:
    """
    Validate a file path for security and existence.
    
    Args:
        file_path: File path to validate
        must_exist: Whether the file must exist
        allowed_extensions: List of allowed file extensions (e.g., ['.pdf', '.epub'])
        
    Returns:
        Validated Path object
        
    Raises:
        ValidationError: If path is invalid
        FileNotFoundError: If file must exist but doesn't
    """
    from .exceptions import FileNotFoundError as MedFlowFileNotFoundError
    
    # Basic path validation
    try:
        path = Path(file_path).resolve()
    except (TypeError, ValueError) as e:
        raise ValidationError(f"Invalid file path: {file_path}") from e
    
    # Check for path traversal attempts
    if '..' in str(path):
        raise ValidationError("Path traversal not allowed")
    
    # Check file extension
    if allowed_extensions:
        if path.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
            raise ValidationError(f"File extension not allowed. Allowed: {allowed_extensions}")
    
    # Check existence if required
    if must_exist and not path.exists():
        raise MedFlowFileNotFoundError(f"File not found: {file_path}")
    
    return path


def validate_hours(hours: float, min_hours: float = 0.0, max_hours: float = 24.0) -> float:
    """
    Validate study hours are within acceptable range.
    
    Args:
        hours: Hours to validate
        min_hours: Minimum acceptable hours
        max_hours: Maximum acceptable hours
        
    Returns:
        Validated hours
        
    Raises:
        ValidationError: If hours are out of range
    """
    try:
        hours_float = float(hours)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"Invalid hours: {hours}. Must be a number") from e
    
    if not (min_hours <= hours_float <= max_hours):
        raise ValidationError(f"Hours must be between {min_hours} and {max_hours}")
    
    return hours_float


def validate_rating(rating: int, min_rating: int = 1, max_rating: int = 5) -> int:
    """
    Validate a rating is within acceptable range.
    
    Args:
        rating: Rating to validate
        min_rating: Minimum acceptable rating
        max_rating: Maximum acceptable rating
        
    Returns:
        Validated rating
        
    Raises:
        ValidationError: If rating is out of range
    """
    try:
        rating_int = int(rating)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"Invalid rating: {rating}. Must be an integer") from e
    
    if not (min_rating <= rating_int <= max_rating):
        raise ValidationError(f"Rating must be between {min_rating} and {max_rating}")
    
    return rating_int
