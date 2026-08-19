"""
Role 5: Frontend & UI Engineer (مهندس الواجهة وتجربة المستخدم)
File: core/frontend_ui.py

Responsibilities:
- Build the conversational web interface using Gradio.
- Luxury Dark Navy Glassmorphism UI styling (custom CSS).
- Interactive HTML/CSS product cards rendering with price & discounts.
- Quick action category buttons and chat session management.
"""

import base64
import os
import re
import uuid
from typing import Any, Dict, List
import gradio as gr

from core.config import FAISS_INDEX_PATH, BM25_INDEX_PATH
from core.data_engine import load_catalog
from core.retrieval_ai import SalesRetrievalEngine
from core.orchestrator import RAGPipeline

# Initialize Data & Search Engine
products = load_catalog()
engine = SalesRetrievalEngine()

if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(BM25_INDEX_PATH):
    try:
        engine.load_indexes(products)
    except Exception:
        engine.build_indexes(products)
else:
    engine.build_indexes(products)

pipeline = RAGPipeline(engine)


def _load_asset_b64(filename: str, mime_type: str) -> str:
    """Helper to load image assets as Base64 strings."""
    path = os.path.join(os.path.dirname(__file__), "..", "assets", filename)
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                return f"data:{mime_type};base64,{base64.b64encode(f.read()).decode('utf-8')}"
        except Exception:
            pass
    return ""


BANNER_B64 = _load_asset_b64("banner.png", "image/png")
LOGO_B64 = _load_asset_b64("logo_dark.jpg", "image/jpeg")


def render_product_cards(products_list: List[Dict[str, Any]]) -> str:
    """Render automotive product search results as modern HTML luxury cards."""
    if not products_list:
        return ""

    cards = []
    for p in products_list[:6]:
        title = p.get("title", "قطع غيار")
        price = float(p.get("final_price", 0) or 0)
        initial_price = float(p.get("initial_price", 0) or 0)
        discount = p.get("discount")
        rating = float(p.get("rating", 0) or 4.5)
        reviews = int(p.get("ratings_count", 0) or 15)
        category = p.get("category", "قطع غيار")
        image_url = p.get("image_url", "")
        product_url = p.get("product_url", "#")
        desc = str(p.get("product_description", ""))[:95]
        if len(str(p.get("product_description", ""))) > 95:
            desc += "..."

        # Stars rating
        full_stars = int(rating)
        stars_html = "★" * full_stars + "☆" * (5 - full_stars)

        discount_badge = ""
        if discount and float(discount) > 0:
            discount_badge = f'<span class="discount-badge">خصم {int(float(discount))}%</span>'

        price_html = f'<span class="price-val">{price:,.0f} <small>ج.م</small></span>'
        if initial_price > price:
            price_html += f' <span class="old-price">{initial_price:,.0f} ج.م</span>'

        img_html = f'<img src="{image_url}" class="card-img" alt="{title}" onerror="this.style.display=\'none\'" />' if image_url else '<div class="card-icon">🚗</div>'

        card_html = f"""
        <div class="product-card">
            {discount_badge}
            <div class="img-container">{img_html}</div>
            <div class="card-content">
                <span class="category-tag">{category}</span>
                <h4 class="card-title" title="{title}">{title}</h4>
                {f'<p class="card-desc">{desc}</p>' if desc else ''}
                <div class="card-rating">
                    <span class="stars">{stars_html}</span>
                    <span class="rating-val">{rating:.1f}</span>
                    <span class="rating-count">({reviews} تقييم)</span>
                </div>
                <div class="card-footer">
                    <div class="price-box">{price_html}</div>
                    {f'<a href="{product_url}" target="_blank" class="details-btn">تفاصيل ↗</a>' if product_url and product_url != '#' else '<span class="in-stock">✓ متوفر</span>'}
                </div>
            </div>
        </div>
        """
        cards.append(card_html)

    return f"""
    <div class="products-container">
        <div class="products-header">
            <span class="hdr-icon">🛒</span>
            <span class="hdr-title">قطع الغيار المتطابقة في المخزون ({len(products_list[:6])}):</span>
        </div>
        <div class="products-grid">
            {''.join(cards)}
        </div>
    </div>
    """


# Clean Dark Navy CSS Theme
UI_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');

body, .gradio-container {
    font-family: 'Cairo', sans-serif !important;
    background: #070d18 !important;
    color: #f1f5f9 !important;
    direction: rtl;
}

.gradio-container {
    max-width: 1080px !important;
    margin: 0 auto !important;
    padding: 10px 14px 24px !important;
}

.hero-banner {
    width: 100%;
    border-radius: 14px;
    overflow: hidden;
    margin-bottom: 10px;
    border: 1px solid rgba(56, 189, 248, 0.2);
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
}

