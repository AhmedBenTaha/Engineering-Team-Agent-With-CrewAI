"""Compatibility fix for CrewAI 1.9.3's legacy HTTPS MCP integration.

CrewAI sanitizes names returned by legacy HTTPS MCP discovery and then uses
that sanitized name both as the LLM-facing tool name and the server-side name.
MCP servers may require their original names (for example,
``resolve-library-id``). Keep the sanitized name for CrewAI, while retaining
the original name in each wrapper for the actual MCP request.

This is deliberately scoped to string-based HTTPS MCP references. Structured
MCP configurations and non-MCP tools continue through CrewAI unchanged.
"""

import asyncio
from typing import Any, cast

from crewai.agent.core import Agent
from crewai.tools.base_tool import BaseTool
from crewai.tools.mcp_tool_wrapper import MCPToolWrapper
from crewai.utilities.string_utils import sanitize_tool_name


def _get_external_mcp_tools(self: Agent, mcp_ref: str) -> list[BaseTool]:
    """Discover HTTPS tools while retaining their original server names."""
    if "#" in mcp_ref:
        server_url, specific_tool = mcp_ref.split("#", 1)
    else:
        server_url, specific_tool = mcp_ref, None

    server_params = {"url": server_url}
    server_name = self._extract_server_name(server_url)
    requested_name = sanitize_tool_name(specific_tool) if specific_tool else None

    async def discover() -> list[Any]:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client

        async with streamablehttp_client(server_url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return list((await session.list_tools()).tools)

    try:
        discovered = asyncio.run(discover())
    except Exception as exc:
        self._logger.log("warning", f"Failed to connect to MCP server {server_url}: {exc}")
        return []

    tools: list[BaseTool] = []
    for mcp_tool in discovered:
        original_name = mcp_tool.name
        llm_name = sanitize_tool_name(original_name)
        if requested_name and llm_name != requested_name:
            continue

        args_schema = None
        if getattr(mcp_tool, "inputSchema", None):
            args_schema = self._json_schema_to_pydantic(llm_name, mcp_tool.inputSchema)
        try:
            wrapper = MCPToolWrapper(
                mcp_server_params=server_params,
                tool_name=llm_name,
                tool_schema={
                    "description": getattr(mcp_tool, "description", ""),
                    "args_schema": args_schema,
                },
                server_name=server_name,
            )
            # MCPToolWrapper uses this attribute in session.call_tool().
            wrapper._original_tool_name = original_name
            tools.append(wrapper)
        except Exception as exc:
            self._logger.log("warning", f"Failed to create MCP tool wrapper for {llm_name}: {exc}")

    if requested_name and not tools:
        self._logger.log(
            "warning", f"Specific tool '{specific_tool}' not found on MCP server: {server_url}"
        )
    return cast(list[BaseTool], tools)


Agent._get_external_mcp_tools = _get_external_mcp_tools
