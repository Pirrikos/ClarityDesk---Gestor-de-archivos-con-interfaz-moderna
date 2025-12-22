"""
EmailService - Email sending operations.

Handles file preparation and mailto link opening.
Does NOT handle persistence (that's EmailHistoryService responsibility).
"""

import os
import shutil
import tempfile
import webbrowser
from pathlib import Path
from typing import List, Optional

from app.core.logger import get_logger
from app.models.email_session import EmailSession
from app.services.path_utils import normalize_path

logger = get_logger(__name__)


class EmailService:
    """Service for preparing files and opening email client."""
    
    def __init__(self):
        """Initialize EmailService."""
        pass
    
    def prepare_files_for_email(self, file_paths: List[str]) -> Optional[str]:
        """
        Copy selected files to a temporary folder for email attachment.
        
        Args:
            file_paths: List of file paths to prepare.
            
        Returns:
            Path to temporary folder, or None if preparation failed.
        """
        if not file_paths:
            logger.warning("No files provided for email preparation")
            return None
        
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix="claritydesk_email_")
            
            # Copy files to temporary directory
            copied_count = 0
            for file_path in file_paths:
                normalized_path = normalize_path(file_path)
                
                # Validate file exists and is readable
                if not os.path.exists(normalized_path):
                    logger.warning(f"File does not exist: {normalized_path}")
                    continue
                
                if not os.access(normalized_path, os.R_OK):
                    logger.error(f"No read permission: {normalized_path}")
                    continue
                
                # Copy file to temp directory
                try:
                    file_name = os.path.basename(normalized_path)
                    dest_path = os.path.join(temp_dir, file_name)
                    
                    # Handle duplicate names
                    counter = 1
                    base_name, ext = os.path.splitext(file_name)
                    while os.path.exists(dest_path):
                        new_name = f"{base_name}_{counter}{ext}"
                        dest_path = os.path.join(temp_dir, new_name)
                        counter += 1
                    
                    shutil.copy2(normalized_path, dest_path)
                    copied_count += 1
                except Exception as e:
                    logger.error(f"Failed to copy file {normalized_path}: {e}")
                    continue
            
            if copied_count == 0:
                logger.warning("No files were copied to temporary folder")
                # Clean up empty temp directory
                try:
                    os.rmdir(temp_dir)
                except Exception:
                    pass
                return None
            
            logger.debug(f"Prepared {copied_count} files in {temp_dir}")
            return temp_dir
            
        except Exception as e:
            logger.error(f"Failed to prepare files for email: {e}", exc_info=True)
            return None
    
    def open_mailto(self, folder_path: Optional[str] = None) -> bool:
        """
        Open default email client with mailto link.
        
        Note: La nueva Outlook para Windows no soporta bien mailto con parámetros.
        Por eso solo abrimos mailto básico sin parámetros, y la carpeta temporal
        se abre por separado para que el usuario pueda arrastrar archivos.
        
        Args:
            folder_path: Optional path to folder with prepared files (not used in mailto).
            
        Returns:
            True if mailto was opened successfully, False otherwise.
        """
        try:
            # Abrir mailto básico sin parámetros para evitar problemas con nueva Outlook
            # La nueva Outlook para Windows muestra error con mailto que tiene parámetros
            mailto_url = "mailto:"
            
            # Open mailto link (non-blocking)
            webbrowser.open(mailto_url)
            logger.debug(f"Opened mailto link: {mailto_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to open mailto: {e}", exc_info=True)
            return False
    
    def create_email_session(self, file_paths: List[str], temp_folder_path: str) -> EmailSession:
        """
        Create EmailSession object from file paths and temp folder.
        
        Does NOT persist the session (that's EmailHistoryService responsibility).
        
        Args:
            file_paths: List of original file paths.
            temp_folder_path: Path to temporary folder with copied files.
            
        Returns:
            EmailSession object.
        """
        from datetime import datetime
        
        return EmailSession(
            timestamp=datetime.now(),
            file_paths=file_paths.copy(),
            temp_folder_path=temp_folder_path
        )

