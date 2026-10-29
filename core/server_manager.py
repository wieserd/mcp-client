"""Manager for multiple concurrent Model Context Protocol (MCP) server sessions."""

from __future__ import annotations
import asyncio
from typing import Any
from core.mcp_client import MCPClientSession


class MCPServerManager:
    """Manages lifecycle and tool routing across multiple MCP servers."""

    def __init__(self):
        self.servers: dict[str, MCPClientSession] = {}

    def register_server(
        self,
        name: str,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> MCPClientSession:
        """Registers a server definition without immediately starting it."""
        session = MCPClientSession(name=name, command=command, args=args, env=env)
        self.servers[name] = session
        return session

    async def start_server(self, name: str) -> bool:
        """Starts an existing registered server."""
        session = self.servers.get(name)
        if not session:
            return False
        return await session.start()

    async def stop_server(self, name: str) -> bool:
        """Stops a running server."""
        session = self.servers.get(name)
        if not session:
            return False
        await session.stop()
        return True

    async def stop_all(self) -> None:
        """Stops all running MCP servers."""
        stop_tasks = [session.stop() for session in self.servers.values()]
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)

    def get_server(self, name: str) -> MCPClientSession | None:
        """Gets a server session by name."""
        return self.servers.get(name)

    def list_servers(self) -> list[dict[str, Any]]:
        """Returns status metadata for all registered servers."""
        info_list = []
        for name, s in self.servers.items():
            info_list.append({
                "name": name,
                "status": s.status,
                "command": s.command,
                "args": s.args,
                "tools_count": len(s.tools),
                "resources_count": len(s.resources),
                "prompts_count": len(s.prompts),
                "server_info": s.server_info,
                "last_error": s.last_error,
            })
        return info_list

    def get_all_tools(self) -> list[dict[str, Any]]:
        """Returns all tools from all connected servers, annotated with server name."""
        all_tools = []
        for server_name, session in self.servers.items():
            if session.status == "connected":
                for t in session.tools:
                    tool_copy = dict(t)
                    tool_copy["_server"] = server_name
                    all_tools.append(tool_copy)
        return all_tools

    def find_tool(self, tool_name: str) -> tuple[MCPClientSession, dict[str, Any]] | None:
        """Finds which active server provides the specified tool."""
        for session in self.servers.values():
            if session.status == "connected":
                for t in session.tools:
                    if t.get("name") == tool_name:
                        return session, t
        return None

    async def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        """Routes a tool call to the appropriate server and returns result."""
        match = self.find_tool(tool_name)
        if not match:
            raise KeyError(f"Tool '{tool_name}' not found on any connected MCP server.")
        session, _ = match
        return await session.call_tool(tool_name, arguments)
