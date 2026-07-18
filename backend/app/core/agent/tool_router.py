import json
import logging

from app.core.rag.hybrid_retriever import HybridRetriever
from app.core.rag.post_processor import PostProcessor
from app.core.mcp.registry import get_mcp_registry
from app.core.memory.memory_service import MemoryService

logger = logging.getLogger(__name__)

_RAG_COLLECTION = {"doctor": "kb_professional", "patient": "kb_patient"}


class ToolRouter:
    """Dispatches tool calls from the ReAct engine to RAG / MCP / Memory."""

    def __init__(self):
        self.hybrid_retriever = HybridRetriever()
        self.post_processor = PostProcessor()
        self.memory_service = MemoryService()

    async def execute(self, action: str, action_input: dict, *,
                      user_id: int = 0, session_id: str = "",
                      message: str = "", role: str = "patient") -> str:
        try:
            if action == "rag.search":
                return await self._rag_search(action_input, role)
            elif action == "memory.get_context":
                return await self._memory_context(user_id, session_id, message)
            elif action == "finish":
                return ""
            else:
                return await self._mcp_invoke(action, action_input)
        except Exception as e:
            logger.exception(f"Tool execution failed: {action}")
            return f"工具执行异常: {str(e)}"

    async def _rag_search(self, params: dict, role: str) -> str:
        query = params.get("query", "")
        if not query:
            return "错误: rag.search 需要 'query' 参数"

        collection = _RAG_COLLECTION.get(role, "kb_professional")
        bm25_docs, vector_docs = await self.hybrid_retriever.search(
            query=query, collection=collection, top_k=10,
        )
        final_docs = await self.post_processor.process(
            bm25_docs, vector_docs, query, top_k=5,
        )

        if not final_docs:
            return "未找到相关知识库结果"

        parts = []
        for i, doc in enumerate(final_docs[:5]):
            content = doc.get("content", "")[:300]
            meta = doc.get("metadata", {})
            title = meta.get("title", f"文档{i + 1}")
            parts.append(f"[{i + 1}] {title}\n{content}...")

        return "\n\n".join(parts)

    async def _mcp_invoke(self, action: str, params: dict) -> str:
        response = await get_mcp_registry().invoke(action, params)
        if response.status.value == "success":
            return json.dumps(response.data, ensure_ascii=False, indent=2)

        if response.status.value == "timeout":
            return f"[工具超时] '{action}' 执行超时，请简化查询条件或尝试其他方式获取信息"
        return f"[工具错误] '{action}' 执行失败: {response.error}。请尝试使用其他工具或直接回答用户问题"

    async def _memory_context(self, user_id: int, session_id: str, message: str) -> str:
        if user_id <= 0:
            return "用户未认证，无法读取记忆上下文"
        ctx = await self.memory_service.get_context(user_id, session_id, message)
        if ctx and ctx.formatted_prompt:
            return ctx.formatted_prompt
        return "暂无相关记忆上下文"
