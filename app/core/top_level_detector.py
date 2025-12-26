"""
TopLevelDetector - Temporary detector for top-level windows during workspace switch.

Detects QEvent.Show on widgets that are windows (isWindow()==True or have window flags).
Logs widget class, objectName, and flags to identify flash sources.
"""

from PySide6.QtCore import QEvent, QObject, Qt
from app.core.logger import get_logger

logger = get_logger(__name__)


class TopLevelDetector(QObject):
    """Event filter to detect top-level window shows during workspace switch."""
    
    def __init__(self, parent=None):
        """Initialize detector."""
        super().__init__(parent)
        self._workspace_switch_active = False
    
    def set_workspace_switch_active(self, active: bool) -> None:
        """Enable/disable detection during workspace switch."""
        self._workspace_switch_active = active
    
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Filter events to detect top-level window shows."""
        if event.type() == QEvent.Type.Show and self._workspace_switch_active:
            # Check if widget is a window
            from PySide6.QtWidgets import QWidget
            if isinstance(obj, QWidget):
                is_window = obj.isWindow()
                flags = obj.windowFlags()
                has_window_flags = bool(
                    flags & Qt.WindowType.Window or
                    flags & Qt.WindowType.Dialog or
                    flags & Qt.WindowType.Tool or
                    flags & Qt.WindowType.Popup
                )
                
                if is_window or has_window_flags:
                    class_name = obj.__class__.__name__
                    object_name = obj.objectName() or "(sin nombre)"
                    parent_name = obj.parent().__class__.__name__ if obj.parent() else "None"
                    
                    logger.warning(
                        f"[TOP-LEVEL DETECTED] "
                        f"Clase: {class_name}, "
                        f"objectName: {object_name}, "
                        f"isWindow: {is_window}, "
                        f"flags: {flags}, "
                        f"parent: {parent_name}"
                    )
                    print(
                        f"\n[TOP-LEVEL DETECTED] "
                        f"Clase: {class_name}, "
                        f"objectName: {object_name}, "
                        f"isWindow: {is_window}, "
                        f"flags: {flags}, "
                        f"parent: {parent_name}\n"
                    )
        
        return super().eventFilter(obj, event)

