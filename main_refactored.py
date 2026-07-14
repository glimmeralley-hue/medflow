#!/usr/bin/env python3
"""
MedFlow - Native Medical School Command Center
A lightweight, native desktop application for medical students
featuring a high-yield planner and scheduler with dark theme aesthetic.

Refactored version with fully modular architecture.
"""

import sys
from pathlib import Path

# Add the medflow package to the path
sys.path.insert(0, str(Path(__file__).parent))

from medflow.database import Database
from medflow.utils import setup_logging, get_config
from medflow.utils.logging import get_logger

# Initialize logging
config = get_config()
setup_logging(
    log_level=config.get('logging.level', 'INFO'),
    log_file=config.get('logging.log_file'),
    log_to_console=config.get('logging.log_to_console', True)
)

logger = get_logger(__name__)

# Import PySide6 components
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Import modular UI components
from medflow.ui import MedFlowMainWindow


def main():
    """Main entry point for MedFlow application."""
    try:
        logger.info("Starting MedFlow application...")
        
        # Initialize database with new architecture
        db = Database()
        logger.info("Database initialized successfully")
        
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("MedFlow")
        app.setApplicationVersion("1.0.0")
        
        # Enable high DPI scaling
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Create main window with modular UI
        window = MedFlowMainWindow(database=db)
        window.show()
        
        logger.info("MedFlow application started successfully")
        
        return app.exec()
        
    except Exception as e:
        logger.error(f"Failed to start MedFlow: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())