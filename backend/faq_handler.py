from typing import Optional
from pathlib import Path
import chromadb

try:
    from backend.config import settings
    from backend.agentic_tools import _model, embed
    from backend.setup_db import ingest_faq_file, get_chroma_client
except ModuleNotFoundError:
    from config import settings
    from agentic_tools import _model, embed
    from setup_db import ingest_faq_file, get_chroma_client

FAQ_PROMPT_TEMPLATE = """You are a helpful customer service AI for an e-commerce platform.
Answer the user query based ONLY on the provided FAQ context.

FAQ Context:
{context}

User Question: {user_query}
Answer: """

# Initialize cached _model instance for FAQ synthesis
faq_model = _model(
    template=FAQ_PROMPT_TEMPLATE,
    invoke_with=["context", "user_query"],
)


def get_faq_collection(collection_name: Optional[str] = None) -> chromadb.Collection:
    """
    Retrieves or ingests the FAQ collection using persistent ChromaDB storage.
    """
    collection_name = collection_name or settings.FAQ_COLLECTION_NAME
    client = get_chroma_client()
    try:
        coll = client.get_collection(name=collection_name)
        if coll.count() > 0:
            return coll
    except Exception:
        pass
    # Ingest if not present
    return ingest_faq_file(collection_name=collection_name)


def retrieve_faq_context(query: str, collection: Optional[chromadb.Collection] = None, n_results: int = 2) -> str:
    """
    Performs vector similarity search against stored FAQ questions to retrieve matching answers.
    """
    collection = collection or get_faq_collection()
    query_embedding = embed.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
    )

    if results["metadatas"] and results["metadatas"][0]:
        matched_answers = [meta["answer"] for meta in results["metadatas"][0]]
        return "\n".join(matched_answers)
    return "No matching FAQ information found."


def handle_faq_query(user_query: str, use_llm: bool = True) -> str:
    """
    Main entry function for FAQ retrieval:
    - If use_llm=False: returns direct ChromaDB answer in ~5ms.
    - If use_llm=True: synthesizes friendly answer using centralized Gemini model.
    """
    context = retrieve_faq_context(user_query)
    if not use_llm:
        return context
    return faq_model.execute_with({"context": context, "user_query": user_query})


if __name__ == "__main__":
    test_query = "Can I pay when the product arrives at my house?"
    print("User Question:", test_query)
    print("Direct Answer (no LLM):", handle_faq_query(test_query, use_llm=False))
    print("Synthesized Answer (with LLM):", handle_faq_query(test_query, use_llm=True))
