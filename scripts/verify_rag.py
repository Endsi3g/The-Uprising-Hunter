import sys
import os
import requests

# Add project root to path
sys.path.append(os.getcwd())

from src.ai_engine.rag_service import rag_service

def verify_rag():
    print("1. Checking Ollama Connection...")
    try:
        requests.get("http://localhost:11434")
        print("   [OK] Ollama is reachable.")
    except Exception:
        print("   [FAIL] Ollama is NOT reachable. Please start it.")
        return

    print("\n2. Testing Embedding Generation...")
    embedding = rag_service.generate_embedding("Test sentence")
    if embedding and len(embedding) > 0:
        print(f"   [OK] Embedding generated (dim: {len(embedding)}).")
    else:
        print("   [FAIL] Could not generate embedding. Check model 'nomic-embed-text' exists.")
        print("   Run: ollama pull nomic-embed-text")
        return

    print("\n3. Testing Ingestion (Dry Run logic)...")
    # We won't run full ingestion to avoid heavy processing, just check path access
    if os.path.exists("docs") or os.path.exists("CompagnieDocs"):
        print("   [OK] Document directories found.")
    else:
        print("   [WARN] Document directories 'docs' or 'CompagnieDocs' not found.")

    print("\n4. Testing Search (Empty Store Check)...")
    results = rag_service.search("hello")
    print(f"   [OK] Search returned {len(results)} results (likely 0 if empty).")

if __name__ == "__main__":
    verify_rag()
