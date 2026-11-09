# 🛍️ E-Commerce Agentic RAG Chatbot

An intelligent, multi-modal conversational assistant for an e-commerce platform. Built with **Semantic Router**, **ChromaDB**, **LangChain Google GenAI**, **FastAPI**, and **React (TypeScript)**, this system classifies user intent and routes queries to either a **Vector FAQ RAG pipeline** or a **Type-Safe Text-to-SQL catalog search**.

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
   (database/chroma - MiniLM-L6)              (Pydantic Structured Output)
                 │                                         │
        Top-K FAQ Retrieval                       Execute SQL on SQLite
                 │                            (database/sqlite/db.sqlite)
                 ▼                                         │
    [ Response Synthesis / Direct ]                        ▼
       (LangChain Google GenAI)                  [ Formatted Product List ]
                 │                                 (Title, Price, %, Link)
                 └────────────────────┬────────────────────┘
                                      │
                                      ▼
                      ┌───────────────┴───────────────┐
                      │                               │
                      ▼                               ▼
            [ ⚡ FastAPI REST API ]          [ 💻 Streamlit UI ]
             (backend/api.py)                    (app.py)
                      │
                      ▼
            [ ⚛️ React + TypeScript ]
                 (frontend/)
```

---

## 🌟 Key Architecture & Features

1. **Semantic Intent Routing (`backend/intent_router.py`)**:
   - Classifies queries into `faq` (customer support) or `sql` (catalog searches) using dense vector similarity (`IndexedRouter`).
   - Bypasses expensive LLM calls for intent routing, delivering deterministic classification in milliseconds.

2. **ChromaDB Vector Store Singleton (`backend/setup_db.py` - `ChromaDBManager`)**:
   - Persistent client configured with HNSW cosine similarity in `database/chroma/`.
   - Uses SHA-256 file hashing to dynamically detect modifications and skip re-indexing unchanged CSVs.
   - Supports instant metadata retrieval (~5ms) and conversational LLM synthesis.

3. **Type-Safe Text-to-SQL Engine (`backend/sql_handler.py`)**:
   - Powered by **Pydantic Structured Output** (`SQLQueryOutput`) via LangChain `.with_structured_output()`.
   - **Zero Regex**: Eliminates fragile regex and tag parsing.
   - Generates reasoning (`thought_process`) before the query (`query`) to reduce hallucinated column names.
   - Enforces read-only execution: blocks non-`SELECT` statements and destructive keywords (`DROP`, `DELETE`, etc.).

4. **Centralized Configuration & Singletons (`backend/config.py` & `agentic_tools.py`)**:
   - **Pydantic Settings**: Single source of truth for all paths, database locations, and model parameters.
   - Centralized database schema (`settings.PRODUCT_SCHEMA`) dynamically injected into prompts.
   - Decoupled prompts stored in `prompts/` (`prompts/faq_prompt.txt`, `prompts/sql_generation_prompt.txt`, `prompts/sql_synthesis_prompt.txt`).
   - Singletons cached with `@functools.lru_cache(maxsize=1)` for the embedding model and Gemini LLM.

5. **Centralized Logging (`backend/logger.py`)**:
   - Standardized helpers (`log_info`, `log_success`, `log_warning`, `log_error`) for clean, uniform console output.

6. **Dual Frontend Options**:
   - **Modern React + TypeScript SPA (`frontend/`)**: Vite 8.3, React 19, interactive chat bubbles, intent pills, live health indicators, and suggestion pills.
   - **Streamlit Prototype (`app.py`)**: Fast prototyping chat interface with route tagging.

---

## 📁 Project Directory Structure

```
rag_chatbot_agentic_ai_application/
├── app.py                      # Streamlit chat interface
├── requirements.txt            # Python backend dependencies
├── .env.example                # Template for environment configuration
├── .gitignore                  # Ignores database/, .venv, node_modules/
├── README.md                   # Project documentation
│
├── backend/
│   ├── api.py                  # FastAPI server with /api/chat, /api/health
│   ├── config.py               # Pydantic Settings & environment manager
│   ├── agentic_tools.py        # Centralized LLM & embedding singletons
│   ├── intent_router.py        # Semantic Router (IndexedRouter)
│   ├── faq_handler.py          # ChromaDB FAQ vector search & synthesis
│   ├── sql_handler.py          # Text-to-SQL generation (Pydantic, zero regex)
│   ├── setup_db.py             # ChromaDBManager & SQLiteDBManager singletons
│   └── logger.py               # Centralized logging utilities
│
├── database/                   # Local database storage (ignored by git)
│   ├── chroma/                 # ChromaDB vector files
│   └── sqlite/
│       └── db.sqlite           # SQLite product catalog database
│
├── datasets/
│   ├── ecommerce_data_final.csv # E-commerce catalog dataset (903 products)
│   └── faq_data.csv             # Store policy Q&A dataset (10 FAQs)
│
├── prompts/
│   ├── faq_prompt.txt          # Context-grounded FAQ prompt template
│   ├── sql_generation_prompt.txt # SQLite query generation prompt ({schema})
│   └── sql_synthesis_prompt.txt  # Product recommendation synthesis prompt
│
└── frontend/                   # Modern React + TypeScript SPA
    ├── src/
    │   ├── App.tsx             # Main chat application component
    │   ├── App.css             # Chat UI styles & responsive layout
    │   ├── api.ts              # Type-safe API client
    │   └── types.ts            # TypeScript data models
    ├── vite.config.ts          # Vite configuration with /api backend proxy
    └── package.json            # Frontend dependencies (React, Vite, TS)
```

---

## ⚡ Quickstart Guide

### 1. Prerequisites
- **Python 3.11 or 3.12**
- **Node.js 18+ and npm**
- A Google Gemini API Key

### 2. Environment Setup
Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### 3. Python Virtual Environment & Dependencies
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install fastapi uvicorn
```

### 4. Initialize Databases
Initialize both ChromaDB and SQLite from `datasets/`:
```powershell
python -m backend.setup_db
```

---

## 🚀 Running the Application

### Option A: React + TypeScript Frontend + FastAPI Backend (Recommended)

1. **Start the FastAPI backend** (Terminal 1):
   ```powershell
   .venv\Scripts\python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
   ```
   *Swagger Docs available at:* `http://localhost:8000/docs`

2. **Start the React frontend** (Terminal 2):
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```
   *Web Application available at:* `http://localhost:5173`

---

### Option B: Streamlit Web Interface

Run the lightweight Streamlit chat application:
```powershell
.venv\Scripts\streamlit run app.py
```
*Application available at:* `http://localhost:8501`

---

## 🧪 Testing the Backend Modules

Verify any component independently from the root directory:
```powershell
# Test Intent Routing
python -m backend.intent_router

# Test FAQ Vector Search
python -m backend.faq_handler

# Test Pydantic Text-to-SQL Pipeline
python -m backend.sql_handler

# Verify Database Ingestion & Hash Checking
python -m backend.setup_db
```
