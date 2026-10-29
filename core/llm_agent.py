"""LLM AI Agent with autonomous Model Context Protocol (MCP) tool-calling support."""

from __future__ import annotations
import asyncio
import json
import re
import urllib.error
import urllib.request
from typing import Any, Callable
from config.loader import LLMConfig
from core.server_manager import MCPServerManager


class AIToolAgent:
    """Orchestrates conversations with LLMs and executes tool calls via the MCP Server Manager."""

    def __init__(self, config: LLMConfig, server_manager: MCPServerManager):
        self.config = config
        self.server_manager = server_manager
        self.conversation_history: list[dict[str, Any]] = []

    def format_tools_schema(self) -> list[dict[str, Any]]:
        """Converts connected MCP tools to standard OpenAI/Ollama function calling schema."""
        tools = self.server_manager.get_all_tools()
        formatted = []
        for t in tools:
            name = t.get("name", "")
            if not name:
                continue
            desc = t.get("description", "")
            schema = t.get("inputSchema", {})
            if not isinstance(schema, dict) or "type" not in schema:
                schema = {"type": "object", "properties": {}}

            formatted.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": desc,
                    "parameters": schema,
                },
            })
        return formatted

    async def process_user_message(
        self,
        user_text: str,
        on_status: Callable[[str], None] | None = None,
    ) -> str:
        """Processes a user input message, handling model communication and tool executions."""
        self.conversation_history.append({"role": "user", "content": user_text})

        provider = (self.config.provider or "mock").lower()

        if provider == "mock":
            return await self._handle_mock(user_text, on_status)
        elif provider == "ollama":
            return await self._handle_ollama(on_status)
        elif provider == "openai":
            return await self._handle_openai(on_status)
        else:
            return f"Unsupported LLM provider: '{provider}'. Supported: ollama, openai, mock."

    async def _handle_mock(
        self,
        user_text: str,
        on_status: Callable[[str], None] | None = None,
    ) -> str:
        """Built-in mock provider for offline demonstration and testing."""
        lower = user_text.lower()

        # Check for math evaluation intent
        math_match = re.search(r"(\d+[\s\+\-\*\/\%\^]+\d+[\d\s\+\-\*\/\%\^]*)", user_text)
        if math_match or any(w in lower for w in ("math", "calculate", "compute", "evaluate")):
            expr = math_match.group(1).strip() if math_match else "42 * 2"
            if on_status:
                on_status(f"Executing MCP tool 'math_eval' with expression: '{expr}'...")
            try:
                res = await self.server_manager.call_tool("math_eval", {"expression": expr})
                ans = self._extract_tool_text(res)
                reply = f"According to the MCP math_eval tool, the result is: {ans}"
            except Exception as e:
                reply = f"Attempted to evaluate '{expr}' via MCP, but encountered: {e}"
            self.conversation_history.append({"role": "assistant", "content": reply})
            return reply

        # Check for system info intent
        if any(w in lower for w in ("system", "os", "platform", "specs", "version", "environment")):
            if on_status:
                on_status("Executing MCP tool 'system_info'...")
            try:
                res = await self.server_manager.call_tool("system_info", {})
                info = self._extract_tool_text(res)
                reply = f"Here is the system information from MCP:\n{info}"
            except Exception as e:
                reply = f"Attempted to retrieve system info via MCP, but encountered: {e}"
            self.conversation_history.append({"role": "assistant", "content": reply})
            return reply

        # Check for echo intent
        if lower.startswith("echo ") or "echo" in lower:
            msg = user_text[5:].strip() if lower.startswith("echo ") else user_text
            if on_status:
                on_status(f"Executing MCP tool 'echo'...")
            try:
                res = await self.server_manager.call_tool("echo", {"message": msg})
                echoed = self._extract_tool_text(res)
                reply = f"MCP Echo returned: {echoed}"
            except Exception as e:
                reply = f"Attempted echo via MCP, but encountered: {e}"
            self.conversation_history.append({"role": "assistant", "content": reply})
            return reply

        # General response explaining available tools
        tools = self.server_manager.get_all_tools()
        tool_names = [t.get("name") for t in tools if t.get("name")]
        reply = (
            f"I am your MCP AI assistant. Connected tools available: {', '.join(tool_names) if tool_names else 'None'}.\n"
            "Try asking me to calculate an expression or inspect your system info!"
        )
        self.conversation_history.append({"role": "assistant", "content": reply})
        return reply

    async def _handle_ollama(
        self,
        on_status: Callable[[str], None] | None = None,
    ) -> str:
        """Executes tool-calling interaction with a local Ollama instance."""
        endpoint = f"{self.config.base_url.rstrip('/')}/api/chat"
        tools = self.format_tools_schema()

        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": self.conversation_history,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools

        try:
            resp_data = await asyncio.to_thread(self._http_post_json, endpoint, payload)
        except urllib.error.URLError as e:
            return (
                f"[bold yellow]Ollama Unreachable:[/] Could not connect to Ollama at {self.config.base_url} ({e}).\n"
                "Ensure Ollama is running (`ollama serve`) or switch provider in settings.yaml."
            )
        except Exception as e:
            return f"[bold red]Ollama Error:[/] {e}"

        msg = resp_data.get("message", {})
        tool_calls = msg.get("tool_calls", [])

        if not tool_calls:
            content = msg.get("content", "(No content returned)")
            self.conversation_history.append({"role": "assistant", "content": content})
            return content

        # Process tool calls
        self.conversation_history.append(msg)

        for call in tool_calls:
            func = call.get("function", {})
            name = func.get("name")
            args = func.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}

            if on_status:
                on_status(f"Executing MCP tool '{name}' with arguments: {args}...")

            try:
                result = await self.server_manager.call_tool(name, args)
                tool_output = self._extract_tool_text(result)
            except Exception as e:
                tool_output = f"Tool execution failed: {e}"

            self.conversation_history.append({
                "role": "tool",
                "content": str(tool_output),
            })

        # Final synthesis call back to Ollama
        final_payload = {
            "model": self.config.model,
            "messages": self.conversation_history,
            "stream": False,
        }
        try:
            final_resp = await asyncio.to_thread(self._http_post_json, endpoint, final_payload)
            final_msg = final_resp.get("message", {})
            final_content = final_msg.get("content", "(Synthesis complete)")
            self.conversation_history.append({"role": "assistant", "content": final_content})
            return final_content
        except Exception as e:
            return f"Tool call succeeded, but synthesis request failed: {e}"

    async def _handle_openai(
        self,
        on_status: Callable[[str], None] | None = None,
    ) -> str:
        """Executes tool-calling interaction with an OpenAI-compatible endpoint."""
        endpoint = f"{self.config.base_url.rstrip('/')}/v1/chat/completions"
        tools = self.format_tools_schema()

        headers = {}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": self.conversation_history,
        }
        if tools:
            payload["tools"] = tools

        try:
            resp_data = await asyncio.to_thread(self._http_post_json, endpoint, payload, headers=headers)
        except urllib.error.URLError as e:
            return f"[bold yellow]API Unreachable:[/] Failed connecting to {endpoint}: {e}"
        except Exception as e:
            return f"[bold red]API Error:[/] {e}"

        choices = resp_data.get("choices", [])
        if not choices:
            return "No response choices returned by model."

        message = choices[0].get("message", {})
        tool_calls = message.get("tool_calls", [])

        if not tool_calls:
            content = message.get("content", "")
            self.conversation_history.append({"role": "assistant", "content": content})
            return content

        self.conversation_history.append(message)

        for call in tool_calls:
            call_id = call.get("id", "call_1")
            func = call.get("function", {})
            name = func.get("name")
            raw_args = func.get("arguments", "{}")
            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

            if on_status:
                on_status(f"Executing MCP tool '{name}'...")

            try:
                result = await self.server_manager.call_tool(name, args)
                tool_output = self._extract_tool_text(result)
            except Exception as e:
                tool_output = f"Tool execution failed: {e}"

            self.conversation_history.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": str(tool_output),
            })

        final_payload = {
            "model": self.config.model,
            "messages": self.conversation_history,
        }
        try:
            final_resp = await asyncio.to_thread(self._http_post_json, endpoint, final_payload, headers=headers)
            final_choices = final_resp.get("choices", [])
            final_content = final_choices[0].get("message", {}).get("content", "") if final_choices else ""
            self.conversation_history.append({"role": "assistant", "content": final_content})
            return final_content
        except Exception as e:
            return f"Tool call succeeded, but synthesis request failed: {e}"

    def _extract_tool_text(self, tool_result: dict[str, Any]) -> str:
        """Extracts human-readable text from standard MCP tool call results."""
        if not isinstance(tool_result, dict):
            return str(tool_result)
        content_items = tool_result.get("content", [])
        texts = []
        for item in content_items:
            if isinstance(item, dict) and item.get("type") == "text":
                texts.append(item.get("text", ""))
            else:
                texts.append(str(item))
        return "\n".join(texts) if texts else json.dumps(tool_result)

    def _http_post_json(
        self,
        url: str,
        data: dict[str, Any],
        headers: dict[str, str] | None = None,
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        """Synchronous HTTP JSON POST helper executed in a thread pool."""
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)

        payload_bytes = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=payload_bytes, headers=req_headers, method="POST")

        with urllib.request.urlopen(req, timeout=timeout) as response:
            resp_bytes = response.read()
            return json.loads(resp_bytes.decode("utf-8"))
