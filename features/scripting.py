"""Scripting, automated triggers, and timer engine for the MCP client."""

from __future__ import annotations
import asyncio
from dataclasses import dataclass
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.app import App


@dataclass
class Trigger:
    """An event-driven trigger that reacts to server output."""
    id: int
    pattern: str
    action: str
    regex: re.Pattern
    enabled: bool = True
    one_shot: bool = False


@dataclass
class Ticker:
    """A recurring timed task."""
    id: int
    interval: float
    command: str
    task: asyncio.Task | None = None


class ScriptManager:
    """Manages triggers and automated tickers."""

    def __init__(self, app: App | None = None):
        self.app = app
        self._triggers: dict[int, Trigger] = {}
        self._tickers: dict[int, Ticker] = {}
        self._next_trigger_id = 1
        self._next_ticker_id = 1

    def add_trigger(
        self,
        pattern: str,
        action: str,
        one_shot: bool = False,
    ) -> int:
        """Compiles and adds a new trigger."""
        compiled = re.compile(pattern, re.IGNORECASE)
        tid = self._next_trigger_id
        self._next_trigger_id += 1
        trigger = Trigger(
            id=tid,
            pattern=pattern,
            action=action,
            regex=compiled,
            one_shot=one_shot,
        )
        self._triggers[tid] = trigger
        return tid

    def remove_trigger(self, trigger_id: int) -> bool:
        """Removes a trigger by ID."""
        return self._triggers.pop(trigger_id, None) is not None

    def toggle_trigger(self, trigger_id: int) -> bool | None:
        """Toggles a trigger's enabled state."""
        trigger = self._triggers.get(trigger_id)
        if trigger:
            trigger.enabled = not trigger.enabled
            return trigger.enabled
        return None

    def list_triggers(self) -> list[Trigger]:
        """Returns all triggers."""
        return list(self._triggers.values())

    def evaluate_triggers(self, text: str) -> list[str]:
        """
        Evaluates incoming text against enabled triggers.
        Returns a list of expanded commands to execute.
        """
        commands_to_run: list[str] = []
        to_remove: list[int] = []

        for tid, trigger in list(self._triggers.items()):
            if not trigger.enabled:
                continue

            match = trigger.regex.search(text)
            if match:
                cmd = trigger.action
                # Substitute groups $1, $2, etc.
                for i in range(1, len(match.groups()) + 1):
                    group_val = match.group(i) or ""
                    cmd = cmd.replace(f"${i}", group_val)

                # Substitute entire match for $0 or $*
                cmd = cmd.replace("$0", match.group(0))
                cmd = cmd.replace("$*", " ".join(match.groups()))

                commands_to_run.append(cmd)

                if trigger.one_shot:
                    to_remove.append(tid)

        for tid in to_remove:
            self._triggers.pop(tid, None)

        return commands_to_run

    def add_ticker(self, interval: float, command: str) -> int:
        """Starts a recurring ticker task."""
        tid = self._next_ticker_id
        self._next_ticker_id += 1

        async def _ticker_loop():
            try:
                while True:
                    await asyncio.sleep(interval)
                    if self.app:
                        from core.commands import process_command
                        await process_command(self.app, command)
            except asyncio.CancelledError:
                pass

        task = asyncio.create_task(_ticker_loop())
        self._tickers[tid] = Ticker(id=tid, interval=interval, command=command, task=task)
        return tid

    def remove_ticker(self, ticker_id: int) -> bool:
        """Stops and removes a recurring ticker."""
        ticker = self._tickers.pop(ticker_id, None)
        if ticker:
            if ticker.task and not ticker.task.done():
                ticker.task.cancel()
            return True
        return False

    def list_tickers(self) -> list[Ticker]:
        """Returns all active tickers."""
        return list(self._tickers.values())

    def stop_all(self) -> None:
        """Stops all running ticker tasks and cleans up."""
        for ticker in self._tickers.values():
            if ticker.task and not ticker.task.done():
                ticker.task.cancel()
        self._tickers.clear()
