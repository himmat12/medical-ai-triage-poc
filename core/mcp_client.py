import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

from pipecat_flows.types import FlowsFunctionSchema

from typing import Dict, Any, List, Optional
from loguru import logger


class MCPClient:
    """
    Enhanced class that integrates MCP client functionality
    """

    def __init__(self):
        self.mcp_session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.available_tools = []
        self.is_initialized = False

    async def initialize(self, server_script_path: str):
        """
        Initialize MCP client connection to your server
        """
        try:
            server_params = StdioServerParameters(
                command="python",
                args=[server_script_path],
                env=os.environ.copy(),
            )

            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            stdio, write = stdio_transport
            self.mcp_session = await self.exit_stack.enter_async_context(
                ClientSession(stdio, write)
            )

            await self.mcp_session.initialize()

            # List available tools
            response = await self.mcp_session.list_tools()
            self.available_tools = response.tools

            logger.info(f"MCP Server connected with {len(self.available_tools)} tools")

            self.is_initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}")

            self.is_initialized = False
            return False

    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        """
        Call an MCP tool and return the result
        """
        if not self.mcp_session:
            raise RuntimeError("MCP session not initialized")

        try:
            result = await self.mcp_session.call_tool(tool_name, tool_args)
            return result.content[0].text if result.content else None
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            raise

    def get_tools_info(self) -> Dict[str, Any]:
        """
        Get detailed information about available tools
        """
        tools_info = {
            "total_tools": len(self.available_tools),
            "tool_categories": {},
            "tools": [],
        }

        for tool in self.available_tools:
            tool_info = {
                "name": tool.name,
                "description": tool.description,
                "parameters": list(tool.inputSchema.get("properties", {}).keys()),
                "required_params": tool.inputSchema.get("required", []),
                "optional_params": [],
            }

            # Calculate optional parameters
            all_params = set(tool.inputSchema.get("properties", {}).keys())
            required_params = set(tool.inputSchema.get("required", []))
            tool_info["optional_params"] = list(all_params - required_params)

            tools_info["tools"].append(tool_info)

        return tools_info

    async def cleanup(self):
        """Clean up MCP resources"""
        try:
            await self.exit_stack.aclose()
            self.is_initialized = False
            logger.info("MCP client cleaned up successfully")
        except Exception as e:
            logger.warning(f"Error during MCP cleanup: {e}")


mcp_client = MCPClient()
