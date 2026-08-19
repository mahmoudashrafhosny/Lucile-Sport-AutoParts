"""
Lucile Sport Core Package
=========================
Exports the modular components for each team role:
- Data Engineering (load_catalog, get_dataset_summary)
- AI & Search Engine (SalesRetrievalEngine, normalize_arabic)
- LLM & Prompts (LLMClient, PromptBuilder, SYSTEM_PROMPT)
- Orchestration (RAGPipeline, SessionMemory, is_handoff_requested)
- Frontend UI (create_app, render_product_cards)
"""

from core.config import get_secret
from core.data_engine import load_catalog, get_dataset_summary
from core.retrieval_ai import SalesRetrievalEngine, normalize_arabic, ARABIC_SYNONYM_MAP
from core.llm_prompts import LLMClient, PromptBuilder, SYSTEM_PROMPT
from core.orchestrator import RAGPipeline, SessionMemory, is_handoff_requested
from core.frontend_ui import create_app, render_product_cards

__all__ = [
    "get_secret",
    "load_catalog",
    "get_dataset_summary",
    "SalesRetrievalEngine",
    "normalize_arabic",
    "ARABIC_SYNONYM_MAP",
    "LLMClient",
    "PromptBuilder",
    "SYSTEM_PROMPT",
    "RAGPipeline",
    "SessionMemory",
    "is_handoff_requested",
    "create_app",
    "render_product_cards",
]
