from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, RichLog, Input
from rich.text import Text
from core.commands import process_command
from core.connection import Connection
from core.mcp_parser import MCPParser
from ui.output_renderer import OutputRenderer
from ui.input_handler import HistoryInput
from features.chat_logger import ChatLogger
from features.macros import MacroManager
from features.notifications import NotificationManager

# This makes the path to the CSS file relative to this file.
CSS_PATH = (Path(__file__).parent / "../assets/themes/default.css").resolve()

class MCPApp(App):
    """A Textual-based MCP client."""

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
        self.renderer = OutputRenderer(self)
        self.parser = MCPParser(self)
        self.connection = Connection(self)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield RichLog(id="chat_window", wrap=True)
        yield HistoryInput(placeholder="Enter command or message...", id="input_bar")
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.title = "MCP-Client"
        self.sub_title = "Disconnected"  # Start in a disconnected state

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
        self.renderer.write("Type [bold cyan]/help[/] for a list of commands.")
        self.query_one("#input_bar").focus()

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
        if self.connection.connected:
            await self.connection.disconnect()
