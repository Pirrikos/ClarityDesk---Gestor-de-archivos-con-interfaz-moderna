"""
FileTileSetup - UI setup for FileTile.

Handles layout construction and widget initialization.
"""

import os
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QFont, QFontMetrics
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget
)

from app.ui.utils.font_manager import FontManager
from app.ui.widgets.file_tile_icon import add_icon_zone
from app.ui.widgets.file_tile_utils import format_filename, is_grid_view
from app.ui.widgets.state_badge_widget import StateBadgeWidget
from app.ui.widgets.text_elision import elide_middle_manual

if TYPE_CHECKING:
    from app.ui.widgets.file_tile import FileTile


def setup_ui(tile: 'FileTile') -> None:
    is_grid = is_grid_view(tile)
    tile_height = 98 if is_grid else 85
    tile.setFixedSize(70, tile_height)
    tile.setAutoFillBackground(False)
    tile.setStyleSheet("QWidget { background-color: transparent; }")
    setup_layout(tile)
    tile.setMouseTracking(True)
    tile.setAcceptDrops(os.path.isdir(tile._file_path))


def setup_layout(tile: 'FileTile') -> None:
    layout = QVBoxLayout(tile)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)
    
    container_widget = QWidget()
    container_widget.setFixedSize(70, 64)
    container_widget.setAutoFillBackground(False)
    container_widget.setStyleSheet("QWidget { background-color: transparent; }")
    container_layout = QVBoxLayout(container_widget)
    container_layout.setContentsMargins(7, 7, 7, 7)
    container_layout.setSpacing(0)
    tile._container_widget = container_widget
    add_icon_zone(tile, container_layout, tile._icon_service)
    layout.addWidget(container_widget, 0, Qt.AlignmentFlag.AlignHCenter)
    
    add_text_band(tile, layout)
    
    layout.setStretchFactor(container_widget, 0)


def add_text_band(tile: 'FileTile', layout: QVBoxLayout) -> None:
    is_grid = is_grid_view(tile)
    is_list_view = not is_grid and not tile._dock_style
    
    name_label = _create_and_configure_name_label(tile)
    
    if is_list_view:
        bottom_band = _create_bottom_band_with_badge(tile, name_label)
        layout.addWidget(bottom_band, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.setStretchFactor(bottom_band, 0)
    else:
        layout.addWidget(name_label, 0, Qt.AlignmentFlag.AlignCenter)


def _create_bottom_band_with_badge(tile: 'FileTile', name_label: QLabel) -> QWidget:
    bottom_band = QWidget()
    bottom_band.setFixedWidth(96)
    bottom_band.setFixedHeight(56)
    bottom_band.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    band_layout = QVBoxLayout(bottom_band)
    band_layout.setContentsMargins(0, 0, 0, 0)
    band_layout.setSpacing(4)
    
    band_layout.addWidget(name_label, 0, Qt.AlignmentFlag.AlignHCenter)
    _add_state_badge_to_band(tile, band_layout, bottom_band)
    
    return bottom_band


def _create_and_configure_name_label(tile: 'FileTile') -> QLabel:
    name_label = QLabel()
    name_label.setWordWrap(True)
    name_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
    
    is_grid = is_grid_view(tile)
    
    # Ancho con margen generoso para evitar cortes
    name_label.setFixedWidth(74)
    name_label.setMinimumWidth(74)
    
    if is_grid:
        # Permitir dos líneas: altura mínima para 1 línea, máxima para 2 líneas
        name_label.setMinimumHeight(22)
        name_label.setMaximumHeight(44)  # ~22px por línea (11px font + 1.2 line-height)
        name_label.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Preferred
        )
    else:
        name_label.setMinimumHeight(12)
        name_label.setMaximumHeight(15)
        name_label.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed
        )
    
    name_label.setScaledContents(False)
    name_label.setStyleSheet("""
        QLabel {
            font-family: 'Segoe UI', sans-serif;
            /* font-size: establecido explícitamente */
            font-weight: 600;
            color: #E8E8E8;
            background-color: transparent;
            padding: 0px;
            line-height: 1.3;
        }
    """)
    FontManager.safe_set_font(
        name_label,
        'Segoe UI',
        FontManager.SIZE_NORMAL,
        QFont.Weight.DemiBold
    )
    _add_dock_text_shadow(name_label)
    
    name_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
    name_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    
    display_name = format_filename(tile._file_path)
    metrics = QFontMetrics(name_label.font())
    
    # Para grid view: dividir manualmente el texto en dos líneas si es necesario
    # Esto evita problemas con wordWrap de Qt que puede cortar el primer carácter
    if is_grid:
        label_width = name_label.width() or name_label.fixedWidth() or 74
        max_width_per_line = label_width - 8  # Margen de seguridad generoso para evitar cortes
        text_width = metrics.horizontalAdvance(display_name)
        
        if text_width <= max_width_per_line:
            # Cabe en una línea, mostrar completo
            name_label.setWordWrap(False)
            name_label.setText(display_name)
        else:
            # No cabe en una línea, dividir manualmente en dos líneas
            name_label.setWordWrap(False)
            # Encontrar el mejor punto de división asegurando que ambas líneas quepan
            split_pos = _find_best_split_point(display_name, metrics, max_width_per_line)
            if split_pos > 0:
                line1 = display_name[:split_pos].strip()
                line2 = display_name[split_pos:].strip()
                
                # Verificar que ambas líneas quepan
                line1_width = metrics.horizontalAdvance(line1)
                line2_width = metrics.horizontalAdvance(line2)
                
                # Si alguna línea es demasiado larga, aplicar elision
                if line1_width > max_width_per_line:
                    line1 = elide_middle_manual(line1, metrics, max_width_per_line)
                if line2_width > max_width_per_line:
                    line2 = elide_middle_manual(line2, metrics, max_width_per_line)
                
                name_label.setText(f"{line1}\n{line2}")
            else:
                # No hay buen punto de división, usar elision en el medio
                elided_text = elide_middle_manual(display_name, metrics, max_width_per_line * 2)
                name_label.setText(elided_text)
    else:
        # Para otros modos: comportamiento original con elision simple
        label_width = name_label.width() or name_label.fixedWidth() or 70
        max_width = label_width - 2
        text_width = metrics.horizontalAdvance(display_name)
        
        if text_width <= max_width:
            name_label.setText(display_name)
        else:
            elided_text = elide_middle_manual(display_name, metrics, max_width)
            name_label.setText(elided_text)
    
    tile._name_label = name_label
    return name_label


