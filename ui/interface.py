from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, RichLog, Input
from core.commands import process_command
from core.connection import Connection
from core.mcp_parser import MCPParser

# This makes the path to the CSS file relative to this file.
CSS_PATH = (Path(__file__).parent / "../assets/themes/default.css").resolve()

class MCPApp(App):
    """A Textual-based MCP client."""

    def __init__(self, config, **kwargs):
        super().__init__(css_path=CSS_PATH, **kwargs)
        self.config = config
        self.connection = Connection(self)
        self.parser = MCPParser(self)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield RichLog(id="chat_window", wrap=True)
        yield Input(placeholder="Enter command or message...", id="input_bar")
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
            logo_text = "MCP-Client"

        # Add a welcome message and some ASCII art to the header
        header = self.query_one(Header)
        header.renderable = logo_text

        chat_log = self.query_one("#chat_window")
        chat_log.write("[bold green]Welcome to the MCP Client![/]")
        chat_log.write("Type [bold cyan]/help[/] for a list of commands.")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Called when the user presses Enter in the input bar."""
        user_input = event.value

        # Process the command
        await process_command(self, user_input)

        # Clear the input bar
        self.query_one(Input).value = ""

    async def on_quit(self) -> None:
        """Called when the app is quitting."""
        if self.connection.connected:
            await self.connection.disconnect()
