"""Flashcard import functionality for CSV and Anki APKG formats."""

import csv
import json
import zipfile
import tempfile
import os
from pathlib import Path
from typing import List, Tuple, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QProgressBar, QTextEdit
)
from PySide6.QtCore import Qt

from medflow.database import Database
from medflow.utils.logging import get_logger

logger = get_logger(__name__)


class FlashcardImporter:
    """Handles importing flashcards from various file formats."""

    @staticmethod
    def import_from_csv(file_path: str, deck_id: int, db: Database) -> int:
        """
        Import flashcards from a CSV file.
        Expected format: front,back (one card per row)
        Returns count of imported cards.
        """
        try:
            count = 0
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        front = row[0].strip()
                        back = row[1].strip()
                        if front and back:
                            db.add_flashcard(deck_id, front, back)
                            count += 1
            logger.info(f"Imported {count} cards from CSV: {file_path}")
            return count
        except Exception as e:
            logger.error(f"Error importing CSV: {e}")
            raise

    @staticmethod
    def import_from_anki_apkg(file_path: str, deck_id: int, db: Database) -> int:
        """
        Import flashcards from Anki .apkg file.
        Extracts the SQLite database from the zip and reads cards.
        Returns count of imported cards.
        """
        try:
            count = 0
            # Anki APKG files are zip archives containing a collection.anki21 file
            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(file_path, 'r') as zf:
                    # Find the .anki21 file
                    anki_files = [f for f in zf.namelist() if f.endswith('.anki21') or f.endswith('.anki2')]
                    if not anki_files:
                        raise ValueError("No Anki database found in APKG file")
                    
                    zf.extract(anki_files[0], tmpdir)
                    anki_db_path = Path(tmpdir) / anki_files[0]
                    
                    # Import Anki database
                    import sqlite3
                    conn = sqlite3.connect(str(anki_db_path))
                    cursor = conn.cursor()
                    
                    # Try to get notes (front/back from fields)
                    try:
                        # Anki stores notes with field content
                        cursor.execute("SELECT sfld, mflds FROM notes LIMIT 1")
                        # Check if it's the new format
                        columns = [desc[0] for desc in cursor.description]
                        
                        cursor.execute("SELECT flds FROM notes")
                        for row in cursor.fetchall():
                            fields = row[0].split('\x1f')  # Anki field separator
                            if len(fields) >= 2:
                                front = fields[0].strip()
                                back = fields[1].strip()
                                db.add_flashcard(deck_id, front, back)
                                count += 1
                    except Exception:
                        # Try alternative table structure
                        cursor.execute("SELECT front, back FROM cards")
                        for row in cursor.fetchall():
                            front, back = row[0], row[1]
                            if front and back:
                                db.add_flashcard(deck_id, front, back)
                                count += 1
                    
                    conn.close()
            
            logger.info(f"Imported {count} cards from APKG: {file_path}")
            return count
        except Exception as e:
            logger.error(f"Error importing APKG: {e}")
            raise

    @staticmethod
    def import_from_txt(file_path: str, deck_id: int, db: Database) -> int:
        """
        Import flashcards from a text file.
        Expected format: Q: question / A: answer or Q&A separated by newlines.
        Returns count of imported cards.
        """
        try:
            count = 0
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try Q/A format
            lines = content.split('\n')
            front = None
            for line in lines:
                line = line.strip()
                if line.startswith('Q:') or line.startswith('Question:'):
                    if front is not None and back is not None:
                        db.add_flashcard(deck_id, front, back)
                        count += 1
                    front = line[2:].strip() if line.startswith('Q:') else line[9:].strip()
                    back = None
                elif line.startswith('A:') or line.startswith('Answer:'):
                    back = line[2:].strip() if line.startswith('A:') else line[7:].strip()
            
            # Don't forget the last card
            if front is not None and back is not None:
                db.add_flashcard(deck_id, front, back)
                count += 1
            
            # If no Q/A format found, try blank-line separated pairs
            if count == 0:
                blocks = content.split('\n\n')
                for i in range(0, len(blocks) - 1, 2):
                    front = blocks[i].strip()
                    back = blocks[i + 1].strip()
                    if front and back:
                        db.add_flashcard(deck_id, front, back)
                        count += 1
            
            logger.info(f"Imported {count} cards from TXT: {file_path}")
            return count
        except Exception as e:
            logger.error(f"Error importing TXT: {e}")
            raise

    @staticmethod
    def import_file(deck_id: int, db: Database, parent: QWidget = None) -> int:
        """
        Show file dialog and import flashcards.
        Returns count of imported cards.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            parent,
            "Import Flashcards",
            "",
            "Flashcard Files (*.csv *.apkg *.txt);;CSV Files (*.csv);;Anki Files (*.apkg);;Text Files (*.txt);;All Files (*)"
        )
        
        if not file_path:
            return 0
        
        ext = Path(file_path).suffix.lower()
        
        try:
            if ext == '.csv':
                return FlashcardImporter.import_from_csv(file_path, deck_id, db)
            elif ext == '.apkg':
                return FlashcardImporter.import_from_anki_apkg(file_path, deck_id, db)
            elif ext == '.txt':
                return FlashcardImporter.import_from_txt(file_path, deck_id, db)
            else:
                QMessageBox.warning(parent, "Unsupported Format", 
                                  f"File format '{ext}' is not supported.")
                return 0
        except Exception as e:
            QMessageBox.critical(parent, "Import Error", 
                                 f"Failed to import file:\n{str(e)}")
            return 0