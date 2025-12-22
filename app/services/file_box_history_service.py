import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from app.core.logger import get_logger
from app.models.file_box_session import FileBoxSession

logger = get_logger(__name__)

# Retention policy constants
MAX_FILES = 200
RETENTION_DAYS = 90


class FileBoxHistoryService:
    def __init__(self, history_path: Optional[str] = None):
        if history_path is None:
            appdata = os.getenv('APPDATA')
            if appdata:
                config_dir = Path(appdata) / "ClarityDesk"
                config_dir.mkdir(parents=True, exist_ok=True)
                history_path = str(config_dir / "file_box_history.json")
            else:
                home_dir = Path.home()
                config_dir = home_dir / ".claritydesk"
                config_dir.mkdir(parents=True, exist_ok=True)
                history_path = str(config_dir / "file_box_history.json")
        
        self._history_path = Path(history_path)
        self._history_path.parent.mkdir(parents=True, exist_ok=True)
    
    def add_session(self, session: FileBoxSession) -> None:
        try:
            sessions = self._load_sessions()
            
            temp_path = session.temp_folder_path
            existing_index = None
            for i, s in enumerate(sessions):
                if s.get("temp_folder_path") == temp_path:
                    existing_index = i
                    break
            
            session_dict = {
                "timestamp": session.timestamp.isoformat(),
                "file_paths": session.file_paths,
                "temp_folder_path": session.temp_folder_path,
                "file_count": session.file_count
            }
            
            if existing_index is not None:
                sessions[existing_index] = session_dict
            else:
                sessions.insert(0, session_dict)
            
            sessions = self._cleanup_sessions(sessions)
            sessions.sort(key=lambda s: s.get("timestamp", ""), reverse=True)
            self._save_sessions(sessions)
            logger.debug(f"Added file box session to history: {session.file_count} files")
            
        except Exception as e:
            logger.error(f"Failed to add session to history: {e}", exc_info=True)
    
    def get_recent_sessions(self, limit: int = 50) -> List[FileBoxSession]:
        try:
            sessions = self._load_sessions()
            
            result = []
            for session_dict in sessions[:limit]:
                try:
                    session = FileBoxSession(
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
    
    def get_session_by_index(self, index: int) -> Optional[FileBoxSession]:
        try:
            sessions = self._load_sessions()
            
            if index < 0 or index >= len(sessions):
                return None
            
            session_dict = sessions[index]
            return FileBoxSession(
                timestamp=datetime.fromisoformat(session_dict["timestamp"]),
                file_paths=session_dict["file_paths"],
                temp_folder_path=session_dict["temp_folder_path"]
            )
            
        except Exception as e:
            logger.error(f"Failed to get session by index {index}: {e}", exc_info=True)
            return None
    
    def _load_sessions(self, apply_cleanup: bool = True) -> List[dict]:
        sessions = []
        
        if self._history_path.exists():
            try:
                with open(self._history_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    sessions = data.get("sessions", [])
                    logger.debug(f"Loaded {len(sessions)} sessions from file_box_history.json")
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in history file: {self._history_path}")
            except Exception as e:
                logger.error(f"Failed to load file box history: {e}", exc_info=True)
        
        if apply_cleanup and sessions:
            cleaned_sessions = self._cleanup_sessions(sessions)
            if len(cleaned_sessions) != len(sessions):
                cleaned_sessions.sort(key=lambda s: s.get("timestamp", ""), reverse=True)
                self._save_sessions(cleaned_sessions)
                sessions = cleaned_sessions
        
        sessions.sort(key=lambda s: s.get("timestamp", ""), reverse=True)
        
        logger.debug(f"Total sessions loaded: {len(sessions)}")
        return sessions
    
    def _cleanup_sessions(self, sessions: List[dict]) -> List[dict]:
        if not sessions:
            return sessions
        
        now = datetime.now()
        cutoff_date = now - timedelta(days=RETENTION_DAYS)
        
        sessions_sorted = sorted(sessions, key=lambda s: s.get("timestamp", ""))
        
        kept_sessions = []
        current_file_count = 0
        
        for session in sessions_sorted:
            session_timestamp_str = session.get("timestamp", "")
            if not session_timestamp_str:
                continue
            
            try:
                session_timestamp = datetime.fromisoformat(session_timestamp_str)
            except (ValueError, TypeError):
                continue
            
            session_file_count = session.get("file_count", len(session.get("file_paths", [])))
            
            if session_timestamp < cutoff_date:
                logger.debug(f"Removing session older than {RETENTION_DAYS} days: {session_timestamp}")
                continue
            
            if current_file_count + session_file_count > MAX_FILES:
                logger.debug(f"Removing session to stay under {MAX_FILES} file limit: {session_file_count} files")
                continue
            
            kept_sessions.append(session)
            current_file_count += session_file_count
        
        removed_count = len(sessions) - len(kept_sessions)
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} sessions. Kept {len(kept_sessions)} sessions with {current_file_count} total files")
        
        return kept_sessions
    
    def _save_sessions(self, sessions: List[dict]) -> None:
        try:
            temp_path = self._history_path.with_suffix('.tmp')
            
            data = {
                "sessions": sessions,
                "version": "1.0"
            }
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            temp_path.replace(self._history_path)
            
        except Exception as e:
            logger.error(f"Failed to save history: {e}", exc_info=True)
            temp_path = self._history_path.with_suffix('.tmp')
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass

