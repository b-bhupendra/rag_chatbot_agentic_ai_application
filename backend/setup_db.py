import hashlib
import re
import sqlite3
from pathlib import Path
from typing import Optional, Union, List, Dict, Any
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


# =====================================================================
# 1. ChromaDB Vector Database Manager (Singleton)
# =====================================================================

class ChromaDBManager:
    """
    Singleton wrapper for ChromaDB vector operations:
    - Persistent client management in settings.CHROMA_PERSIST_DIR
    - HNSW cosine similarity collections
    - Dynamic FAQ ingestion with SHA-256 hash change detection
    - Semantic vector context retrieval
    """
    _instance: Optional["ChromaDBManager"] = None

    def __new__(cls, *args, **kwargs) -> "ChromaDBManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, persist_dir: Optional[Union[str, Path]] = None) -> None:
        if self._initialized:
            return
        self.persist_dir = Path(persist_dir or settings.CHROMA_PERSIST_DIR)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self._initialized = True

    def get_collection(self, collection_name: Optional[str] = None) -> chromadb.Collection:
        """Retrieves an existing ChromaDB collection."""
        name = collection_name or settings.FAQ_COLLECTION_NAME
        return self.client.get_collection(name=name)

    def get_or_create_collection(self, collection_name: Optional[str] = None) -> chromadb.Collection:
        """Retrieves or creates a ChromaDB collection using cosine similarity."""
        name = collection_name or settings.FAQ_COLLECTION_NAME
        return self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}
        )

    def ingest_faq_file(
        self,
        file_path: Optional[Union[str, Path]] = None,
        collection_name: Optional[str] = None,
        force_reload: bool = False,
    ) -> chromadb.Collection:
        """
        Ingests a CSV of FAQs into ChromaDB with SHA-256 hash checking.
        Defaults to settings.FAQ_DATA_PATH. Skips re-indexing if unmodified.
        """
        raw_path = file_path or settings.FAQ_DATA_PATH
        path = Path(raw_path)
        if not path.is_absolute():
            path = settings.BASE_DIR / path

        if not path.exists():
            raise FileNotFoundError(f"FAQ file not found: {path}")

        collection = self.get_or_create_collection(collection_name)
        current_hash = get_file_hash(path)
        filename = path.name

        # Check existing metadata for hash match
        existing = collection.get(where={"source_file": filename})
        if existing["ids"] and not force_reload:
            first_meta = existing["metadatas"][0] if existing["metadatas"] else {}
            if first_meta.get("file_hash") == current_hash:
                log_info(f"File '{filename}' is already indexed in Chroma collection '{collection.name}' (hash matched). Skipping.")
                return collection
            else:
                log_info(f"File '{filename}' was modified. Refreshing records in collection '{collection.name}'...")
                collection.delete(ids=existing["ids"])

        log_info(f"Ingesting FAQ records from: {path}...")
        df = pd.read_csv(path)
        if "question" not in df.columns or "answer" not in df.columns:
            raise ValueError(f"File {filename} must contain 'question' and 'answer' columns.")

        documents = df["question"].astype(str).tolist()
        answers = df["answer"].astype(str).tolist()

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
        log_success(f"Ingested {len(df)} FAQ items into collection '{collection.name}'. Total: {collection.count()}")
        return collection

    def retrieve_context(
        self,
        query: str,
        collection_name: Optional[str] = None,
        n_results: int = 2,
    ) -> str:
        """
        Queries ChromaDB for semantic matches and returns the concatenated answer text.
        """
        name = collection_name or settings.FAQ_COLLECTION_NAME
        try:
            collection = self.get_collection(name)
            if collection.count() == 0:
                collection = self.ingest_faq_file(collection_name=name)
        except Exception:
            collection = self.ingest_faq_file(collection_name=name)

        query_embedding = embed.encode([query]).tolist()
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
        )

        if results["metadatas"] and results["metadatas"][0]:
            matched_answers = [meta["answer"] for meta in results["metadatas"][0]]
            return "\n".join(matched_answers)
        return "No matching FAQ information found."


# =====================================================================
# 2. SQLite Database Manager (Singleton)
# =====================================================================

