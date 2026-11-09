import re
import sqlite3
import pandas as pd

try:
    from backend.config import settings
    from backend.agentic_tools import _model
    from backend.setup_db import ingest_sqlite_products
except ModuleNotFoundError:
    from config import settings
    from agentic_tools import _model
    from setup_db import ingest_sqlite_products


# Reusable centralized models using prompts imported via settings
sql_generator_model = _model(
    template=settings.SQL_GENERATION_PROMPT,
    invoke_with=["question"],
)

synthesis_model = _model(
    template=settings.SQL_SYNTHESIS_PROMPT,
    invoke_with=["question", "data"],
)


def get_db_connection() -> sqlite3.Connection:
    """Returns connection to centralized SQLite DB path."""
    if not settings.SQLITE_DB_PATH.exists():
        ingest_sqlite_products()
    return sqlite3.connect(settings.SQLITE_DB_PATH)


def extract_sql_query(raw_output: str) -> str:
    """Extracts raw SQL query from <SQL> tags or markdown code fences."""
    match = re.search(r"<SQL>(.*?)</SQL>", raw_output, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r"```sql\s*(.*?)\s*```", raw_output, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return raw_output.replace("```", "").strip()


def execute_sql_query(sql_query: str) -> pd.DataFrame:
    """Executes a SELECT query safely against the SQLite database."""
    conn = get_db_connection()
    try:
        df = pd.read_sql_query(sql_query, conn)
        return df
    finally:
        conn.close()


def handle_sql_query(user_query: str) -> str:
    """
    End-to-end Text-to-SQL pipeline:
    1. Generates SQL query using centralized Gemini model with settings.SQL_GENERATION_PROMPT.
    2. Runs query against SQLite database.
    3. Synthesizes a natural, formatted product recommendation with settings.SQL_SYNTHESIS_PROMPT.
    """
    # Step 1: Generate SQL query
    raw_sql = sql_generator_model.execute_with({"question": user_query})
    cleaned_sql = extract_sql_query(raw_sql)

    # Step 2: Execute SQL query
    try:
        df = execute_sql_query(cleaned_sql)
    except Exception as e:
        return f"Error executing query: {str(e)}"

    if df.empty:
        data_str = "No matching products found."
    else:
        data_str = df.to_string(index=False)

    # Step 3: Synthesize final response
    return synthesis_model.execute_with({"question": user_query, "data": data_str})


if __name__ == "__main__":
    test_q = "Show me Nike shoes with rating above 4"
    print("User Question:", test_q)
    print("Response:\n", handle_sql_query(test_q))
