"""MUD Client Protocol (MCP) 2.1 parser and message dispatcher."""

from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
import secrets
import shlex
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from textual.app import App


@dataclass
class MCPMessage:
    """Represents a structured MCP 2.1 message."""
    name: str
    auth_key: str | None = None
    fields: dict[str, str] = field(default_factory=dict)
    data: dict[str, list[str]] = field(default_factory=dict)


class MCPParser:
    """Parses, dispatches, and handles MCP 2.1 protocol messages."""

    def __init__(self, app: App):
        self.app = app
        self.auth_key: str = secrets.token_hex(8)
        self.server_auth_key: str | None = None
        self.server_packages: dict[str, dict[str, str]] = {}
        self._handlers: dict[str, Callable[[MCPMessage], None | asyncio.Future]] = {}
        self._pending_data: dict[str, tuple[MCPMessage, str]] = {}

        self._register_default_handlers()

    @property
    def renderer(self):
        return getattr(self.app, "renderer", None)

    def register_handler(self, command: str, handler: Callable[[MCPMessage], None]) -> None:
        """Registers a handler for a given MCP command name."""
        self._handlers[command.lower()] = handler

    def _register_default_handlers(self) -> None:
        """Registers built-in handlers for MCP core protocol messages."""
        self.register_handler("mcp", self._handle_mcp_init)
        self.register_handler("mcp-negotiate-can", self._handle_negotiate_can)
        self.register_handler("mcp-negotiation-can", self._handle_negotiate_can)
        self.register_handler("mcp-negotiate-end", self._handle_negotiate_end)

    def parse(self, message: str) -> None:
        """Parses an incoming raw line or chunk from the server."""
        lines = message.splitlines()
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("#$#*"):
                self._handle_multiline_data(line_str)
            elif line_str.startswith("#$#:"):
                self._handle_multiline_end(line_str)
            elif line_str.startswith("#$#"):
                self._handle_mcp_header(line_str)
            else:
                # Regular in-band text from the MUD
                if self.renderer:
                    self.renderer.write_server(line)
                else:
                    self.app.query_one("#chat_window").write(line)

    def _tokenize(self, line: str) -> list[str]:
        """Safely tokenizes an MCP string respecting double quotes."""
        try:
            return shlex.split(line, posix=True)
        except Exception:
            return line.split()

    def _handle_mcp_header(self, line: str) -> None:
        """Parses and dispatches a single MCP header line (#$#name ...)."""
        content = line[3:].strip()
        if not content:
            return

        tokens = self._tokenize(content)
        if not tokens:
            return

        cmd_name = tokens[0].lower()
        auth_key: str | None = None
        idx = 1

        # Check for optional auth key (token without ':')
        if idx < len(tokens) and not tokens[idx].endswith(":") and ":" not in tokens[idx]:
            auth_key = tokens[idx]
            idx += 1

        fields: dict[str, str] = {}
        while idx < len(tokens):
            tok = tokens[idx]
            if ":" in tok:
                k, v = tok.split(":", 1)
                if not v:
                    idx += 1
                    v = tokens[idx] if idx < len(tokens) else ""
                fields[k.lower()] = v
            idx += 1

        msg = MCPMessage(name=cmd_name, auth_key=auth_key, fields=fields)

        # Check if message declares a multiline data tag
        data_tag = fields.get("_data-tag")
        if data_tag:
            self._pending_data[data_tag] = (msg, "lines")
            return

        self._dispatch(msg)

    def _handle_multiline_data(self, line: str) -> None:
        """Handles multiline data continuation line (#$#* tag [field:] content)."""
        parts = line[4:].strip().split(maxsplit=1)
        if not parts:
            return

        tag = parts[0]
        content = parts[1] if len(parts) > 1 else ""

        if tag in self._pending_data:
            msg, default_field = self._pending_data[tag]
            # Check if content starts with a specific field
            if ":" in content and " " in content and content.index(":") < content.index(" "):
                field_name, field_val = content.split(":", 1)
                field_name = field_name.strip().lower()
                msg.data.setdefault(field_name, []).append(field_val.strip())
            else:
                msg.data.setdefault(default_field, []).append(content)

    def _handle_multiline_end(self, line: str) -> None:
        """Handles multiline data termination (#$#: tag)."""
        parts = line[4:].strip().split()
        if not parts:
            return
        tag = parts[0]
        if tag in self._pending_data:
            msg, _ = self._pending_data.pop(tag)
            self._dispatch(msg)

    def _dispatch(self, msg: MCPMessage) -> None:
        """Dispatches an MCP message to registered handlers."""
        handler = self._handlers.get(msg.name)
        if handler:
            handler(msg)
        else:
            if self.renderer:
                details = f" {msg.fields}" if msg.fields else ""
                self.renderer.write_mcp(f"Received {msg.name}{details}")

    def send_mcp(self, command: str, auth_key: str | None = None, **fields: str) -> None:
        """Formats and sends an MCP message to the connected server."""
        connection = getattr(self.app, "connection", None)
        if not connection or not connection.writer or not connection.connected:
            return

        tokens = [f"#$#{command}"]
        if auth_key:
            tokens.append(auth_key)

        for k, v in fields.items():
            clean_k = k.replace("_", "-")
            tokens.append(f'{clean_k}: "{v}"')

        payload = " ".join(tokens) + "\n"
        connection.writer.write(payload.encode("utf-8"))

    # --- Built-in Handlers ---

    def _handle_mcp_init(self, msg: MCPMessage) -> None:
        """Handles server initiation '#$#mcp version: ...'."""
        server_min = msg.fields.get("version", "2.1")
        server_max = msg.fields.get("to", server_min)

        if self.renderer:
            self.renderer.write_mcp(f"Negotiating MCP (Server version: {server_min} - {server_max})")

        # Reply with client version and generated session auth-key
        self.send_mcp("mcp", authentication_key=self.auth_key, version="2.1", to="2.1")

        # Announce client packages
        self.send_mcp(
            "mcp-negotiate-can",
            self.auth_key,
            package="mcp-negotiate",
            min_version="1.0",
            max_version="2.0",
        )
        self.send_mcp(
            "mcp-negotiate-end",
            self.auth_key,
        )

    def _handle_negotiate_can(self, msg: MCPMessage) -> None:
        """Handles '#$#mcp-negotiate-can package: ...'."""
        pkg = msg.fields.get("package")
        min_v = msg.fields.get("min-version", "1.0")
        max_v = msg.fields.get("max-version", min_v)
        if pkg:
            self.server_packages[pkg] = {"min_version": min_v, "max_version": max_v}
            if self.renderer:
                self.renderer.write_mcp(f"Server package registered: [bold cyan]{pkg}[/] (v{min_v}-{max_v})")

    def _handle_negotiate_end(self, msg: MCPMessage) -> None:
        """Handles '#$#mcp-negotiate-end'."""
        if msg.auth_key:
            self.server_auth_key = msg.auth_key
        if self.renderer:
            self.renderer.write_mcp("MCP 2.1 negotiation completed.")
