"""
Vector Retriever Module
Provides simple keyword/semantic similarity retrieval over a sample knowledge corpus.
"""
from typing import List, Dict

class SimpleKnowledgeBase:
    """In-memory knowledge base with cosine-similarity / keyword ranking."""
    def __init__(self):
        self.documents: List[Dict[str, str]] = [
            {
                "id": "doc-1",
                "title": "Agentic AI Concepts",
                "content": "Agentic AI refers to systems where an LLM is given tools, memory, and a feedback loop to autonomously make decisions and take actions towards a specific goal."
            },
            {
                "id": "doc-2",
                "title": "Retrieval Augmented Generation (RAG)",
                "content": "RAG reduces hallucinations by retrieving relevant documents from an external vector index or search engine and providing them as context in the prompt."
            },
            {
                "id": "doc-3",
                "title": "ReAct Framework",
                "content": "ReAct stands for Reason + Act. It prompts the model to generate reasoning traces ('Thought') followed by action calls ('Action') and tool observation processing ('Observation')."
            },
            {
                "id": "doc-4",
                "title": "Vector Embeddings",
                "content": "Embeddings are dense numerical vector representations of text where semantically similar texts are closer in vector space."
            }
        ]

    def query(self, search_text: str, top_k: int = 2) -> List[Dict[str, str]]:
        """Score documents based on keyword overlap for self-contained demonstration."""
        terms = set(search_text.lower().split())
        scored_docs = []
        for doc in self.documents:
            doc_words = set((doc["title"] + " " + doc["content"]).lower().split())
            overlap = len(terms.intersection(doc_words))
            if overlap > 0:
                scored_docs.append((overlap, doc))
        
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        results = [doc for _, doc in scored_docs[:top_k]]
        return results if results else self.documents[:top_k]
