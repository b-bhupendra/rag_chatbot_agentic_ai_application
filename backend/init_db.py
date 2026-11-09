"""
Backward-compatible database initialization script.
Delegates to the SQLiteDBManager singleton in backend.setup_db.
"""
try:
    from backend.setup_db import sql_db, setup_database
except ModuleNotFoundError:
    from setup_db import sql_db, setup_database


if __name__ == "__main__":
    setup_database()
