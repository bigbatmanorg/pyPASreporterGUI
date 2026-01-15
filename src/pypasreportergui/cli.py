#!/usr/bin/env python3
"""pyPASreporterGUI CLI - Main entry point for the application.

This CLI provides commands to run, initialize, and manage the pyPASreporterGUI application.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from pypasreportergui import __app_name__, __version__
from pypasreportergui.runtime import (
    create_admin_user,
    ensure_home_dir,
    generate_config,
    get_superset_home,
    init_database,
    run_superset_server,
    is_frozen,
    get_frozen_base_path,
    get_superset_dir,
)

app = typer.Typer(
    name="pypasreportergui",
    help="pyPASreporterGUI - A branded Superset-based data analytics GUI",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold]{__app_name__}[/bold] version [green]{__version__}[/green]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """pyPASreporterGUI - A branded Superset-based data analytics GUI with DuckDB support."""
    pass


@app.command()
def run(
    port: int = typer.Option(8088, "--port", "-p", help="Port to run the server on"),
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload for development"),
    no_init: bool = typer.Option(False, "--no-init", help="Skip database initialization"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug mode"),
) -> None:
    """Start the pyPASreporterGUI server.

    This command initializes the database (if needed) and starts the Superset server
    with pyPASreporterGUI branding and configuration.
    """
    console.print(f"[bold blue]Starting {__app_name__}...[/bold blue]")

    home_dir = ensure_home_dir()
    config_path = generate_config(home_dir)

    os.environ["SUPERSET_CONFIG_PATH"] = str(config_path)
    os.environ["SUPERSET_HOME"] = str(home_dir)

    if debug:
        os.environ["FLASK_ENV"] = "development"
        os.environ["FLASK_DEBUG"] = "1"

    if not no_init:
        console.print("[dim]Initializing database...[/dim]")
        init_database()
        create_admin_user()

    console.print(f"[green]✓[/green] Server starting at [link]http://{host}:{port}[/link]")
    console.print(f"[dim]Config: {config_path}[/dim]")
    console.print(f"[dim]Home: {home_dir}[/dim]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")

    run_superset_server(host=host, port=port, reload=reload, debug=debug)


@app.command()
def init(
    admin_username: str = typer.Option("admin", "--admin-username", help="Admin username"),
    admin_password: str = typer.Option("admin", "--admin-password", help="Admin password"),
    admin_email: str = typer.Option("admin@pypasreportergui.local", "--admin-email", help="Admin email"),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-initialization"),
) -> None:
    """Initialize the database and create admin user.

    This command runs database migrations and creates an admin user without
    starting the server.
    """
    console.print(f"[bold blue]Initializing {__app_name__}...[/bold blue]")

    home_dir = ensure_home_dir()
    config_path = generate_config(home_dir, force=force)

    os.environ["SUPERSET_CONFIG_PATH"] = str(config_path)
    os.environ["SUPERSET_HOME"] = str(home_dir)

    console.print("[dim]Running database migrations...[/dim]")
    init_database()

    console.print(f"[dim]Creating admin user: {admin_username}[/dim]")
    create_admin_user(
        username=admin_username,
        password=admin_password,
        email=admin_email,
    )

    console.print(f"[green]✓[/green] {__app_name__} initialized successfully!")
    console.print(f"[dim]Config: {config_path}[/dim]")
    console.print(f"[dim]Database: {home_dir / 'superset.db'}[/dim]")


@app.command()
def doctor() -> None:
    """Print version info, paths, and run sanity checks.

    This command helps diagnose installation issues by printing all relevant
    configuration and checking that dependencies are available.
    """
    console.print(f"[bold blue]{__app_name__} Doctor[/bold blue]\n")

    # Frozen mode detection
    frozen = is_frozen()
    console.print(f"[bold]Execution Mode:[/bold] {'[cyan]Frozen (PyInstaller)[/cyan]' if frozen else '[dim]Normal Python[/dim]'}")
    console.print(f"[bold]sys.executable:[/bold] {sys.executable}")
    if frozen:
        console.print(f"[bold]sys._MEIPASS:[/bold] {get_frozen_base_path()}")
    console.print()

    # Environment info
    env_table = Table(title="Environment")
    env_table.add_column("Variable", style="cyan")
    env_table.add_column("Value", style="yellow")
    env_table.add_row("HOME", os.environ.get("HOME", "[not set]"))
    env_table.add_row("PATH (first 80 chars)", os.environ.get("PATH", "")[:80] + "...")
    console.print(env_table)
    console.print()

    # Version info
    table = Table(title="Version Information")
    table.add_column("Component", style="cyan")
    table.add_column("Version", style="green")

    table.add_row(__app_name__, __version__)

    try:
        import superset

        table.add_row("Apache Superset", getattr(superset, "__version__", "unknown"))
    except ImportError:
        table.add_row("Apache Superset", "[red]NOT INSTALLED[/red]")

    try:
        import duckdb

        table.add_row("DuckDB", duckdb.__version__)
    except ImportError:
        table.add_row("DuckDB", "[red]NOT INSTALLED[/red]")

    try:
        import flask

        table.add_row("Flask", flask.__version__)
    except ImportError:
        table.add_row("Flask", "[red]NOT INSTALLED[/red]")

    table.add_row("Python", sys.version.split()[0])

    console.print(table)
    console.print()

    # Path info
    path_table = Table(title="Paths")
    path_table.add_column("Path", style="cyan")
    path_table.add_column("Location", style="yellow")
    path_table.add_column("Status", style="green")

    home_dir = get_superset_home()
    config_path = home_dir / "superset_config.py"
    db_path = home_dir / "superset.db"

    path_table.add_row(
        "PYPASREPORTERGUI_HOME",
        str(home_dir),
        "[green]✓ exists[/green]" if home_dir.exists() else "[yellow]○ will be created[/yellow]",
    )
    path_table.add_row(
        "Config file",
        str(config_path),
        "[green]✓ exists[/green]" if config_path.exists() else "[yellow]○ will be generated[/yellow]",
    )
    path_table.add_row(
        "SQLite database",
        str(db_path),
        "[green]✓ exists[/green]" if db_path.exists() else "[yellow]○ will be created[/yellow]",
    )

    console.print(path_table)
    console.print()

    # Bundled assets check (critical for frozen apps)
    all_ok = True
    if frozen:
        console.print("[bold]Bundled Assets (Frozen Mode):[/bold]")
        superset_dir = get_superset_dir()
        
        required_dirs = [
            ("migrations", superset_dir / "migrations"),
            ("migrations/versions", superset_dir / "migrations" / "versions"),
            ("templates", superset_dir / "templates"),
            ("static/assets", superset_dir / "static" / "assets"),
        ]
        
        for name, path in required_dirs:
            if path.exists():
                if path.is_dir():
                    count = len(list(path.iterdir()))
                    console.print(f"[green]✓[/green] {name}: {path} ({count} items)")
                else:
                    console.print(f"[green]✓[/green] {name}: {path}")
            else:
                console.print(f"[red]✗[/red] {name}: {path} [red]MISSING[/red]")
                all_ok = False
        console.print()

    # Sanity checks
    console.print("[bold]Sanity Checks:[/bold]")

    # Check Superset
    try:
        from superset.app import create_app

        console.print("[green]✓[/green] Superset app factory available")
    except ImportError as e:
        console.print(f"[red]✗[/red] Superset import failed: {e}")
        all_ok = False

    # Check DuckDB engine
    try:
        from sqlalchemy import create_engine

        engine = create_engine("duckdb:///:memory:")
        with engine.connect() as conn:
            result = conn.execute("SELECT 42 as answer")
            row = result.fetchone()
            if row and row[0] == 42:
                console.print("[green]✓[/green] DuckDB engine working")
            else:
                console.print("[red]✗[/red] DuckDB engine returned unexpected result")
                all_ok = False
    except Exception as e:
        console.print(f"[red]✗[/red] DuckDB engine test failed: {e}")
        all_ok = False

    # Check SQLAlchemy dialect entry points
    try:
        from importlib.metadata import entry_points
        eps = entry_points(group='sqlalchemy.dialects')
        duckdb_eps = [ep.name for ep in eps if 'duck' in ep.name.lower()]
        if duckdb_eps:
            console.print(f"[green]✓[/green] DuckDB SQLAlchemy dialect registered: {duckdb_eps}")
        else:
            console.print(f"[yellow]![/yellow] DuckDB dialect not in entry_points (found: {[ep.name for ep in list(eps)[:5]]}...)")
            all_ok = False
    except Exception as e:
        console.print(f"[yellow]![/yellow] Could not check entry_points: {e}")
        all_ok = False

    # Check branding module
    try:
        from pypasreportergui.branding.blueprint import branding_bp

        console.print("[green]✓[/green] Branding blueprint available")
    except ImportError as e:
        console.print(f"[red]✗[/red] Branding blueprint import failed: {e}")
        all_ok = False

    console.print()
    if all_ok:
        console.print(f"[bold green]All checks passed! {__app_name__} is ready to use.[/bold green]")
    else:
        console.print(f"[bold red]Some checks failed. See above for details.[/bold red]")
        raise typer.Exit(1)


@app.command("add-duckdb")
def add_duckdb(
    path: Path = typer.Option(..., "--path", "-p", help="Path to DuckDB file"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Database display name"),
    read_only: bool = typer.Option(False, "--read-only", "-r", help="Open in read-only mode"),
) -> None:
    """Register a DuckDB database connection.

    This command adds a DuckDB file as a database connection in pyPASreporterGUI.
    You can then use it to explore data and create visualizations.
    """
    path = path.resolve()

    if not path.exists():
        console.print(f"[yellow]Warning:[/yellow] File does not exist: {path}")
        console.print("[dim]It will be created when DuckDB first writes to it.[/dim]")

    db_name = name or path.stem

    # Build SQLAlchemy URI
    if read_only:
        uri = f"duckdb:///{path}?read_only=true"
    else:
        uri = f"duckdb:///{path}"

    console.print(f"[bold blue]DuckDB Connection Details[/bold blue]")
    console.print()
    console.print(f"[cyan]Name:[/cyan] {db_name}")
    console.print(f"[cyan]Path:[/cyan] {path}")
    console.print(f"[cyan]SQLAlchemy URI:[/cyan]")
    console.print(f"  [green]{uri}[/green]")
    console.print()
    console.print("[bold]To add this database in pyPASreporterGUI:[/bold]")
    console.print("1. Go to [bold]Data → Databases → + Database[/bold]")
    console.print("2. Click [bold]'SUPPORTED DATABASES'[/bold] dropdown")
    console.print("3. Select [bold]'Other'[/bold]")
    console.print("4. Enter the [bold]Display Name[/bold] and paste the [bold]SQLAlchemy URI[/bold] above")
    console.print("5. Click [bold]'Test Connection'[/bold] then [bold]'Connect'[/bold]")
    console.print()

    # Try to add programmatically if Superset is available and initialized
    home_dir = get_superset_home()
    config_path = home_dir / "superset_config.py"

    if config_path.exists():
        console.print("[dim]Attempting to register database programmatically...[/dim]")
        try:
            os.environ["SUPERSET_CONFIG_PATH"] = str(config_path)
            os.environ["SUPERSET_HOME"] = str(home_dir)

            from superset import db
            from superset.app import create_app
            from superset.models.core import Database

            app = create_app()
            with app.app_context():
                existing = db.session.query(Database).filter_by(database_name=db_name).first()
                if existing:
                    console.print(f"[yellow]Database '{db_name}' already exists.[/yellow]")
                else:
                    database = Database(
                        database_name=db_name,
                        sqlalchemy_uri=uri,
                        expose_in_sqllab=True,
                        allow_run_async=False,
                        allow_ctas=True,
                        allow_cvas=True,
                        allow_dml=True,
                    )
                    db.session.add(database)
                    db.session.commit()
                    console.print(f"[green]✓[/green] Database '{db_name}' added successfully!")
        except Exception as e:
            console.print(f"[yellow]Could not add programmatically: {e}[/yellow]")
            console.print("[dim]Please add manually using the steps above.[/dim]")
    else:
        console.print("[dim]Run 'pypasreportergui init' first, then add the database via the UI.[/dim]")


if __name__ == "__main__":
    app()
