from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
import sys
import os
from app.ui.widgets.folder_tree_sidebar import FolderTreeSidebar

def main():
    app = QApplication.instance() or QApplication(sys.argv)
    sidebar = FolderTreeSidebar()
    sidebar.show()
    QTest.qWaitForWindowExposed(sidebar)
    root_path = os.path.normpath(os.path.join(os.getcwd(), "app"))
    child_path = os.path.normpath(os.path.join(os.getcwd(), "app", "ui"))
    sidebar.add_focus_path(root_path)
    sidebar.add_focus_path(child_path)
    received = []
    sidebar.folder_selected.connect(lambda p: received.append(p))
    view = sidebar._tree_view
    idx_root = sidebar._model.indexFromItem(sidebar._path_to_item[root_path])
    idx_child = sidebar._model.indexFromItem(sidebar._path_to_item[child_path])
    def dbl(index):
        sidebar._pending_click_index = index
        sidebar._click_expand_timer.start()
        sidebar._on_tree_double_clicked(index)
        QTest.qWait(50)
    dbl(idx_root)
    dbl(idx_child)
    dbl(idx_root)
    dbl(idx_child)
    dbl(idx_root)
    expected = [root_path, child_path, root_path, child_path, root_path]
    ok = received[:5] == expected
    print("RESULT:", "OK" if ok else "FAIL", received[:5])
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
