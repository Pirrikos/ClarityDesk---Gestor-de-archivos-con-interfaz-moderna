"""
Application-wide constants.

Centralizes magic numbers and configuration values for better maintainability.
"""

# Timer intervals (milliseconds)
SELECTION_UPDATE_INTERVAL_MS = 200
DOUBLE_CLICK_THRESHOLD_MS = 350
SELECTION_RESTORE_DELAY_MS = 50
WORKER_TIMEOUT_MS = 1000

# Debounce delays (milliseconds)
FILE_SYSTEM_DEBOUNCE_MS = 500

# UI dimensions (pixels)
SIDEBAR_MAX_WIDTH = 400
FILE_VIEW_LEFT_MARGIN = 8
RESIZE_EDGE_DETECTION_MARGIN = 8

# Workspace selector dimensions
WORKSPACE_HEADER_HEIGHT = 52
WORKSPACE_BUTTON_HEIGHT = 28

# Rounded background styling (Finder-like)
ROUNDED_BG_TOP_OFFSET = 8
ROUNDED_BG_RADIUS = 12

# UI colors
CENTRAL_AREA_BG = "#202326"
SIDEBAR_BG = "#1A1D22"
SEPARATOR_LINE_COLOR = "rgba(255, 255, 255, 0.15)"

# Header and menu colors
APP_HEADER_BG = "#1A1D22"
APP_HEADER_BORDER = "#2A2E36"
MENU_BG = "#1A1D22"
MENU_BORDER = "#2A2E36"
MENU_HOVER_BG = "#20242A"
MENU_ACCENT = "#3D7BFF"
MENU_ACCENT_BORDER = "#2F61CC"

# Menu colors (additional variants)
MENU_BG_ALPHA = "rgba(26, 29, 34, 0.95)"
MENU_BORDER_LIGHT = "rgba(255, 255, 255, 0.1)"
MENU_TEXT = "rgba(255, 255, 255, 0.92)"
MENU_TEXT_HOVER = "rgba(255, 255, 255, 0.98)"
MENU_ITEM_TEXT = "rgba(255, 255, 255, 0.8)"
MENU_ITEM_TEXT_HOVER = "rgba(255, 255, 255, 0.95)"
MENU_ITEM_HOVER_BG = "rgba(255, 255, 255, 0.1)"

# Button colors
BUTTON_BG_DARK = "#20242A"
BUTTON_BORDER_DARK = "#343A44"
BUTTON_BG_DARK_HOVER = "#252A31"
BUTTON_BORDER_DARK_HOVER = "#3A404B"

# Button colors (light theme variants)
BUTTON_BG_LIGHT = "rgba(255, 255, 255, 0.12)"
BUTTON_BORDER_LIGHT = "rgba(255, 255, 255, 0.16)"
BUTTON_TEXT_LIGHT = "rgba(255, 255, 255, 0.8)"
BUTTON_BG_LIGHT_HOVER = "rgba(255, 255, 255, 0.16)"
BUTTON_BORDER_LIGHT_HOVER = "rgba(255, 255, 255, 0.22)"
BUTTON_BG_LIGHT_PRESSED = "rgba(255, 255, 255, 0.20)"

# Header button colors
BUTTON_BG_HEADER = "rgba(255, 255, 255, 0.03)"
BUTTON_BORDER_HEADER = "rgba(255, 255, 255, 0.08)"
BUTTON_TEXT_HEADER = "rgba(255, 255, 255, 0.7)"
BUTTON_BG_HEADER_HOVER = "rgba(255, 255, 255, 0.08)"
BUTTON_BORDER_HEADER_HOVER = "rgba(255, 255, 255, 0.15)"
BUTTON_TEXT_HEADER_HOVER = "rgba(255, 255, 255, 0.9)"
BUTTON_BG_HEADER_PRESSED = "rgba(255, 255, 255, 0.12)"
BUTTON_TEXT_HEADER_DISABLED = "rgba(255, 255, 255, 0.35)"

# Text colors
TEXT_SUBFOLDER = "#B0B5BA"
CHEVRON_COLOR = "#9CA3AF"
TEXT_LIST = "#E8E8E8"  # Color del texto en lista

# List view colors
CHECKBOX_BORDER = "rgba(255, 255, 255, 0.3)"
CHECKBOX_BORDER_HOVER = "#80C5FF"
CHECKBOX_BG_CHECKED = "#80C5FF"
CHECKBOX_BG_CHECKED_HOVER = "#66B3FF"

# Header colors (list view)
HEADER_BG = "#1A1D22"  # Gris más oscuro que CENTRAL_AREA_BG (#202326)
HEADER_TEXT_COLOR = "rgba(255, 255, 255, 0.45)"
HEADER_BORDER_RIGHT = "rgba(255, 255, 255, 0.05)"
HEADER_BORDER_BOTTOM = "rgba(255, 255, 255, 0.08)"
HEADER_TEXT_HOVER = "rgba(255, 255, 255, 0.6)"
HEADER_BORDER_CORNER = "rgba(255, 255, 255, 0.1)"

# Scrollbar colors
SCROLLBAR_HANDLE_BG = "rgba(255, 255, 255, 0.12)"
SCROLLBAR_HANDLE_HOVER = "rgba(255, 255, 255, 0.22)"
SCROLLBAR_HANDLE_PRESSED = "rgba(255, 255, 255, 0.30)"

# Icon service limits
MAX_CONCURRENT_ICON_WORKERS = 4
MAX_ICON_CACHE_SIZE_MB = 500

# UI feedback delays (milliseconds)
CURSOR_BUSY_TIMEOUT_MS = 180
ANIMATION_DURATION_MS = 220
ANIMATION_CLEANUP_DELAY_MS = 250
UPDATE_DELAY_MS = 300

# Progress thresholds
PROGRESS_DIALOG_THRESHOLD = 5  # Show progress for >N files

# Layout debugging mode
# Cambiar a True para activar bordes de depuración del layout
# 
# Cuando está activo, muestra bordes de colores alrededor de todos los componentes:
# - Rojo: Ventana principal
# - Azul: Central widget (RaycastPanel)
# - Verde: WindowHeader (barra superior con botones)
# - Amarillo: AppHeader (barra de aplicación)
# - Magenta: QSplitter (contenedor principal)
# - Cyan: WorkspaceSelector (selector izquierdo)
# - Naranja: FolderTreeSidebar (sidebar navegación)
# - Rosa: FileViewContainer (contenido principal)
# - Blanco: SizeGripContainer (zona inferior)
#
# Útil para detectar solapamientos, desbordes y errores de jerarquía de layout.
# No modifica tamaños, posiciones ni comportamiento de los widgets.
DEBUG_LAYOUT = False

