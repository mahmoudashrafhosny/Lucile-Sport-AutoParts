import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Logger setup
logger = logging.getLogger("lucile_sport")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

def get_secret(key: str) -> Optional[str]:
    """Retrieve API key or secret from environment variables."""
    return os.getenv(key)

# Default file paths
DATA_PATH = os.getenv("DATA_PATH", "data/products_clean.csv")
FAISS_INDEX_PATH = os.getenv("FAISS_PATH", "database/faiss.index")
BM25_INDEX_PATH = os.getenv("BM25_PATH", "database/bm25_index.pkl")

# Data schema definitions
TEXT_COLUMNS = [
    "title", "category", "product_description",
    "product_specifications", "what_customers_said", "vendor", "sku", "tags"
]
NUMERIC_COLUMNS = ["final_price", "initial_price", "discount", "rating", "ratings_count"]

# Business logic: Official installment plans and interest rates
INSTALLMENT_RATES = {
    3: 0.00,   # 3 months: 0% interest (Promotion)
    6: 0.05,   # 6 months: 5% interest
    9: 0.07,   # 9 months: 7% interest
    12: 0.10,  # 12 months: 10% interest
}

# RRF hyperparameter for hybrid rank fusion
RRF_K = 60
