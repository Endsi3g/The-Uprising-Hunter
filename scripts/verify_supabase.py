import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load env from root
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(root_dir, ".env")
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL not set in .env")
    sys.exit(1)

print(f"Testing connection to: {DATABASE_URL.split('@')[-1]}") # Hide credentials

try:
    # Use standard create_engine
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"SUCCESS: Connected to PostgreSQL!")
        print(f"Version: {version}")
except Exception as e:
    print(f"FAILURE: Could not connect to database.")
    print(f"Error: {e}")
    sys.exit(1)
