"""
Role 1: Data Engineer (مهندس البيانات)
File: core/data_engine.py

Responsibilities:
- Ingest and clean the automotive spare parts catalog.
- Normalize missing values, data types, and numeric columns.
- Provide data validation and summary statistics for the catalog.
"""

import os
from typing import Any, Dict, List, Optional
import pandas as pd
from core.config import DATA_PATH, TEXT_COLUMNS, NUMERIC_COLUMNS, logger


def load_catalog(csv_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load and clean the automotive products dataset from CSV.
    Ensures correct types for prices, ratings, and text fields.
    """
    path = csv_path or DATA_PATH
    if not os.path.exists(path):
        # Fallback candidates if running from a different working directory
        candidates = ["data/products_clean.csv", "products_clean.csv"]
        for c in candidates:
            if os.path.exists(c):
                path = c
                break
        else:
            raise FileNotFoundError(f"Products dataset not found at: {path}")

    df = pd.read_csv(path)

    # 1. Filter only active items if 'is_active' column exists
    if "is_active" in df.columns:
        df = df[df["is_active"] == 1].copy()

    # 2. Clean text fields: fill missing with empty strings and strip extra whitespace
    for col in TEXT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    # 3. Clean numeric fields: coerce bad entries to 0.0
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # 4. Ensure each product has a unique string ID
    if "product_id" not in df.columns:
        df["product_id"] = df.index.astype(str)
    df["product_id"] = df["product_id"].astype(str)

    products = df.to_dict(orient="records")
    logger.info(f"Loaded {len(products)} active products from '{path}'")
    return products


def get_dataset_summary(products: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate summary statistics of the catalog.
    Useful for data inspection and presentation demos.
    """
    if not products:
        return {"total_products": 0}

    df = pd.DataFrame(products)
    categories = df["category"].value_counts().to_dict() if "category" in df.columns else {}
    avg_price = float(df["final_price"].mean()) if "final_price" in df.columns else 0.0
    max_price = float(df["final_price"].max()) if "final_price" in df.columns else 0.0

    return {
        "total_products": len(df),
        "total_categories": len(categories),
        "top_categories": list(categories.keys())[:5],
        "average_price_egp": round(avg_price, 2),
        "max_price_egp": round(max_price, 2),
    }


# Backwards compatibility alias
load_products_from_csv = load_catalog
ProductCatalogLoader = load_catalog
