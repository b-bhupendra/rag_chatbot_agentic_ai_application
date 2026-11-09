import hashlib
import sqlite3
from pathlib import Path
from typing import Optional, Union, List
import pandas as pd
import chromadb

try:
    from backend.config import settings
    from backend.agentic_tools import embed
except ModuleNotFoundError:
    from config import settings
    from agentic_tools import embed


def get_file_hash(file_path: Union[str, Path]) -> str:
    """Computes SHA256 hash of a file to detect modifications."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_chroma_client() -> chromadb.PersistentClient:
    """
    Returns a persistent ChromaDB client saving to settings.CHROMA_PERSIST_DIR.
    """
    settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(settings.CHROMA_PERSIST_DIR))


def ingest_faq_file(
    file_path: Union[str, Path] = "datasets/faq_data.csv",
    collection_name: Optional[str] = None,
    force_reload: bool = False,
) -> chromadb.Collection:
    """
    Extensible and dynamic FAQ ingestion function:
    - Reads any CSV file containing 'question' and 'answer' columns.
    - Tracks ingested files using file hashes in ChromaDB metadata.
    - If the file has already been ingested and not modified, it skips re-indexing.
    - If a new or modified file is provided, it dynamically adds/updates the records.
    """
    path = Path(file_path)
    if not path.is_absolute():
        path = settings.BASE_DIR / path

    if not path.exists():
        raise FileNotFoundError(f"FAQ file not found: {path}")

    collection_name = collection_name or settings.FAQ_COLLECTION_NAME
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    current_hash = get_file_hash(path)
    filename = path.name

    # Check if this file has already been ingested
    existing = collection.get(where={"source_file": filename})
    if existing["ids"] and not force_reload:
        first_meta = existing["metadatas"][0] if existing["metadatas"] else {}
        if first_meta.get("file_hash") == current_hash:
            print(f"ℹ️ File '{filename}' is already ingested with matching hash. Skipping re-index.")
            return collection
        else:
            print(f"🔄 File '{filename}' was modified. Updating existing records...")
            collection.delete(ids=existing["ids"])

    print(f"📥 Ingesting FAQ records from: {path}...")
    df = pd.read_csv(path)
    if "question" not in df.columns or "answer" not in df.columns:
        raise ValueError(f"File {filename} must contain 'question' and 'answer' columns.")

    documents = df["question"].astype(str).tolist()
    answers = df["answer"].astype(str).tolist()
    
    # Prefix IDs with filename to allow multiple files seamlessly
    ids = [f"{filename}_{i}" for i in range(len(df))]
    metadatas = [
        {
            "answer": answers[i],
            "source_file": filename,
            "file_hash": current_hash,
            "row_index": i,
        }
        for i in range(len(df))
    ]

    embeddings = embed.encode(documents).tolist()

    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )
    print(f"✅ Ingested {len(df)} FAQ items into collection '{collection_name}'. Total: {collection.count()}")
    return collection


def ingest_sqlite_products(
    csv_path: Union[str, Path] = "datasets/ecommerce_data_final.csv",
    table_name: str = "product",
    force_reload: bool = False,
) -> Path:
    """
    Extensible product catalog ingestion into SQLite:
    - Reads product CSV and creates/updates SQLite table.
    - If table already populated, skips re-loading unless force_reload is True.
    """
    path = Path(csv_path)
    if not path.is_absolute():
        path = settings.BASE_DIR / path

    if not path.exists():
        raise FileNotFoundError(f"Product CSV file not found: {path}")

    db_path = settings.SQLITE_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if table exists and has rows
    cursor.execute(
        "SELECT count(name) FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    table_exists = cursor.fetchone()[0] > 0

    if table_exists and not force_reload:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        if row_count > 0:
            print(f"ℹ️ SQLite table '{table_name}' already exists with {row_count} rows. Skipping re-load.")
            conn.close()
            return db_path

    print(f"📥 Loading products into SQLite table '{table_name}' from: {path}...")
    df = pd.read_csv(path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()
    print(f"✅ Loaded {len(df)} products into '{table_name}' at {db_path}.")
    return db_path


def init_all_databases(force_reload: bool = False):
    """
    Initializes both ChromaDB persistent storage and SQLite product catalog.
    """
    print("🚀 Initializing Application Databases...")
    ingest_faq_file(force_reload=force_reload)
    ingest_sqlite_products(force_reload=force_reload)
    print("✨ All databases are initialized and ready.")


if __name__ == "__main__":
    init_all_databases()
