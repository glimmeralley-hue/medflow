"""Library book data model."""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class LibraryBook:
    """Represents a book in the digital library."""
    
    id: Optional[int] = None
    title: str = ""
    author: Optional[str] = None
    file_path: str = ""
    category: str = "General"
    custom_category: Optional[str] = None
    description: Optional[str] = None
    pages: int = 0
    current_page: int = 0
    is_read: bool = False
    rating: Optional[int] = None
    notes: Optional[str] = None
    date_added: Optional[str] = None
    last_opened: Optional[str] = None
    
    def __post_init__(self):
        """Validate book data after initialization."""
        if not self.title:
            raise ValueError("Book title is required")
        if not self.file_path:
            raise ValueError("File path is required")
        if self.rating is not None and not (1 <= self.rating <= 5):
            raise ValueError("Rating must be between 1 and 5")
        if self.pages < 0:
            raise ValueError("Pages cannot be negative")
        if self.current_page < 0:
            raise ValueError("Current page cannot be negative")
    
    @property
    def reading_progress(self) -> float:
        """Get reading progress as percentage."""
        if self.pages > 0:
            return (self.current_page / self.pages) * 100
        return 0.0
    
    @property
    def is_started(self) -> bool:
        """Check if book has been started."""
        return self.current_page > 0
    
    def to_dict(self) -> dict:
        """Convert book to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'file_path': self.file_path,
            'category': self.category,
            'custom_category': self.custom_category,
            'description': self.description,
            'pages': self.pages,
            'current_page': self.current_page,
            'is_read': self.is_read,
            'rating': self.rating,
            'notes': self.notes,
            'date_added': self.date_added,
            'last_opened': self.last_opened,
            'reading_progress': self.reading_progress,
            'is_started': self.is_started
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LibraryBook':
        """Create book from dictionary."""
        return cls(
            id=data.get('id'),
            title=data.get('title', ''),
            author=data.get('author'),
            file_path=data.get('file_path', ''),
            category=data.get('category', 'General'),
            custom_category=data.get('custom_category'),
            description=data.get('description'),
            pages=data.get('pages', 0),
            current_page=data.get('current_page', 0),
            is_read=bool(data.get('is_read', False)),
            rating=data.get('rating'),
            notes=data.get('notes'),
            date_added=data.get('date_added'),
            last_opened=data.get('last_opened')
        )


@dataclass
class Bookmark:
    """Represents a bookmark in a library book."""
    
    id: Optional[int] = None
    book_id: int = 0
    page_number: int = 0
    note: Optional[str] = None
    created_at: Optional[str] = None
    
    def __post_init__(self):
        """Validate bookmark data after initialization."""
        if self.page_number < 0:
            raise ValueError("Page number cannot be negative")
    
    def to_dict(self) -> dict:
        """Convert bookmark to dictionary."""
        return {
            'id': self.id,
            'book_id': self.book_id,
            'page_number': self.page_number,
            'note': self.note,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Bookmark':
        """Create bookmark from dictionary."""
        return cls(
            id=data.get('id'),
            book_id=data.get('book_id', 0),
            page_number=data.get('page_number', 0),
            note=data.get('note'),
            created_at=data.get('created_at')
        )
