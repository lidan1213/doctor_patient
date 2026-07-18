from dataclasses import dataclass
from enum import Enum

from app.core.model_adapter.adapter_registry import get_adapter_registry


class Intent(str, Enum):
    CONSULT = "consult"
    REPORT_INTERPRET = "report_interpret"
    REHAB = "rehab"
    KNOWLEDGE_SEARCH = "knowledge_search"
    DECISION_SUPPORT = "decision_support"
    CHITCHAT = "chitchat"


@dataclass
class IntentResult:
    intent: Intent
    confidence: float


INTENT_PROMPT = """你是医疗意图分类专家。根据用户输入和角色，将意图归类为以下之一：
- consult: 诊前咨询、症状问诊、科室导诊
- report_interpret: 医学报告解读、化验单分析
- rehab: 诊后康复指导、用药管理
- knowledge_search: 医学知识检索、文献查询
- decision_support: 临床决策支持、病例分析
- chitchat: 闲聊、问候、非医疗问题

输出JSON格式: {"intent": "<类型>", "confidence": <0-1之间的数值>}"""


class IntentClassifier:
    async def classify(self, message: str, role: str) -> IntentResult:
        adapter = get_adapter_registry()
        result = await adapter.generate(
            messages=[
                {"role": "system", "content": INTENT_PROMPT},
                {"role": "user", "content": f"角色: {role}\n用户消息: {message}"},
            ],
            temperature=0.1,
            max_tokens=128,
        )
        try:
            import json
            data = json.loads(result.strip().removeprefix("```json").removesuffix("```"))
            return IntentResult(intent=Intent(data["intent"]), confidence=float(data["confidence"]))
        except Exception:
            return IntentResult(intent=Intent.CHITCHAT, confidence=0.5)
