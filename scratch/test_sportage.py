import os, sys
sys.path.insert(0, '.')
from core.data_loader import load_products_from_csv
from core.retrieval import SalesRetrievalEngine
from core.pipeline import RAGPipeline

products = load_products_from_csv()
engine = SalesRetrievalEngine()
print("Building fresh indexes with synonym support...")
engine.build_indexes(products)

print("\n--- TEST: 'اسبورتاج' ---")
res1 = engine.hybrid_search("اسبورتاج", top_k=5)
for p in res1:
    print(" *", p.get("title"), f"({p.get('final_price')} EGP)")

print("\n--- TEST: 'سبورتاج' ---")
res2 = engine.hybrid_search("سبورتاج", top_k=5)
for p in res2:
    print(" *", p.get("title"), f"({p.get('final_price')} EGP)")

print("\n--- PIPELINE END-TO-END: 'اسبورتاج' ---")
pipe = RAGPipeline(engine)
reply = pipe.process_message("اسبورتاج", session_id="sportage_test")
print("\nBot Response:\n", reply["message"])
