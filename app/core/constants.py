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

