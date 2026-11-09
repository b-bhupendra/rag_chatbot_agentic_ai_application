import os
import re
import sqlite3
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# Load environment configuration
load_dotenv()

DB_PATH = Path(__file__).parent / "db.sqlite"
CSV_PATH = Path(__file__).parent.parent / "datasets" / "ecommerce_data_final.csv"


def init_database():
    """
    Initializes SQLite product table from ecommerce_data_final.csv if not exists.
    """
    if not DB_PATH.exists():
        df = pd.read_csv(CSV_PATH)
        conn = sqlite3.connect(DB_PATH)
        df.to_sql("product", conn, if_exists="replace", index=False)
        conn.close()


def get_db_connection():
    return sqlite3.connect(DB_PATH)


# Initialize DB on module load
init_database()

# Initialize Google Gemini LLM with thinking turned off
llm = ChatGoogleGenerativeAI(
    model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
    temperature=0.1,
    api_version="v1beta",
    thinking_budget=0,
    google_api_key=os.environ.get("GOOGLE_API_KEY"),
)

SQL_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""You are an expert SQL engineer. Given a natural language question, generate an executable SQLite SELECT query for the 'product' table.

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
""",
)

SYNTHESIS_PROMPT = PromptTemplate(
    input_variables=["question", "data"],
    template="""You are an e-commerce shopping assistant.
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
""",
)


def extract_sql_query(raw_output: str) -> str:
    """
    Extracts raw SQL query from <SQL> tags or markdown code fences.
    """
    match = re.search(r"<SQL>(.*?)</SQL>", raw_output, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r"```sql\s*(.*?)\s*```", raw_output, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return raw_output.replace("```", "").strip()


def execute_sql_query(sql_query: str) -> pd.DataFrame:
    """
    Executes a SELECT query safely against the SQLite database.
    """
    conn = get_db_connection()
    try:
        df = pd.read_sql_query(sql_query, conn)
        return df
    finally:
        conn.close()


def handle_sql_query(user_query: str) -> str:
    """
    End-to-end Text-to-SQL pipeline:
    1. Generates SQL query using Gemini.
    2. Runs query against SQLite database.
    3. Synthesizes a natural, formatted product recommendation.
    """
    # Step 1: Generate SQL query
    sql_chain = SQL_PROMPT | llm
    raw_sql = sql_chain.invoke({"question": user_query})
    sql_text = (
        raw_sql.content
        if isinstance(raw_sql.content, str)
        else "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in raw_sql.content
        )
    )
    cleaned_sql = extract_sql_query(sql_text)

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
    synth_chain = SYNTHESIS_PROMPT | llm
    synth_res = synth_chain.invoke({"question": user_query, "data": data_str})
    output_text = (
        synth_res.content
        if isinstance(synth_res.content, str)
        else "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in synth_res.content
        )
    )
    return output_text


if __name__ == "__main__":
    test_q = "Show me Nike shoes with rating above 4"
    print("User Question:", test_q)
    print("Response:\n", handle_sql_query(test_q))
