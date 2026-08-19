"""
Role 3: LLM & Prompt Engineer (مهندس النماذج اللغوية وهندسة الأوامر)
File: core/llm_prompts.py

Responsibilities:
- Prompt Engineering & System Persona (Lucile Sport Sales Representative).
- Context Assembly & Anti-Hallucination Grounding.
- Multi-Model LLM Client (Google Gemini API & OpenRouter) with automatic fallback.
"""

import os
import re
from typing import Any, Dict, List, Optional
import requests

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from core.config import get_secret, logger


# Persona & Core System Prompt
SYSTEM_PROMPT = """أنتِ لوسيل، مساعدة المبيعات الذكية لمتجر "لوسيل لقطع غيار السيارات" في مصر (Lucile Auto Parts Egypt).

القواعد الأساسية:
1. استخدمي فقط بيانات قطع الغيار والمنتجات المقدمة للحقائق والأسعار والتقييمات — لا تخترعي أي معلومة أو قطعة غير موجودة.
2. إذا سأل العميل عن سيارة معينة (مثل: "اسبورتاج" أو "فيرنا" أو "كورولا" أو "النترا" أو "صني")، اعرضي له قطع الغيار المتوفرة لهذه السيارة من قائمة المنتجات المرفقة (مثل تيل الفرامل، الطنابير، الفلاتر، المساعدين، البوجيهات) واذكري أسعارها وتقييماتها واسأليه عن القطعة وسنة الموديل.
3. إذا سأل العميل عن قطعة غير متوفرة في البيانات، قولي بذوق: "معنديش القطعة دي حالياً في المخزون" واعرضي تحويله لموظف الصيانة أو خدمة العملاء لتوفيرها.
4. أسلوبك في الحوار مصري مهني، ودود، وخبير بمصطلحات السيارات وقطع الغيار في مصر.
5. اذكري السعر دائماً بالجنيه المصري (ج.م) والتقييم عند التحدث عن أي قطعة.
6. وضحي خطط التقسيط بدقة: (3 شهور بدون فوائد 0%، 6 شهور 5%، 9 شهور 7%، 12 شهر 10%).
7. ردي بنفس لغة العميل (عربي أو إنجليزي)."""


