import asyncio
from textual.app import App
from core.mcp_parser import MCPParser

class Connection:
    """Manages the asyncio-based TCP connection to the server."""

    def __init__(self, app: App):
        self.app = app
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self.connected = False
        self.parser = getattr(app, "parser", None) or MCPParser(app)
        self._listen_task: asyncio.Task | None = None

    async def connect(self, host: str, port: int) -> None:
        """Establishes a connection to the server and starts listening for messages."""
        chat_log = self.app.query_one("#chat_window")
        try:
            chat_log.write(f"[yellow]Attempting to connect to {host}:{port}...[/]")
            self.reader, self.writer = await asyncio.open_connection(host, port)
            self.connected = True
            chat_log.write(f"[bold green]Connection successful![/]")
            self.app.sub_title = f"Connected to {host}:{port}"
            # Start and keep a reference to the background task
            self._listen_task = asyncio.create_task(self.listen_for_messages())
        except Exception as e:
            chat_log.write(f"[bold red]Connection failed: {e}[/]")
            self.app.sub_title = "Disconnected"

    async def disconnect(self) -> None:
        """Closes the connection to the server."""
        chat_log = self.app.query_one("#chat_window")

        # Cancel the listener task if still running and not currently executing disconnect
        if self._listen_task and self._listen_task is not asyncio.current_task() and not self._listen_task.done():
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        self._listen_task = None

        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass

        self.connected = False
        self.reader = None
        self.writer = None
        chat_log.write("[yellow]Disconnected from server.[/]")
        self.app.sub_title = "Disconnected"

    async def listen_for_messages(self) -> None:
        """Listens for incoming messages from the server and passes them to the parser."""
        chat_log = self.app.query_one("#chat_window")
        try:
            while self.reader and not self.reader.at_eof():
                line_bytes = await self.reader.readline()
                if not line_bytes:
                    break  # Connection closed by server
                message = line_bytes.decode('utf-8', 'ignore').rstrip('\r\n')
                self.parser.parse(message)
        except asyncio.CancelledError:
            return
        except Exception as e:
            chat_log.write(f"[bold red]Error receiving data: {e}[/]")
        finally:
            if self.connected:
                await self.disconnect()
