"""FolderTreeStyles - Skin oscuro tipo Raycast para FolderTreeSidebar."""

# Variables "CSS" simuladas en Python (Qt no soporta variables CSS nativas)
# Paleta oscura con bajo contraste, estilo Raycast
BG_GRADIENT_TOP = "#16181D"
BG_GRADIENT_BOTTOM = "#13161B"
SIDEBAR_TINT_TOP = "#1A1D22"
SIDEBAR_TINT_BOTTOM = "#171A1F"
TEXT_PRIMARY = "#E6E7EA"
TEXT_SECONDARY = "#B8BBC2"
HOVER_BG = "#1F2228"
SELECT_BG = "#22262C"
SELECT_LINE = "#3B82F6"  # Azul sobrio, poco saturado
SCROLL_HANDLE = "#2A2E35"
SCROLL_HANDLE_HOVER = "#343943"
FONT_FAMILY = '"Inter", "SF Pro Display", "Segoe UI", -apple-system, system-ui'
FONT_SIZE_BASE = "13px"
FONT_SIZE_L1 = "14px"          # Nivel 1 semibold
ICON_SIZE_PX = 16              # Iconos 16x16
ITEM_HEIGHT = 36               # Altura base de ítem
ITEM_V_SPACING = 12            # Espaciado vertical entre elementos
ITEM_H_PADDING = 16            # Padding horizontal

def get_base_stylesheet() -> str:
    """Estilo base del contenedor del sidebar (fondo con gradiente, sin líneas duras)."""
    return """
        QWidget#FolderTreeSidebar {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 """ + SIDEBAR_TINT_TOP + """, stop:1 """ + SIDEBAR_TINT_BOTTOM + """);
            border: none;
        }
        
        /* Botón superior (+) con tipografía y medidas pedidas */
        QPushButton#AddButton {
            background-color: transparent;
            border: none;
            font-size: """ + FONT_SIZE_BASE + """;
            font-weight: 600; /* semibold para principal */
            font-family: """ + FONT_FAMILY + """;
            color: """ + TEXT_PRIMARY + """;
            padding: 8px """ + str(ITEM_H_PADDING) + """px;
            text-align: left;
            border-radius: 6px;
            margin: 8px """ + str(ITEM_H_PADDING) + """px 4px """ + str(ITEM_H_PADDING) + """px;
            min-width: 50px;
        }
        
        QPushButton#AddButton:hover {
            background-color: """ + HOVER_BG + """;
        }
        
        QPushButton#AddButton:pressed {
            background-color: #262A31;
        }
    """

def get_tree_base_stylesheet() -> str:
    """Estilo base del QTreeView: tipografía, color, espaciado y estados (oscuro sobrio)."""
    return """
        QTreeView {
            background: transparent;
            color: """ + TEXT_PRIMARY + """;
            border: none;
            outline: none;
            font-size: """ + FONT_SIZE_BASE + """;
            font-family: """ + FONT_FAMILY + """;
            font-weight: 400;
            padding: 0px """ + str(max(0, ITEM_H_PADDING - 4)) + """px;
            padding-left: 16px; /* Espacio adicional para chevron de raíz */
            selection-background-color: rgba(0,0,0,0);
            selection-color: """ + TEXT_PRIMARY + """;
        }
        
        QTreeView::viewport {
            background: transparent;
        }
        
        QTreeView::item {
            height: """ + str(ITEM_HEIGHT) + """px;
            min-height: """ + str(ITEM_HEIGHT) + """px;
            padding: 8px """ + str(ITEM_H_PADDING) + """px;
            border-radius: 6px;
            margin: 6px """ + str(max(0, ITEM_H_PADDING - 8)) + """px; /* ~12px espaciamiento vertical total */
            border: none;
            background-color: transparent;
        }
        
        QTreeView::item:hover {
            background-color: transparent;
        }
        
        QTreeView::item:selected {
            background-color: transparent;
            color: """ + TEXT_PRIMARY + """;
            border: none;
        }
        
        QTreeView::item:selected:hover { background-color: transparent; }
        QTreeView::item:selected:active { background-color: transparent; }
        QTreeView::item:selected:!active { background-color: transparent; }
    """

def get_tree_branch_stylesheet() -> str:
    """Estilo para ramas: sin chevrons personalizados (minimalista)."""
    return """
        QTreeView::branch {
            background-color: transparent;
        }
        
        QTreeView::branch:has-siblings:!adjoins-item,
        QTreeView::branch:has-siblings:adjoins-item,
        QTreeView::branch:!has-children:!has-siblings:adjoins-item {
            border-image: none;
            background: transparent;
        }
        
        /* Chevron collapsed (▶) */
        QTreeView::branch:has-children:!has-siblings:closed,
        QTreeView::branch:closed:has-children:has-siblings {
            border-image: none;
            background: transparent;
            image: none;
            margin: 0px;
        }
        
        /* Chevron expanded (▼) */
        QTreeView::branch:open:has-children:!has-siblings,
        QTreeView::branch:open:has-children:has-siblings {
            border-image: none;
            background: transparent;
            image: none;
            margin: 0px;
        }
    """

def get_scrollbar_stylesheet() -> str:
    """Scrollbar delgado y discreto en oscuro."""
    return """
        QScrollBar:vertical {
            background: transparent;
            width: 8px;
            margin: 0px;
            border: none;
        }
        
        QScrollBar::handle:vertical {
            background: """ + SCROLL_HANDLE + """;
            border-radius: 4px;
            min-height: 30px;
        }
        
        QScrollBar::handle:vertical:hover {
            background: """ + SCROLL_HANDLE_HOVER + """;
        }
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
            border: none;
        }
        
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {
            background: transparent;
        }
    """

def get_button_stylesheet() -> str:
    """Estilos del botón (+) para aplicación directa (oscuro)."""
    return """
        QPushButton#AddButton {
            background-color: transparent;
            border: none;
            font-size: """ + FONT_SIZE_BASE + """;
            font-weight: 600;
            font-family: """ + FONT_FAMILY + """;
            color: """ + TEXT_PRIMARY + """;
            padding: 8px """ + str(ITEM_H_PADDING) + """px;
            text-align: left;
            border-radius: 6px;
            margin: 8px """ + str(ITEM_H_PADDING) + """px 4px """ + str(ITEM_H_PADDING) + """px;
        }
        
        QPushButton#AddButton:hover {
            background-color: """ + HOVER_BG + """;
        }
        
        QPushButton#AddButton:pressed {
            background-color: #262A31;
        }
    """

def get_menu_stylesheet() -> str:
    """Estilos del menú contextual (tres puntitos)."""
    return """
        QMenu {
            background: rgba(23, 26, 31, 240);
            border: 1px solid rgba(255, 255, 255, 25);
            border-radius: 10px;
            padding: 6px 8px;
            color: #E6E7EA;
        }
        QMenu::item {
            padding: 6px 12px;
            border-radius: 6px;
            background: transparent;
        }
        QMenu::item:selected {
            background: #1F2228;
        }
    """


def get_complete_stylesheet() -> str:
    """Construye el stylesheet completo (skin oscuro tipo Raycast)."""
    return (
        get_base_stylesheet() +
        get_tree_base_stylesheet() +
        get_tree_branch_stylesheet() +
        get_scrollbar_stylesheet()
    )
