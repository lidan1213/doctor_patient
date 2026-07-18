import logging
import time

from app.core.memory.short_term import ShortTermMemory, TurnEntry
from app.core.memory.long_term import LongTermMemory
from app.core.memory.event_extractor import EventExtractor
from app.core.memory.memory_reader import MemoryReader, MemoryContext

logger = logging.getLogger(__name__)


class MemoryService:
    def __init__(self):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()
        self.event_extractor = EventExtractor()
        self.reader = MemoryReader()

    async def get_context(self, user_id: int, session_id: str, current_query: str) -> MemoryContext:
        return await self.reader.read(user_id, session_id, current_query)

    async def save_turn(
        self,
        user_id: int,
        session_id: str,
        user_message: str,
        assistant_response: str,
        intent: str,
    ) -> None:
        # Layer 1: Short-term memory (Redis) — always try
        try:
            ts = time.time()
            entry = TurnEntry(role="user", content=user_message, intent=intent, timestamp=ts)
            await self.short_term.save(session_id, entry)
            entry_assistant = TurnEntry(role="assistant", content=assistant_response, intent=intent, timestamp=ts)
            await self.short_term.save(session_id, entry_assistant)
        except Exception:
            logger.warning("Failed to save turn to short-term memory", exc_info=True)

        # Layer 2: Long-term memory (ChromaDB) — extract medical events and persist
        if user_id > 0:
            try:
                events = await self.event_extractor.extract(user_message, assistant_response)
                if (events.symptoms or events.diagnosis or events.medications
                        or events.allergies or events.key_events):
                    await self.long_term.save(user_id, events)
            except Exception:
                logger.warning("Failed to save turn to long-term memory", exc_info=True)