def _find_best_split_point(text: str, metrics: QFontMetrics, max_width: int) -> int:
    """Encontrar el mejor punto para dividir el texto en dos líneas."""
    # Buscar espacios o guiones bajos como puntos de división
    split_chars = [' ', '_', '-']
    best_pos = -1
    best_pos_width = 0
    
    for i, char in enumerate(text):
        if char in split_chars:
            # Verificar si el texto hasta aquí cabe en una línea
            prefix = text[:i]
            prefix_width = metrics.horizontalAdvance(prefix)
            if prefix_width <= max_width and prefix_width > best_pos_width:
                best_pos = i
                best_pos_width = prefix_width
    
    # Si no encontramos un buen punto, buscar el punto medio aproximado
    if best_pos == -1:
        # Dividir aproximadamente por la mitad, pero buscar el espacio más cercano
        mid = len(text) // 2
        for i in range(mid, len(text)):
            if text[i] in split_chars:
                prefix = text[:i]
                if metrics.horizontalAdvance(prefix) <= max_width:
                    return i
        # Si no hay espacio, dividir por la mitad
        return mid
    
    return best_pos


def _add_dock_text_shadow(name_label: QLabel) -> None:
    text_shadow = QGraphicsDropShadowEffect(name_label)
    text_shadow.setBlurRadius(3)
    text_shadow.setXOffset(0)
    text_shadow.setYOffset(1)
    text_shadow.setColor(QColor(0, 0, 0, 180))
    name_label.setGraphicsEffect(text_shadow)


def _add_state_badge_to_band(tile: 'FileTile', band_layout: QVBoxLayout, band_widget: QWidget) -> None:
    tile._state_badge = StateBadgeWidget(band_widget)
    tile._state_badge.setFixedWidth(96)
    tile._state_badge.setFixedHeight(20)
    band_layout.addWidget(tile._state_badge, 0, Qt.AlignmentFlag.AlignHCenter)



