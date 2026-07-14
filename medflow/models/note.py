"""Note data models."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class StudyNote:
    """Represents a high-yield fact linked to an academic event."""
    
    id: Optional[int] = None
    event_id: Optional[int] = None
    high_yield_fact: str = ""
    created_at: Optional[str] = None
    
    def __post_init__(self):
        """Validate study note data after initialization."""
        if not self.high_yield_fact:
            raise ValueError("High-yield fact is required")
    
    def to_dict(self) -> dict:
        """Convert study note to dictionary."""
        return {
            'id': self.id,
            'event_id': self.event_id,
            'high_yield_fact': self.high_yield_fact,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'StudyNote':
        """Create study note from dictionary."""
        return cls(
            id=data.get('id'),
            event_id=data.get('event_id'),
            high_yield_fact=data.get('high_yield_fact', ''),
            created_at=data.get('created_at')
        )


@dataclass
class AppNote:
    """Represents a general application note."""
    
    id: Optional[int] = None
    title: str = ""
    content: str = ""
    category: str = "General"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        """Validate app note data after initialization."""
        if not self.title:
            raise ValueError("Note title is required")
        if not self.content:
            raise ValueError("Note content is required")
    
    @property
    def word_count(self) -> int:
        """Get word count of note content."""
        return len(self.content.split())
    
    @property
    def character_count(self) -> int:
        """Get character count of note content."""
        return len(self.content)
    
    def to_dict(self) -> dict:
        """Convert app note to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'word_count': self.word_count,
            'character_count': self.character_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AppNote':
        """Create app note from dictionary."""
        return cls(
            id=data.get('id'),
            title=data.get('title', ''),
            content=data.get('content', ''),
            category=data.get('category', 'General'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
