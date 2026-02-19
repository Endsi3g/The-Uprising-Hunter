import os
import sys

# Ensure src is importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import engine, DATABASE_URL

print(f"Final DATABASE_URL used: {DATABASE_URL}")

try:
    with engine.connect() as connection:
        result = connection.execute("SELECT version()")
        version = result.fetchone()[0]
        print(f"SUCCESS: Connected via src/core/database.py!")
        print(f"Version: {version}")
except Exception as e:
    print(f"FAILURE: Could not connect using src/core/database.py logic.")
    print(f"Error: {e}")
    sys.exit(1)
