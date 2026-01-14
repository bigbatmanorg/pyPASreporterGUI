"""Unit tests for pyPASreporterGUI CLI."""
from __future__ import annotations

import os
from pathlib import Path

import pytest


class TestCLI:
    """Tests for the CLI module."""

    def test_import(self):
        """Test that CLI module can be imported."""
        from pypasreportergui import cli
        assert hasattr(cli, "app")

    def test_version(self):
        """Test that version is defined."""
        from pypasreportergui import __version__
        assert __version__
        assert isinstance(__version__, str)

    def test_app_name(self):
        """Test that app name is defined."""
        from pypasreportergui import __app_name__
        assert __app_name__ == "pyPASreporterGUI"


class TestRuntime:
    """Tests for the runtime module."""

    def test_import(self):
        """Test that runtime module can be imported."""
        from pypasreportergui import runtime
        assert hasattr(runtime, "get_superset_home")
        assert hasattr(runtime, "generate_config")

    def test_get_superset_home_default(self, monkeypatch):
        """Test default home directory."""
        from pypasreportergui.runtime import get_superset_home
        
        # Clear environment variable if set
        monkeypatch.delenv("PYPASREPORTERGUI_HOME", raising=False)
        home = get_superset_home()
        assert home == Path.home() / ".pypasreportergui"

    def test_get_superset_home_env(self, tmp_path, monkeypatch):
        """Test home directory from environment variable."""
        from pypasreportergui.runtime import get_superset_home
        
        custom_home = str(tmp_path / "custom_home")
        monkeypatch.setenv("PYPASREPORTERGUI_HOME", custom_home)
        home = get_superset_home()
        assert home == Path(custom_home)

    def test_ensure_home_dir(self, tmp_path, monkeypatch):
        """Test that home directory is created."""
        from pypasreportergui.runtime import ensure_home_dir
        
        custom_home = str(tmp_path / "new_home")
        monkeypatch.setenv("PYPASREPORTERGUI_HOME", custom_home)
        home = ensure_home_dir()
        assert home.exists()
        assert home.is_dir()

    def test_generate_secret_key(self):
        """Test secret key generation."""
        from pypasreportergui.runtime import generate_secret_key
        
        key1 = generate_secret_key()
        key2 = generate_secret_key()
        
        assert key1 != key2
        assert len(key1) == 64  # 32 bytes hex = 64 chars

    def test_generate_config(self, tmp_path):
        """Test config file generation."""
        from pypasreportergui.runtime import generate_config
        
        config_path = generate_config(tmp_path)
        
        assert config_path.exists()
        assert config_path.name == "superset_config.py"
        
        content = config_path.read_text()
        assert "pyPASreporterGUI" in content
        assert "SECRET_KEY" in content
        assert "SQLALCHEMY_DATABASE_URI" in content

    def test_config_not_regenerated(self, tmp_path):
        """Test that config is not regenerated if it exists."""
        from pypasreportergui.runtime import generate_config
        
        # Create initial config
        config_path = generate_config(tmp_path)
        content1 = config_path.read_text()
        
        # Try to generate again (should not change)
        config_path2 = generate_config(tmp_path)
        content2 = config_path2.read_text()
        
        assert content1 == content2

    def test_config_force_regenerate(self, tmp_path):
        """Test force regeneration of config."""
        from pypasreportergui.runtime import generate_config
        
        # Create initial config
        config_path = generate_config(tmp_path)
        
        # Modify it
        config_path.write_text("# modified")
        
        # Force regenerate
        config_path2 = generate_config(tmp_path, force=True)
        content = config_path2.read_text()
        
        assert "pyPASreporterGUI" in content


class TestBranding:
    """Tests for the branding module."""

    def test_import(self):
        """Test that branding module can be imported."""
        from pypasreportergui.branding import branding_bp
        assert branding_bp is not None

    def test_blueprint_name(self):
        """Test blueprint configuration."""
        from pypasreportergui.branding.blueprint import branding_bp
        assert branding_bp.name == "pypasreportergui_branding"

    def test_static_dir_exists(self):
        """Test that static directory exists."""
        from pypasreportergui.branding.blueprint import STATIC_DIR
        assert STATIC_DIR.exists()
        assert STATIC_DIR.is_dir()

    def test_branding_assets_exist(self):
        """Test that branding assets exist."""
        from pypasreportergui.branding.blueprint import STATIC_DIR
        
        logo = STATIC_DIR / "logo-horiz.png"
        favicon = STATIC_DIR / "favicon.png"
        
        assert logo.exists(), f"Logo not found at {logo}"
        assert favicon.exists(), f"Favicon not found at {favicon}"


class TestDuckDB:
    """Tests for DuckDB integration."""

    def test_duckdb_import(self):
        """Test that DuckDB can be imported."""
        import duckdb
        assert duckdb.__version__

    def test_duckdb_engine_import(self):
        """Test that duckdb-engine can be imported."""
        import duckdb_engine
        assert duckdb_engine

    def test_duckdb_sqlalchemy(self):
        """Test DuckDB with SQLAlchemy."""
        from sqlalchemy import create_engine, text
        
        engine = create_engine("duckdb:///:memory:")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 42 as answer"))
            row = result.fetchone()
            assert row[0] == 42

    def test_duckdb_file(self, tmp_path):
        """Test DuckDB with file database."""
        from sqlalchemy import create_engine, text
        
        db_path = tmp_path / "test.duckdb"
        engine = create_engine(f"duckdb:///{db_path}")
        
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE test (id INTEGER, name VARCHAR)"))
            conn.execute(text("INSERT INTO test VALUES (1, 'hello')"))
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM test"))
            rows = result.fetchall()
            assert len(rows) == 1
            assert rows[0][1] == "hello"
        
        assert db_path.exists()
