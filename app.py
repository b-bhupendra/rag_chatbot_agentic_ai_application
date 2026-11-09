import streamlit as st
import time
from backend.faq_handler import handle_faq_query
from backend.intent_router import route_query
from backend.sql_handler import handle_sql_query

# Page Configuration
st.set_page_config(
    page_title="E-Commerce AI Assistant",
    page_icon="🛍️",
    layout="centered",
)

st.title("🛍️ E-Commerce AI Assistant")
st.caption("Powered by ChromaDB Vector Search, Semantic Router & LangChain Google Gemini")

# Initialize Chat History in session_state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I can answer store policy questions (FAQ) or search products from our catalog (Text-to-SQL). How can I assist you today?",
            "route": "system",
        }
    ]

# Display Chat Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("route") and message["route"] != "system":
            st.caption(f"🛣️ Routed via: `{message['route'].upper()}`")

# User Input Widget
if prompt := st.chat_input("Ask about products, pricing, discounts, returns, or shipping..."):
    # Append and display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process Query through Router & Handlers
    with st.chat_message("assistant"):
        with st.spinner("Classifying intent and retrieving response..."):
            start_time = time.time()
            selected_route = route_query(prompt)

            if selected_route == "faq":
                response = handle_faq_query(prompt)
            elif selected_route == "sql":
                response = handle_sql_query(prompt)
            else:
                # Fallback to FAQ search if route is ambiguous
                response = handle_faq_query(prompt)
                selected_route = "faq (fallback)"

            elapsed = time.time() - start_time

            st.markdown(response)
            st.caption(f"🛣️ Routed via: `{selected_route.upper()}` | ⚡ {elapsed:.2f}s")

    # Store assistant response in history
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
            "route": selected_route,
        }
    )

