"""Model Context Protocol (MCP) JSON-RPC client session over stdio."""

from __future__ import annotations
import asyncio
import json
import os
from typing import Any, Callable


class MCPClientSession:
    """Manages an active Model Context Protocol (MCP) session with an external server."""

    def __init__(
        self,
        name: str,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        cwd: str | None = None,
    ):
        self.name = name
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.cwd = cwd
        self.process: asyncio.subprocess.Process | None = None

        self._request_id: int = 1
        self._pending_requests: dict[int, asyncio.Future[Any]] = {}
        self._read_task: asyncio.Task | None = None
        self._stderr_task: asyncio.Task | None = None

        self.server_info: dict[str, Any] = {}
        self.capabilities: dict[str, Any] = {}
        self.tools: list[dict[str, Any]] = []
        self.resources: list[dict[str, Any]] = []
        self.prompts: list[dict[str, Any]] = []
        self.status: str = "stopped"  # stopped, connecting, connected, error
        self.last_error: str | None = None

    async def start(self) -> bool:
        """Starts the server subprocess and executes the MCP initialization handshake."""
        if self.status == "connected" and self.process and self.process.returncode is None:
            return True

        self.status = "connecting"
        self.last_error = None

        # Build environment
        full_env = os.environ.copy()
        full_env.update(self.env)

        try:
            self.process = await asyncio.create_subprocess_exec(
                self.command,
                *self.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=full_env,
                cwd=self.cwd,
            )
        except Exception as e:
            self.status = "error"
            self.last_error = f"Failed to spawn process '{self.command}': {e}"
            return False

        # Start stdout/stderr readers
        self._read_task = asyncio.create_task(self._listen_stdout())
        self._stderr_task = asyncio.create_task(self._listen_stderr())

        try:
            # Send MCP 'initialize' handshake request (Anthropic MCP standard)
            init_params = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {},
                },
                "clientInfo": {
                    "name": "mcp-terminal-client",
                    "version": "1.0.0",
                },
            }
            init_res = await self.send_request("initialize", init_params, timeout=15.0)
            self.server_info = init_res.get("serverInfo", {})
            self.capabilities = init_res.get("capabilities", {})

            # Send 'notifications/initialized'
            await self.send_notification("notifications/initialized")

            # Fetch available tools, resources, and prompts
            await self.refresh_capabilities()

            self.status = "connected"
            return True
        except Exception as e:
            self.status = "error"
            self.last_error = f"MCP initialization handshake failed: {e}"
            await self.stop()
            return False

    async def stop(self) -> None:
        """Gracefully shuts down the server subprocess."""
        self.status = "stopped"

        # Cancel all pending request futures
        for fut in self._pending_requests.values():
            if not fut.done():
                fut.cancel()
        self._pending_requests.clear()

        if self._read_task and not self._read_task.done():
            self._read_task.cancel()
        self._read_task = None

        if self._stderr_task and not self._stderr_task.done():
            self._stderr_task.cancel()
        self._stderr_task = None

        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=2.0)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None

    async def send_request(self, method: str, params: dict[str, Any] | None = None, timeout: float = 30.0) -> Any:
        """Sends a JSON-RPC 2.0 request and awaits the result."""
        if not self.process or not self.process.stdin or self.process.returncode is not None:
            raise RuntimeError(f"Server '{self.name}' is not running.")

        req_id = self._request_id
        self._request_id += 1

        payload: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
        }
        if params is not None:
            payload["params"] = params

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._pending_requests[req_id] = future

        message_bytes = (json.dumps(payload) + "\n").encode("utf-8")
        self.process.stdin.write(message_bytes)
        await self.process.stdin.drain()

        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending_requests.pop(req_id, None)
            raise TimeoutError(f"Request {method} (id={req_id}) timed out after {timeout}s")

    async def send_notification(self, method: str, params: dict[str, Any] | None = None) -> None:
        """Sends a JSON-RPC 2.0 notification (no response expected)."""
        if not self.process or not self.process.stdin or self.process.returncode is not None:
            return

        payload: dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params is not None:
            payload["params"] = params

        message_bytes = (json.dumps(payload) + "\n").encode("utf-8")
        self.process.stdin.write(message_bytes)
        await self.process.stdin.drain()

    async def refresh_capabilities(self) -> None:
        """Fetches active tools, resources, and prompts from the server."""
        # 1. Tools
        try:
            tools_res = await self.send_request("tools/list", timeout=10.0)
            self.tools = tools_res.get("tools", [])
        except Exception:
            self.tools = []

        # 2. Resources
        try:
            res_data = await self.send_request("resources/list", timeout=10.0)
            self.resources = res_data.get("resources", [])
        except Exception:
            self.resources = []

        # 3. Prompts
        try:
            prompts_res = await self.send_request("prompts/list", timeout=10.0)
            self.prompts = prompts_res.get("prompts", [])
        except Exception:
            self.prompts = []

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        """Calls an MCP tool by name with arguments."""
        params = {
            "name": name,
            "arguments": arguments or {},
        }
        return await self.send_request("tools/call", params)

    async def read_resource(self, uri: str) -> dict[str, Any]:
        """Reads an MCP resource by URI."""
        return await self.send_request("resources/read", {"uri": uri})

    async def get_prompt(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        """Gets a prompt template from the server."""
        return await self.send_request("prompts/get", {"name": name, "arguments": arguments or {}})

    async def _listen_stdout(self) -> None:
        """Reads incoming JSON-RPC lines from server stdout."""
        while self.process and self.process.stdout and not self.process.stdout.at_eof():
            try:
                line = await self.process.stdout.readline()
                if not line:
                    break
                line_str = line.decode("utf-8", "ignore").strip()
                if not line_str:
                    continue

                try:
                    data = json.loads(line_str)
                except json.JSONDecodeError:
                    continue

                req_id = data.get("id")
                if req_id is not None and req_id in self._pending_requests:
                    fut = self._pending_requests.pop(req_id)
                    if not fut.done():
                        if "error" in data:
                            err = data["error"]
                            msg = err.get("message", "Unknown JSON-RPC error")
                            fut.set_exception(RuntimeError(f"MCP Error ({err.get('code')}): {msg}"))
                        else:
                            fut.set_result(data.get("result", {}))

            except asyncio.CancelledError:
                break
            except Exception:
                break

    async def _listen_stderr(self) -> None:
        """Reads stderr lines from server for debugging."""
        while self.process and self.process.stderr and not self.process.stderr.at_eof():
            try:
                line = await self.process.stderr.readline()
                if not line:
                    break
            except asyncio.CancelledError:
                break
            except Exception:
                break
