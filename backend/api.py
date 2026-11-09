import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from backend.config import settings
    from backend.setup_db import chroma_db, sql_db, init_all_databases
    from backend.intent_router import route_query
    from backend.faq_handler import handle_faq_query
    from backend.sql_handler import handle_sql_query, handle_sql_query_with_products
    from backend.logger import log_info, log_success, log_error
except ModuleNotFoundError:
    from config import settings
    from setup_db import chroma_db, sql_db, init_all_databases
    from intent_router import route_query
    from faq_handler import handle_faq_query
    from sql_handler import handle_sql_query, handle_sql_query_with_products
    from logger import log_info, log_success, log_error


# =====================================================================
# 1. Pydantic Request & Response Schemas
# =====================================================================

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The user's input question or search query.")
    session_id: Optional[str] = Field(default=None, description="Optional session/conversation identifier.")
    use_llm_for_faq: bool = Field(default=True, description="Whether to synthesize FAQ responses with Gemini.")


class ChatResponse(BaseModel):
    response: str = Field(..., description="The assistant's generated response.")
    route: str = Field(..., description="The intent route: 'faq', 'sql', or 'fallback'.")
    elapsed_seconds: float = Field(..., description="Response latency in seconds.")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    products: Optional[List[Dict[str, Any]]] = Field(default=None, description="Structured product results if query returned products.")
    sql_query: Optional[str] = Field(default=None, description="Executed SQL query if available.")


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Query string for dedicated testing.")


class RouteResponse(BaseModel):
    query: str
    route: str


class HealthResponse(BaseModel):
    status: str
    model: str
    faq_count: int
    product_count: int
    chroma_dir: str
    sqlite_path: str


class SuggestionItem(BaseModel):
    text: str
    category: str


# =====================================================================
# 2. Application Lifespan & Initialization
# =====================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensures databases and embeddings are initialized upon server startup."""
    log_info("Starting FastAPI server for E-Commerce RAG Assistant...")
    try:
        init_all_databases()
        log_success("All databases verified and ready for API traffic.")
    except Exception as e:
        log_error(f"Failed to initialize databases on startup: {e}")
    yield
    log_info("Shutting down FastAPI server.")


app = FastAPI(
    title="E-Commerce Agentic RAG Chatbot API",
    description="FastAPI service connecting Semantic Router, ChromaDB FAQ vector search, and Text-to-SQL product recommendations.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================================
# 3. API Routes
# =====================================================================

@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Returns system status, active Gemini model, and database statistics."""
    try:
        faq_collection = chroma_db.get_collection()
        faq_count = faq_collection.count()
    except Exception:
        faq_count = 0

    try:
        conn = sql_db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM product")
        product_count = cursor.fetchone()[0]
        conn.close()
    except Exception:
        product_count = 0

    return HealthResponse(
        status="healthy",
        model=settings.GEMINI_MODEL,
        faq_count=faq_count,
        product_count=product_count,
        chroma_dir=str(settings.CHROMA_PERSIST_DIR),
        sqlite_path=str(settings.SQLITE_DB_PATH),
    )


@app.get("/api/suggestions", response_model=List[SuggestionItem], tags=["Chat"])
def get_prompt_suggestions():
    """Provides sample questions to populate interactive suggestion pills in the frontend."""
    return [
        SuggestionItem(text="What is your return policy?", category="FAQ"),
        SuggestionItem(text="Can I return my order?", category="FAQ"),
        SuggestionItem(text="What payment methods do you accept?", category="FAQ"),
        SuggestionItem(text="Show me Nike shoes with rating above 4", category="Catalog"),
        SuggestionItem(text="Find Puma shoes under 3000", category="Catalog"),
        SuggestionItem(text="Are there any running shoes with 50% discount?", category="Catalog"),
    ]


@app.get("/api/products/featured", response_model=List[Dict[str, Any]], tags=["Products"])
def get_featured_products(limit: int = 8):
    """Returns top-rated popular products to display on the storefront showcase."""
    try:
        conn = sql_db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT product_link, title, brand, price, discount, avg_rating, total_ratings
            FROM product
            WHERE avg_rating >= 4.0
            ORDER BY avg_rating DESC, total_ratings DESC
            LIMIT ?
            """,
            (limit,)
        )
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        log_error(f"Failed to fetch featured products: {e}")
        return []



@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
def chat(request: ChatRequest):
    """
    Primary chat orchestration endpoint:
    1. Classifies intent using Semantic Router (IndexedRouter) -> 'faq' or 'sql'.
    2. Dispatches to handle_faq_query() or handle_sql_query().
    3. Returns response, route tag, and execution latency.
    """
    user_query = request.message.strip()
    if not user_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty."
        )

    log_info(f"Incoming chat query: '{user_query}'")
    start_time = time.time()

    try:
        selected_route = route_query(user_query)
        products = None
        sql_query = None

        if selected_route == "faq":
            response_text = handle_faq_query(user_query, use_llm=request.use_llm_for_faq)
        elif selected_route == "sql":
            sql_result = handle_sql_query_with_products(user_query)
            response_text = sql_result["response"]
            products = sql_result.get("products")
            sql_query = sql_result.get("sql_query")
        else:
            # Fallback to FAQ search for general store inquiries
            response_text = handle_faq_query(user_query, use_llm=request.use_llm_for_faq)
            selected_route = "fallback"

        elapsed = round(time.time() - start_time, 2)
        log_success(f"Dispatched via '{selected_route.upper()}' in {elapsed}s")

        return ChatResponse(
            response=response_text,
            route=selected_route,
            elapsed_seconds=elapsed,
            products=products,
            sql_query=sql_query,
        )

    except Exception as e:
        log_error(f"Error handling chat query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your request: {str(e)}"
        )


@app.post("/api/route", response_model=RouteResponse, tags=["Utilities"])
def test_routing(request: QueryRequest):
    """Utility endpoint to test intent routing classification independently."""
    route = route_query(request.query)
    return RouteResponse(query=request.query, route=route)


@app.post("/api/faq", response_model=ChatResponse, tags=["Direct Handlers"])
def direct_faq(request: QueryRequest):
    """Directly queries the ChromaDB FAQ handler, bypassing the intent router."""
    start_time = time.time()
    response_text = handle_faq_query(request.query)
    elapsed = round(time.time() - start_time, 2)
    return ChatResponse(response=response_text, route="faq", elapsed_seconds=elapsed)


@app.post("/api/sql", response_model=ChatResponse, tags=["Direct Handlers"])
def direct_sql(request: QueryRequest):
    """Directly queries the Text-to-SQL handler, bypassing the intent router."""
    start_time = time.time()
    sql_result = handle_sql_query_with_products(request.query)
    elapsed = round(time.time() - start_time, 2)
    return ChatResponse(
        response=sql_result["response"],
        route="sql",
        elapsed_seconds=elapsed,
        products=sql_result.get("products"),
        sql_query=sql_result.get("sql_query"),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api:app", host="0.0.0.0", port=8000, reload=True)

