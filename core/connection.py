import asyncio
from textual.app import App

class Connection:
    """Manages the asyncio-based TCP connection to the server."""

    def __init__(self, app: App):
        self.app = app
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self.connected = False

    async def connect(self, host: str, port: int) -> None:
        """Establishes a connection to the server and starts listening for messages."""
        chat_log = self.app.query_one("#chat_window")
        try:
            chat_log.write(f"[yellow]Attempting to connect to {host}:{port}...[/]")
            self.reader, self.writer = await asyncio.open_connection(host, port)
            self.connected = True
            chat_log.write(f"[bold green]Connection successful![/]")
            self.app.sub_title = f"Connected to {host}:{port}"
            # Start a background task to listen for incoming messages
            asyncio.create_task(self.listen_for_messages())
        except Exception as e:
            chat_log.write(f"[bold red]Connection failed: {e}[/]")
            self.app.sub_title = "Disconnected"

    async def disconnect(self) -> None:
        """Closes the connection to the server."""
        chat_log = self.app.query_one("#chat_window")
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.connected = False
        self.reader = None
        self.writer = None
        chat_log.write("[yellow]Disconnected from server.[/]")
        self.app.sub_title = "Disconnected"

    async def listen_for_messages(self) -> None:
        """Listens for incoming messages from the server and displays them."""
        chat_log = self.app.query_one("#chat_window")
        while self.reader and not self.reader.at_eof():
            try:
                data = await self.reader.read(1024)
                if data:
                    # For now, just decode and print the raw message
                    chat_log.write(f"[blue]FROM SERVER:[/] {data.decode('utf-8', 'ignore').strip()}")
                else:
                    break # Connection closed by server
            except Exception as e:
                chat_log.write(f"[bold red]Error receiving data: {e}[/]")
                break
        await self.disconnect()
