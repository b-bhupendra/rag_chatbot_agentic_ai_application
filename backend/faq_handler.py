from typing import Optional

try:
    from backend.config import settings
    from backend.agentic_tools import _model
    from backend.setup_db import chroma_db
    from backend.logger import log_info, log_success, log_warning, log_error
except ModuleNotFoundError:
    from config import settings
    from agentic_tools import _model
    from setup_db import chroma_db
    from logger import log_info, log_success, log_warning, log_error


# Initialize cached _model instance using prompt loaded via settings
faq_model = _model(
    template=settings.FAQ_PROMPT,
    invoke_with=["context", "user_query"],
)


def retrieve_faq_context(query: str, n_results: int = 2) -> str:
    """
    Performs vector similarity search against stored FAQ questions
    using the singleton ChromaDBManager instance.
    """
    return chroma_db.retrieve_context(query=query, n_results=n_results)


def handle_faq_query(user_query: str, use_llm: bool = True) -> str:
    """
    Main entry function for FAQ retrieval:
    - If use_llm=False: returns direct ChromaDB answer in ~5ms.
    - If use_llm=True: synthesizes friendly answer using centralized Gemini model with settings.FAQ_PROMPT.
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
