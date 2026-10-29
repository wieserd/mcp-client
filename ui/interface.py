from pathlib import Path
import asyncio
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Header, Footer, RichLog, Input
from rich.text import Text
from core.commands import process_command
from core.connection import Connection
from core.mcp_parser import MCPParser
from core.server_manager import MCPServerManager
from ui.output_renderer import OutputRenderer
from ui.input_handler import HistoryInput
from ui.user_list import UserListSidebar
from ui.status_bar import StatusBar
from ui.search_box import SearchBox
from features.chat_logger import ChatLogger
from features.macros import MacroManager
from features.notifications import NotificationManager
from features.scripting import ScriptManager

# This makes the path to the CSS file relative to this file.
CSS_PATH = (Path(__file__).parent / "../assets/themes/default.css").resolve()

class MCPApp(App):
    """A Textual-based MCP client."""

    BINDINGS = [
        Binding("f2", "toggle_users", "Toggle User List", show=True),
        Binding("ctrl+b", "toggle_users", "Toggle User List", show=False),
        Binding("f3", "toggle_status_bar", "Toggle Status Bar", show=True),
        Binding("ctrl+f", "toggle_search", "Search Scrollback", show=True),
        Binding("f4", "toggle_search", "Search Scrollback", show=False),
    ]

    def __init__(self, config, **kwargs):
        super().__init__(css_path=CSS_PATH, **kwargs)
        self.config = config
        logging_cfg = getattr(config, "logging", None) or (config.get("logging", {}) if isinstance(config, dict) else {})
        enabled = getattr(logging_cfg, "enabled", True) if hasattr(logging_cfg, "enabled") else logging_cfg.get("enabled", True)
        log_dir = getattr(logging_cfg, "path", "logs") if hasattr(logging_cfg, "path") else logging_cfg.get("path", "logs")
        level = getattr(logging_cfg, "level", "full") if hasattr(logging_cfg, "level") else logging_cfg.get("level", "full")
        self.logger = ChatLogger(enabled=enabled, log_dir=log_dir, level=level)

        initial_macros = getattr(config, "macros", None) or (config.get("macros", {}) if isinstance(config, dict) else {})
        self.macros = MacroManager(initial_macros if isinstance(initial_macros, dict) else {})

        self.notifications = NotificationManager(app=self)
        self.scripts = ScriptManager(app=self)
        self.server_manager = MCPServerManager()
        mcp_servers = getattr(config, "mcp_servers", {})
        if isinstance(mcp_servers, dict):
            for s_name, s_def in mcp_servers.items():
                self.server_manager.register_server(
                    name=s_name,
                    command=s_def.command,
                    args=s_def.args,
                    env=s_def.env,
                )

        self.renderer = OutputRenderer(self)
        self.parser = MCPParser(self)
        self.connection = Connection(self)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Horizontal(id="content_area"):
            yield RichLog(id="chat_window", wrap=True)
            yield UserListSidebar(id="user_sidebar")
        yield SearchBox(id="search_box")
        yield StatusBar(id="status_bar")
        yield HistoryInput(placeholder="Enter command or message...", id="input_bar")
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.title = "MCP-Client"
        self.sub_title = "Disconnected"  # Start in a disconnected state

        # Check configured initial visibility for the user sidebar and status bar
        ui_cfg = getattr(self.config, "ui", None) or (self.config.get("ui", {}) if isinstance(self.config, dict) else {})
        show_users = getattr(ui_cfg, "show_user_list", True) if hasattr(ui_cfg, "show_user_list") else ui_cfg.get("show_user_list", True)
        if not show_users:
            try:
                self.query_one(UserListSidebar).add_class("hidden")
            except Exception:
                pass

        show_status_bar = getattr(ui_cfg, "show_status_bar", True) if hasattr(ui_cfg, "show_status_bar") else ui_cfg.get("show_status_bar", True)
        if not show_status_bar:
            try:
                self.query_one(StatusBar).add_class("hidden")
            except Exception:
                pass

        self.set_interval(1.0, self._tick_status_bar)

        # Load the ASCII art logo from the file
        logo_path = (Path(__file__).parent / "../assets/logo.txt").resolve()
        try:
            with open(logo_path, "r") as f:
                logo_text = f.read()
        except FileNotFoundError:
            logo_text = ""

        if logo_text.strip():
            self.renderer.write(f"[bold cyan]{logo_text}[/]")

        self.renderer.write_success("Welcome to the MCP Client!")
        self.renderer.write("Type [bold cyan]/help[/] for a list of commands, or [bold cyan]/tools[/] for available MCP tools.")
        self.query_one("#input_bar").focus()

        # Auto-connect configured MCP servers
        if hasattr(self, "server_manager") and self.server_manager.servers:
            for s_name in self.server_manager.servers:
                asyncio.create_task(self._auto_start_mcp_server(s_name))

    async def _auto_start_mcp_server(self, name: str) -> None:
        """Asynchronously starts a configured MCP server in the background on startup."""
        try:
            ok = await self.server_manager.start_server(name)
            if ok:
                session = self.server_manager.get_server(name)
                tools_cnt = len(session.tools) if session else 0
                self.renderer.write_success(f"MCP server '[bold cyan]{name}[/]' connected ({tools_cnt} tools available).")
            else:
                session = self.server_manager.get_server(name)
                err = session.last_error if session else "Unknown error"
                self.renderer.write_warning(f"Could not connect MCP server '{name}': {err}")
        except Exception as e:
            self.renderer.write_error(f"Error starting MCP server '{name}': {e}")

    def action_toggle_users(self) -> None:
        """Toggles the visibility of the user sidebar."""
        try:
            sidebar = self.query_one(UserListSidebar)
            visible = sidebar.toggle()
            if hasattr(self, "renderer"):
                state = "shown" if visible else "hidden"
                self.renderer.write_info(f"User list {state}.")
        except Exception:
            pass

    def _tick_status_bar(self) -> None:
        """Periodic tick to update the status bar clock and telemetry."""
        try:
            self.query_one(StatusBar).refresh_status()
        except Exception:
            pass

    def action_toggle_status_bar(self) -> None:
        """Toggles the visibility of the bottom status bar."""
        try:
            bar = self.query_one(StatusBar)
            visible = bar.toggle()
            if hasattr(self, "renderer"):
                state = "shown" if visible else "hidden"
                self.renderer.write_info(f"Status bar {state}.")
        except Exception:
            pass

    def action_toggle_search(self) -> None:
        """Toggles the interactive search box."""
        try:
            self.query_one(SearchBox).toggle()
        except Exception:
            pass

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Called when the user presses Enter in the input bar."""
        user_input = event.value

        if hasattr(event.input, "add_history"):
            event.input.add_history(user_input)

        # Process the command
        await process_command(self, user_input)

        # Clear the input bar
        event.input.value = ""

    async def on_quit(self) -> None:
        """Called when the app is quitting."""
        if hasattr(self, "server_manager"):
            await self.server_manager.stop_all()
        if hasattr(self, "scripts"):
            self.scripts.stop_all()
        if self.connection.connected:
            await self.connection.disconnect()
