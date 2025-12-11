"""Tests for FilesController."""

from app.controllers.files_controller import FilesController


class StubRenameService:
    """Stub for RenameService."""
    
    def __init__(self):
        self._apply_rename_called = False
        self._apply_rename_paths = None
        self._apply_rename_names = None
        self._should_raise = False
    
    def apply_rename(self, paths: list[str], names: list[str], watcher=None) -> None:
        """Track apply_rename calls."""
        self._apply_rename_called = True
        self._apply_rename_paths = paths
        self._apply_rename_names = names
        if self._should_raise:
            raise RuntimeError("Test error")


class StubDeleteService:
    """Stub for delete_file function."""
    _called_paths = []
    _called_with_trash = False
    
    @classmethod
    def reset(cls):
        """Reset call tracking."""
        cls._called_paths = []
        cls._called_with_trash = False
    
    @classmethod
    def delete_file(cls, path: str, watcher=None, is_trash_focus: bool = False):
        """Track delete calls."""
        cls._called_paths.append(path)
        cls._called_with_trash = is_trash_focus
        return type('Result', (), {'success': True})()


class StubMoveService:
    """Stub for move_file function."""
    _called_paths = []
    _called_targets = []
    
    @classmethod
    def reset(cls):
        """Reset call tracking."""
        cls._called_paths = []
        cls._called_targets = []
    
    @classmethod
    def move_file(cls, source: str, destination_folder: str, watcher=None):
        """Track move calls."""
        cls._called_paths.append(source)
        cls._called_targets.append(destination_folder)
        return type('Result', (), {'success': True})()


def test_delete_files_calls_service(monkeypatch):
    """Test that delete_files() calls delete service."""
    StubDeleteService.reset()
    
    def mock_delete_file(path, watcher=None, is_trash_focus=False):
        return StubDeleteService.delete_file(path, watcher, is_trash_focus)
    
    import app.controllers.files_controller as fc_module
    monkeypatch.setattr(fc_module, 'delete_file', mock_delete_file)
    
    rename_service = StubRenameService()
    controller = FilesController(rename_service)
    
    paths = ["/file1.txt", "/file2.txt"]
    controller.delete_files(paths)
    
    assert len(StubDeleteService._called_paths) == 2
    assert "/file1.txt" in StubDeleteService._called_paths
    assert "/file2.txt" in StubDeleteService._called_paths


def test_delete_files_with_trash_focus(monkeypatch):
    """Test that delete_files() passes is_trash_focus flag."""
    StubDeleteService.reset()
    
    def mock_delete_file(path, watcher=None, is_trash_focus=False):
        return StubDeleteService.delete_file(path, watcher, is_trash_focus)
    
    import app.controllers.files_controller as fc_module
    monkeypatch.setattr(fc_module, 'delete_file', mock_delete_file)
    
    rename_service = StubRenameService()
    controller = FilesController(rename_service)
    
    controller.delete_files(["/file.txt"], is_trash_focus=True)
    
    assert StubDeleteService._called_with_trash is True


def test_rename_batch_executes_without_exception():
    """Test that rename_batch() executes without exception."""
    rename_service = StubRenameService()
    controller = FilesController(rename_service)
    
    paths = ["/file1.txt", "/file2.txt"]
    names = ["new1.txt", "new2.txt"]
    
    result = controller.rename_batch(paths, names)
    
    assert result is True
    assert rename_service._apply_rename_called is True
    assert rename_service._apply_rename_paths == paths
    assert rename_service._apply_rename_names == names


def test_rename_batch_handles_exception():
    """Test that rename_batch() handles exceptions."""
    rename_service = StubRenameService()
    rename_service._should_raise = True
    controller = FilesController(rename_service)
    
    result = controller.rename_batch(["/file.txt"], ["new.txt"])
    
    assert result is False


def test_move_files_executes_movements(monkeypatch):
    """Test that move_files() executes movements."""
    StubMoveService.reset()
    
    def mock_move_file(source, destination_folder, watcher=None):
        return StubMoveService.move_file(source, destination_folder, watcher)
    
    import app.controllers.files_controller as fc_module
    monkeypatch.setattr(fc_module, 'move_file', mock_move_file)
    
    rename_service = StubRenameService()
    controller = FilesController(rename_service)
    
    paths = ["/file1.txt", "/file2.txt"]
    target = "/target/folder"
    
    controller.move_files(paths, target)
    
    assert len(StubMoveService._called_paths) == 2
    assert "/file1.txt" in StubMoveService._called_paths
    assert "/file2.txt" in StubMoveService._called_paths
    assert all(t == target for t in StubMoveService._called_targets)

