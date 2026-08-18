import base64
import os
import re
import sys
import uuid
from typing import Any, Dict, List
import gradio as gr

from core.config import DEFAULT_FAISS_PATH, DEFAULT_BM25_PATH
from core.data_loader import load_products_from_csv
from core.retrieval import SalesRetrievalEngine
from core.pipeline import RAGPipeline

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

print("[Lucile] Loading product catalogue...")
products = load_products_from_csv()
engine = SalesRetrievalEngine()

if os.path.exists(DEFAULT_FAISS_PATH) and os.path.exists(DEFAULT_BM25_PATH):
    try:
        print("[Lucile] Loading search indexes from disk...")
        engine.load_indexes(products)
        if engine.faiss_index is None or engine.faiss_index.ntotal != len(products):
            print(f"[Lucile] Index count mismatch ({getattr(engine.faiss_index, 'ntotal', 0)} vs {len(products)}). Rebuilding...")
            engine.build_indexes(products)
    except Exception as e:
        print(f"[Lucile] Index load issue ({e}). Rebuilding indexes...")
        engine.build_indexes(products)
else:
    print("[Lucile] Building search indexes...")
    engine.build_indexes(products)

pipeline = RAGPipeline(engine)
print("[Lucile] Pipeline ready - launching Gradio...")

# Load banner image as base64
BANNER_B64 = ""
banner_path = os.path.join(os.path.dirname(__file__), "..", "assets", "banner.png")
if os.path.exists(banner_path):
    try:
        with open(banner_path, "rb") as f:
            BANNER_B64 = f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
    except Exception as e:
        print(f"[Lucile] Warning: Could not load banner image: {e}")

# Load Lucile Sport dark logo as base64
LOGO_B64 = ""
logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo_dark.jpg")
if os.path.exists(logo_path):
    try:
        with open(logo_path, "rb") as f:
            LOGO_B64 = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"
    except Exception as e:
        print(f"[Lucile] Warning: Could not load logo image: {e}")

def _render_product_cards(products: List[Dict[str, Any]]) -> str:
    """Render product results as styled Navy & White luxury HTML cards."""
    if not products:
        return ""
    cards = []
    for p in products[:6]:
        title = p.get("title", "Unknown")
        price = float(p.get("final_price", 0) or 0)
        initial = float(p.get("initial_price", 0) or 0)
        discount = p.get("discount", "")
        rating = float(p.get("rating", 0) or 4.5)
        reviews = int(p.get("ratings_count", 0) or 20)
        category = p.get("category", "قطع غيار")
        vendor = p.get("vendor", "")
        image_url = p.get("image_url", "")
        product_url = p.get("product_url", "#")
        description = str(p.get("product_description", ""))[:110]
        if description and len(str(p.get("product_description", ""))) > 110:
            description += "…"

        full_stars = int(rating)
        half_star = 1 if (rating - full_stars) >= 0.3 else 0
        empty_stars = 5 - full_stars - half_star
        stars_html = "★" * full_stars + ("½" if half_star else "") + "☆" * empty_stars

        discount_html = ""
        if discount and float(discount) > 0:
            discount_html = f'<span class="discount-badge">خصم {int(float(discount))}%</span>'

        price_html = f'<span class="product-price">{price:,.0f} <small>ج.م</small></span>'
        if initial and initial > price:
            price_html += f' <span class="product-original-price">{initial:,.0f} ج.م</span>'

        img_html = ""
        if image_url:
            img_html = f'<div class="product-img-wrap"><img src="{image_url}" alt="{title}" class="product-img" onerror="this.style.display=\'none\'" /></div>'
        else:
            img_html = '<div class="product-img-wrap product-img-placeholder">🚗</div>'

        vendor_badge = f'<span class="product-vendor">{vendor}</span>' if vendor and vendor != "Egy Car Parts" else ""

        cards.append(f"""
        <div class="product-card">
            {img_html}
            <div class="product-card-body">
                <div class="product-card-header">
                    <span class="product-category">{category}</span>
                    {vendor_badge}
                    {discount_html}
                </div>
                <h4 class="product-title" title="{title}">{title}</h4>
                <p class="product-desc">{description}</p>
                <div class="product-meta">
                    <div class="product-rating">
                        <span class="stars">{stars_html}</span>
                        <span class="review-count">{rating}/5 ({reviews})</span>
                    </div>
                    <div class="product-price-row">{price_html}</div>
                </div>
            </div>
        </div>
        """)
    return f'<div class="product-cards-grid">{"".join(cards)}</div>'


CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');

/* ─── Navy Blue & Pure White Theme Variables ──────────────────────── */
:root {
    --navy-bg:       #050c1a;
    --navy-surface:  #0a162e;
    --navy-card:     #0f2247;
    --navy-card-hover: #142d5e;
    --navy-border:   rgba(56, 189, 248, 0.22);
    --navy-border-hover: rgba(56, 189, 248, 0.55);

    --blue-royal:    #1d4ed8;
    --blue-primary:  #2563eb;
    --cyan-accent:   #38bdf8;
    --cyan-glow:     rgba(56, 189, 248, 0.35);

    --text-white:    #ffffff;
    --text-light:    #f1f5f9;
    --text-muted:    #94a3b8;
    --text-dim:      #64748b;

    --success:       #10b981;
    --warning:       #f59e0b;
    --danger:        #ef4444;

    --radius-sm:     8px;
    --radius-md:     14px;
    --radius-lg:     20px;
    --radius-xl:     28px;

    --shadow-card:   0 8px 32px rgba(2, 6, 23, 0.6);
    --shadow-glow:   0 0 24px rgba(56, 189, 248, 0.25);
    --shadow-blue:   0 8px 24px rgba(37, 99, 235, 0.35);
}

/* ─── Global Background & Typography ──────────────────────────────── */
body, .gradio-container, .main, .contain {
    background: var(--navy-bg) !important;
    color: var(--text-white) !important;
    font-family: 'Cairo', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.gradio-container {
    max-width: 1040px !important;
    margin: 0 auto !important;
    padding: 16px !important;
}

/* ─── Futuristic Deep Navy Radial Atmosphere ──────────────────────── */
body::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 70% 45% at 50% 0%, rgba(37, 99, 235, 0.22) 0%, transparent 70%),
        radial-gradient(ellipse 60% 35% at 85% 90%, rgba(14, 165, 233, 0.12) 0%, transparent 60%),
        radial-gradient(ellipse 50% 30% at 15% 70%, rgba(29, 78, 216, 0.14) 0%, transparent 50%),
        linear-gradient(180deg, #050c1a 0%, #08142c 50%, #040914 100%);
    z-index: -1;
    pointer-events: none;
}

/* ─── Hero Banner Container ───────────────────────────────────────── */
.hero-banner-wrap {
    width: 100%;
    margin-bottom: 20px;
    border-radius: var(--radius-lg);
    overflow: hidden;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.7), var(--shadow-glow);
    border: 1.5px solid var(--navy-border);
    position: relative;
    background: #000000;
}

.hero-banner-img {
    width: 100%;
    height: auto;
    max-height: 240px;
    object-fit: cover;
    display: block;
    transition: transform 0.4s ease;
}

.hero-banner-wrap:hover .hero-banner-img {
    transform: scale(1.015);
}

/* ─── Brand Logo ─────────────────────────────────────────────────── */
.brand-logo-wrap {
    text-align: center;
    margin: 4px auto 14px;
}

.brand-logo-img {
    max-width: 320px;
    height: auto;
    border-radius: var(--radius-md);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5), var(--shadow-glow);
    border: 1.5px solid rgba(56, 189, 248, 0.3);
    transition: transform 0.3s ease, border-color 0.3s ease;
    display: inline-block;
}

.brand-logo-img:hover {
    transform: scale(1.03);
    border-color: var(--cyan-accent);
    box-shadow: 0 10px 30px rgba(56, 189, 248, 0.4);
}

/* ─── Header & Brand Section ─────────────────────────────────────── */
.app-header {
    text-align: center;
    padding: 8px 16px 20px;
    position: relative;
}

.brand-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(37, 99, 235, 0.18);
    border: 1px solid rgba(56, 189, 248, 0.4);
    color: var(--cyan-accent);
    padding: 5px 16px;
    border-radius: 99px;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    margin-bottom: 12px;
    box-shadow: var(--shadow-glow);
}

