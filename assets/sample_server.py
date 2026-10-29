#!/usr/bin/env python3
"""Standalone sample Model Context Protocol (MCP 2024-11-05) server over stdio."""

import ast
import json
import operator
import platform
import sys
from datetime import datetime
from typing import Any

# Safe math evaluator using Python's AST
_MATH_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node: ast.AST) -> float | int:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _MATH_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return _MATH_OPERATORS[op_type](left, right)
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _MATH_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = _safe_eval(node.operand)
        return _MATH_OPERATORS[op_type](operand)
    raise ValueError(f"Unsupported expression component: {type(node).__name__}")


def evaluate_math(expr_str: str) -> str:
    try:
        parsed = ast.parse(expr_str.strip(), mode="eval")
        result = _safe_eval(parsed)
        return str(result)
    except Exception as e:
        return f"Error evaluating '{expr_str}': {e}"


def handle_initialize(req_id: Any) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
                "prompts": {"listChanged": False},
            },
            "serverInfo": {
                "name": "sample-python-server",
                "version": "1.0.0",
            },
        },
    }


def handle_tools_list(req_id: Any) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "tools": [
                {
                    "name": "echo",
                    "description": "Echoes back the provided text message.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Text message to echo back",
                            }
                        },
                        "required": ["message"],
                    },
                },
                {
                    "name": "system_info",
                    "description": "Returns current platform, OS, architecture, and timestamp.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                    },
                },
                {
                    "name": "math_eval",
                    "description": "Evaluates a safe mathematical expression (e.g. '42 * 2 + 10').",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "Mathematical expression string",
                            }
                        },
                        "required": ["expression"],
                    },
                },
            ]
        },
    }


def handle_tools_call(req_id: Any, params: dict[str, Any]) -> dict[str, Any]:
    name = params.get("name")
    args = params.get("arguments", {})

    if name == "echo":
        msg = args.get("message", "")
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": f"Echo: {msg}"}]
            },
        }

    if name == "system_info":
        info = (
            f"OS / Platform: {platform.platform()}\n"
            f"Architecture: {platform.machine()}\n"
            f"Python Version: {platform.python_version()}\n"
            f"Server Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": info}]
            },
        }

    if name == "math_eval":
        expr = args.get("expression", "")
        res = evaluate_math(expr)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": res}]
            },
        }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": -32601,
            "message": f"Tool '{name}' not found.",
        },
    }


def handle_resources_list(req_id: Any) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "resources": [
                {
                    "uri": "memo://welcome",
                    "name": "Welcome Memo",
                    "description": "Welcome guide for Model Context Protocol in terminal",
                    "mimeType": "text/plain",
                }
            ]
        },
    }


def handle_resources_read(req_id: Any, params: dict[str, Any]) -> dict[str, Any]:
    uri = params.get("uri")
    if uri == "memo://welcome":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "contents": [
                    {
                        "uri": "memo://welcome",
                        "mimeType": "text/plain",
                        "text": "Welcome to Model Context Protocol (MCP) in your terminal client!",
                    }
                ]
            },
        }
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": -32602,
            "message": f"Resource with URI '{uri}' not found.",
        },
    }


def handle_prompts_list(req_id: Any) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "prompts": [
                {
                    "name": "system_check",
                    "description": "Template prompt to request system health check",
                }
            ]
        },
    }


def main() -> None:
    """Reads line-delimited JSON-RPC 2.0 messages from stdin."""
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        resp = None

        if method == "initialize":
            resp = handle_initialize(req_id)
        elif method == "notifications/initialized":
            # Notification: no response required
            continue
        elif method == "tools/list":
            resp = handle_tools_list(req_id)
        elif method == "tools/call":
            resp = handle_tools_call(req_id, params)
        elif method == "resources/list":
            resp = handle_resources_list(req_id)
        elif method == "resources/read":
            resp = handle_resources_read(req_id, params)
        elif method == "prompts/list":
            resp = handle_prompts_list(req_id)
        else:
            if req_id is not None:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method '{method}' not found.",
                    },
                }

        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
