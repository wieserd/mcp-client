from textual.app import App

class MCPParser:
    """Parses and handles MCP 2.1 protocol messages."""

    def __init__(self, app: App):
        self.app = app

    def parse(self, message: str):
        """Parses an incoming message from the server."""
        chat_log = self.app.query_one("#chat_window")

        # MCP messages are on their own lines.
        lines = message.strip().splitlines()

        for line in lines:
            if line.startswith("#$#"):
                self._handle_mcp_message(line)
            else:
                # It's just regular text from the MUD.
                chat_log.write(line)

    def _handle_mcp_message(self, mcp_string: str):
        """Handles a single, validated MCP message string."""
        chat_log = self.app.query_one("#chat_window")
        parts = mcp_string.split()
        command = parts[0][3:] # Remove the "#$#"

        # For now, we only handle the initial negotiation message.
        if command == "mcp-negotiation-can" and "package:" in mcp_string and "version:" in mcp_string:
            chat_log.write("[bold magenta]MCP:[/] Server supports MCP 2.1. Negotiation started.")
            # In the future, we would parse the packages and versions here.
        else:
            # For now, just display any other MCP messages for debugging.
            chat_log.write(f"[bold magenta]MCP:[/] Received unknown command: {command}")