.hero-banner img {
    width: 100%;
    max-height: 200px;
    object-fit: cover;
    display: block;
}

.header-panel {
    text-align: center;
    background: #0c1829;
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 14px;
    padding: 12px 18px;
    margin-bottom: 12px;
}

.logo-circle {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    border: 2px solid #38bdf8;
    margin: 0 auto 8px;
    display: block;
}

.brand-title {
    color: #ffffff;
    font-size: 1.5rem;
    font-weight: 800;
    margin: 4px 0;
}

.brand-desc {
    color: #94a3b8;
    font-size: 0.88rem;
    margin: 0;
}

.badges-row {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin-top: 8px;
    flex-wrap: wrap;
}

.badge-item {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #cbd5e1;
    font-size: 0.75rem;
    padding: 2px 8px;
    border-radius: 10px;
}

.quick-chips-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    justify-content: center;
    margin: 8px 0;
}

.quick-chip button {
    background: #102038 !important;
    border: 1px solid rgba(56, 189, 248, 0.25) !important;
    color: #cbd5e1 !important;
    font-size: 0.8rem !important;
    border-radius: 16px !important;
    padding: 3px 12px !important;
}

.quick-chip button:hover {
    border-color: #38bdf8 !important;
    color: #38bdf8 !important;
}

.products-container {
    background: #0c1829;
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 12px;
    padding: 12px;
    margin: 10px 0;
}

.products-header {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 10px;
    color: #38bdf8;
    font-weight: 700;
    font-size: 0.92rem;
}

.products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 10px;
}

.product-card {
    background: #070e1a;
    border: 1px solid rgba(56, 189, 248, 0.18);
    border-radius: 10px;
    overflow: hidden;
    position: relative;
    display: flex;
    flex-direction: column;
}

.product-card:hover {
    border-color: #38bdf8;
    box-shadow: 0 4px 16px rgba(56, 189, 248, 0.2);
}

.discount-badge {
    position: absolute;
    top: 6px;
    left: 6px;
    background: #ef4444;
    color: #fff;
    font-size: 0.68rem;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
}

.img-container {
    height: 110px;
    background: #03070f;
    display: flex;
    align-items: center;
    justify-content: center;
}

.card-img {
    max-height: 95px;
    max-width: 90%;
    object-fit: contain;
}

.card-icon {
    font-size: 2.2rem;
}

.card-content {
    padding: 8px 10px;
    display: flex;
    flex-direction: column;
    flex: 1;
    gap: 4px;
}

.category-tag {
    font-size: 0.7rem;
    color: #38bdf8;
    background: rgba(56, 189, 248, 0.1);
    padding: 1px 6px;
    border-radius: 4px;
    align-self: flex-start;
}

.card-title {
    font-size: 0.85rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0;
    line-height: 1.3;
}

.card-desc {
    font-size: 0.72rem;
    color: #94a3b8;
    margin: 0;
}

.card-rating {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.72rem;
}

