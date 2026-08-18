import re
from typing import Any, Dict, List, Optional

from core.llm import LLMManager
from core.retrieval import SalesRetrievalEngine

class PromptBuilder:
    SYSTEM_PROMPT = """أنتِ لوسيل، مساعدة المبيعات الذكية لمتجر "لوسيل لقطع غيار السيارات" في مصر (Lucile Auto Parts Egypt).

القواعد:
1. استخدمي فقط بيانات قطع الغيار والمنتجات المقدمة للحقائق والأسعار والتقييمات — لا تخترعي أي معلومة أو قطعة غير موجودة.
2. إذا سأل العميل عن سيارة معينة (مثل: "اسبورتاج" أو "سبورتاج" أو "فيرنا" أو "كورولا" أو "النترا")، اعرضي له قطع الغيار المتاحة لهذه السيارة من قائمة المنتجات المرفقة أدناه (مثل تيل الفرامل، الطنابير، الفلاتر، المساعدين، البوجيهات، السيور) واذكري أسعارها وتقييماتها واسأليه عن القطعة المحددة وسنة الموديل.
3. لو العميل بيسأل عن قطعة محددة مش موجودة في البيانات، قولي "معنديش القطعة دي حالياً أو مش متوفرة في المخزون" بكل أدب واعرضي تحويله لموظف الصيانة لطلبها.
4. تكلمي بأسلوب مصري متخصص وودود خبير بالسيارات في مصر (تويوتا، هيونداي، كيا، نيسان، شيفورليه، فيات، رينو، سكودا، إم جي).
5. اذكري السعر بالجنيه المصري (ج.م) والتقييم دايماً لما بتتكلمي عن أي قطعة غيار.
6. وضحي خطة التقسيط بدقة بالجنيه المصري عند السؤال: (3 شهور بدون فائدة، 6 شهور 5%، 9 شهور 7%، 12 شهر 10%).
7. اقترحي قطع غيار متوافقة وتكميلية (زي فلتر زيت مع الزيت أو تيل مع طنابير) فقط إذا دعمتها البيانات.
8. ردي بنفس لغة العميل — عربي أو إنجليزي."""

    def build_prompt(
        self,
        user_message: str,
        products_found: List[Dict[str, Any]],
        viewed_products: List[Dict[str, Any]],
        chat_history: List[Dict[str, str]],
        installment_info: Optional[Dict[str, Any]] = None,
        all_categories: Optional[List[str]] = None,
        installment_terms: Optional[Dict[int, float]] = None,
    ) -> str:
        return f"""
===============================================
USER MESSAGE: {user_message}
===============================================

POTENTIALLY RELEVANT PRODUCTS FROM SEARCH:
===============================================
{self._format_products(products_found)}

===============================================
FULL CATALOGUE CATEGORY LIST (only when supplied — this is EVERY category
in the store, not just what was retrieved above; use it, and only it, when
the user asks what categories/kinds of products the store carries):
===============================================
{self._format_categories(all_categories)}

===============================================
GENERAL INSTALLMENT TERMS (store policy — always safe to mention, even
without a specific computed plan):
===============================================
{self._format_installment_terms(installment_terms)}

===============================================
INSTALLMENT PLAN COMPUTED FOR A SPECIFIC PRODUCT (only when supplied):
===============================================
{self._format_installment(installment_info)}

===============================================
PRODUCTS USER ALREADY VIEWED:
===============================================
{self._format_viewed(viewed_products)}

===============================================
CONVERSATION HISTORY (last 5 messages):
===============================================
{self._format_history(chat_history)}

===============================================
INSTRUCTIONS:
===============================================
Answer the user's message directly in friendly Egyptian Arabic. Use retrieved products that match the car or part asked about.
State exact prices in EGP (ج.م) and ratings only from the supplied product data. If an installment plan is requested, show its terms accurately.
"""

    def _format_products(self, products: List[Dict[str, Any]]) -> str:
        if not products:
            return "No products found."
        lines = []
        for i, p in enumerate(products, 1):
            price = p.get("final_price", "N/A")
            initial = p.get("initial_price")
            discount = p.get("discount")
            price_line = f"   Price: {price} ج.م"
            if initial and discount:
                price_line += f" (was {initial} ج.م, {discount}% off)"
            lines.append(
                f"{i}. {p.get('title', 'Unknown product')}\n"
                f"{price_line}\n"
                f"   Rating: {p.get('rating', 'N/A')}/5 ({p.get('ratings_count', 0)} reviews)\n"
                f"   Category: {p.get('category', 'N/A')}\n"
                f"   Description: {p.get('product_description', 'N/A')}\n"
                f"   Customers said: {p.get('what_customers_said', 'N/A')}"
            )
        return "\n\n".join(lines)

    def _format_categories(self, categories: Optional[List[str]]) -> str:
        if not categories:
            return "Not requested for this message."
        return ", ".join(categories)

    def _format_installment_terms(self, terms: Optional[Dict[int, float]]) -> str:
        if not terms:
            return "Not available."
        lines = [f"- {months} شهور بفائدة {rate * 100:.0f}%" for months, rate in sorted(terms.items())]
        return "\n".join(lines)

    def _format_installment(self, installment_info: Optional[Dict[str, Any]]) -> str:
        if not installment_info:
            return "No installment plan was supplied."
        return (
            f"{installment_info['months']} شهور -> "
            f"{installment_info['monthly_payment']} ج.م/شهرياً "
            f"(الإجمالي {installment_info['total_with_interest']} ج.م)"
        )

    def _format_viewed(self, viewed: List[Dict[str, Any]]) -> str:
        if not viewed:
            return "User hasn't viewed any products yet."
        return ", ".join(p.get("title", "Unknown") for p in viewed)

    def _format_history(self, history: List[Dict[str, str]]) -> str:
        if not history:
            return "This is the start of the conversation."
        lines = []
        for msg in history[-5:]:
            role = "User" if msg.get("role") == "user" else "Bot"
            lines.append(f"{role}: {msg.get('content', '')}")
        return "\n".join(lines)


