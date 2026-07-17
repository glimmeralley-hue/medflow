# MedFlow Architecture Documentation

## Project Structure

```
medflow/
├── medflow/                    # Main package
│   ├── __init__.py            # Package initialization
│   ├── database/              # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py      # Connection pooling and management
│   │   ├── models.py          # Database operations
│   │   ├── repositories.py    # Repository pattern for typed data access
│   │   └── migrations.py      # Migration system
│   ├── models/                # Data models
│   │   ├── __init__.py
│   │   ├── event.py           # Academic event model
│   │   ├── exam.py            # Exam score model
│   │   ├── note.py            # Note models
│   │   ├── book.py            # Library book model
│   │   └── profile.py         # User profile model
│   ├── ui/                    # UI layer
│   │   ├── __init__.py
│   │   ├── styles.py          # Centralized stylesheets
│   │   ├── style_guide.py     # StyleGuide for consistent widget creation
│   │   ├── main_window.py     # Main application window
│   │   ├── planner.py         # Calendar and event management
│   │   ├── timer.py           # Pomodoro timer
│   │   ├── notes.py           # Notes section
│   │   ├── results.py         # Results ledger
│   │   ├── library.py         # Digital library
│   │   └── profile.py         # User profile
│   └── utils/                 # Utilities
│       ├── __init__.py
│       ├── exceptions.py      # Custom exceptions
│       ├── logging.py         # Logging configuration
│       ├── validators.py      # Input validation
│       └── config.py          # Configuration management
├── main.py                    # Original monolithic file (backward compatibility)
├── main_refactored.py         # New entry point with modular architecture
├── requirements.txt           # Dependencies with version pinning
├── BUILDING.md                # Build instructions
└── DESIGN_ASSESSMENT.md       # Design assessment and improvement recommendations
```

## Architecture Layers

### 1. Database Layer (`medflow/database/`)
- **Connection Management**: Connection pooling with singleton pattern
- **Migration System**: Version-controlled schema migrations
- **Data Operations**: CRUD operations with validation and error handling
- **Transaction Management**: Context managers for safe transactions
- **Repository Pattern**: Type-safe data access via `repositories.py`

### 2. Models Layer (`medflow/models/`)
- **Data Classes**: Type-safe data structures using dataclasses
- **Validation**: Built-in validation in model constructors
- **Serialization**: Dictionary conversion for API/database operations
- **Business Logic**: Computed properties and helper methods

### 3. UI Layer (`medflow/ui/`)
- **Centralized Styles**: Consistent theming via `theme_manager.py`
- **StyleGuide**: Factory for creating theme-aware styled widgets
- **Widget Components**: Modular UI widgets for each feature
- **Event Handling**: Signal/slot connections
- **State Management**: UI state synchronization with database

### 4. Utils Layer (`medflow/utils/`)
- **Logging**: Structured logging with file and console output
- **Validation**: Input sanitization and validation functions
- **Configuration**: JSON-based configuration management
- **Exceptions**: Custom exception hierarchy

## Key Improvements

### Database Improvements
- ✅ Connection pooling with singleton pattern
- ✅ Migration system with version tracking
- ✅ Foreign key constraints enabled
- ✅ Database indexes for performance
- ✅ Transaction management with context managers
- ✅ Comprehensive error handling and logging
- ✅ Repository pattern for typed data access

### Code Quality
- ✅ Modular architecture with clear separation of concerns
- ✅ Type hints throughout codebase
- ✅ Comprehensive input validation
- ✅ Custom exception hierarchy
- ✅ Structured logging system
- ✅ Configuration management
- ✅ StyleGuide for consistent UI styling

### Security
- ✅ Input sanitization
- ✅ File path validation
- ✅ SQL injection prevention (parameterized queries)
- ✅ Path traversal protection

## Refactored Components (Phase 3)

