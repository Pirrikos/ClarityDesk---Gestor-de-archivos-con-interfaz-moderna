from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class FileBoxSession:
    timestamp: datetime
    file_paths: List[str]
    temp_folder_path: str
    
    @property
    def file_count(self) -> int:
        return len(self.file_paths)

