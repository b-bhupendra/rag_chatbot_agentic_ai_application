import os
import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
# LangChain & Google GenAI Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
# Load environment variables
load_dotenv()

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.Client()

def ingest_faq_data(csv_path="datasets/faq_data.csv"):
    """
    Ingests FAQ questions into ChromaDB collection.
    Only questions are stored as embeddings; answers are kept in metadata.
    Avoids re-ingestion if data is already present.
    """
    collection = chroma_client.get_or_create_collection(name="faq_collection")
    if collection.count() > 0:
        return collection

    df = pd.read_csv(csv_path)
    documents = df["question"].tolist()
    metadatas = [{"answer": ans} for ans in df["answer"].tolist()]
    ids = [f"id_{i}" for i in range(len(df))]
    
    embeddings = embedding_model.encode(documents).tolist()
    
    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    return collection

def retrieve_faq_context(query, collection, n_results=2):
    """
    Performs vector similarity search against stored questions to retrieve answers.
    """
    query_embedding = embedding_model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results
    )
    
    matched_answers = [meta["answer"] for meta in results["metadatas"][0]]
    return "\n".join(matched_answers)

def generate_faq_response_langchain(user_query, context):
    """
    Uses LangChain and Google GenAI (Gemini) to synthesize a coherent response.
    """
    # 1. Initialize Google Gemini LLM via LangChain
    llm = ChatGoogleGenerativeAI(
        model=os.environ.get("GEMINI_MODEL"),
        temperature=0.2,
        google_api_key=os.environ.get("GOOGLE_API_KEY")
    )

    # 2. Define a PromptTemplate using LangChain Core
    prompt_template = PromptTemplate(
        input_variables=["context", "user_query"],
        template="""You are a helpful customer service AI for an e-commerce platform.
                    Answer the user query based ONLY on the provided FAQ context.

                    FAQ Context:
                        {context}

                    User Question: {user_query}
                Answer: """
    )

    # 3. Create a Chain using the Runnable Pipe (|) operator
    chain = prompt_template | llm

    # 4. Invoke the chain with variables
    response = chain.invoke({"context": context, "user_query": user_query})
    
    if isinstance(response.content, list):
        return "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in response.content)
    return response.content


def handle_faq_query(user_query):
    """
    Main entry function for the FAQ RAG Pipeline.
    """
    collection = ingest_faq_data()
    context = retrieve_faq_context(user_query, collection)
    return generate_faq_response_langchain(user_query, context)


if __name__ == "__main__":
    test_query = "Can I pay when the product arrives at my house?"
    print("User Question:", test_query)
    print("Chatbot Answer:", handle_faq_query(test_query))