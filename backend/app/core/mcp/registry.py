import asyncio
import logging

from app.schemas.mcp import ToolDefinition, ToolCallResponse, ToolStatus
from app.core.mcp.base import BaseMCPModule

logger = logging.getLogger(__name__)


class MCPToolRegistry:
    def __init__(self):
        self._modules: dict[str, BaseMCPModule] = {}
        self._tool_index: dict[str, str] = {}

    def register(self, module: BaseMCPModule) -> None:
        self._modules[module.module_name] = module
        for tool in module.get_tools():
            self._tool_index[tool.name] = module.module_name
        logger.info(f"MCP module '{module.module_name}' registered with {len(module.get_tools())} tools")

    def get_all_tools(self) -> list[ToolDefinition]:
        tools: list[ToolDefinition] = []
        for module in self._modules.values():
            tools.extend(module.get_tools())
        return tools

    async def invoke(self, tool_name: str, params: dict) -> ToolCallResponse:
        module_name = self._tool_index.get(tool_name)
        if module_name is None:
            logger.warning(f"MCP tool not found: '{tool_name}'")
            return ToolCallResponse(
                tool=tool_name,
                status=ToolStatus.ERROR,
                error=f"Unknown tool: '{tool_name}'. Available: {list(self._tool_index.keys())}",
            )

        module = self._modules[module_name]
        # Retry once on timeout; errors are programmatic and won't change on retry
        max_attempts = 2

        for attempt in range(max_attempts):
            try:
                result = await asyncio.wait_for(
                    module.execute(tool_name, params),
                    timeout=module.timeout,
                )
                return result

            except asyncio.TimeoutError:
                if attempt < max_attempts - 1:
                    logger.warning(
                        f"MCP tool '{tool_name}' timed out (attempt {attempt + 1}/{max_attempts}), retrying..."
                    )
                    continue
                logger.error(f"MCP tool '{tool_name}' timed out after {module.timeout}s × {max_attempts}")
                return ToolCallResponse(
                    tool=tool_name,
                    status=ToolStatus.TIMEOUT,
                    error=f"Tool '{tool_name}' timed out after {module.timeout}s × {max_attempts} attempts",
                )

            except Exception as e:
                logger.error(f"MCP tool '{tool_name}' execution failed: {e}", exc_info=True)
                return ToolCallResponse(
                    tool=tool_name,
                    status=ToolStatus.ERROR,
                    error=str(e),
                )

        # Should not reach here
        return ToolCallResponse(
            tool=tool_name,
            status=ToolStatus.ERROR,
            error=f"All {max_attempts} attempts for '{tool_name}' failed",
        )


_mcp_registry: MCPToolRegistry | None = None


def get_mcp_registry() -> MCPToolRegistry:
    global _mcp_registry
    if _mcp_registry is None:
        _mcp_registry = MCPToolRegistry()
        from app.core.mcp.patient_record import PatientRecordModule
        from app.core.mcp.identity import IdentityModule
        _mcp_registry.register(PatientRecordModule())
        _mcp_registry.register(IdentityModule())
    return _mcp_registry
