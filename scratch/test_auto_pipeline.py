import os
import sys
sys.path.insert(0, os.path.abspath("."))
from core.data_loader import load_products_from_csv
from core.retrieval import SalesRetrievalEngine
from core.pipeline import RAGPipeline

print("1. Loading products from CSV...")
products = load_products_from_csv()
print(f"Loaded {len(products)} products.")

print("2. Building / Loading indexes...")
engine = SalesRetrievalEngine()
engine.build_indexes(products)
print(f"Indexes built. Categories: {engine.categories}")

print("3. Testing hybrid search for 'تيل فرامل تويوتا'...")
results = engine.hybrid_search("تيل فرامل تويوتا", top_k=3)
for p in results:
    print(f" - [{p.get('category')}] {p.get('title')} -> {p.get('final_price')} EGP")

print("4. Testing pipeline end-to-end...")
pipe = RAGPipeline(engine)
res = pipe.process_message("عايز زيت موتور تخليقي كويس لهيونداي النترا ومعاه فلتر زيت والتقسيط 6 شهور")
print("\nBot Response:\n", res["message"])
print("\nProducts found:", len(res.get("products", [])))
