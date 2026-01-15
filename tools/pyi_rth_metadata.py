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

    # Add MEIPASS to the metadata search path
    meipass = sys._MEIPASS

    try:
        # Python 3.9+ has importlib.metadata built-in
        import importlib.metadata as metadata

        # Get the original distributions function
        original_distributions = metadata.distributions

        def patched_distributions(**kwargs):
            """Patched distributions() that includes MEIPASS in search path."""
            # Add MEIPASS to path if not already there
            if meipass not in sys.path:
                sys.path.insert(0, meipass)
            return original_distributions(**kwargs)

        metadata.distributions = patched_distributions

    except ImportError:
        pass


# Run the patch immediately when this hook is loaded
_patch_metadata()
