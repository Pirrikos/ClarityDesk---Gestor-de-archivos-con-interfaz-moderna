"""
Logger - Centralized logging configuration.

Provides centralized logging setup for the entire application.
Logs are written to both file (AppData/Local/ClarityDesk/logs/) and console.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """
    Setup and return a logger instance with centralized configuration.
    
    Args:
        name: Logger name (typically __name__ of the module).
        level: Logging level (default: INFO).
        log_to_file: Whether to log to file (default: True).
        log_to_console: Whether to log to console (default: True).
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Formato: timestamp - nivel - módulo - mensaje
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para archivo
    if log_to_file:
        try:
            log_dir = _get_log_directory()
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Archivo de log con fecha
            log_file = log_dir / f'claritydesk_{datetime.now().strftime("%Y%m%d")}.log'
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}")
    
    # Handler para consola - SIEMPRE activado para ver logs en PowerShell
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def _get_log_directory() -> Path:
    """
    Get log directory path (AppData/Local/ClarityDesk/logs/).
    
    Returns:
        Path to log directory.
    """
    # Usar LOCALAPPDATA en Windows, ~/.local/share en Linux/Mac
    if os.name == 'nt':
        appdata = os.getenv('LOCALAPPDATA', os.path.expanduser('~'))
        return Path(appdata) / 'ClarityDesk' / 'logs'
    else:
        return Path.home() / '.local' / 'share' / 'ClarityDesk' / 'logs'


def get_logger(name: Optional[str] = None, level: Optional[int] = None) -> logging.Logger:
    """
    Get logger instance for a module.
    
    Convenience function that uses module name automatically.
    
    Args:
        name: Optional logger name. If None, uses caller's __name__.
        level: Optional logging level. If None, uses default (DEBUG for preview modules, INFO otherwise).
               Use logging.DEBUG for debug messages.
    
    Returns:
        Logger instance.
    """
    if name is None:
        import inspect
        # Get caller's module name
        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get('__name__', 'claritydesk')
        else:
            name = 'claritydesk'
    
    if level is None:
        # Respetar override por variable de entorno CLARITY_LOG_LEVEL
        env_level = os.getenv('CLARITY_LOG_LEVEL')
        if env_level:
            level = getattr(logging, env_level.upper(), logging.INFO)
        else:
            # Priorizar DEBUG solo para módulos de búsqueda si se necesitara
            level = logging.DEBUG if 'search' in name.lower() else logging.INFO
    
    return setup_logger(name, level=level)