class PromptBuilder:
    """Constructs dynamic, grounded prompt payloads for LLM inference."""

    def __init__(self, system_prompt: str = SYSTEM_PROMPT) -> None:
        self.system_prompt = system_prompt

    def build(
        self,
        user_message: str,
        products: List[Dict[str, Any]],
        chat_history: List[Dict[str, str]],
        installment_info: Optional[Dict[str, Any]] = None,
        installment_terms: Optional[Dict[int, float]] = None,
        all_categories: Optional[List[str]] = None,
        viewed_products: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Assemble retrieved context, history, and instructions into a clean user prompt."""
        sections = [f"USER QUERY: {user_message}\n"]

        # 1. Retrieved Products
        if products:
            prod_lines = ["MATCHING PRODUCTS FROM CATALOG:"]
            for i, p in enumerate(products, 1):
                price = p.get("final_price", "N/A")
                initial = p.get("initial_price")
                discount = p.get("discount")
                price_str = f"{price} ج.م"
                if initial and discount:
                    price_str += f" (السابق: {initial} ج.م - خصم {discount}%)"

                prod_lines.append(
                    f"{i}. {p.get('title', 'Unknown')}\n"
                    f"   - السعر: {price_str}\n"
                    f"   - التقييم: {p.get('rating', 'N/A')}/5 ({p.get('ratings_count', 0)} تقييم)\n"
                    f"   - القسم: {p.get('category', 'عام')}\n"
                    f"   - الوصف: {p.get('product_description', 'لا يوجد وصف')}"
                )
            sections.append("\n".join(prod_lines))
        else:
            sections.append("MATCHING PRODUCTS: لم يتم العثور على قطع غيار مطابقة في قاعدة البيانات.")

        # 2. General Installment Terms
        if installment_terms:
            terms_str = "STORE INSTALLMENT POLICY:\n" + "\n".join(
                f"- تقسيط {m} شهور: فائدة {int(rate * 100)}%" for m, rate in sorted(installment_terms.items())
            )
            sections.append(terms_str)

        # 3. Computed Installment for specific item
        if installment_info:
            sections.append(
                f"CALCULATED INSTALLMENT PLAN:\n"
                f"- مدة التقسيط: {installment_info['months']} شهور\n"
                f"- القسط الشهري: {installment_info['monthly_payment']} ج.م/شهرياً\n"
                f"- الإجمالي بعد الفائدة: {installment_info['total_with_interest']} ج.م"
            )

        # 4. Catalog categories (if user asked about available categories)
        if all_categories:
            sections.append(f"ALL STORE CATEGORIES: {', '.join(all_categories)}")

        # 5. Recent conversation history
        if chat_history:
            history_lines = ["RECENT CONVERSATION:"]
            for msg in chat_history[-5:]:
                sender = "العميل" if msg.get("role") == "user" else "لوسيل"
                history_lines.append(f"{sender}: {msg.get('content', '')}")
            sections.append("\n".join(history_lines))

        sections.append(
            "INSTRUCTIONS:\n"
            "ردي على استفسار العميل مباشرة باللهجة المصرية الودودة بالاعتماد حصراً على المنتجات المرفقة أعلاه."
        )

        return "\n\n".join(sections)


class LLMClient:
    """Unified LLM client supporting Google Gemini and OpenRouter with automatic failover."""

    def __init__(
        self,
        gemini_model: str = "gemini-3.6-flash",
        openrouter_model: str = "meta-llama/llama-3.3-70b-instruct:free",
        temperature: float = 0.2,
    ) -> None:
        self.gemini_key = get_secret("GEMINI_API_KEY")
        self.openrouter_key = get_secret("OPEN_ROUTER_KEY")
        self.gemini_model = gemini_model
        self.openrouter_model = openrouter_model
        self.temperature = temperature

        # OpenRouter LangChain client
        self.openrouter_client = ChatOpenAI(
            model=self.openrouter_model,
            openai_api_key=self.openrouter_key or "not-set",
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=temperature,
            max_retries=1,
            timeout=12,
        )

    def generate(self, system_prompt: str, user_prompt: str) -> Dict[str, str]:
        """Generate response with primary provider and fallback protection."""
        # 1. Try Gemini first if key exists
        if self.gemini_key:
            try:
                reply = self._call_gemini(system_prompt, user_prompt)
                return {"content": reply, "source": "gemini", "status": "success"}
            except Exception as e:
                logger.warning(f"Gemini API attempt failed: {e}. Trying fallback...")

        # 2. Try OpenRouter as backup
        if self.openrouter_key:
            try:
                messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
                res = self.openrouter_client.invoke(messages)
                return {"content": res.content, "source": "openrouter", "status": "success"}
            except Exception as e:
                logger.error(f"OpenRouter fallback failed: {e}")

        # Fallback friendly message if no API keys work
        fallback_text = (
            "أهلاً بك في لوسيل سبورت! 🚗\n"
            "حالياً الخدمة بتواجه بطء في الاتصال بالذكاء الاصطناعي. "
            "تقدر تستعرض قطع الغيار المتاحة أو تطلب التحدث مع فني الصيانة لمساعدتك فوراً!"
        )
        return {"content": fallback_text, "source": "fallback", "status": "offline"}

    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """Call Google Gemini REST endpoint directly."""
        models = [
            "gemini-3.1-flash-lite",
            "gemma-4-31b-it",
            "gemini-3.5-flash",
            self.gemini_model,
        ]

        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_key}"
            payload = {
                "contents": [{"parts": [{"text": f"{system_prompt}\n\nUser: {user_prompt}"}]}],
                "generationConfig": {"temperature": self.temperature, "maxOutputTokens": 600},
            }

            try:
                res = requests.post(url, json=payload, timeout=12)
                res.raise_for_status()
                data = res.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    continue

                parts = candidates[0].get("content", {}).get("parts", [])
                # Collect non-thinking text parts
                text_segments = [p.get("text", "") for p in parts if not p.get("thought") and p.get("text")]
                full_text = "\n".join(text_segments) if text_segments else (parts[0].get("text", "") if parts else "")

                # Clean thinking tokens or meta commentary
                cleaned = re.sub(r"<think>.*?</think>", "", full_text, flags=re.DOTALL).strip()
                if cleaned:
                    return cleaned
            except Exception as ex:
                logger.debug(f"Gemini model {model} error: {ex}")
                continue

        raise RuntimeError("All Gemini candidate models returned empty or failed.")


# Backwards compatibility aliases
LLMManager = LLMClient
