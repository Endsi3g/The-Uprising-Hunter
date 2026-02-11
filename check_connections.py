import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from src.core.database import DATABASE_URL

def check_env():
    load_dotenv()
    
    apollo_key = os.getenv("APOLLO_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    print("🔍 Environment Check:")
    if apollo_key and apollo_key != "your_apollo_api_key_here":
        print("  ✅ Apollo API Key found")
    else:
        print("  ❌ Apollo API Key missing or default")
        
    if openai_key and openai_key != "your_openai_api_key_here":
        print("  ✅ OpenAI API Key found")
    else:
        print("  ❌ OpenAI API Key missing or default")

def check_db():
    print("\n🔍 Database Check:")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("  ✅ Database connection successful")
            print(f"  📂 Database URL: {DATABASE_URL}")
    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")

if __name__ == "__main__":
    check_env()
    check_db()
