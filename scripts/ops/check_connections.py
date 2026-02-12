import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.database import DATABASE_URL

def check_env():
    load_dotenv()
    
    apollo_key = os.getenv("APOLLO_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    print("[CHECK] Environment")
    if apollo_key and apollo_key != "your_apollo_api_key_here":
        print("  [OK] Apollo API Key found")
    else:
        print("  [WARN] Apollo API Key missing or default")
        
    if openai_key and openai_key != "your_openai_api_key_here":
        print("  [OK] OpenAI API Key found")
    else:
        print("  [WARN] OpenAI API Key missing or default")

def check_db():
    print("\n[CHECK] Database")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("  [OK] Database connection successful")
            print(f"  [INFO] Database URL: {DATABASE_URL}")
    except Exception as e:
        print(f"  [ERROR] Database connection failed: {e}")

if __name__ == "__main__":
    check_env()
    check_db()
