"""Academic event data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AcademicEvent:
    """Represents an academic event in the scheduler."""
    
    id: Optional[int] = None
    title: str = ""
    category: str = ""
    subtopic: Optional[str] = None
    date: str = ""
    time_start: str = ""
    time_end: str = ""
    notes: Optional[str] = None
    completed: bool = False
    reminder_minutes: int = 15
    reminder_enabled: bool = True
    created_at: Optional[str] = None
    
    def __post_init__(self):
        """Validate event data after initialization."""
        if not self.title:
            raise ValueError("Event title is required")
        if not self.category:
            raise ValueError("Event category is required")
        if not self.date:
            raise ValueError("Event date is required")
        if not self.time_start:
            raise ValueError("Start time is required")
        if not self.time_end:
            raise ValueError("End time is required")
    
    def to_dict(self) -> dict:
        """Convert event to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'subtopic': self.subtopic,
            'date': self.date,
            'time_start': self.time_start,
            'time_end': self.time_end,
            'notes': self.notes,
            'completed': self.completed,
            'reminder_minutes': self.reminder_minutes,
            'reminder_enabled': self.reminder_enabled,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AcademicEvent':
        """Create event from dictionary."""
        return cls(
            id=data.get('id'),
            title=data.get('title', ''),
            category=data.get('category', ''),
            subtopic=data.get('subtopic'),
            date=data.get('date', ''),
            time_start=data.get('time_start', ''),
            time_end=data.get('time_end', ''),
            notes=data.get('notes'),
            completed=bool(data.get('completed', False)),
            reminder_minutes=data.get('reminder_minutes', 15),
            reminder_enabled=bool(data.get('reminder_enabled', True)),
            created_at=data.get('created_at')
        )