class ConversationMemory:
    def __init__(self) -> None:
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def _session(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self._sessions:
            if len(self._sessions) >= 100:
                oldest = next(iter(self._sessions))
                del self._sessions[oldest]
            self._sessions[session_id] = {"messages": [], "viewed_products": []}
        return self._sessions[session_id]

    def save_message(self, session_id: str, role: str, content: str) -> None:
        self._session(session_id)["messages"].append({"role": role, "content": content})

    def get_last_n_messages(self, session_id: str, n: int = 5) -> List[Dict[str, str]]:
        return self._session(session_id)["messages"][-n:]

    def get_all_messages(self, session_id: str) -> List[Dict[str, str]]:
        return self._session(session_id)["messages"]

    def add_viewed_products(self, session_id: str, products: List[Dict[str, Any]]) -> None:
        seen_ids = {p.get("product_id") for p in self._session(session_id)["viewed_products"]}
        for p in products:
            if p.get("product_id") not in seen_ids:
                self._session(session_id)["viewed_products"].append(p)
                seen_ids.add(p.get("product_id"))

    def get_viewed_products(self, session_id: str) -> List[Dict[str, Any]]:
        return self._session(session_id)["viewed_products"]

    def get_last_viewed_product(self, session_id: str) -> Optional[Dict[str, Any]]:
        viewed = self._session(session_id)["viewed_products"]
        return viewed[-1] if viewed else None


class HumanHandoffPolicy:
    _EXPLICIT_REQUEST_PHRASES = (
        "talk to a human", "speak to a human", "talk to a person",
        "speak to a person", "human agent", "live agent",
        "human representative", "customer representative",
        "contact support", "customer service",
        "\u0645\u0648\u0638\u0641 \u062e\u062f\u0645\u0629 \u0627\u0644\u0639\u0645\u0644\u0627\u0621",
        "\u062f\u0639\u0645 \u0628\u0634\u0631\u064a",
        "\u0627\u062a\u0643\u0644\u0645 \u0645\u0639 \u062d\u062f",
        "\u0627\u062a\u0643\u0644\u0645 \u0645\u0639 \u0634\u062e\u0635",
        "\u0627\u0643\u0644\u0645 \u062d\u062f",
        "\u0623\u0643\u0644\u0645 \u062d\u062f",
        "\u0623\u062a\u0643\u0644\u0645 \u0645\u0639 \u062d\u062f",
        "\u0645\u0648\u0638\u0641",
    )

    def evaluate(self, user_message: str, request_handoff: bool = False) -> Optional[str]:
        if request_handoff:
            return "frontend_request"
        normalized = " ".join((user_message or "").casefold().split())
        if any(phrase in normalized for phrase in self._EXPLICIT_REQUEST_PHRASES):
            return "explicit_customer_request"
        return None


class RAGPipeline:
    _CATEGORY_INTENT_RE = re.compile(
        r"(what|which).{0,20}\bcategor(y|ies)\b"
        r"|\blist\b.{0,20}\bcategor(y|ies)\b"
        r"|\bcategories\b.{0,20}\b(you|do you|available)\b"
        r"|\bwhat.{0,15}(kinds?|types?).{0,10}(of )?products?\b"
        r"|\u0627\u0644\u0641\u0626\u0627\u062a\b|\u0627\u0644\u0623\u0642\u0633\u0627\u0645\b"
        r"|\u0623\u0646\u0648\u0627\u0639\s+\u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a",
        re.IGNORECASE,
    )

    def __init__(
        self,
        engine: SalesRetrievalEngine,
        llm_manager: Optional[LLMManager] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        memory: Optional[ConversationMemory] = None,
        handoff_policy: Optional[HumanHandoffPolicy] = None,
    ) -> None:
        self.engine = engine
        self.llm = llm_manager or LLMManager()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.memory = memory or ConversationMemory()
        self.handoff_policy = handoff_policy or HumanHandoffPolicy()

    def process_message(
        self,
        user_message: str,
        session_id: str,
        request_handoff: bool = False,
        installment_months: Optional[int] = None,
    ) -> Dict[str, Any]:
        handoff_reason = self.handoff_policy.evaluate(user_message, request_handoff)
        self.memory.save_message(session_id, "user", user_message)

        if handoff_reason:
            summary = self._generate_handoff_summary(session_id, handoff_reason)
            return {
                "type": "handoff",
                "message": "حاضر، هحولك حالاً لموظف خدمة العملاء لمساعدتك 📞",
                "summary_for_agent": summary,
                "handoff_reason": handoff_reason,
            }

        products = self._retrieve_products(user_message)
        installment_info = self._build_installment_plan(session_id, installment_months)
        installment_terms = self.engine.get_installment_terms()
        all_categories = (
            self.engine.get_all_categories()
            if self._CATEGORY_INTENT_RE.search(user_message or "")
            else None
        )

        chat_history = self.memory.get_last_n_messages(session_id, n=5)
        viewed_products = self.memory.get_viewed_products(session_id)
        prompt = self.prompt_builder.build_prompt(
            user_message=user_message,
            products_found=products,
            viewed_products=viewed_products,
            chat_history=chat_history,
            installment_info=installment_info,
            all_categories=all_categories,
            installment_terms=installment_terms,
        )

        llm_response = self.llm.chat(
            system_prompt=self.prompt_builder.SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        surfaced_products = self._filter_surfaced_products(products, llm_response["content"])

        self.memory.save_message(session_id, "bot", llm_response["content"])
        if surfaced_products:
            self.memory.add_viewed_products(session_id, surfaced_products[:1])

        return {
            "type": "response",
            "message": llm_response["content"],
            "products": surfaced_products,
            "installment": installment_info,
            "llm_source": llm_response["source"],
        }

    def _filter_surfaced_products(
        self, products: List[Dict[str, Any]], llm_content: str
    ) -> List[Dict[str, Any]]:
        """Filter retrieved products to only those actually mentioned in the LLM text."""
        if not products or not llm_content:
            return []
        surfaced = []
        for p in products:
            title = p.get("title", "").strip()
            if not title:
                continue

            words = title.split()
            first_word = words[0] if words else ""

            matched = False
            if len(first_word) >= 3:
                pattern = r"\b" + re.escape(first_word) + r"\b"
                if re.search(pattern, llm_content, re.IGNORECASE):
                    matched = True

            if not matched and len(words) >= 2:
                two_words = " ".join(words[:2])
                if len(two_words) >= 4:
                    pattern = r"\b" + re.escape(two_words) + r"\b"
                    if re.search(pattern, llm_content, re.IGNORECASE):
                        matched = True

            if matched:
                surfaced.append(p)

        return surfaced

    def _retrieve_products(self, user_message: str) -> List[Dict[str, Any]]:
        text = (user_message or "").strip()
        if not text:
            return []
        try:
            results = self.engine.hybrid_search(text, top_k=5)
        except Exception as error:
            print(f"[RAGPipeline] Retrieval failed: {error}")
            results = []
        try:
            exact_matches = self.engine.keyword_lookup(text, limit=3)
        except Exception as error:
            print(f"[RAGPipeline] Keyword lookup failed: {error}")
            exact_matches = []
        seen_ids = {p.get("product_id") for p in results}
        for product in exact_matches:
            if product.get("product_id") not in seen_ids:
                results.append(product)
                seen_ids.add(product.get("product_id"))
        return results

    def _build_installment_plan(
        self, session_id: str, installment_months: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        if (
            not isinstance(installment_months, int)
            or isinstance(installment_months, bool)
            or installment_months <= 0
        ):
            return None
        viewed = self.memory.get_last_viewed_product(session_id)
        if not viewed or not viewed.get("final_price"):
            return None
        return self.engine.calculate_installment(
            float(viewed["final_price"]), months=installment_months
        )

    def _generate_handoff_summary(self, session_id: str, handoff_reason: str) -> str:
        history = self.memory.get_all_messages(session_id)
        summary_prompt = (
            "Summarize this customer conversation for a human agent. "
            "Include the latest request, products viewed, any unresolved support issue, and the "
            f"handoff reason code ({handoff_reason}). Be concise and factual.\n\n"
            f"Conversation:\n{history}"
        )
        result = self.llm.chat(
            "You are a conversation summarizer. Be concise and factual.",
            summary_prompt,
        )
        return result["content"]
