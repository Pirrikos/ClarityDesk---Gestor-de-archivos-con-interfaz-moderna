from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
import sys
import os
from app.ui.widgets.folder_tree_sidebar import FolderTreeSidebar

def main():
    app = QApplication.instance() or QApplication(sys.argv)
    sidebar = FolderTreeSidebar()
    sidebar.show()
    QTest.qWaitForWindowExposed(sidebar)
    # Use existing real directories in repo
    base = os.path.normpath(os.path.join(os.getcwd(), "app"))
    candidates = [
        base,
        os.path.normpath(os.path.join(base, "ui")),
        os.path.normpath(os.path.join(base, "managers")),
        os.path.normpath(os.path.join(base, "services")),
        os.path.normpath(os.path.join(base, "ui", "widgets")),
        os.path.normpath(os.path.join(base, "ui", "windows")),
    ]
    for p in candidates:
        sidebar.add_focus_path(p)
    received = []
    sidebar.folder_selected.connect(lambda p: received.append(p))
    # Double click each candidate in order using the pending index logic
    for p in candidates:
        item = sidebar._path_to_item.get(p)
        if not item:
            print("RESULT: FAIL", "missing item for", p)
            sys.exit(1)
        idx = sidebar._model.indexFromItem(item)
        sidebar._pending_click_index = idx
        sidebar._click_expand_timer.start()
        sidebar._on_tree_double_clicked(idx)
        QTest.qWait(30)
    ok = received[:len(candidates)] == candidates
    print("RESULT:", "OK" if ok else "FAIL", received[:len(candidates)])
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
