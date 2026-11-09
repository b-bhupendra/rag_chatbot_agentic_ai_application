# RAG Chatbot Agentic AI Application

An end-to-end Agentic RAG (Retrieval-Augmented Generation) Chatbot application built for the AI Bootcamp.

## 🌟 Overview

This project demonstrates how an AI agent uses tools and retrieval-augmented generation to:
1. **Analyze user queries** and formulate a step-by-step reasoning plan.
2. **Retrieve context** from internal knowledge bases or documents.
3. **Execute tools** dynamically (retrieval, calculation, synthesis).
4. **Deliver grounded, verifiable responses** to the user.

---

## 🏗️ Architecture

```
User Query
    │
    ▼
[ Agent Controller ] ◄─── (Thought / Reasoning Loop)
    │
    ├──► [ Tool: Vector Retriever ] ──► Knowledge Base / Embeddings
    ├──► [ Tool: Calculator / Utils ] 
    │
    ▼
Synthesized & Grounded Response
```

---

## ⚡ Quickstart

### 1. Environment Setup
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys
Copy the example environment configuration:
```bash
cp .env.example .env
```
Fill in your LLM provider key (e.g. `GEMINI_API_KEY` or `OPENAI_API_KEY`).

### 4. Run the Application
```bash
python app.py
```
