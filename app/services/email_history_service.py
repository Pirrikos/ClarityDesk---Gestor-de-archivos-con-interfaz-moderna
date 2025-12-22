"""
EmailHistoryService - Email history persistence.

Manages persistent storage of email sending sessions in JSON.
Only this service is responsible for persistence decisions.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.core.logger import get_logger
from app.models.email_session import EmailSession

logger = get_logger(__name__)


class EmailHistoryService:
    """Service for persisting email sending history."""
    
    def __init__(self, history_path: Optional[str] = None):
        """
        Initialize EmailHistoryService with storage path.
        
        Args:
            history_path: Optional custom path. Defaults to %APPDATA%/ClarityDesk/email_history.json
        """
        if history_path is None:
            appdata = os.getenv('APPDATA')
            if appdata:
                config_dir = Path(appdata) / "ClarityDesk"
                config_dir.mkdir(parents=True, exist_ok=True)
                history_path = str(config_dir / "email_history.json")
            else:
                # Fallback to home directory
                home_dir = Path.home()
                config_dir = home_dir / ".claritydesk"
                config_dir.mkdir(parents=True, exist_ok=True)
                history_path = str(config_dir / "email_history.json")
        
        self._history_path = Path(history_path)
        self._history_path.parent.mkdir(parents=True, exist_ok=True)
    
    def add_session(self, session: EmailSession) -> None:
        """
        Add email session to persistent history.
        
        Args:
            session: EmailSession to persist.
        """
        try:
            sessions = self._load_sessions()
            
            # Add new session at the beginning (most recent first)
            session_dict = {
                "timestamp": session.timestamp.isoformat(),
                "file_paths": session.file_paths,
                "temp_folder_path": session.temp_folder_path,
                "file_count": session.file_count
            }
            sessions.insert(0, session_dict)
            
            # Keep reasonable limit (last 1000 sessions)
            if len(sessions) > 1000:
                sessions = sessions[:1000]
            
            self._save_sessions(sessions)
            logger.debug(f"Added email session to history: {session.file_count} files")
            
        except Exception as e:
            logger.error(f"Failed to add session to history: {e}", exc_info=True)
    
    def get_recent_sessions(self, limit: int = 50) -> List[EmailSession]:
        """
        Get recent email sessions from history.
        
        Args:
            limit: Maximum number of sessions to return.
            
        Returns:
            List of EmailSession objects, most recent first.
        """
        try:
            sessions = self._load_sessions()
            
            result = []
            for session_dict in sessions[:limit]:
                try:
                    session = EmailSession(
                        timestamp=datetime.fromisoformat(session_dict["timestamp"]),
                        file_paths=session_dict["file_paths"],
                        temp_folder_path=session_dict["temp_folder_path"]
                    )
                    result.append(session)
                except Exception as e:
                    logger.warning(f"Failed to parse session: {e}")
                    continue
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to load recent sessions: {e}", exc_info=True)
            return []
    
    def get_session_by_index(self, index: int) -> Optional[EmailSession]:
        """
        Get email session by index (0 = most recent).
        
        Args:
            index: Index of session to retrieve.
            
        Returns:
            EmailSession if found, None otherwise.
        """
        try:
            sessions = self._load_sessions()
            
            if index < 0 or index >= len(sessions):
                return None
            
            session_dict = sessions[index]
            return EmailSession(
                timestamp=datetime.fromisoformat(session_dict["timestamp"]),
                file_paths=session_dict["file_paths"],
                temp_folder_path=session_dict["temp_folder_path"]
            )
            
        except Exception as e:
            logger.error(f"Failed to get session by index {index}: {e}", exc_info=True)
            return None
    
    def _load_sessions(self) -> List[dict]:
        """Load sessions from JSON file."""
        if not self._history_path.exists():
            return []
        
        try:
            with open(self._history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("sessions", [])
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in history file: {self._history_path}")
            return []
        except Exception as e:
            logger.error(f"Failed to load history: {e}", exc_info=True)
            return []
    
    def _save_sessions(self, sessions: List[dict]) -> None:
        """Save sessions to JSON file with atomic write."""
        try:
            # Atomic write: write to temp file, then rename
            temp_path = self._history_path.with_suffix('.tmp')
            
            data = {
                "sessions": sessions,
                "version": "1.0"
            }
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_path.replace(self._history_path)
            
        except Exception as e:
            logger.error(f"Failed to save history: {e}", exc_info=True)
            # Clean up temp file if rename failed
            temp_path = self._history_path.with_suffix('.tmp')
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass

