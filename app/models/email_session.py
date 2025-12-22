"""
EmailSession - Data model for email sending sessions.

Pure data structure representing an email sending attempt.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class EmailSession:
    """Represents an email sending session."""
    
    timestamp: datetime
    file_paths: List[str]
    temp_folder_path: str
    
    @property
    def file_count(self) -> int:
        """Get number of files in this session."""
        return len(self.file_paths)

