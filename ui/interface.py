from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, RichLog, Input
from core.commands import process_command

# This makes the path to the CSS file relative to this file.
CSS_PATH = (Path(__file__).parent / "../assets/themes/default.css").resolve()

class MCPApp(App):
    """A Textual-based MCP client."""

    def __init__(self, config, **kwargs):
        super().__init__(css_path=CSS_PATH, **kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield RichLog(id="chat_window", wrap=True)
        yield Input(placeholder="Enter command or message...", id="input_bar")
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.title = "MCP-Client"
        self.sub_title = f"Connecting to {self.config['server']['host']}:{self.config['server']['port']}"

        # Add a welcome message and some ASCII art to the header
        header = self.query_one(Header)
        header.renderable = r"""[bold cyan]
  __  __  ___   ___  
 |  \/  |/ __| / __| 
 | |\/| | (__ | |    
 |_|  |_|\___| \_|    
[/] - [white]Retro-Futuristic Edition[/]"""

        chat_log = self.query_one("#chat_window")
        chat_log.write("[bold green]Welcome to the MCP Client![/]")
        chat_log.write("Type [bold cyan]/help[/] for a list of commands.")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Called when the user presses Enter in the input bar."""
        user_input = event.value

        # Process the command
        process_command(self, user_input)

        # Clear the input bar
        self.query_one(Input).value = ""
