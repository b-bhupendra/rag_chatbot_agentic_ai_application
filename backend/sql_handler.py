import re
import sqlite3
import pandas as pd
from pathlib import Path

try:
    from backend.config import settings
    from backend.agentic_tools import _model
    from backend.setup_db import ingest_sqlite_products
except ModuleNotFoundError:
    from config import settings
    from agentic_tools import _model
    from setup_db import ingest_sqlite_products


SQL_PROMPT_TEMPLATE = """You are an expert SQL engineer. Given a natural language question, generate an executable SQLite SELECT query for the 'product' table.

<schema>
Table: product
Columns:
- product_link: TEXT (hyperlink to product)
- title: TEXT (title of the product)
- brand: TEXT (brand of product, e.g. Nike, Puma, Campus)
- price: INTEGER (price in Indian Rupees)
- discount: REAL (e.g., 0.10 for 10% off, 0.50 for 50% off)
- avg_rating: REAL (rating from 0 to 5.0)
- total_ratings: INTEGER (number of user reviews)
</schema>

Rules:
1. Always use 'SELECT *' so all product details are retrieved.
2. For brand matching, use case-insensitive LIKE: e.g. LOWER(brand) LIKE '%nike%'. Never use ILIKE.
3. If looking for discounts, remember discount is a float (e.g. 50% discount is 'discount >= 0.50').
4. Always add LIMIT 5 unless the user requests a specific count.
5. Output ONLY the raw SQL query wrapped inside <SQL> and </SQL> tags.

Question: {question}
SQL Query:
"""

SYNTHESIS_PROMPT_TEMPLATE = """You are an e-commerce shopping assistant.
Formulate a helpful and friendly response to the customer's question based ONLY on the provided product data.

Question: {question}
Product Data:
{data}

Formatting Rules:
- If products are found, present each product clearly as a numbered list with:
  Title: [Product Title]
  Price: ₹[Price] ([Discount * 100]% off) | Rating: [Rating]⭐ ([Total Ratings] reviews)
  Link: [Product Link]
- If no products match, politely explain that no matching items were found and suggest adjusting their filters.
- Keep the response clean, friendly, and concise.
"""

# Reusable centralized models using Pydantic settings & LRU cache
sql_generator_model = _model(
    template=SQL_PROMPT_TEMPLATE,
    invoke_with=["question"],
)

synthesis_model = _model(
    template=SYNTHESIS_PROMPT_TEMPLATE,
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
    1. Generates SQL query using centralized Gemini model.
    2. Runs query against SQLite database.
    3. Synthesizes a natural, formatted product recommendation.
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
