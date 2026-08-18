import os
import re
from typing import Dict, List

import requests
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from core.config import get_secret, logger

class LLMManager:
    FALLBACK_MESSAGE = (
        "بعتذر جداً، الخدمة غير متاحة حالياً بسبب خطأ في الاتصال أو عدم ضبط مفتاح الـ API. "
        "يرجى التأكد من إضافة OPEN_ROUTER_KEY أو GEMINI_API_KEY في ملف .env وتجربة الرسالة مرة تانية 💜"
    )

    def __init__(
        self,
        openrouter_model: str = None,
        gemini_model: str = "gemini-3.6-flash",
        temperature: float = 0.2,
        timeout: int = 10,
    ) -> None:
        self.openrouter_model = openrouter_model or os.getenv(
            "OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free"
        )
        self.gemini_model = gemini_model
        self.openrouter_key = get_secret("OPEN_ROUTER_KEY")
        self.gemini_key = get_secret("GEMINI_API_KEY")
        self.gemini_url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.gemini_model}:generateContent"
        )
        self.primary_llm = ChatOpenAI(
            model=self.openrouter_model,
            openai_api_key=self.openrouter_key or "not-set",
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=temperature,
            max_retries=1,
            timeout=timeout,
        )
        self.usage_log: List[Dict[str, str]] = []

    def chat(self, system_prompt: str, user_prompt: str) -> Dict[str, str]:
        # If Gemini key is set and OpenRouter key is not set, try Gemini first
        if self.gemini_key and not self.openrouter_key:
            try:
                text = self._call_gemini(system_prompt, user_prompt)
                self.usage_log.append({"source": "gemini", "status": "success"})
                if len(self.usage_log) > 500:
                    self.usage_log.pop(0)
                return {"content": text, "source": "gemini", "status": "success"}
            except Exception as e:
                logger.error(f"[LLMManager] Gemini failed: {e}")

        # Otherwise try OpenRouter first
        if self.openrouter_key:
            try:
                messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
                response = self.primary_llm.invoke(messages)
                self.usage_log.append({"source": "openrouter", "status": "success"})
                if len(self.usage_log) > 500:
                    self.usage_log.pop(0)
                return {"content": response.content, "source": "openrouter", "status": "success"}
            except Exception as e:
                logger.error(f"[LLMManager] OpenRouter failed: {e}")

        # Backup try Gemini if not tried yet
        if self.gemini_key:
            try:
                text = self._call_gemini(system_prompt, user_prompt)
                self.usage_log.append({"source": "gemini_backup", "status": "fallback"})
                if len(self.usage_log) > 500:
                    self.usage_log.pop(0)
                return {"content": text, "source": "gemini_backup", "status": "fallback"}
            except Exception as e2:
                logger.error(f"[LLMManager] Gemini backup failed: {e2}")

        self.usage_log.append({"source": "none", "status": "failed"})
        if len(self.usage_log) > 500:
            self.usage_log.pop(0)
        return {"content": self.FALLBACK_MESSAGE, "source": "none", "status": "failed"}

    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        if not self.gemini_key:
            raise RuntimeError("GEMINI_API_KEY is not set.")
        
        models_to_try = [
            "gemini-3.1-flash-lite",
            "gemma-4-31b-it",
            "gemini-3.5-flash",
            "gemini-flash-latest",
            self.gemini_model,
        ]
        last_exception = None

        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_key}"
            gen_config = {
                "temperature": 0.2,
                "maxOutputTokens": 600,
            }
            if not model.startswith("gemma"):
                gen_config["thinkingConfig"] = {"thinkingBudget": 0}

            payload = {
                "contents": [{"parts": [{"text": f"{system_prompt}\n\nUser: {user_prompt}"}]}],
                "generationConfig": gen_config,
            }
            try:
                r = requests.post(url, json=payload, timeout=15)
                r.raise_for_status()
                data = r.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    continue
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if not parts:
                    continue
                
                # Extract non-thought parts
                texts = []
                for p in parts:
                    if p.get("thought"):
                        continue
                    t = p.get("text", "")
                    if t:
                        texts.append(t)
                
                full_text = "\n".join(texts) if texts else parts[0].get("text", "")
                
                # Clean residual thinking text or tags
                full_text = re.sub(r"<think>.*?</think>", "", full_text, flags=re.DOTALL)
                clean_lines = []
                for line in full_text.splitlines():
                    s = line.strip()
                    if s.startswith("Constraint Check") or s.startswith("Thought:") or s.startswith("Reasoning:"):
                        continue
                    clean_lines.append(line)
                
                result_text = "\n".join(clean_lines).strip()
                if result_text:
                    return result_text
            except Exception as e:
                last_exception = e
                logger.warning(f"[LLMManager] Model {model} failed: {e}")
                continue

        if last_exception:
            raise last_exception
        raise ValueError("All Gemini model attempts failed.")
