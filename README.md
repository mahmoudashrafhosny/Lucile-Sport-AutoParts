# 🚗 Lucile Sport — AI Sales Representative & Auto Parts RAG Chatbot
> **لوسيل سبورت لقطع غيار السيارات في مصر** — مساعد المبيعات الذكي المدعوم بالذكاء الاصطناعي والبحث الهجين (Hybrid RAG).

---

## 🌟 Overview
**Lucile Sport (لوسيل سبورت)** is an end-to-end AI Sales Assistant built for the Egyptian automotive spare parts market. It combines **LLM reasoning (Gemini & OpenRouter)** with a **Hybrid RAG search engine (FAISS + BM25)** indexing over **14,000+ real automotive parts** scraped from top Egyptian platforms (EgyCarParts, Tawfiqia, AutoSpare).

The system understands Egyptian car dialect, models (Kia Sportage, Hyundai Verna, Toyota Corolla, Nissan Sunny, Renault Logan, Fiat Tipo, etc.), calculates dynamic installment plans (0% interest for 3 months), and renders luxury visual product cards in real time.

---

## 🚀 Key Features

- **🚗 14,000+ Automotive Products Catalog**: Real spare parts with accurate EGP pricing, discounts, brands (BOSCH, BREMBO, TEXTAR, OSRAM, VALEO, DENSO, OPTIBELT), and compatibility specifications.
- **🔍 Hybrid Retrieval (Dense FAISS + Sparse BM25)**: Combines semantic embeddings (`all-MiniLM-L6-v2`) with BM25 lexical search using Reciprocal Rank Fusion (RRF).
- **🇪🇬 Egyptian Car Dialect & Synonym Mapping**: Smart mapping and expansion for queries like `اسبورتاج` ⟷ `سبورتاج` ⟷ `Sportage`, `النترا` ⟷ `Elantra`, `فيرنا` ⟷ `Verna`, `تيل` ⟷ `فرامل`, `طنابير`, `مساعدين`, `عفشة`.
- **💳 Egyptian Installment Policy Engine**:
  - 3 months: **0% interest**
  - 6 months: **5% interest**
  - 9 months: **7% interest**
  - 12 months: **10% interest**
- **🎨 Luxury Navy & Pure White UI**: Futuristic glassmorphism interface with custom hero banner, Lucile Sport brand logo, quick category chips, and real-time product cards.
- **🔄 Multi-Model Fallback**: Seamless fallback across `gemini-3.1-flash-lite`, `gemma-4-31b-it`, and OpenRouter to ensure 100% uptime.
- **👨‍💼 Human Maintenance Handoff**: Auto-detects customer maintenance inquiries and prepares an instant technical briefing summary for engineers.

---

## 📂 Project Structure

```text
Lucile-Sport-AutoParts/
│
├── .env.example               # Template for API keys
├── .gitignore                 # Protected keys and binary indexes
├── app.py                     # Entry point for the application
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
│
├── assets/                    # UI branding assets
│   ├── banner.png             # Hero banner
│   └── logo_dark.jpg          # Lucile Sport dark emblem
│
├── core/                      # Application backend core
│   ├── config.py              # Constants, rates, and paths
│   ├── data_loader.py         # CSV loading and validation
│   ├── retrieval.py           # FAISS + BM25 engine + Egyptian synonym map
│   ├── llm.py                 # Multi-LLM client with automatic fallback
│   ├── pipeline.py            # RAG orchestration, memory, and prompts
│   └── ui.py                  # Gradio frontend layout and CSS
│
└── data/                      # Dataset directory
    └── products_clean.csv     # 14,000+ cleaned auto parts dataset
```

---

## ⚙️ Quick Start & Installation

### 1. Clone the repository
```bash
git clone https://github.com/mahmoudashrafhosny/Lucile-Sport-AutoParts.git
cd Lucile-Sport-AutoParts
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

*(Or install core packages directly)*:
```bash
pip install gradio faiss-cpu sentence-transformers rank-bm25 pandas numpy requests python-dotenv
```

### 3. Configure API Key
Create a `.env` file from `.env.example`:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Run the Chatbot
```bash
python app.py
```

Open your browser at **`http://localhost:7860`**.

---

## 🛠️ Tech Stack
- **Language**: Python 3.10+
- **Frontend**: Gradio 6.0 with custom Dark Navy Glassmorphism CSS
- **Vector Search**: FAISS (Facebook AI Similarity Search)
- **Keyword Search**: BM25Okapi
- **Embeddings**: Sentence-Transformers (`all-MiniLM-L6-v2`)
- **LLMs**: Google Gemini API (`gemini-3.1-flash-lite`, `gemma-4-31b-it`) & OpenRouter

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
