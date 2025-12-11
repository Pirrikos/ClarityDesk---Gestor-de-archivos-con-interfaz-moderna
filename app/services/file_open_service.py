"""
FileOpenService - File opening operations.

Handles opening files with default system application.
"""

import os
import platform
import subprocess


def open_file_with_system(file_path: str) -> None:
    """Open file with default system application."""
    try:
        if platform.system() == 'Windows':
            os.startfile(file_path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', file_path])
        else:  # Linux
            subprocess.run(['xdg-open', file_path])
    except Exception:
        pass

