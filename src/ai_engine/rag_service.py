import os
import json
import logging
import requests
import numpy as np
from typing import List, Dict, Any
import pypdf
from glob import glob

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
VECTOR_STORE_PATH = os.path.join(os.getcwd(), 'data', 'vector_store.json')
DOCS_DIR = os.path.join(os.getcwd(), 'docs')
COMPAGNIE_DOCS_DIR = os.path.join(os.getcwd(), 'CompagnieDocs')
SRC_DIR = os.path.join(os.getcwd(), 'src') # Include source code
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = "nomic-embed-text"  # Lightweight and effective

class RAGService:
    def __init__(self):
        self.vector_store: List[Dict[str, Any]] = []
        self._load_store()

    def _load_store(self):
        """Loads the vector store from disk."""
        if os.path.exists(VECTOR_STORE_PATH):
            try:
                with open(VECTOR_STORE_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.vector_store = data
                    logger.info(f"Loaded {len(self.vector_store)} documents from vector store.")
            except Exception as e:
                logger.error(f"Error loading vector store: {e}")
                self.vector_store = []
        else:
            logger.info("No vector store found. Starting fresh.")
            self.vector_store = []

    def save_store(self):
        """Saves the vector store to disk."""
        os.makedirs(os.path.dirname(VECTOR_STORE_PATH), exist_ok=True)
        try:
            with open(VECTOR_STORE_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.vector_store, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self.vector_store)} documents to vector store.")
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")

    def generate_embedding(self, text: str) -> List[float]:
        """Generates an embedding for the given text using Ollama."""
        try:
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/embeddings",
                json={"model": EMBEDDING_MODEL, "prompt": text}
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []

    def ingest_documents(self) -> Dict[str, int]:
        """Scans docs and CompagnieDocs, ingests them, and updates the store."""
        new_docs_count = 0
        failed_docs_count = 0
        
        # Updated to include user uploads
        LIBRARY_UPLOADS = os.path.join(os.getcwd(), 'uploads', 'library')
        
        # Collect all files
        files = []
        for directory in [DOCS_DIR, COMPAGNIE_DOCS_DIR, SRC_DIR, LIBRARY_UPLOADS]:
            if os.path.exists(directory):
                # Recursively find files
                for root, _, filenames in os.walk(directory):
                    # Skip __pycache__ and hidden dirs
                    if '__pycache__' in root or '/.' in root or '\\.' in root:
                        continue
                        
                    for filename in filenames:
                        # Added .csv to supported formats
                        if filename.lower().endswith(('.pdf', '.md', '.txt', '.py', '.ts', '.tsx', '.json', '.yaml', '.yml', '.css', '.html', '.csv')):
                            files.append(os.path.join(root, filename))

        existing_sources = {doc['source'] for doc in self.vector_store}

        for file_path in files:
            if file_path in existing_sources:
                continue

            text_content = ""
            try:
                if file_path.lower().endswith('.pdf'):
                    reader = pypdf.PdfReader(file_path)
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text_content += extracted + "\n"
                else:
                    # Generic text reading for code/md/txt
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text_content = f.read()

                if not text_content.strip():
                    logger.warning(f"Skipping empty file: {file_path}")
                    continue

                # Chunking (simple overlap)
                chunk_size = 1000
                overlap = 200
                chunks = [text_content[i:i+chunk_size] for i in range(0, len(text_content), chunk_size - overlap)]

                for i, chunk in enumerate(chunks):
                    embedding = self.generate_embedding(chunk)
                    if embedding:
                        self.vector_store.append({
                            "text": chunk,
                            "embedding": embedding,
                            "source": file_path,
                            "chunk_id": i
                        })
                
                new_docs_count += 1
                logger.info(f"Ingested: {file_path}")

            except Exception as e:
                logger.error(f"Failed to ingest {file_path}: {e}")
                failed_docs_count += 1

        if new_docs_count > 0:
            self.save_store()

        return {"ingested": new_docs_count, "failed": failed_docs_count, "total_chunks": len(self.vector_store)}

    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Searches for the most similar documents to the query."""
        if not self.vector_store:
            return []

        query_embedding = self.generate_embedding(query)
        if not query_embedding:
            return []

        # Calculate cosine similarity
        results = []
        q_vec = np.array(query_embedding)
        norm_q = np.linalg.norm(q_vec)

        for doc in self.vector_store:
            d_vec = np.array(doc['embedding'])
            norm_d = np.linalg.norm(d_vec)
            
            if norm_q == 0 or norm_d == 0:
                similarity = 0
            else:
                similarity = np.dot(q_vec, d_vec) / (norm_q * norm_d)
            
            results.append({
                "text": doc['text'],
                "source": doc['source'],
                "score": float(similarity)
            })

        # Sort by similarity desc
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:k]

    def list_documents(self) -> List[Dict[str, Any]]:
        """Lists all supported documents in docs folders with metadata and status."""
        docs_list = []
        indexed_sources = {doc['source'] for doc in self.vector_store}
        
        # Added SRC_DIR to listing
        for directory in [DOCS_DIR, COMPAGNIE_DOCS_DIR, SRC_DIR]:
            if not os.path.exists(directory):
                continue
            for root, _, filenames in os.walk(directory):
                # Skip __pycache__ and hidden dirs
                if '__pycache__' in root or '/.' in root or '\\.' in root:
                    continue
                    
                for filename in filenames:
                    # Expanded extension list
                    if not filename.lower().endswith(('.pdf', '.md', '.txt', '.py', '.ts', '.tsx', '.json', '.yaml', '.yml', '.css', '.html')):
                        continue
                        
                    file_path = os.path.join(root, filename)
                    try:
                        stat = os.stat(file_path)
                        is_indexed = file_path in indexed_sources
                        
                        relative_path = os.path.relpath(file_path, os.getcwd())
                        # Normalize slashes for URL
                        url_path = relative_path.replace("\\", "/")
                        web_path = None
                        
                        # Only expose simple paths for web viewing if needed, 
                        # or maybe we restrict raw_path for source code to avoid leakage if publicly exposed.
                        # But this is an admin dashboard, so maybe it's fine.
                        # For now, let's keep raw_path logic for docs only.
                        if url_path.startswith("docs/"):
                            web_path = "/" + url_path
                        elif url_path.startswith("CompagnieDocs/"):
                            web_path = "/" + url_path

                        docs_list.append({
                            "doc_id": str(hash(file_path)),
                            "title": filename,
                            "ext": os.path.splitext(filename)[1].lower().replace('.', '').upper(),
                            "status": "processed" if is_indexed else "pending_conversion", 
                            "size_bytes": stat.st_size,
                            "updated_at": str(stat.st_mtime), # Frontend can handle this or we format
                            "raw_path": web_path
                        })
                    except Exception as e:
                        logger.error(f"Error listing {file_path}: {e}")
        return docs_list

rag_service = RAGService()