class SQLiteDBManager:
    """
    Singleton wrapper for SQLite relational database operations:
    - Connection lifecycle management in settings.SQLITE_DB_PATH
    - Arbitrary CSV ingestion with SHA-256 hash tracking via _ingestion_metadata
    - Secure, read-only SELECT query execution
    """
    _instance: Optional["SQLiteDBManager"] = None

    def __new__(cls, *args, **kwargs) -> "SQLiteDBManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        if self._initialized:
            return
        self.db_path = Path(db_path or settings.SQLITE_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_metadata_table()
        self._initialized = True

    def get_connection(self) -> sqlite3.Connection:
        """Returns a connection to the SQLite database."""
        return sqlite3.connect(self.db_path)

    def _ensure_metadata_table(self) -> None:
        """Ensures the internal ingestion metadata tracking table exists."""
        conn = self.get_connection()
        try:
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
        finally:
            conn.close()

    def ingest_table(
        self,
        csv_path: Optional[Union[str, Path]] = None,
        table_name: str = "product",
        force_reload: bool = False,
    ) -> Path:
        """
        Extensible CSV ingestion into SQLite:
        - Ingests ANY CSV file into any specified table.
        - Defaults to settings.ECOMMERCE_DATA_PATH.
        - Uses SHA-256 hash checking to skip unchanged files.
        """
        raw_path = csv_path or settings.ECOMMERCE_DATA_PATH
        path = Path(raw_path)
        if not path.is_absolute():
            path = settings.BASE_DIR / path

        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")

        current_hash = get_file_hash(path)
        filename = path.name

        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT file_hash, row_count FROM _ingestion_metadata WHERE table_name = ?",
                (table_name,),
            )
            meta_row = cursor.fetchone()

            if meta_row and not force_reload:
                saved_hash, row_count = meta_row
                if saved_hash == current_hash:
                    log_info(f"SQLite table '{table_name}' is up-to-date ({row_count} rows, hash matched). Skipping.")
                    return self.db_path
                else:
                    log_info(f"File '{filename}' modified. Refreshing SQLite table '{table_name}'...")

            log_info(f"Loading '{filename}' into SQLite table '{table_name}'...")
            df = pd.read_csv(path)
            df.to_sql(table_name, conn, if_exists="replace", index=False)

            cursor.execute("""
            INSERT OR REPLACE INTO _ingestion_metadata (table_name, source_file, file_hash, row_count, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (table_name, filename, current_hash, len(df)))
            conn.commit()

            log_success(f"Loaded {len(df)} records into SQLite table '{table_name}' at {self.db_path}.")
            return self.db_path
        finally:
            conn.close()

    def ingest_products(
        self,
        csv_path: Optional[Union[str, Path]] = None,
        table_name: str = "product",
        force_reload: bool = False,
    ) -> Path:
        """Convenience alias for ingesting the product catalog."""
        return self.ingest_table(csv_path=csv_path or settings.ECOMMERCE_DATA_PATH, table_name=table_name, force_reload=force_reload)

    def execute_query(self, query: str) -> pd.DataFrame:
        """
        Executes a SQL query safely against SQLite:
        - Ensures database file and tables exist before executing.
        - Security Guard: Enforces SELECT-only queries.
        - Blocks destructive statements (DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE).
        """
        clean_query = query.strip()

        if not clean_query.upper().startswith("SELECT"):
            raise ValueError("Security violation: Only SELECT queries are permitted.")

        destructive_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
        for kw in destructive_keywords:
            if re.search(rf"\b{kw}\b", clean_query, re.IGNORECASE):
                raise ValueError(f"Security violation: Keyword '{kw}' is prohibited.")

        # Ensure database is initialized
        if not self.db_path.exists():
            self.setup_database()

        conn = self.get_connection()
        try:
            return pd.read_sql_query(clean_query, conn)
        finally:
            conn.close()

    def setup_database(self, force_reload: bool = False) -> Path:
        """Initializes the SQLite product catalog."""
        log_info("Setting up SQLite product database...")
        return self.ingest_products(force_reload=force_reload)


# =====================================================================
# 3. Global Singleton Instances & Top-Level Compatibility Aliases
# =====================================================================

chroma_db = ChromaDBManager()
sql_db = SQLiteDBManager()


def get_chroma_client() -> chromadb.PersistentClient:
    """Returns persistent ChromaDB client from the singleton."""
    return chroma_db.client


def ingest_faq_file(
    file_path: Optional[Union[str, Path]] = None,
    collection_name: Optional[str] = None,
    force_reload: bool = False,
) -> chromadb.Collection:
    """Compatibility alias delegating to chroma_db singleton."""
    return chroma_db.ingest_faq_file(file_path=file_path, collection_name=collection_name, force_reload=force_reload)


def ingest_sqlite_table(
    csv_path: Optional[Union[str, Path]] = None,
    table_name: str = "product",
    force_reload: bool = False,
) -> Path:
    """Compatibility alias delegating to sql_db singleton."""
    return sql_db.ingest_table(csv_path=csv_path, table_name=table_name, force_reload=force_reload)


def ingest_sqlite_products(
    csv_path: Optional[Union[str, Path]] = None,
    table_name: str = "product",
    force_reload: bool = False,
) -> Path:
    """Compatibility alias delegating to sql_db singleton."""
    return sql_db.ingest_products(csv_path=csv_path, table_name=table_name, force_reload=force_reload)


def setup_database(force_reload: bool = False) -> Path:
    """Compatibility alias delegating to sql_db singleton."""
    return sql_db.setup_database(force_reload=force_reload)


def init_all_databases(force_reload: bool = False) -> None:
    """Initializes both ChromaDB vector store and SQLite catalog."""
    log_info("Initializing all application databases (ChromaDB + SQLite)...")
    chroma_db.ingest_faq_file(force_reload=force_reload)
    sql_db.setup_database(force_reload=force_reload)
    log_success("All databases are initialized and ready.")


if __name__ == "__main__":
    init_all_databases()