.app-header h1 {
    font-size: 2.2rem;
    font-weight: 900;
    color: var(--text-white) !important;
    text-shadow: 0 2px 14px rgba(56, 189, 248, 0.35);
    margin: 0 0 10px;
    line-height: 1.2;
    letter-spacing: -0.02em;
}

.app-header p {
    font-size: 0.96rem;
    color: var(--text-muted) !important;
    margin: 0 auto;
    max-width: 680px;
    line-height: 1.65;
    font-weight: 500;
}

.header-badges-row {
    display: flex;
    justify-content: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 14px;
}

.header-pill {
    background: rgba(15, 34, 71, 0.85);
    border: 1px solid rgba(56, 189, 248, 0.25);
    color: var(--text-light);
    padding: 6px 14px;
    border-radius: 99px;
    font-size: 0.8rem;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 6px;
}

.header-divider {
    width: 80px;
    height: 3px;
    background: linear-gradient(90deg, transparent, var(--cyan-accent), transparent);
    border-radius: 99px;
    margin: 18px auto 0;
}

/* ─── Chatbot Container (Sleek Deep Navy Glass) ────────────────────── */
.chatbot-container, .chatbot-container > div, .chatbot, [data-testid="chatbot"],
.chatbot-container .wrapper, .chatbot-container .bubble-wrap, .chatbot-container .scroll-container,
.chatbot-container .message-wrap, .dark .chatbot-container {
    background: var(--navy-surface) !important;
    background-color: var(--navy-surface) !important;
    border: 1.5px solid var(--navy-border) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: var(--shadow-card), inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
    direction: rtl !important;
    text-align: right !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
}

/* Force all text in chatbot to be pure white */
.chatbot-container .message,
.chatbot-container .message *,
.chatbot-container [data-testid="user-message"],
.chatbot-container [data-testid="user-message"] *,
.chatbot-container [data-testid="bot-message"],
.chatbot-container [data-testid="bot-message"] * {
    color: #ffffff !important;
    line-height: 1.7 !important;
}

/* ─── User Message Bubble (Royal Blue Gradient + Pure White) ───────── */
.chatbot-container .user, 
.chatbot-container [data-testid="user-message"],
.chatbot-container .message-row.user-row .message,
.chatbot-container .message.user,
.chatbot-container div.user {
    background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%) !important;
    background-color: #2563eb !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 20px 20px 4px 20px !important;
    padding: 13px 20px !important;
    font-family: 'Cairo', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.96rem !important;
    box-shadow: var(--shadow-blue) !important;
    direction: rtl !important;
    text-align: right !important;
    margin-left: auto !important;
}

.chatbot-container .user *, 
.chatbot-container [data-testid="user-message"] *,
.chatbot-container .message.user * {
    color: #ffffff !important;
    background: transparent !important;
}

/* ─── Bot Message Bubble (Midnight Navy + Cyan Edge + Crisp White) ─── */
.chatbot-container .bot, 
.chatbot-container [data-testid="bot-message"],
.chatbot-container .message-row.bot-row .message,
.chatbot-container .message.bot,
.chatbot-container div.bot {
    background: #0f2347 !important;
    background-color: #0f2347 !important;
    color: #ffffff !important;
    border: 1.5px solid rgba(56, 189, 248, 0.3) !important;
    border-radius: 20px 20px 20px 4px !important;
    padding: 16px 22px !important;
    font-family: 'Cairo', sans-serif !important;
    font-size: 0.96rem !important;
    line-height: 1.8 !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.06) !important;
    direction: rtl !important;
    text-align: right !important;
    margin-right: auto !important;
}

.chatbot-container .bot *, 
.chatbot-container [data-testid="bot-message"] *,
.chatbot-container .message.bot * {
    color: #ffffff !important;
}

.chatbot-container .bot strong,
.chatbot-container .bot b {
    color: #38bdf8 !important;
    font-weight: 700 !important;
}

