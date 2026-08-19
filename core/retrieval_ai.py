"""
Role 2: AI & Search Retrieval Engineer (مهندس البحث والذكاء الاصطناعي)
File: core/retrieval_ai.py

Responsibilities:
- Hybrid Search (Dense FAISS Vector Search + Sparse BM25 Lexical Search).
- Egyptian automotive dialect normalization and synonym expansion.
- Reciprocal Rank Fusion (RRF) for result re-ranking.
- Product recommendation engine and installment calculations.
"""

import os
import pickle
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from core.config import (
    FAISS_INDEX_PATH,
    BM25_INDEX_PATH,
    INSTALLMENT_RATES,
    RRF_K,
    logger,
)

# Common Egyptian car dialect terms & spare parts synonym mapping
ARABIC_SYNONYM_MAP: Dict[str, List[str]] = {
    # Car Models
    "اسبورتاج": ["سبورتاج", "sportage", "كيا"],
    "سبورتاج": ["اسبورتاج", "sportage", "كيا"],
    "sportage": ["سبورتاج", "اسبورتاج", "كيا"],
    "النترا": ["elantra", "إلنترا", "هيونداي"],
    "إلنترا": ["elantra", "النترا", "هيونداي"],
    "elantra": ["النترا", "إلنترا", "هيونداي"],
    "فيرنا": ["verna", "هيونداي"],
    "verna": ["فيرنا", "هيونداي"],
    "كورولا": ["corolla", "تويوتا"],
    "corolla": ["كورولا", "تويوتا"],
    "توسان": ["tucson", "هيونداي"],
    "tucson": ["توسان", "هيونداي"],
    "سيراتو": ["cerato", "كيا"],
    "cerato": ["سيراتو", "كيا"],
    "اوكتافيا": ["octavia", "أوكتافيا", "سكودا"],
    "أوكتافيا": ["octavia", "اوكتافيا", "سكودا"],
    "octavia": ["اوكتافيا", "سكودا"],
    "لانوس": ["lanos", "دايو", "شيفورليه"],
    "lanos": ["لانوس", "شيفورليه"],
    "نوبيرا": ["nubira", "دايو"],
    "nubira": ["نوبيرا"],
    "اوبترا": ["optra", "أوبترا", "شيفورليه"],
    "optra": ["اوبترا", "شيفورليه"],
    "صني": ["sunny", "نيسان"],
    "sunny": ["صني", "نيسان"],
    "لوجان": ["logan", "رينو"],
    "logan": ["لوجان", "رينو"],
    "تيبو": ["tipo", "فيات"],
    "tipo": ["تيبو", "فيات"],

    # Spare Parts Terms
    "تيل": ["فرامل", "تيل"],
    "فرامل": ["تيل", "طنابير"],
    "طنبوره": ["طنابير", "فرامل"],
    "طنابير": ["طنبوره", "فرامل"],
    "مساعد": ["مساعدين", "عفشه"],
    "مساعدين": ["مساعد", "عفشه"],
    "بوجيه": ["بوجيهات", "اشعال"],
    "بوجيهات": ["بوجيه", "اشعال"],
    "موبينه": ["مباين", "كويل"],
    "كاتينه": ["سير", "شداد"],
    "دبرياج": ["ديسك", "اسطوانه", "بليه"],
    "كاوتش": ["اطارات", "فرده", "كفر"],
    "بطاريه": ["بطاريات", "كلورايد", "فارتا"],
    "فانوس": ["فوانيس", "لمبات", "ليد"],
}

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*|[\u0621-\u064A0-9]+")
_DIACRITICS_PATTERN = re.compile(r"[\u064B-\u065F\u0640]")


