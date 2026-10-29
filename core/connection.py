"""TCP Connection manager with automatic reconnection and protocol dispatching."""

from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING
from core.mcp_parser import MCPParser

if TYPE_CHECKING:
    from textual.app import App


class Connection:
    """Manages the asyncio-based TCP connection to the server with auto-reconnection."""

    def __init__(self, app: App):
        self.app = app
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self.connected = False
        self.parser = getattr(app, "parser", None) or MCPParser(app)
        self._listen_task: asyncio.Task | None = None
        self._reconnect_task: asyncio.Task | None = None
        self._manual_disconnect: bool = False
        self._last_host: str | None = None
        self._last_port: int | None = None

    @property
    def renderer(self):
        return getattr(self.app, "renderer", None)

    def cancel_reconnect(self) -> None:
        """Cancels any pending auto-reconnect task."""
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
        self._reconnect_task = None

    async def connect(self, host: str, port: int, is_reconnect: bool = False) -> None:
        """Establishes a connection to the server and starts listening for messages."""
        if not is_reconnect:
            self.cancel_reconnect()
            self._manual_disconnect = False

        self._last_host = host
        self._last_port = port

        if self.renderer:
            self.renderer.write_warning(f"Attempting to connect to {host}:{port}...")
        else:
            self.app.query_one("#chat_window").write(f"[yellow]Attempting to connect to {host}:{port}...[/]")

        try:
            self.reader, self.writer = await asyncio.open_connection(host, port)
            self.connected = True
            if self.renderer:
                self.renderer.write_success("Connection successful!")
            else:
                self.app.query_one("#chat_window").write("[bold green]Connection successful![/]")
            self.app.sub_title = f"Connected to {host}:{port}"
            self._listen_task = asyncio.create_task(self.listen_for_messages())
        except Exception as e:
            self.connected = False
            self.reader = None
            self.writer = None
            if self.renderer:
                self.renderer.write_error(f"Connection failed: {e}")
            else:
                self.app.query_one("#chat_window").write(f"[bold red]Connection failed: {e}[/]")
            self.app.sub_title = "Disconnected"
            raise

    async def disconnect(self, manual: bool = True) -> None:
        """Closes the connection to the server."""
        if manual:
            self._manual_disconnect = True
            self.cancel_reconnect()

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

        was_connected = self.connected
        self.connected = False
        self.reader = None
        self.writer = None

        if was_connected:
            if self.renderer:
                self.renderer.write_warning("Disconnected from server.")
            else:
                self.app.query_one("#chat_window").write("[yellow]Disconnected from server.[/]")
            self.app.sub_title = "Disconnected"

        # If dropped unexpectedly and not manually disconnected, schedule auto-reconnection
        if not manual and not self._manual_disconnect and self._last_host and self._last_port:
            self._trigger_auto_reconnect()

    def _trigger_auto_reconnect(self) -> None:
        """Schedules auto-reconnect in a background task."""
        self.cancel_reconnect()
        self._reconnect_task = asyncio.create_task(self._auto_reconnect_loop())

    async def _auto_reconnect_loop(self) -> None:
        """Attempts to reconnect up to reconnect_attempts times with reconnect_delay."""
        server_cfg = getattr(self.app.config, "server", None)
        attempts = 3
        delay = 5
        if server_cfg:
            attempts = getattr(server_cfg, "reconnect_attempts", 3)
            delay = getattr(server_cfg, "reconnect_delay", 5)

        host = self._last_host
        port = self._last_port

        if not host or not port:
            return

        for attempt in range(1, attempts + 1):
            if self._manual_disconnect:
                return

            msg = f"Connection lost. Reconnecting to {host}:{port} (attempt {attempt}/{attempts}) in {delay}s..."
            if self.renderer:
                self.renderer.write_warning(msg)
            else:
                self.app.query_one("#chat_window").write(f"[yellow]{msg}[/]")
            self.app.sub_title = f"Reconnecting ({attempt}/{attempts})..."

            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                return

            if self._manual_disconnect:
                return

            try:
                await self.connect(host, port, is_reconnect=True)
                if self.connected:
                    return
            except Exception:
                pass

        if not self.connected and not self._manual_disconnect:
            fail_msg = f"Auto-reconnect failed after {attempts} attempts. Use /connect to retry manually."
            if self.renderer:
                self.renderer.write_error(fail_msg)
            else:
                self.app.query_one("#chat_window").write(f"[bold red]{fail_msg}[/]")
            self.app.sub_title = "Disconnected"

    async def listen_for_messages(self) -> None:
        """Listens for incoming messages from the server and passes them to the parser."""
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
            if self.renderer:
                self.renderer.write_error(f"Error receiving data: {e}")
            else:
                self.app.query_one("#chat_window").write(f"[bold red]Error receiving data: {e}[/]")
        finally:
            if self.connected:
                # Triggered automatically because server dropped connection
                await self.disconnect(manual=False)