/* ─── Text Input Box (Crisp Navy & Glowing Cyan Focus) ─────────────── */
input, textarea, .input-container textarea, [data-testid="textbox"] {
    direction: rtl !important;
    text-align: right !important;
    font-family: 'Cairo', sans-serif !important;
    font-size: 0.98rem !important;
    color: #ffffff !important;
    background: #0a1836 !important;
    border: 1.5px solid rgba(56, 189, 248, 0.3) !important;
    border-radius: var(--radius-md) !important;
    padding: 12px 18px !important;
    transition: all 0.25s ease !important;
}

input:focus, textarea:focus, [data-testid="textbox"]:focus-within {
    border-color: var(--cyan-accent) !important;
    box-shadow: 0 0 18px var(--cyan-glow) !important;
    background: #0d2045 !important;
}

input::placeholder, textarea::placeholder {
    color: #94a3b8 !important;
    font-family: 'Cairo', sans-serif !important;
}

/* ─── Quick-Action Chips ──────────────────────────────────────────── */
.quick-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 6px 0 4px;
    justify-content: center;
}

.quick-actions button,
.quick-chip {
    background: rgba(15, 34, 71, 0.85) !important;
    border: 1px solid rgba(56, 189, 248, 0.25) !important;
    border-radius: 99px !important;
    padding: 8px 18px !important;
    font-size: 0.84rem !important;
    font-weight: 700 !important;
    color: #f1f5f9 !important;
    cursor: pointer !important;
    transition: all 0.22s cubic-bezier(.4,0,.2,1) !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
    font-family: 'Cairo', sans-serif !important;
}

.quick-actions button:hover,
.quick-chip:hover {
    background: linear-gradient(135deg, #1d4ed8 0%, #0284c7 100%) !important;
    border-color: var(--cyan-accent) !important;
    color: #ffffff !important;
    box-shadow: var(--shadow-glow), var(--shadow-blue) !important;
    transform: translateY(-2px) !important;
}

/* ─── Send Button ─────────────────────────────────────────────────── */
button.primary {
    background: linear-gradient(135deg, #1d4ed8 0%, #0284c7 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-blue) !important;
    transition: all 0.22s ease !important;
    font-family: 'Cairo', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1rem !important;
}

button.primary:hover {
    background: linear-gradient(135deg, #2563eb 0%, #38bdf8 100%) !important;
    box-shadow: var(--shadow-glow), 0 6px 20px rgba(37, 99, 235, 0.45) !important;
    transform: translateY(-1.5px) !important;
}

/* ─── Secondary Control Buttons (Handoff / Clear) ─────────────────── */
.handoff-btn {
    background: rgba(15, 34, 71, 0.75) !important;
    border: 1px solid rgba(56, 189, 248, 0.2) !important;
    border-radius: var(--radius-md) !important;
    padding: 9px 20px !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: #cbd5e1 !important;
    transition: all 0.22s ease !important;
    font-family: 'Cairo', sans-serif !important;
}

.handoff-btn:hover {
    border-color: var(--cyan-accent) !important;
    color: #ffffff !important;
    background: rgba(30, 64, 175, 0.4) !important;
    transform: translateY(-1px) !important;
}

/* ─── Product Cards Grid & Luxury Navy Cards ──────────────────────── */
.product-cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
    padding: 10px 0 16px;
    direction: rtl;
}

.product-card {
    background: var(--navy-card);
    border: 1.5px solid var(--navy-border);
    border-radius: var(--radius-lg);
    padding: 16px;
    transition: all 0.28s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: var(--shadow-card);
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.product-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--blue-primary), var(--cyan-accent), #60a5fa);
    opacity: 0.7;
    transition: opacity 0.25s;
}

.product-card:hover {
    box-shadow: 0 14px 40px rgba(0, 0, 0, 0.8), var(--shadow-glow);
    border-color: var(--navy-border-hover);
    transform: translateY(-5px);
    background: var(--navy-card-hover);
}

.product-card:hover::before {
    opacity: 1;
    height: 4px;
}

.product-img-wrap {
    width: 100%;
    height: 140px;
    border-radius: var(--radius-md);
    overflow: hidden;
    background: #071224;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 12px;
    border: 1px solid rgba(255, 255, 255, 0.06);
}

.product-img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    padding: 6px;
    transition: transform 0.3s ease;
}

.product-card:hover .product-img {
    transform: scale(1.05);
}

