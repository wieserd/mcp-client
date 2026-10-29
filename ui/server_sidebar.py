"""MCP Server and Tool Explorer sidebar widget."""

from __future__ import annotations
from typing import Any
from rich.text import Text
from textual.containers import Vertical
from textual.widgets import Static


class ServerToolsSidebar(Vertical):
    """Sidebar displaying registered MCP servers, active status, and discovered tools/resources."""

    DEFAULT_CSS = """
    ServerToolsSidebar {
        width: 32;
        height: 1fr;
        background: #141419;
        border: round #3b4252;
        padding: 0 1;
    }
    ServerToolsSidebar.hidden {
        display: none;
    }
    #server_sidebar_header {
        color: #88c0d0;
        text-style: bold;
        border-bottom: solid #434c5e;
        margin-bottom: 1;
        height: auto;
        text-align: center;
    }
    #server_sidebar_body {
        height: 1fr;
        overflow-y: auto;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_content: str = ""

    def compose(self):
        yield Static("MCP Explorer (0)", id="server_sidebar_header")
        yield Static("[dim]Loading MCP servers...[/dim]", id="server_sidebar_body")

    def on_mount(self) -> None:
        self.refresh_servers()

    def refresh_servers(self) -> None:
        """Fetches active server metadata from the MCP server manager and refreshes the UI."""
        try:
            header = self.query_one("#server_sidebar_header", Static)
            body = self.query_one("#server_sidebar_body", Static)
        except Exception:
            return

        mgr = getattr(self.app, "server_manager", None)
        if not mgr:
            header.update("MCP Explorer (0)")
            body.update("[dim red]Manager unavailable[/dim red]")
            return

        server_list = mgr.list_servers()
        header.update(f"MCP Explorer ({len(server_list)})")

        if not server_list:
            body.update(
                "[dim]No MCP servers registered.[/dim]\n\n"
                "[dim]Add one with:\n[cyan]/servers add <n> <cmd>[/cyan][/dim]"
            )
            return

        lines: list[str] = []

        for s in server_list:
            status = s.get("status", "stopped")
            name = s.get("name", "unknown")

            if status == "connected":
                badge = "[bold green]●[/] [bold white]" + name + "[/] [green]✓[/]"
            elif status == "connecting":
                badge = "[bold yellow]●[/] [bold white]" + name + "[/] [yellow]…[/]"
            elif status == "error":
                badge = "[bold red]●[/] [bold white]" + name + "[/] [red]✗[/]"
            else:
                badge = "[dim]○[/] [dim white]" + name + "[/] [dim]off[/]"

            lines.append(badge)

            session = mgr.get_server(name)
            if session and status == "connected":
                # Tools
                if session.tools:
                    lines.append(f"  [bold #81a1c1]Tools ({len(session.tools)}):[/]")
                    for tool in session.tools:
                        t_name = tool.get("name", "unnamed")
                        desc = tool.get("description", "")
                        lines.append(f"    [cyan]•[/] [bold]{t_name}[/]")
                        if desc:
                            short_desc = desc[:28] + "..." if len(desc) > 28 else desc
                            lines.append(f"      [dim]{short_desc}[/dim]")

                # Resources
                if session.resources:
                    lines.append(f"  [bold #b48ead]Resources ({len(session.resources)}):[/]")
                    for res in session.resources:
                        uri = res.get("uri", "")
                        lines.append(f"    [magenta]•[/] [dim]{uri}[/dim]")

                # Prompts
                if session.prompts:
                    lines.append(f"  [bold #ebcb8b]Prompts ({len(session.prompts)}):[/]")
                    for p in session.prompts:
                        p_name = p.get("name", "")
                        lines.append(f"    [yellow]•[/] [dim]{p_name}[/dim]")
            elif status == "error":
                err = s.get("last_error") or "Unknown error"
                short_err = err[:30] + "..." if len(err) > 30 else err
                lines.append(f"  [dim red]{short_err}[/dim red]")
            elif status == "stopped":
                lines.append(f"  [dim]Start: /servers start {name}[/dim]")

            lines.append("")  # Spacer between servers

        content = "\n".join(lines).strip()
        if content != self._last_content:
            self._last_content = content
            body.update(content)

    def toggle(self) -> bool:
        """Toggles sidebar visibility and returns new visibility state."""
        self.toggle_class("hidden")
        return not self.has_class("hidden")

    def get_servers(self) -> list[str]:
        """Returns list of registered server names."""
        mgr = getattr(self.app, "server_manager", None)
        return list(mgr.servers.keys()) if mgr else []

    def get_users(self) -> list[str]:
        """Backward-compatibility shim for legacy user queries."""
        mgr = getattr(self.app, "server_manager", None)
        if not mgr:
            return []
        items = list(mgr.servers.keys())
        for s in mgr.servers.values():
            for t in s.tools:
                items.append(t.get("name", ""))
        return [i for i in items if i]
