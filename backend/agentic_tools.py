import functools
from typing import List, Dict, Any, Union
from sentence_transformers import SentenceTransformer
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

try:
    from backend.config import settings
except ModuleNotFoundError:
    from config import settings


@functools.lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Cached SentenceTransformer embedding model.
    Instantiated once and shared across all modules.
    """
    return SentenceTransformer(settings.EMBEDDING_MODEL)


@functools.lru_cache(maxsize=1)
def get_shared_llm() -> ChatGoogleGenerativeAI:
    """
    Cached ChatGoogleGenerativeAI instance.
    Uses settings from Pydantic config. Adjusts thinking_budget and temperature
    automatically based on model family (flash-lite models use fixed sampling).
    """
    kwargs = {
        "model": settings.GEMINI_MODEL,
        "google_api_key": settings.GOOGLE_API_KEY,
    }

    if "lite" not in settings.GEMINI_MODEL.lower():
        kwargs["temperature"] = settings.GEMINI_TEMPERATURE
        kwargs["api_version"] = settings.GEMINI_API_VERSION
        if settings.GEMINI_THINKING_BUDGET is not None:
            kwargs["thinking_budget"] = settings.GEMINI_THINKING_BUDGET

    return ChatGoogleGenerativeAI(**kwargs)


class _model:
    """
    Standardized, cached LLM chain wrapper.
    Accepts prompt template and expected variables, then executes with input dictionary.
    """
    def __init__(self, template: str, invoke_with: List[str]):
        self.template = template
        self.invoke_with = invoke_with
        self.llm = get_shared_llm()

    def execute_with(self, invoke: Dict[str, Any]) -> str:
        if set(invoke.keys()) != set(self.invoke_with):
            raise ValueError(
                f"Prompt template variables do not match expected: {self.invoke_with}, got: {list(invoke.keys())}"
            )

        prompt_template = PromptTemplate(
            input_variables=self.invoke_with,
            template=self.template,
        )
        chain = prompt_template | self.llm
        response = chain.invoke(invoke)

        if isinstance(response.content, list):
            return "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in response.content
            )
        return response.content


# Reusable embedding instance
embed = get_embedding_model()