.product-img-placeholder {
    font-size: 2.8rem;
    color: var(--cyan-accent);
}

.product-card-body {
    display: flex;
    flex-direction: column;
    flex: 1;
}

.product-card-header {
    display: flex;
    gap: 6px;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 8px;
}

.product-category {
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--cyan-accent);
    background: rgba(56, 189, 248, 0.12);
    padding: 3px 10px;
    border-radius: 99px;
    border: 1px solid rgba(56, 189, 248, 0.25);
}

.product-vendor {
    font-size: 0.7rem;
    font-weight: 700;
    color: #e2e8f0;
    background: rgba(255, 255, 255, 0.1);
    padding: 3px 8px;
    border-radius: 99px;
}

.discount-badge {
    background: rgba(239, 68, 68, 0.18);
    color: #f87171;
    font-size: 0.72rem;
    font-weight: 800;
    padding: 3px 9px;
    border-radius: 99px;
    border: 1px solid rgba(239, 68, 68, 0.35);
    margin-right: auto;
}

.product-title {
    font-size: 0.95rem;
    font-weight: 800;
    color: #ffffff !important;
    margin: 0 0 6px;
    line-height: 1.45;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.product-desc {
    font-size: 0.78rem;
    color: var(--text-muted);
    line-height: 1.55;
    margin: 0 0 14px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.product-meta {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding-top: 12px;
    margin-top: auto;
}

.product-rating .stars {
    color: #fbbf24;
    font-size: 0.88rem;
    letter-spacing: 1px;
}

.product-rating .review-count {
    font-size: 0.72rem;
    color: var(--text-dim);
    display: block;
    margin-top: 2px;
}

.product-price {
    font-size: 1.18rem;
    font-weight: 900;
    color: #ffffff;
    background: linear-gradient(135deg, #38bdf8 0%, #60a5fa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.product-price small {
    font-size: 0.78rem;
    font-weight: 700;
}

.product-original-price {
    font-size: 0.76rem;
    color: var(--text-dim);
    text-decoration: line-through;
    display: block;
    text-align: left;
}

/* ─── Status Bar ──────────────────────────────────────────────────── */
.status-bar {
    text-align: center;
    padding: 12px;
    font-size: 0.78rem;
    color: var(--text-muted);
    letter-spacing: 0.01em;
}

.status-dot {
    display: inline-block;
    width: 8px; height: 8px;
    background: var(--success);
    border-radius: 50%;
    margin-left: 8px;
    box-shadow: 0 0 10px #10b981;
    animation: pulse 2s ease-in-out infinite;
    vertical-align: middle;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: .4; transform: scale(.8); }
}

footer { display: none !important; }

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--navy-bg); }
::-webkit-scrollbar-thumb { background: rgba(56, 189, 248, 0.3); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--cyan-accent); }

