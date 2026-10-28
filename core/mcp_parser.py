from textual.app import App

class MCPParser:
    """Parses and handles MCP 2.1 protocol messages."""

    def __init__(self, app: App):
        self.app = app

    @property
    def renderer(self):
        return getattr(self.app, "renderer", None)

    def parse(self, message: str):
        """Parses an incoming message from the server."""
        lines = message.splitlines()

        for line in lines:
            if line.startswith("#$#"):
                self._handle_mcp_message(line)
            else:
                # Regular text from the MUD
                if self.renderer:
                    self.renderer.write_server(line)
                else:
                    self.app.query_one("#chat_window").write(line)

    def _handle_mcp_message(self, mcp_string: str):
        """Handles a single, validated MCP message string."""
        parts = mcp_string.split()
        if not parts:
            return
        command = parts[0][3:]  # Remove the "#$#"

        # For now, we handle the initial negotiation message.
        if command == "mcp-negotiation-can" and "package:" in mcp_string and "version:" in mcp_string:
            if self.renderer:
                self.renderer.write_mcp("Server supports MCP 2.1. Negotiation started.")
            else:
                self.app.query_one("#chat_window").write("[bold magenta]MCP:[/] Server supports MCP 2.1. Negotiation started.")
        else:
            if self.renderer:
                self.renderer.write_mcp(f"Received unknown command: {command}")
            else:
                self.app.query_one("#chat_window").write(f"[bold magenta]MCP:[/] Received unknown command: {command}")
