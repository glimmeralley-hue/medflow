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
│   │   └── migrations.py      # Migration system
│   ├── models/                # Data models
│   │   ├── __init__.py
│   │   ├── event.py           # Academic event model
│   │   ├── exam.py            # Exam score model
│   │   ├── note.py            # Note models
│   │   ├── book.py            # Library book model
│   │   └── profile.py         # User profile model
│   ├── ui/                    # UI layer (to be completed)
│   │   ├── __init__.py
│   │   ├── styles.py          # Centralized stylesheets
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
├── main.py                    # Original monolithic file (to be replaced)
├── main_refactored.py         # New entry point with modular architecture
├── requirements.txt           # Dependencies with version pinning
└── BUILDING.md                # Build instructions
```

## Architecture Layers

### 1. Database Layer (`medflow/database/`)
- **Connection Management**: Connection pooling with singleton pattern
- **Migration System**: Version-controlled schema migrations
- **Data Operations**: CRUD operations with validation and error handling
- **Transaction Management**: Context managers for safe transactions

### 2. Models Layer (`medflow/models/`)
- **Data Classes**: Type-safe data structures using dataclasses
- **Validation**: Built-in validation in model constructors
- **Serialization**: Dictionary conversion for API/database operations
- **Business Logic**: Computed properties and helper methods

### 3. UI Layer (`medflow/ui/`)
- **Centralized Styles**: Consistent theming via `styles.py`
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
- ✅ CHECK constraints for data validation
- ✅ Transaction management with context managers
- ✅ Comprehensive error handling and logging

### Code Quality
- ✅ Modular architecture with clear separation of concerns
- ✅ Type hints throughout codebase
- ✅ Comprehensive input validation
- ✅ Custom exception hierarchy
- ✅ Structured logging system
- ✅ Configuration management

### Security
- ✅ Input sanitization
- ✅ File path validation
- ✅ SQL injection prevention (parameterized queries)
- ✅ Path traversal protection

## Migration Status

### Completed (Phase 1-2)
- ✅ Project structure created
- ✅ Database layer refactored
- ✅ Models layer created
- ✅ Utils layer completed
- ✅ Configuration system implemented
- ✅ Migration system implemented
- ✅ Centralized stylesheets created

### In Progress (Phase 1)
- 🔄 UI layer extraction (partially complete)
- 🔄 Entry point refactoring

### Pending (Phase 3-10)
- ⏳ User-friendly error messages
- ⏳ Input validation in UI forms
- ⏳ Testing framework setup
- ⏳ UI widget extraction
- ⏳ Export/import functionality
- ⏳ Performance optimizations
- ⏳ Enhanced features
- ⏳ Documentation updates

## Usage

### Running the Refactored Version
```bash
python main_refactored.py
```

### Running the Original Version
```bash
python main.py
```

### Running Tests (when implemented)
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
- `schema_migrations` - Migration version tracking

## Development Guidelines

### Adding New Features
1. Create data model in `medflow/models/`
2. Add database operations in `medflow/database/models.py`
3. Create UI widget in `medflow/ui/`
4. Add validation in `medflow/utils/validators.py`
5. Update configuration if needed

### Database Migrations
1. Add migration script to `MigrationManager.MIGRATIONS`
2. Increment version number
3. Test migration on fresh database
4. Document schema changes

### UI Development
1. Use centralized styles from `styles.py`
2. Follow existing widget patterns
3. Implement proper error handling
4. Add keyboard shortcuts where appropriate
5. Ensure accessibility compliance

## Future Enhancements

### High Priority
- Complete UI layer extraction
- Implement comprehensive testing
- Add export/import functionality
- Implement backup/restore UI

### Medium Priority
- Add recurring events support
- Implement study streak tracking
- Create mobile version
- Add calendar integration

### Low Priority
- Advanced analytics dashboard
- Spaced repetition system
- Flashcard integration
- API for third-party integrations