@media (max-width: 640px) {
    .gradio-container { padding: 8px !important; }
    .product-cards-grid { grid-template-columns: 1fr; }
    .app-header h1 { font-size: 1.6rem; }
    .hero-banner-img { max-height: 160px; }
}
"""

def create_app() -> gr.Blocks:
    with gr.Blocks(
        css=CUSTOM_CSS,
        title="لوسيل لقطع غيار السيارات — Lucile Auto Parts",
        theme=gr.themes.Base(
            primary_hue=gr.themes.colors.blue,
            secondary_hue=gr.themes.colors.sky,
            neutral_hue=gr.themes.colors.slate,
            font=gr.themes.GoogleFont("Cairo"),
            radius_size=gr.themes.sizes.radius_lg,
        ).set(
            body_background_fill="#050c1a",
            body_background_fill_dark="#050c1a",
            block_background_fill="rgba(10, 22, 46, 0.85)",
            block_background_fill_dark="rgba(10, 22, 46, 0.85)",
            block_border_color="rgba(56, 189, 248, 0.2)",
            block_border_color_dark="rgba(56, 189, 248, 0.2)",
            block_label_text_color="#94a3b8",
            block_label_text_color_dark="#94a3b8",
            block_title_text_color="#ffffff",
            block_title_text_color_dark="#ffffff",
            body_text_color="#ffffff",
            body_text_color_dark="#ffffff",
            body_text_color_subdued="#94a3b8",
            body_text_color_subdued_dark="#94a3b8",
            input_background_fill="#0a1836",
            input_background_fill_dark="#0a1836",
            input_border_color="rgba(56, 189, 248, 0.3)",
            input_border_color_dark="rgba(56, 189, 248, 0.3)",
            button_primary_background_fill="#2563eb",
            button_primary_background_fill_dark="#2563eb",
            button_primary_text_color="#ffffff",
            button_primary_text_color_dark="#ffffff",
            button_secondary_background_fill="#0f2247",
            button_secondary_background_fill_dark="#0f2247",
            button_secondary_border_color="rgba(56, 189, 248, 0.25)",
            button_secondary_border_color_dark="rgba(56, 189, 248, 0.25)",
            button_secondary_text_color="#f1f5f9",
            button_secondary_text_color_dark="#f1f5f9",
        ),
    ) as app:
        session_state = gr.State(value=lambda: str(uuid.uuid4()))

        # Hero Banner
        banner_html = ""
        if BANNER_B64:
            banner_html = f"""
            <div class="hero-banner-wrap">
                <img src="{BANNER_B64}" alt="الثقة تبدأ من الفرامل — لوسيل سبورت لقطع غيار السيارات" class="hero-banner-img" />
            </div>
            """

        # Lucile Sport Logo
        logo_html = ""
        if LOGO_B64:
            logo_html = f"""
            <div class="brand-logo-wrap">
                <img src="{LOGO_B64}" alt="لوسيل سبورت — Lucile Sport" class="brand-logo-img" />
            </div>
            """

        gr.HTML(f"""
        {banner_html}
        <div class="app-header">
            {logo_html}
            <div class="brand-badge">⚡ لوسيل سبورت — مساعدتك الذكية لقطع غيار السيارات في مصر</div>
            <h1>لوسيل سبورت لقطع غيار السيارات</h1>
            <p>اسأل عن أي قطعة غيار، تيل فرامل، فلاتر وزيوت، أسعار، توافق مع سيارتك أو خطط التقسيط المريحة<br>
            بالعربي أو الإنجليزي — في خدمتك لحظياً 🚗</p>
            <div class="header-badges-row">
                <span class="header-pill">📦 14,170+ قطعة أصلية</span>
                <span class="header-pill">🛡️ ضمان الجودة والاسترجاع</span>
                <span class="header-pill">💳 تقسيط بدون فوائد (3 شهور 0%)</span>
                <span class="header-pill">🚚 شحن لجميع محافظات مصر</span>
            </div>
            <div class="header-divider"></div>
        </div>
        """)

        chatbot = gr.Chatbot(
            value=[],
            elem_classes=["chatbot-container"],
            height=440,
            show_label=False,
            avatar_images=(None, "https://api.dicebear.com/9.x/bottts-neutral/svg?seed=lucile_auto&backgroundColor=1d4ed8&eyes=shade01&mouth=smile01"),
            placeholder="<p style='text-align:center;color:#94a3b8;padding:40px 20px;font-size:1rem;font-family:Cairo,sans-serif;'>👋 مرحباً بك في <b>لوسيل سبورت لقطع غيار السيارات</b>! اسألني عن أي قطعة غيار أو اكتب اسم وموديل عربيتك وسأساعدك فوراً 🚗</p>",
        )

        product_display = gr.HTML(value="", visible=False)

        with gr.Row(elem_classes=["quick-actions"]):
            qa_trending    = gr.Button("🔥 الأكثر طلباً", elem_classes=["quick-chip"], size="sm")
            qa_brakes      = gr.Button("⚙️ فرامل وتيل", elem_classes=["quick-chip"], size="sm")
            qa_maintenance = gr.Button("🛢️ زيوت وفلاتر", elem_classes=["quick-chip"], size="sm")
            qa_lights      = gr.Button("💡 بطاريات وإضاءة", elem_classes=["quick-chip"], size="sm")
            qa_sportage    = gr.Button("🚗 كيا سبورتاج", elem_classes=["quick-chip"], size="sm")
            qa_install     = gr.Button("📅 خطط التقسيط", elem_classes=["quick-chip"], size="sm")

        with gr.Row():
            msg_input = gr.Textbox(
                placeholder="اكتب استفسارك، قطعة الغيار المطلوبة، أو نوع عربيتك هنا...",
                show_label=False,
                container=False,
                scale=7,
                autofocus=True,
            )
            send_btn = gr.Button("إرسال ▶", variant="primary", scale=1, min_width=95)

        with gr.Row():
            handoff_btn = gr.Button("📞 تواصل مع فني صيانة", elem_classes=["handoff-btn"], size="sm")
            clear_btn   = gr.Button("🗑️ مسح المحادثة", elem_classes=["handoff-btn"], size="sm")

        status_html = gr.HTML('<div class="status-bar"><span class="status-dot"></span>متصل — لوسيل سبورت (Lucile Sport) · 14,177+ قطعة غيار أصلية متوفرة في المخزون · Hybrid RAG Engine</div>')

        def respond(user_message: str, chat_history: list, session_id: str):
            if not user_message or not user_message.strip():
                return "", chat_history, gr.update(visible=False, value=""), session_id

            chat_history = chat_history + [{"role": "user", "content": user_message}]

            installment_months = None
            match = re.search(r'\b(\d+)\s*(?:months?|mo|شهر|شهور|أشهر)\b', user_message, re.IGNORECASE)
            if match:
                installment_months = int(match.group(1))

            result = pipeline.process_message(
                user_message,
                session_id=session_id,
                installment_months=installment_months
            )

            bot_reply = result["message"]
            chat_history = chat_history + [{"role": "assistant", "content": bot_reply}]

            products_html = ""
            show_products = False
            if result.get("products"):
                products_html = _render_product_cards(result["products"])
                show_products = True

            return "", chat_history, gr.update(visible=show_products, value=products_html), session_id

        def handle_handoff(chat_history: list, session_id: str):
            chat_history = chat_history + [{"role": "user", "content": "[طلب التحدث مع موظف فني]"}]

            result = pipeline.process_message(
                "عايز أكلم موظف خدمة عملاء أو فني صيانة متخصص",
                session_id=session_id,
                request_handoff=True,
            )
            bot_reply = result["message"]
            if result.get("summary_for_agent"):
                bot_reply += f"\n\n*تم إعداد موجز طلبك لتحويله للمهندس الفني.*"

            chat_history = chat_history + [{"role": "assistant", "content": bot_reply}]
            return chat_history, gr.update(visible=False, value=""), session_id

        def send_quick_action(action_text: str, chat_history: list, session_id: str):
            return respond(action_text, chat_history, session_id)

        def clear_chat():
            new_session = str(uuid.uuid4())
            return [], gr.update(visible=False, value=""), new_session

        send_inputs  = [msg_input, chatbot, session_state]
        send_outputs = [msg_input, chatbot, product_display, session_state]

        msg_input.submit(respond, send_inputs, send_outputs)
        send_btn.click(respond, send_inputs, send_outputs)

        qa_trending.click(
            lambda h, s: respond("عايز أشوف أكتر قطع الغيار طلباً ومبيعاً", h, s),
            [chatbot, session_state], send_outputs,
        )
        qa_brakes.click(
            lambda h, s: respond("وريني تيل الفرامل والطنابير المتاحة", h, s),
            [chatbot, session_state], send_outputs,
        )
        qa_maintenance.click(
            lambda h, s: respond("عايز زيوت وفلاتر للعربيات", h, s),
            [chatbot, session_state], send_outputs,
        )
        qa_lights.click(
            lambda h, s: respond("وريني البطاريات ولمبات الإضاءة والفوانيس المتاحة", h, s),
            [chatbot, session_state], send_outputs,
        )
        qa_sportage.click(
            lambda h, s: respond("إيه قطع الغيار المتاحة لكيا سبورتاج؟", h, s),
            [chatbot, session_state], send_outputs,
        )
        qa_install.click(
            lambda h, s: respond("إيه هي خطط وأنظمة التقسيط المتاحة؟", h, s),
            [chatbot, session_state], send_outputs,
        )

        handoff_btn.click(handle_handoff, [chatbot, session_state], [chatbot, product_display, session_state])
        clear_btn.click(clear_chat, [], [chatbot, product_display, session_state])

    return app
