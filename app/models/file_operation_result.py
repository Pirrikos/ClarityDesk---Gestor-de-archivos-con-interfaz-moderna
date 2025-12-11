"""
FileOperationResult - Structured result for filesystem operations.

Simple dataclass for returning success/error results from file operations.
"""

from dataclasses import dataclass


@dataclass
class FileOperationResult:
    """Structured result for filesystem operations."""
    success: bool
    error_message: str = ""

    @classmethod
    def ok(cls) -> 'FileOperationResult':
        """Create a successful result."""
        return cls(success=True)

    @classmethod
    def error(cls, message: str) -> 'FileOperationResult':
        """Create an error result with message."""
        return cls(success=False, error_message=message)

