"""
Version check module to verify code updates are included in PyInstaller build.
"""

# Incrementar este número con cada build para verificar que el ejecutable usa código nuevo
BUILD_VERSION = "2026-01-01-14:30"
BUILD_ID = 1001

def get_build_info() -> str:
    """Return build information string."""
    return f"Build {BUILD_ID} ({BUILD_VERSION})"
