"""
Backward-compatible database initialization script.
Delegates to backend.setup_db.setup_database for production-grade ingestion
with hash-based caching and full catalog support.
"""
try:
    from backend.setup_db import setup_database, init_all_databases
except ModuleNotFoundError:
    from setup_db import setup_database, init_all_databases

if __name__ == "__main__":
    setup_database()

