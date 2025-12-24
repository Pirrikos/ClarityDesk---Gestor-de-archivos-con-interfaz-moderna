import os
import shutil
import tempfile
from datetime import datetime
from typing import List, Optional

from app.core.logger import get_logger
from app.models.file_box_session import FileBoxSession
from app.services.path_utils import normalize_path

logger = get_logger(__name__)


class FileBoxService:
    def prepare_files(self, file_paths: List[str]) -> Optional[str]:
        if not file_paths:
            logger.warning("No files provided for file box preparation")
            return None
        
        try:
            temp_dir = tempfile.mkdtemp(prefix="claritydesk_filebox_")
            
            copied_count = 0
            for file_path in file_paths:
                normalized_path = normalize_path(file_path)
                
                if not os.path.exists(normalized_path):
                    logger.warning(f"File does not exist: {normalized_path}")
                    continue
                
                if not os.access(normalized_path, os.R_OK):
                    logger.error(f"No read permission: {normalized_path}")
                    continue
                
                try:
                    file_name = os.path.basename(normalized_path)
                    dest_path = os.path.join(temp_dir, file_name)
                    
                    counter = 1
                    base_name, ext = os.path.splitext(file_name)
                    while os.path.exists(dest_path):
                        new_name = f"{base_name}_{counter}{ext}"
                        dest_path = os.path.join(temp_dir, new_name)
                        counter += 1
                    
                    if os.path.isdir(normalized_path):
                        shutil.copytree(normalized_path, dest_path, dirs_exist_ok=True)
                    else:
                        shutil.copy2(normalized_path, dest_path)
                    copied_count += 1
                except PermissionError as e:
                    logger.error(f"Permission denied copying file {normalized_path}: {e}")
                    continue
                except OSError as e:
                    logger.error(f"OS error copying file {normalized_path}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Failed to copy file {normalized_path}: {e}")
                    continue
            
            if copied_count == 0:
                logger.warning("No files were copied to temporary folder")
                try:
                    os.rmdir(temp_dir)
                except Exception:
                    pass
                return None
            
            logger.debug(f"Prepared {copied_count} files in {temp_dir}")
            return temp_dir
            
        except Exception as e:
            logger.error(f"Failed to prepare files for file box: {e}", exc_info=True)
            return None
    
    def create_file_box_session(self, file_paths: List[str], temp_folder_path: str) -> FileBoxSession:
        return FileBoxSession(
            timestamp=datetime.now(),
            file_paths=file_paths.copy(),
            temp_folder_path=temp_folder_path
        )

