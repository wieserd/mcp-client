"""Detailed status bar widget for real-time connection and feature telemetry."""

from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING
from rich.text import Text
from textual.widgets import Static

if TYPE_CHECKING:
    from textual.app import App


class StatusBar(Static):
    """Bottom status bar displaying live client state, logging, and stats."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: #181822;
        color: #a0a0a0;
        padding: 0 1;
        dock: bottom;
    }
    StatusBar.hidden {
        display: none;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_mount(self) -> None:
        self.refresh_status()

    def refresh_status(self) -> None:
        """Polls connected modules and updates the status bar text."""
        app = self.app

        # Connection status
        conn = getattr(app, "connection", None)
        if conn and conn.connected:
            host = conn._last_host or "server"
            port = conn._last_port or ""
            target = f"{host}:{port}" if port else host
            conn_part = f"[bold green]● CONNECTED[/] ([white]{target}[/])"
        elif conn and conn._reconnect_task and not conn._reconnect_task.done():
            conn_part = "[bold yellow]● RECONNECTING...[/]"
        else:
            conn_part = "[bold red]● DISCONNECTED[/]"

        # Logging status
        logger = getattr(app, "logger", None)
        if logger and logger.enabled:
            log_part = f"[cyan]LOG: ON[/] ({logger.level})"
        else:
            log_part = "[dim]LOG: OFF[/dim]"

        # Notifications status
        notify = getattr(app, "notifications", None)
        if notify and notify.enabled:
            kws_cnt = len(notify.list_keywords())
            sound_icon = " ♫" if notify.sound else ""
            notify_part = f"[magenta]ALERTS: ON[/] ({kws_cnt}{sound_icon})"
        else:
            notify_part = "[dim]ALERTS: OFF[/dim]"

        # Triggers / Scripts status
        scripts = getattr(app, "scripts", None)
        if scripts:
            trig_cnt = len([t for t in scripts.list_triggers() if t.enabled])
            tick_cnt = len(scripts.list_tickers())
            script_part = f"[yellow]TRIG: {trig_cnt}[/] [orange3]TICK: {tick_cnt}[/]"
        else:
            script_part = "[dim]TRIG: 0[/dim]"

        # Clock
        time_str = datetime.now().strftime("%H:%M:%S")
        clock_part = f"[bold white]{time_str}[/]"

        content = f"{conn_part}  │  {log_part}  │  {notify_part}  │  {script_part}  │  {clock_part}"
        self.update(Text.from_markup(content))

    def toggle(self) -> bool:
        """Toggles the status bar visibility and returns whether it is visible."""
        self.toggle_class("hidden")
        return not self.has_class("hidden")
