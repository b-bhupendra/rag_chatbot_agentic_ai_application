import hashlib
import sqlite3
from pathlib import Path
from typing import Optional, Union
import pandas as pd
import chromadb

try:
    from backend.config import settings
    from backend.agentic_tools import embed
    from backend.logger import log_info, log_success, log_warning, log_error
except ModuleNotFoundError:
    from config import settings
    from agentic_tools import embed
    from logger import log_info, log_success, log_warning, log_error


def get_file_hash(file_path: Union[str, Path]) -> str:
    """Computes SHA256 hash of a file to detect modifications."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


# ==========================================
# 1. ChromaDB Vector Database Ingestion (FAQ)
# ==========================================

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

    # Check if this file has already been ingested with the same hash
    existing = collection.get(where={"source_file": filename})
    if existing["ids"] and not force_reload:
        first_meta = existing["metadatas"][0] if existing["metadatas"] else {}
        if first_meta.get("file_hash") == current_hash:
            log_info(f"File '{filename}' is already indexed in collection '{collection_name}' with matching hash. Skipping.")
            return collection
        else:
            log_info(f"File '{filename}' was modified. Refreshing records in collection '{collection_name}'...")
            collection.delete(ids=existing["ids"])

    log_info(f"Ingesting FAQ records from: {path}...")
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
    log_success(f"Ingested {len(df)} FAQ items into collection '{collection_name}'. Total: {collection.count()}")
    return collection


# ==========================================
# 2. SQLite Database Ingestion (Product Catalog & Arbitrary CSVs)
# ==========================================

def _ensure_sqlite_metadata_table(conn: sqlite3.Connection) -> None:
    """Creates internal metadata table to track file hashes for SQLite tables."""
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS _ingestion_metadata (
        table_name TEXT PRIMARY KEY,
        source_file TEXT,
        file_hash TEXT,
        row_count INTEGER,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()


def ingest_sqlite_table(
    csv_path: Union[str, Path],
    table_name: str = "product",
    force_reload: bool = False,
) -> Path:
    """
    Extensible and lean SQLite ingestion function:
    - Ingests ANY CSV file into any specified table in db.sqlite.
    - Uses SHA-256 hash tracking via _ingestion_metadata to avoid re-reading unmodified files.
    - If modified or new, replaces table and updates metadata hash.
    """
    path = Path(csv_path)
    if not path.is_absolute():
        path = settings.BASE_DIR / path

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    db_path = settings.SQLITE_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)

    current_hash = get_file_hash(path)
    filename = path.name

    conn = sqlite3.connect(db_path)
    try:
        _ensure_sqlite_metadata_table(conn)
        cursor = conn.cursor()

        # Check if table already exists with matching hash
        cursor.execute(
            "SELECT file_hash, row_count FROM _ingestion_metadata WHERE table_name = ?",
            (table_name,),
        )
        meta_row = cursor.fetchone()

        if meta_row and not force_reload:
            saved_hash, row_count = meta_row
            if saved_hash == current_hash:
                log_info(f"SQLite table '{table_name}' is already up-to-date ({row_count} rows, hash matched). Skipping.")
                return db_path
            else:
                log_info(f"File '{filename}' modified. Refreshing SQLite table '{table_name}'...")

        # Ingest CSV into SQLite table
        log_info(f"Loading '{filename}' into SQLite table '{table_name}'...")
        df = pd.read_csv(path)
        df.to_sql(table_name, conn, if_exists="replace", index=False)

        # Update metadata table
        cursor.execute("""
        INSERT OR REPLACE INTO _ingestion_metadata (table_name, source_file, file_hash, row_count, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (table_name, filename, current_hash, len(df)))
        conn.commit()

        log_success(f"Loaded {len(df)} records into SQLite table '{table_name}' at {db_path}.")
        return db_path
    finally:
        conn.close()


def ingest_sqlite_products(
    csv_path: Union[str, Path] = "datasets/ecommerce_data_final.csv",
    table_name: str = "product",
    force_reload: bool = False,
) -> Path:
    """Convenience alias for ingesting the product catalog into SQLite."""
    return ingest_sqlite_table(csv_path=csv_path, table_name=table_name, force_reload=force_reload)


def setup_database(force_reload: bool = False) -> Path:
    """
    Initializes the SQLite database with products.
    Backward-compatible entry point for the tutorial interface.
    """
    log_info("Setting up SQLite product database...")
    return ingest_sqlite_products(force_reload=force_reload)


def init_all_databases(force_reload: bool = False) -> None:
    """
    Initializes both ChromaDB persistent storage and SQLite product catalog.
    """
    log_info("Initializing all application databases (ChromaDB + SQLite)...")
    ingest_faq_file(force_reload=force_reload)
    ingest_sqlite_products(force_reload=force_reload)
    log_success("All databases are initialized and ready.")


if __name__ == "__main__":
    init_all_databases()
