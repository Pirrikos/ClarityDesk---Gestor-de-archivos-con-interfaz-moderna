"""
Tests for EmailHistoryService.

Tests email history persistence and retrieval.
"""

import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from app.models.email_session import EmailSession
from app.services.email_history_service import EmailHistoryService


class TestEmailHistoryService(unittest.TestCase):
    """Test cases for EmailHistoryService."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Use temporary directory for test history
        self.test_dir = tempfile.mkdtemp()
        self.history_path = os.path.join(self.test_dir, "test_history.json")
        self.service = EmailHistoryService(history_path=self.history_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_add_session(self):
        """Test adding session to history."""
        session = EmailSession(
            timestamp=datetime.now(),
            file_paths=["/path/to/file1.txt", "/path/to/file2.txt"],
            temp_folder_path="/tmp/test123"
        )
        
        self.service.add_session(session)
        
        # Verify file was created
        self.assertTrue(os.path.exists(self.history_path))
        
        # Verify session was added
        sessions = self.service.get_recent_sessions(limit=10)
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0].file_count, 2)
    
    def test_get_recent_sessions(self):
        """Test retrieving recent sessions."""
        # Add multiple sessions
        for i in range(5):
            session = EmailSession(
                timestamp=datetime.now(),
                file_paths=[f"/path/to/file{i}.txt"],
                temp_folder_path=f"/tmp/test{i}"
            )
            self.service.add_session(session)
        
        # Get recent sessions
        sessions = self.service.get_recent_sessions(limit=3)
        self.assertEqual(len(sessions), 3)
        
        # Most recent should be first
        self.assertEqual(sessions[0].temp_folder_path, "/tmp/test4")
    
    def test_get_session_by_index(self):
        """Test retrieving session by index."""
        # Add sessions
        for i in range(3):
            session = EmailSession(
                timestamp=datetime.now(),
                file_paths=[f"/path/to/file{i}.txt"],
                temp_folder_path=f"/tmp/test{i}"
            )
            self.service.add_session(session)
        
        # Get by index
        session = self.service.get_session_by_index(0)
        self.assertIsNotNone(session)
        self.assertEqual(session.temp_folder_path, "/tmp/test2")  # Most recent
        
        session = self.service.get_session_by_index(2)
        self.assertIsNotNone(session)
        self.assertEqual(session.temp_folder_path, "/tmp/test0")  # Oldest
        
        # Invalid index
        session = self.service.get_session_by_index(10)
        self.assertIsNone(session)
    
    def test_persistence_across_instances(self):
        """Test that history persists across service instances."""
        session = EmailSession(
            timestamp=datetime.now(),
            file_paths=["/path/to/file1.txt"],
            temp_folder_path="/tmp/test123"
        )
        
        self.service.add_session(session)
        
        # Create new service instance with same path
        new_service = EmailHistoryService(history_path=self.history_path)
        sessions = new_service.get_recent_sessions(limit=10)
        
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0].temp_folder_path, "/tmp/test123")


if __name__ == '__main__':
    unittest.main()

