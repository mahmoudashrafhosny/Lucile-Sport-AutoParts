"""
Role 4: Backend & Orchestration Engineer (مهندس الباك إند والربط والتدفق)
File: core/orchestrator.py

Responsibilities:
- End-to-end RAG workflow orchestration.
- Multi-user session management and conversation memory.
- Human support / Maintenance engineer handoff detection.
- Post-generation product extraction and linking for UI cards.
"""

import re
from typing import Any, Dict, List, Optional

from core.llm_prompts import LLMClient, PromptBuilder, SYSTEM_PROMPT
from core.retrieval_ai import SalesRetrievalEngine


# Keywords indicating customer wants to speak with human agent or technician
HANDOFF_PHRASES = (
    "talk to human", "speak to a human", "customer service",
    "خدمة العملاء", "دعم بشري", "موظف", "عايز أكلم حد",
    "عايز اكلم حد", "فني صيانة", "مهندس", "اشتكي", "مشكلة",
)


class SessionMemory:
    """Simple in-memory conversation history and viewed products store."""

    def __init__(self, max_sessions: int = 100) -> None:
        self.max_sessions = max_sessions
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def get_session(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            if len(self.sessions) >= self.max_sessions:
                # Evict oldest session
                self.sessions.pop(next(iter(self.sessions)))
            self.sessions[session_id] = {"messages": [], "viewed_products": []}
        return self.sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str) -> None:
        session = self.get_session(session_id)
        session["messages"].append({"role": role, "content": content})

    def get_history(self, session_id: str, last_n: int = 5) -> List[Dict[str, str]]:
        return self.get_session(session_id)["messages"][-last_n:]

    def track_viewed(self, session_id: str, products: List[Dict[str, Any]]) -> None:
        session = self.get_session(session_id)
        existing_ids = {p.get("product_id") for p in session["viewed_products"]}
        for p in products:
            if p.get("product_id") not in existing_ids:
                session["viewed_products"].append(p)
                existing_ids.add(p.get("product_id"))

    def get_last_viewed(self, session_id: str) -> Optional[Dict[str, Any]]:
        viewed = self.get_session(session_id)["viewed_products"]
        return viewed[-1] if viewed else None


def is_handoff_requested(message: str, force_flag: bool = False) -> bool:
    """Check if the customer query requires human technician intervention."""
    if force_flag:
        return True
    clean_msg = (message or "").lower()
    return any(phrase in clean_msg for phrase in HANDOFF_PHRASES)


class RAGPipeline:
    """Main Orchestrator tying Search, Memory, Context Builder, and LLM together."""

    CATEGORY_QUERY_PATTERN = re.compile(
        r"(what|which).{0,20}\bcategor|list.{0,20}\bcategor|الفئات|الأقسام|أنواع المنتجات",
        re.IGNORECASE,
    )

    def __init__(
        self,
        engine: SalesRetrievalEngine,
        llm_client: Optional[LLMClient] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        memory: Optional[SessionMemory] = None,
    ) -> None:
        self.engine = engine
        self.llm = llm_client or LLMClient()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.memory = memory or SessionMemory()

    def process_message(
        self,
        user_message: str,
        session_id: str,
        request_handoff: bool = False,
        installment_months: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Process an incoming user message through the full RAG pipeline."""
        self.memory.add_message(session_id, "user", user_message)

        # 1. Handle support handoff
        if is_handoff_requested(user_message, request_handoff):
            summary = self._generate_handoff_summary(session_id)
            handoff_reply = "حاضر، تم تسجيل طلبك وجاري تحويلك لأحد مهندسي الصيانة وخدمة العملاء فوراً 📞"
            self.memory.add_message(session_id, "bot", handoff_reply)
            return {
                "type": "handoff",
                "message": handoff_reply,
                "summary_for_agent": summary,
                "products": [],
            }

        # 2. Hybrid Retrieval
        retrieved_products = self._retrieve(user_message)

        # 3. Dynamic context (Installments, Categories, History)
        installment_info = self._calculate_installment_context(session_id, installment_months)
        installment_terms = self.engine.get_installment_terms()
        all_categories = (
            self.engine.get_all_categories()
            if self.CATEGORY_QUERY_PATTERN.search(user_message)
            else None
        )
        chat_history = self.memory.get_history(session_id, last_n=5)

        # 4. Prompt Assembly & LLM Generation
        prompt = self.prompt_builder.build(
            user_message=user_message,
            products=retrieved_products,
            chat_history=chat_history,
            installment_info=installment_info,
            installment_terms=installment_terms,
            all_categories=all_categories,
        )

        response = self.llm.generate(
            system_prompt=self.prompt_builder.system_prompt,
            user_prompt=prompt,
        )
        bot_reply = response["content"]

        # 5. Extract products actually mentioned by the LLM for UI Cards
        matched_products = self._extract_mentioned_products(retrieved_products, bot_reply)

        # 6. Update session state
        self.memory.add_message(session_id, "bot", bot_reply)
        if matched_products:
            self.memory.track_viewed(session_id, matched_products)

        return {
            "type": "response",
            "message": bot_reply,
            "products": matched_products,
            "installment": installment_info,
            "llm_source": response["source"],
        }

    def _retrieve(self, text: str) -> List[Dict[str, Any]]:
        """Perform hybrid search and keyword fallback."""
        if not text.strip():
            return []
        try:
            results = self.engine.hybrid_search(text, top_k=5)
        except Exception as err:
            results = []

        try:
            exact = self.engine.keyword_lookup(text, limit=3)
        except Exception:
            exact = []

        seen_ids = {p.get("product_id") for p in results}
        for item in exact:
            if item.get("product_id") not in seen_ids:
                results.append(item)
                seen_ids.add(item.get("product_id"))
        return results

    def _calculate_installment_context(
        self, session_id: str, months: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """Calculate installment for the last viewed product if requested."""
        if not isinstance(months, int) or months <= 0:
            return None
        last_item = self.memory.get_last_viewed(session_id)
        if not last_item or not last_item.get("final_price"):
            return None
        try:
            return self.engine.calculate_installment(float(last_item["final_price"]), months=months)
        except Exception:
            return None

    def _extract_mentioned_products(
        self, candidates: List[Dict[str, Any]], reply_text: str
    ) -> List[Dict[str, Any]]:
        """Filter retrieved candidates to only those named in the LLM answer."""
        if not candidates or not reply_text:
            return []

        surfaced = []
        for p in candidates:
            title = p.get("title", "").strip()
            if not title:
                continue
            words = title.split()
            first_word = words[0] if words else ""
            if len(first_word) >= 3 and re.search(r"\b" + re.escape(first_word) + r"\b", reply_text, re.IGNORECASE):
                surfaced.append(p)
            elif len(words) >= 2:
                two_words = " ".join(words[:2])
                if len(two_words) >= 4 and re.search(r"\b" + re.escape(two_words) + r"\b", reply_text, re.IGNORECASE):
                    surfaced.append(p)

        return surfaced

    def _generate_handoff_summary(self, session_id: str) -> str:
        """Create a technical briefing summary for maintenance engineers."""
        history = self.memory.get_history(session_id, last_n=10)
        history_text = "\n".join(f"{m['role']}: {m['content']}" for m in history)
        prompt = f"لخص محادثة العميل واحتياجاته أو مشكلته في نقاط سريعة لمهندس الصيانة:\n{history_text}"
        res = self.llm.generate("أنت مساعد تلخيص فني لمهندسي صيانة السيارات.", prompt)
        return res["content"]


# Backwards compatibility aliases
ConversationMemory = SessionMemory
HumanHandoffPolicy = is_handoff_requested