def normalize_arabic(text: str) -> str:
    """Normalize Arabic text (remove diacritics, unify alefs and teh marbuta)."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", str(text)).lower()
    text = _DIACRITICS_PATTERN.sub("", text)
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ة", "ه").replace("ى", "ي")
    return re.sub(r"\s+", " ", text).strip()


def tokenize_and_expand(text: str) -> List[str]:
    """Tokenize text and expand words with relevant Egyptian automotive synonyms."""
    norm = normalize_arabic(text)
    tokens = _TOKEN_PATTERN.findall(norm)
    expanded = []

    for t in tokens:
        expanded.append(t)
        # Strip Arabic definite article 'الـ'
        if t.startswith("ال") and len(t) > 3:
            root = t[2:]
            expanded.append(root)
            if root in ARABIC_SYNONYM_MAP:
                expanded.extend(ARABIC_SYNONYM_MAP[root])
        if t in ARABIC_SYNONYM_MAP:
            expanded.extend(ARABIC_SYNONYM_MAP[t])

    # Remove duplicates while preserving insertion order
    return list(dict.fromkeys(expanded))


class SalesRetrievalEngine:
    """Hybrid search engine combining FAISS (Dense embeddings) and BM25 (Sparse keyword)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model: Optional[SentenceTransformer] = None
        self.faiss_index: Optional[faiss.IndexFlatL2] = None
        self.bm25: Optional[BM25Okapi] = None
        self.products: List[Dict[str, Any]] = []
        self.rich_texts: List[str] = []
        self.categories: List[str] = []
        self._is_ready = False

    @property
    def model(self) -> SentenceTransformer:
        """Lazy loader for the SentenceTransformer model."""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _build_product_text(self, p: Dict[str, Any]) -> str:
        """Create a dense textual document representing a spare part."""
        fields = [
            str(p.get("title", "")),
            str(p.get("category", "")),
            str(p.get("product_description", "")),
            str(p.get("product_specifications", "")),
        ]
        base_text = " ".join(f for f in fields if f).strip()
        synonyms = " ".join(tokenize_and_expand(base_text))
        return f"{base_text} {synonyms}".strip()

    def build_indexes(
        self,
        products: List[Dict[str, Any]],
        faiss_path: str = FAISS_INDEX_PATH,
        bm25_path: str = BM25_INDEX_PATH,
    ) -> None:
        """Build FAISS vector index and BM25 index from clean product list."""
        if not products:
            raise ValueError("Cannot build index from empty product catalog.")

        for p in (faiss_path, bm25_path):
            os.makedirs(os.path.dirname(p), exist_ok=True)

        self.products = list(products)
        self.rich_texts = [self._build_product_text(p) for p in self.products]
        self.categories = sorted({p.get("category", "") for p in self.products if p.get("category")})

        # 1. FAISS Dense Indexing
        embeddings = self.model.encode(
            self.rich_texts,
            normalize_embeddings=False,
            show_progress_bar=True,
            convert_to_numpy=True,
        )
        vectors = np.ascontiguousarray(embeddings, dtype=np.float32)
        dim = vectors.shape[1]
        self.faiss_index = faiss.IndexFlatL2(dim)
        self.faiss_index.add(vectors)
        faiss.write_index(self.faiss_index, faiss_path)

        # 2. BM25 Sparse Indexing
        tokenized_corpus = [tokenize_and_expand(text) for text in self.rich_texts]
        self.bm25 = BM25Okapi(tokenized_corpus)
        with open(bm25_path, "wb") as f:
            pickle.dump(self.bm25, f)

        self._is_ready = True
        logger.info(f"Built FAISS ({self.faiss_index.ntotal} items) and BM25 successfully.")

    def load_indexes(
        self,
        products: List[Dict[str, Any]],
        faiss_path: str = FAISS_INDEX_PATH,
        bm25_path: str = BM25_INDEX_PATH,
    ) -> None:
        """Load pre-computed FAISS and BM25 indexes from disk."""
        if not os.path.exists(faiss_path) or not os.path.exists(bm25_path):
            raise FileNotFoundError("Pre-computed indexes not found. Build them first.")

        self.products = list(products)
        self.rich_texts = [self._build_product_text(p) for p in self.products]
        self.categories = sorted({p.get("category", "") for p in self.products if p.get("category")})

        self.faiss_index = faiss.read_index(faiss_path)
        with open(bm25_path, "rb") as f:
            self.bm25 = pickle.load(f)

        self._is_ready = True
        logger.info(f"Loaded FAISS ({self.faiss_index.ntotal} items) and BM25 index from disk.")

    def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Execute Hybrid Search:
        1. Dense semantic search via FAISS.
        2. Sparse lexical search via BM25.
        3. Merge rankings with Reciprocal Rank Fusion (RRF).
        """
        if not self._is_ready:
            raise RuntimeError("Search engine is not ready. Call load_indexes() or build_indexes().")

        query = query.strip()
        if not query:
            return []

        # 1. Dense retrieval
        expanded_query = " ".join(tokenize_and_expand(query))
        query_vector = self.model.encode([expanded_query], convert_to_numpy=True)
        query_vector = np.ascontiguousarray(query_vector, dtype=np.float32)
        _, dense_indices = self.faiss_index.search(query_vector, min(25, self.faiss_index.ntotal))
        dense_hits = [int(i) for i in dense_indices[0] if i != -1]

        # 2. Sparse retrieval
        query_tokens = tokenize_and_expand(query)
        bm25_scores = np.asarray(self.bm25.get_scores(query_tokens))
        sparse_hits = []
        if bm25_scores.size > 0:
            k = min(25, bm25_scores.size)
            partition = np.argpartition(-bm25_scores, k - 1)[:k]
            sparse_hits = [int(i) for i in partition[np.argsort(-bm25_scores[partition])]]

        # 3. Reciprocal Rank Fusion (RRF)
        score_map: Dict[int, float] = {}
        for rank, idx in enumerate(dense_hits):
            score_map[idx] = score_map.get(idx, 0.0) + (1.0 / (rank + RRF_K))
        for rank, idx in enumerate(sparse_hits):
            score_map[idx] = score_map.get(idx, 0.0) + (1.0 / (rank + RRF_K))

        # Sort by highest RRF score
        ranked_indices = sorted(score_map.keys(), key=lambda idx: score_map[idx], reverse=True)
        return [dict(self.products[idx]) for idx in ranked_indices[:top_k]]

    def get_recommendations(self, product_id: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Find alternative products in the same price category with high customer ratings."""
        if not self._is_ready:
            return []

        # Find target product
        origin = next((p for p in self.products if str(p.get("product_id")) == str(product_id)), None)
        if not origin:
            return []

        price = float(origin.get("final_price", 0.0))
        if price <= 0:
            return []

        # Search similar items using dense embeddings
        doc_text = self._build_product_text(origin)
        vec = np.ascontiguousarray(self.model.encode([doc_text], convert_to_numpy=True), dtype=np.float32)
        _, indices = self.faiss_index.search(vec, 20)

        candidates = []
        for idx in indices[0]:
            if idx == -1:
                continue
            item = self.products[idx]
            if str(item.get("product_id")) == str(product_id):
                continue
            item_price = float(item.get("final_price", 0.0))
            if 0.7 <= (item_price / price) <= 1.3:
                candidates.append(item)

        # Sort candidates by rating descending
        candidates.sort(key=lambda x: (-float(x.get("rating", 0.0)), -float(x.get("ratings_count", 0))))
        return candidates[:top_k]

    def keyword_lookup(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Exact substring lookup by product title or SKU/ID."""
        norm_query = normalize_arabic(query)
        if not norm_query:
            return []

        matches = []
        for p in self.products:
            title = normalize_arabic(str(p.get("title", "")))
            pid = normalize_arabic(str(p.get("product_id", "")))
            if (norm_query in title) or (norm_query == pid):
                matches.append(dict(p))
                if len(matches) >= limit:
                    break
        return matches

    def calculate_installment(self, price: float, months: int = 6) -> Dict[str, Any]:
        """Compute monthly installment payments based on interest rate tiers."""
        if price <= 0:
            raise ValueError("Price must be positive.")
        if months not in INSTALLMENT_RATES:
            raise ValueError(f"Supported installment periods: {list(INSTALLMENT_RATES.keys())} months")

        rate = INSTALLMENT_RATES[months]
        total = price * (1.0 + rate)
        monthly = total / months
        return {
            "monthly_payment": round(monthly, 2),
            "total_with_interest": round(total, 2),
            "interest_percentage": int(rate * 100),
            "months": months,
        }

    def get_installment_terms(self) -> Dict[int, float]:
        """Return the store installment terms dictionary."""
        return dict(INSTALLMENT_RATES)

    def get_all_categories(self) -> List[str]:
        """Return the list of all available product categories."""
        return list(self.categories)
