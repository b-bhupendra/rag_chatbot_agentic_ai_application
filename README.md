# 🛍️ E-Commerce Agentic RAG Chatbot

An end-to-end intelligent conversational assistant for an e-commerce platform. Built with **Semantic Router**, **ChromaDB**, **LangChain**, and **Google Gemini**, this application intelligently classifies user intent and provides accurate responses by routing queries either to a **Vector FAQ RAG system** or a dynamic **Text-to-SQL catalog search**.

---

## 🏗️ System Architecture

```
                                  User Query
                                      │
                                      ▼
                        [ 🛣️ Semantic Intent Router ]
                       (Aurelio Labs IndexedRouter)
                                      │
                 ┌────────────────────┴────────────────────┐
                 │                                         │
                 ▼                                         ▼
         [ 'faq' Route ]                            [ 'sql' Route ]
                 │                                         │
                 ▼                                         ▼
       [ ChromaDB Vector DB ]                    [ Text-to-SQL Engine ]
   (all-MiniLM-L6-v2 Embeddings)               (LangChain Gemini 2.5 Flash)
                 │                                         │
        Top-K FAQ Retrieval                       Execute SQL on SQLite
                 │                                   (backend/db.sqlite)
                 ▼                                         │
    [ Response Synthesis / Direct ]                        ▼
       (LangChain Google GenAI)                  [ Formatted Product List ]
                 │                                 (Title, Price, %, Link)
                 └────────────────────┬────────────────────┘
                                      │
                                      ▼
                          [ 💻 Streamlit Chat UI ]
```

---

## 🌟 Key Features

1. **Semantic Intent Routing (`backend/intent_router.py`)**:
   - Classifies user queries into `faq` (customer support policies) or `sql` (product catalog searches) using dense vector similarity (`IndexedRouter`).
   - Prevents unnecessary LLM calls and routes queries deterministically in milliseconds.

2. **FAQ Vector Search (`backend/faq_handler.py`)**:
   - Embeds FAQ questions into a persistent **ChromaDB** vector store using local `sentence-transformers/all-MiniLM-L6-v2`.
   - Supports both instant direct metadata retrieval (~5ms) and LLM-assisted conversational synthesis.

3. **Text-to-SQL Product Querying (`backend/sql_handler.py`)**:
   - Converts natural language product queries (e.g., *"Nike shoes under ₹4000 with rating above 4"*) into sanitized SQLite queries.
   - Executes against a 900+ product catalog in `backend/db.sqlite` and presents clean, clickable markdown recommendations.

4. **Centralized Configuration & Singletons (`backend/config.py` & `agentic_tools.py`)**:
   - Managed via **Pydantic Settings** (`pydantic-settings`).
   - Employs `@functools.lru_cache` singletons for LLM clients and embedding models to prevent repeated initialization overhead.
   - Deep reasoning / thinking budget turned off (`thinking_budget=0`) for ultra-fast Gemini responses (~1.3s).

5. **Extensible Ingestion with File Hashing (`backend/setup_db.py`)**:
   - SHA-256 hash checks prevent re-indexing unchanged datasets.
   - Easily handles new or updated CSV files dynamically.

6. **Interactive Web Interface (`app.py`)**:
   - Built with **Streamlit** chat components, persistent session state, and visual route-tagging badges.

---

## 📁 Project Directory Structure

```
rag_chatbot_agentic_ai_application/
├── app.py                      # Streamlit chat interface
├── requirements.txt            # Python dependencies
├── .env.example                # Template for environment configuration
├── .gitignore                  # Excludes .env, .venv, chroma_db/
├── README.md                   # Project documentation
│
├── backend/
│   ├── config.py               # Pydantic Settings & environment manager
│   ├── agentic_tools.py        # Centralized LLM & embedding singletons
│   ├── intent_router.py        # Semantic Router (IndexedRouter)
│   ├── faq_handler.py          # ChromaDB FAQ vector search & synthesis
│   ├── sql_handler.py          # Text-to-SQL generation & catalog query
│   ├── setup_db.py             # Hash-based DB initialization script
│   ├── db.sqlite               # SQLite product database
│   └── chroma_db/              # Persistent ChromaDB vector files (ignored by git)
│
└── datasets/
    ├── ecommerce_data_final.csv # E-commerce catalog dataset
    └── faq_data.csv             # Store policy Q&A dataset
```

---

## ⚡ Setup & Installation

### 1. Prerequisites
- **Python 3.11 or 3.12** (recommended for full pre-built binary wheel compatibility with PyTorch and ChromaDB).
- A Google Gemini API Key.

### 2. Create and Activate Virtual Environment
```powershell
py -3.12 -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and insert your Gemini API Key:
```env
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### 5. Initialize Databases
Populate persistent ChromaDB FAQ embeddings and the SQLite product catalog:
```bash
python -m backend.setup_db
```

---

## 🚀 Running the Application

Launch the Streamlit web interface:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 Testing Individual Modules

Each backend module includes standalone CLI execution blocks for quick testing:

* **Test Intent Router:**
  ```bash
  python -m backend.intent_router
  ```
* **Test FAQ Vector Search:**
  ```bash
  python -m backend.faq_handler
  ```
* **Test Text-to-SQL Catalog Query:**
  ```bash
  python -m backend.sql_handler
  ```
