from typing import Union, List, Dict, Any, Optional
import pandas as pd
from pydantic import BaseModel, Field

try:
    from backend.config import settings
    from backend.agentic_tools import _model
    from backend.setup_db import sql_db
    from backend.logger import log_info, log_success, log_warning, log_error
except ModuleNotFoundError:
    from config import settings
    from agentic_tools import _model
    from setup_db import sql_db
    from logger import log_info, log_success, log_warning, log_error


class SQLQueryOutput(BaseModel):
    """
    Structured Pydantic schema for SQL query generation.
    Using thought_process before query enables autoregressive reasoning (CoT)
    to accurately map filters and column names.
    """
    thought_process: str = Field(
        description="Brief step-by-step reasoning about required filters, sorting, and limit clauses based strictly on the schema."
    )
    query: str = Field(
        description="The clean, executable SQLite SELECT query. Must start with SELECT and adhere strictly to the schema."
    )


# Structured model for query generation (zero regex required)
sql_generator_model = _model(
    template=settings.SQL_GENERATION_PROMPT,
    invoke_with=["schema", "question"],
    output_schema=SQLQueryOutput,
)

# Standard model for response synthesis
synthesis_model = _model(
    template=settings.SQL_SYNTHESIS_PROMPT,
    invoke_with=["question", "data"],
)


def generate_sql_query(user_query: str) -> str:
    """
    Translates a natural language question into a safe SQLite query
    using Pydantic structured output directly from Gemini (bypassing regex entirely).
    """
    log_info(f"Generating structured SQL query for: '{user_query}'...")
    schema = sql_db.get_schema("product")
    result: SQLQueryOutput = sql_generator_model.execute_with({
        "schema": schema,
        "question": user_query,
    })
    log_info(f"Reasoning: {result.thought_process}")
    log_info(f"Generated SQL: {result.query}")
    return result.query.strip()


def execute_sql_query(query: str) -> pd.DataFrame:
    """
    Executes generated SELECT SQL query safely via SQLiteDBManager singleton.
    Security checks (enforcing SELECT and blocking destructive keywords)
    and connection pooling are handled by the singleton.
    """
    return sql_db.execute_query(query)


def synthesize_sql_response(user_query: str, data: Union[pd.DataFrame, List[Dict[str, Any]], str]) -> str:
    """
    Converts raw database query results into a natural language conversational summary
    using the centralized Gemini model and external prompt template.
    """
    if isinstance(data, pd.DataFrame):
        data_str = "No matching products found." if data.empty else data.to_string(index=False)
    elif isinstance(data, list):
        data_str = "No matching products found." if not data else str(data)
    else:
        data_str = str(data)

    log_info("Synthesizing user response from query results...")
    return synthesis_model.execute_with({"question": user_query, "data": data_str})


def handle_sql_query(user_query: str) -> str:
    """
    Main orchestration function for the Text-to-SQL pipeline:
    1. Generates structured SQL query with cached Gemini model (Pydantic, zero regex).
    2. Executes SQL query safely via SQLiteDBManager singleton.
    3. Synthesizes a friendly, formatted product recommendation.
    """
    try:
        sql_query = generate_sql_query(user_query)
        data = execute_sql_query(sql_query)
        return synthesize_sql_response(user_query, data)
    except Exception as e:
        log_error(f"Text-to-SQL pipeline failed: {e}")
        return f"I encountered an issue retrieving the products: {str(e)}"


# --- Quick Test Run ---
if __name__ == "__main__":
    test_q = "Show me Nike shoes with rating above 4"
    print("User Question:", test_q)
    print("Response:\n", handle_sql_query(test_q))
