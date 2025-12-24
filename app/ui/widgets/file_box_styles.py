"""FileBoxStyles - Estilos CSS compartidos para FileBoxPanel y FileBoxHistoryPanel."""

from typing import Optional

from app.core.constants import (
    FILE_BOX_PANEL_BG,
    FILE_BOX_HEADER_BG,
    FILE_BOX_BORDER_LEFT,
    FILE_BOX_BORDER,
    FILE_BOX_LIST_BG,
    FILE_BOX_HOVER_BG,
    FILE_BOX_TEXT,
    FILE_BOX_BUTTON_TEXT,
    FILE_BOX_BUTTON_PRIMARY,
    FILE_BOX_BUTTON_PRIMARY_HOVER,
    FILE_BOX_BUTTON_PRIMARY_PRESSED,
)
from app.services.file_box_utils import FILE_BOX_SCROLLBAR_STYLES


def get_file_box_panel_stylesheet(object_name: str) -> str:
    """Retorna el stylesheet del panel principal."""
    return f"""
        QWidget#{object_name} {{
            background-color: {FILE_BOX_PANEL_BG};
            border-left: 2px solid {FILE_BOX_BORDER_LEFT};
            border-radius: 12px;
        }}
    """


def get_file_box_header_stylesheet(object_name: str) -> str:
    """Retorna el stylesheet del header."""
    return f"""
        QWidget#{object_name} {{
            background-color: {FILE_BOX_HEADER_BG};
            border-bottom: 1px solid {FILE_BOX_BORDER};
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
        }}
    """


def get_file_box_body_stylesheet(object_name: str) -> str:
    """Retorna el stylesheet del cuerpo."""
    return f"""
        QWidget#{object_name} {{
            background-color: {FILE_BOX_PANEL_BG};
            border-bottom-left-radius: 12px;
            border-bottom-right-radius: 12px;
        }}
    """


def get_file_box_list_stylesheet(min_height: Optional[int] = None) -> str:
    """Retorna el stylesheet de las listas."""
    min_height_css = f"\n                min-height: {min_height}px;" if min_height else ""
    return f"""
        QListWidget {{{min_height_css}
            border: 1px solid {FILE_BOX_BORDER};
            border-radius: 8px;
            padding: 4px;
            background-color: {FILE_BOX_LIST_BG};
            color: {FILE_BOX_TEXT};
        }}
        QListWidget::item {{
            padding: 6px 8px;
            border: none;
            color: {FILE_BOX_TEXT};
            height: 32px;
        }}
        QListWidget::item::icon {{
            padding-right: 8px;
        }}
        QListWidget::item:hover {{
            background-color: {FILE_BOX_HOVER_BG};
        }}
        {FILE_BOX_SCROLLBAR_STYLES}
    """


def get_file_box_button_stylesheet(font_size: int = 18) -> str:
    """Retorna el stylesheet de los botones de header."""
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {FILE_BOX_BUTTON_TEXT};
            border: none;
            border-radius: 4px;
            font-size: {font_size}px;
            font-weight: 300;
            padding: 0px;
        }}
        QPushButton:hover {{
            background-color: {FILE_BOX_HOVER_BG};
            color: {FILE_BOX_TEXT};
        }}
        QPushButton:pressed {{
            background-color: {FILE_BOX_BORDER};
        }}
    """


def get_file_box_close_button_stylesheet() -> str:
    """Retorna el stylesheet del botón cerrar."""
    return get_file_box_button_stylesheet(font_size=20)


def get_file_box_label_stylesheet() -> str:
    """Retorna el stylesheet de las etiquetas."""
    return f"font-weight: 600; font-size: 14px; color: {FILE_BOX_TEXT};"


def get_file_box_primary_button_stylesheet() -> str:
    """Retorna el stylesheet del botón primario 'Abrir carpeta'."""
    return f"""
        QPushButton {{
            background-color: {FILE_BOX_BUTTON_PRIMARY};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {FILE_BOX_BUTTON_PRIMARY_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {FILE_BOX_BUTTON_PRIMARY_PRESSED};
        }}
    """

