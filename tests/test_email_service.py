"""
Tests for EmailService.

Tests file preparation and mailto opening functionality.
"""

import os
import tempfile
import unittest
from pathlib import Path

from app.services.email_service import EmailService


class TestEmailService(unittest.TestCase):
    """Test cases for EmailService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = EmailService()
        self.test_dir = tempfile.mkdtemp()
        self.test_file1 = os.path.join(self.test_dir, "test1.txt")
        self.test_file2 = os.path.join(self.test_dir, "test2.txt")
        
        # Create test files
        with open(self.test_file1, 'w') as f:
            f.write("Test content 1")
        with open(self.test_file2, 'w') as f:
            f.write("Test content 2")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_prepare_files_for_email_success(self):
        """Test successful file preparation."""
        file_paths = [self.test_file1, self.test_file2]
        temp_folder = self.service.prepare_files_for_email(file_paths)
        
        self.assertIsNotNone(temp_folder)
        self.assertTrue(os.path.exists(temp_folder))
        self.assertTrue(os.path.isdir(temp_folder))
        
        # Check files were copied
        copied_files = os.listdir(temp_folder)
        self.assertEqual(len(copied_files), 2)
        self.assertIn("test1.txt", copied_files)
        self.assertIn("test2.txt", copied_files)
    
    def test_prepare_files_for_email_empty_list(self):
        """Test preparation with empty file list."""
        temp_folder = self.service.prepare_files_for_email([])
        self.assertIsNone(temp_folder)
    
    def test_prepare_files_for_email_nonexistent_file(self):
        """Test preparation with non-existent file."""
        nonexistent = os.path.join(self.test_dir, "nonexistent.txt")
        temp_folder = self.service.prepare_files_for_email([nonexistent])
        self.assertIsNone(temp_folder)
    
    def test_create_email_session(self):
        """Test email session creation."""
        file_paths = [self.test_file1, self.test_file2]
        temp_folder = tempfile.mkdtemp()
        
        session = self.service.create_email_session(file_paths, temp_folder)
        
        self.assertIsNotNone(session)
        self.assertEqual(len(session.file_paths), 2)
        self.assertEqual(session.temp_folder_path, temp_folder)
        self.assertEqual(session.file_count, 2)
        
        # Clean up
        import shutil
        shutil.rmtree(temp_folder)
    
    def test_open_mailto(self):
        """Test mailto opening (non-blocking, just verify it doesn't crash)."""
        # This test just verifies the method doesn't crash
        # Actual mailto opening is tested manually
        result = self.service.open_mailto()
        # Should return True if successful, False if failed, but not crash
        self.assertIsInstance(result, bool)


if __name__ == '__main__':
    unittest.main()

