import pytest

from app.core.agent.intent import Intent, IntentResult, IntentClassifier


class TestIntentClassifier:
    async def test_classify_consult(self, mock_adapter):
        mock_adapter.generate.return_value = '{"intent": "consult", "confidence": 0.95}'

        classifier = IntentClassifier()
        result = await classifier.classify("headache which department", "patient")

        assert result.intent == Intent.CONSULT
        assert result.confidence == 0.95

    async def test_classify_knowledge_search(self, mock_adapter):
        mock_adapter.generate.return_value = '{"intent": "knowledge_search", "confidence": 0.88}'

        classifier = IntentClassifier()
        result = await classifier.classify("metformin renal impairment dose adjustment", "doctor")

        assert result.intent == Intent.KNOWLEDGE_SEARCH
        assert result.confidence == 0.88

    async def test_invalid_json_falls_back_to_chitchat(self, mock_adapter):
        mock_adapter.generate.return_value = "not valid json"

        classifier = IntentClassifier()
        result = await classifier.classify("hello", "patient")

        assert result.intent == Intent.CHITCHAT
        assert result.confidence == 0.5

    async def test_empty_result_falls_back_to_chitchat(self, mock_adapter):
        mock_adapter.generate.return_value = ""

        classifier = IntentClassifier()
        result = await classifier.classify("", "patient")

        assert result.intent == Intent.CHITCHAT

    async def test_all_intent_values_are_valid(self):
        valid = {"consult", "report_interpret", "rehab", "knowledge_search", "decision_support", "chitchat"}
        assert {i.value for i in Intent} == valid

    async def test_prompt_includes_role(self, mock_adapter):
        mock_adapter.generate.return_value = '{"intent": "chitchat", "confidence": 0.9}'

        classifier = IntentClassifier()
        await classifier.classify("test message", "doctor")

        call_args = mock_adapter.generate.call_args
        user_msg = call_args.kwargs["messages"][1]["content"]
        assert "doctor" in user_msg
        assert "test message" in user_msg