.stars { color: #f59e0b; }
.rating-val { color: #f1f5f9; font-weight: 700; }
.rating-count { color: #64748b; }

.card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: auto;
    padding-top: 6px;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.price-val {
    font-size: 0.95rem;
    font-weight: 800;
    color: #38bdf8;
}

.old-price {
    font-size: 0.72rem;
    color: #64748b;
    text-decoration: line-through;
}

.details-btn {
    background: #2563eb;
    color: #ffffff !important;
    font-size: 0.72rem;
    padding: 2px 8px;
    border-radius: 5px;
    text-decoration: none;
}

.in-stock {
    font-size: 0.7rem;
    color: #22c55e;
}
"""


def create_app() -> gr.Blocks:
    """Build and return the Gradio web application."""

    with gr.Blocks(title="لوسيل سبورت — قطع غيار السيارات", css=UI_CSS) as app:
        session_id = gr.State(value=lambda: str(uuid.uuid4()))

        # Header Section
        banner_tag = f'<div class="hero-banner"><img src="{BANNER_B64}" alt="Lucile Sport" /></div>' if BANNER_B64 else ""
        logo_tag = f'<img src="{LOGO_B64}" class="logo-circle" alt="Logo" />' if LOGO_B64 else ""

        gr.HTML(f"""
        {banner_tag}
        <div class="header-panel">
            {logo_tag}
            <h1 class="brand-title">لوسيل سبورت لقطع غيار السيارات</h1>
            <p class="brand-desc">مساعدتك الذكية للبحث عن قطع الغيار، الأسعار، التوافق، وخطط التقسيط في مصر 🚗</p>
            <div class="badges-row">
                <span class="badge-item">📦 14,000+ قطعة أصلية</span>
                <span class="badge-item">💳 تقسيط 0% (3 شهور)</span>
                <span class="badge-item">🚚 شحن لكافة المحافظات</span>
            </div>
        </div>
        """)

        # Chatbot Window
        chatbot = gr.Chatbot(
            value=[],
            height=420,
            show_label=False,
            avatar_images=(None, "https://api.dicebear.com/9.x/bottts-neutral/svg?seed=lucile_auto&backgroundColor=1d4ed8"),
            placeholder="<p style='text-align:center;color:#94a3b8;padding:30px;'>👋 مرحباً بك في <b>لوسيل سبورت</b>! اسألني عن أي قطعة غيار أو موديل عربيتك 🚗</p>",
        )

        # Product Display Container
        product_box = gr.HTML(value="", visible=False)

        # Quick Chips Row
        with gr.Row(elem_classes=["quick-chips-row"]):
            btn_trending = gr.Button("🔥 الأكثر طلباً", elem_classes=["quick-chip"], size="sm")
            btn_brakes   = gr.Button("⚙️ فرامل وتيل", elem_classes=["quick-chip"], size="sm")
            btn_oil      = gr.Button("🛢️ زيوت وفلاتر", elem_classes=["quick-chip"], size="sm")
            btn_sportage = gr.Button("🚗 كيا سبورتاج", elem_classes=["quick-chip"], size="sm")
            btn_install  = gr.Button("📅 خطط التقسيط", elem_classes=["quick-chip"], size="sm")

        # User Input Row
        with gr.Row():
            user_msg = gr.Textbox(
                placeholder="اكتب استفسارك، قطعة الغيار المطلوبة، أو نوع عربيتك هنا...",
                show_label=False,
                scale=7,
                autofocus=True,
            )
            send_btn = gr.Button("إرسال ▶", variant="primary", scale=1)

        # Action Buttons Row
        with gr.Row():
            handoff_btn = gr.Button("📞 تواصل مع فني صيانة", size="sm")
            clear_btn   = gr.Button("🗑️ مسح المحادثة", size="sm")

        # Chat Handler
        def respond(message: str, history: list, sess_id: str):
            if not message or not message.strip():
                return "", history, gr.update(visible=False, value=""), sess_id

            history = history + [{"role": "user", "content": message}]

            # Detect installment query
            months = None
            m = re.search(r'\b(\d+)\s*(?:شهر|شهور|months?)\b', message, re.IGNORECASE)
            if m:
                months = int(m.group(1))

            result = pipeline.process_message(message, session_id=sess_id, installment_months=months)
            history = history + [{"role": "assistant", "content": result["message"]}]

            show_prods = bool(result.get("products"))
            prods_html = render_product_cards(result.get("products", [])) if show_prods else ""

            return "", history, gr.update(visible=show_prods, value=prods_html), sess_id

        def handle_support(history: list, sess_id: str):
            history = history + [{"role": "user", "content": "[طلب تواصل مع فني الصيانة]"}]
            result = pipeline.process_message("عايز أكلم فني الصيانة", session_id=sess_id, request_handoff=True)
            history = history + [{"role": "assistant", "content": result["message"]}]
            return history, gr.update(visible=False, value=""), sess_id

        def reset_chat():
            return [], gr.update(visible=False, value=""), str(uuid.uuid4())

        # Event Bindings
        inputs = [user_msg, chatbot, session_id]
        outputs = [user_msg, chatbot, product_box, session_id]

        user_msg.submit(respond, inputs, outputs)
        send_btn.click(respond, inputs, outputs)

        btn_trending.click(lambda h, s: respond("وريني أكثر قطع الغيار طلباً ومبيعاً", h, s), [chatbot, session_id], outputs)
        btn_brakes.click(lambda h, s: respond("وريني تيل الفرامل والطنابير المتاحة", h, s), [chatbot, session_id], outputs)
        btn_oil.click(lambda h, s: respond("عايز زيوت وفلاتر للعربيات", h, s), [chatbot, session_id], outputs)
        btn_sportage.click(lambda h, s: respond("إيه قطع الغيار المتاحة لكيا سبورتاج؟", h, s), [chatbot, session_id], outputs)
        btn_install.click(lambda h, s: respond("إيه هي أنظمة وخطط التقسيط المتاحة؟", h, s), [chatbot, session_id], outputs)

        handoff_btn.click(handle_support, [chatbot, session_id], [chatbot, product_box, session_id])
        clear_btn.click(reset_chat, [], [chatbot, product_box, session_id])

    return app


# Backwards compatibility alias
_render_product_cards = render_product_cards
