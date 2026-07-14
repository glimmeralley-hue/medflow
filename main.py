#!/usr/bin/env python3
"""
MedFlow - Native Medical School Command Center
A lightweight, native desktop application for medical students
featuring a high-yield planner and scheduler with dark theme aesthetic.

This file is kept for backward compatibility. The modular UI has been
extracted to medflow/ui/. Run main_refactored.py for the new version.
"""

import sys
from pathlib import Path

# Add the medflow package to the path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the modular version
from main_refactored import main

if __name__ == "__main__":
    sys.exit(main())