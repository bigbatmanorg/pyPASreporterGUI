"""PyInstaller runtime hook to fix importlib.metadata discovery in frozen apps.

This hook ensures that package metadata (dist-info directories) bundled by
PyInstaller can be discovered by importlib.metadata.entry_points().

Without this hook, SQLAlchemy dialect entry points (like duckdb_engine)
won't be discovered in frozen builds.
"""
import sys
import os


def _patch_metadata():
    """Patch importlib.metadata to find dist-info in sys._MEIPASS."""
    if not hasattr(sys, '_MEIPASS'):
        return

    meipass = sys._MEIPASS

    # Method 1: Add MEIPASS to sys.path immediately
    if meipass not in sys.path:
        sys.path.insert(0, meipass)

    # Method 2: Set PYTHONPATH to include MEIPASS for subprocess calls
    existing_path = os.environ.get('PYTHONPATH', '')
    if meipass not in existing_path:
        os.environ['PYTHONPATH'] = meipass + os.pathsep + existing_path if existing_path else meipass


# Run the patch immediately when this hook is loaded (before any other imports)
_patch_metadata()
