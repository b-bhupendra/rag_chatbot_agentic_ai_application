from semantic_router import Route, IndexedRouter
from semantic_router.encoders import HuggingFaceEncoder

# 1. Define Utterances for the FAQ Route
faq_utterances = [
    "What is the return policy of the products?",
    "Do I get discount with the HDFC credit card?",
    "How can I track my order?",
    "What payment methods are accepted?",
    "How long does it take to process a refund?",
    "Can I return my order?",
    "Do you accept cash on delivery?",
    "What if I receive a damaged item?",
]

# 2. Define Utterances for the SQL (Product Catalog) Route
sql_utterances = [
    "I want to buy nike shoes that have 50% discount.",
    "Are there any shoes under Rs. 3000?",
    "Do you have formal shoes in size 9?",
    "Are there any Puma shoes on sale?",
    "What is the price of puma running shoes?",
    "Show me shoes with rating above 4.5",
    "List top 5 products",
    "Find cheap running shoes",
]

# Create Route definitions
faq_route = Route(name="faq", utterances=faq_utterances)
sql_route = Route(name="sql", utterances=sql_utterances)

# Initialize modern HuggingFace encoder
encoder = HuggingFaceEncoder(name="sentence-transformers/all-MiniLM-L6-v2")

# Modern semantic-router >= 1.0 IndexedRouter
router = IndexedRouter(encoder=encoder, routes=[faq_route, sql_route])


def route_query(query: str) -> str:
    """
    Classifies user query into 'faq', 'sql', or 'none'.
    """
    match = router(query)
    return match.name if match and match.name else "none"


if __name__ == "__main__":
    queries = [
        "What is your policy on defective product?",
        "Pink Puma shoes in price range 5000 to 1000",
        "What payment methods do you support?",
        "Show me running shoes with discount",
    ]
    for q in queries:
        print(f"Query: '{q}' -> Route: {route_query(q)}")