### StyleGuide (`medflow/ui/style_guide.py`)
Centralized widget styling factory that eliminates code duplication:
- `button_primary()` - Primary action buttons (PRIMARY color)
- `button_secondary()` - Secondary/cancel buttons
- `button_success()` - Success/confirm buttons
- `button_danger()` - Delete/danger buttons
- `input_text()` - Text input fields
- `input_multiline()` - Textarea inputs
- `combo()` - Combo box selectors
- `group_box()` - Styled group boxes
- `list_widget()` - Styled list widgets
- `table_widget()` - Styled tables

### Repository Pattern (`medflow/database/repositories.py`)
Type-safe data access layer:
- `EventRepository` - Academic events with `AcademicEvent` models
- `NoteRepository` - App notes with `AppNote` models
- `ExamRepository` - Exam scores
- `StudyHoursRepository` - Study time tracking
- `LibraryRepository` - Library book management
- `FlashcardRepository` - Flashcards and decks
- `ProfileRepository` - User profile management

## Migration Status

### Completed (Phase 1-3)
- ✅ Project structure created
- ✅ Database layer refactored
- ✅ Models layer created
- ✅ Utils layer completed
- ✅ Configuration system implemented
- ✅ Migration system implemented
- ✅ Centralized theme management
- ✅ StyleGuide factory created
- ✅ Repository pattern implemented

### Remaining Items
- 🔄 Connect StyleGuide to existing widgets (gradual migration)
- 🔄 Add theme integration to results.py
- ⏳ Add comprehensive UI tests
- ⏳ Refactor large widget files into smaller components

## Usage

### Running the Application
```bash
python main_refactored.py
```

### Running Tests
```bash
pytest tests/
```

### Code Quality Checks
```bash
black medflow/
flake8 medflow/
mypy medflow/
```

## Configuration

Configuration is managed via `~/.medflow/config.json`. Default configuration is automatically created on first run.

Key configuration options:
- Database path and backup settings
- UI theme and window settings
- Timer preferences
- Notification settings
- Logging configuration

## Database Schema

The database uses SQLite with the following tables:
- `academic_events` - Scheduled events and classes
- `study_notes` - High-yield facts linked to events
- `study_debt` - Missed/incomplete tasks
- `exam_scores` - Exam results tracking
- `study_hours` - Study time logging
- `completed_tasks` - Task completion tracking
- `user_profile` - User information
- `library_books` - Digital library catalog
- `book_bookmarks` - Reading position bookmarks
- `app_notes` - General study notes
- `flashcard_decks` - Flashcard deck metadata
- `flashcards` - Individual flashcard cards
- `schema_migrations` - Migration version tracking

## Development Guidelines

### Adding New Features
1. Create data model in `medflow/models/`
2. Add repository class in `medflow/database/repositories.py`
3. Create repository method in `medflow/database/models.py`
4. Create UI widget in `medflow/ui/` using StyleGuide
5. Add validation in `medflow/utils/validators.py`
6. Update configuration if needed

### UI Development with StyleGuide
```python
from medflow.ui import StyleGuide

sg = StyleGuide()
# Create themed widgets
save_btn = sg.button_primary(text="Save Note", tooltip="Ctrl+S")
title_input = sg.input_text(placeholder="Note title...")
category_combo = sg.combo(items=["General", "Anatomy", "Physiology"])
```

### Database Migrations
1. Add migration script to `MigrationManager.MIGRATIONS`
2. Increment version number
3. Test migration on fresh database
4. Document schema changes

## Future Enhancements

### High Priority
- Complete StyleGuide adoption across all widgets
- Add theme integration to results.py
- Implement comprehensive testing

### Medium Priority
- Add recurring events support
- Implement study streak tracking dashboard
- Split large widget files into smaller components

### Low Priority
- Mobile version (Toga/Kivy)
- Calendar integration (Google Calendar/iCal)
- API for third-party integrations

---

*This documentation was updated with Phase 3 improvements on 2026-07-16*