import os
import json
import logging
import requests
import numpy as np
import re
import hashlib
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
LIBRARY_UPLOADS = os.path.join(os.getcwd(), 'uploads', 'library')
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = "nomic-embed-text"  # Lightweight and effective
SUPPORTED_EXTENSIONS = ('.pdf', '.md', '.txt', '.py', '.ts', '.tsx', '.json', '.yaml', '.yml', '.css', '.html', '.csv')

SECRET_PATTERNS = [
    re.compile(r'sk-[a-zA-Z0-9]{32,}', re.IGNORECASE), # OpenAI-like
    re.compile(r'AIza[0-9A-Za-z-_]{35}', re.IGNORECASE), # Google-like
    re.compile(r'(?:password|passwd|api[-_]?key)\s*[:=]\s*["\'][^"\'\n]*?["\']', re.IGNORECASE), # common assignments
    re.compile(r'-----BEGIN (?:RSA|PRIVATE) KEY-----[\s\S]*?-----END (?:RSA|PRIVATE) KEY-----', re.DOTALL), # PEM keys
    re.compile(r'AKIA[0-9A-Z]{16}', re.IGNORECASE), # AWS Access Key ID
    re.compile(r'postgres://(?P<user>[^:]+):(?P<pass>[^@]+)@', re.IGNORECASE), # DB URIs
    re.compile(r'Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*', re.IGNORECASE), # Bearer tokens
]

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
                json={"model": EMBEDDING_MODEL, "prompt": text},
                timeout=10
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
        
        # Collect all files
        files = []
        for directory in [DOCS_DIR, COMPAGNIE_DOCS_DIR, SRC_DIR, LIBRARY_UPLOADS]:
            if os.path.exists(directory):
                # Recursively find files
                for root, _, filenames in os.walk(directory):
                    # Skip __pycache__ and hidden dirs
                    if '__pycache__' in root or '/.' in root or '\\.' in root:
                        continue
                    
                    is_src = directory == SRC_DIR
                    for filename in filenames:
                        # Security: Skip sensitive files in source dir
                        if is_src:
                            lower_name = filename.lower()
                            if lower_name.startswith(".env") or lower_name.endswith((".key", ".pem", ".cert")):
                                continue
                            if filename.endswith((".pyc", ".pyo", ".so", ".dll", ".exe")):
                                continue

                        if filename.lower().endswith(SUPPORTED_EXTENSIONS):
                            files.append(os.path.join(root, filename))

        # Build map of source -> max(mtime) for existing docs
        source_metadata = {}
        for doc in self.vector_store:
            src = doc.get('source')
            if not src:
                continue
            mtime = doc.get('mtime', 0)
            source_metadata[src] = max(source_metadata.get(src, 0), mtime)

        for file_path in files:
            current_mtime = os.path.getmtime(file_path)
            if file_path in source_metadata and current_mtime <= source_metadata[file_path]:
                continue

            # Modified or new file: Remove old entries if they exist
            if file_path in source_metadata:
                self.vector_store = [d for d in self.vector_store if d.get('source') != file_path]

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

                # Redaction: pattern matching for common secret formats
                for p in SECRET_PATTERNS:
                    text_content = p.sub("[REDACTED_SECRET]", text_content)

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
                            "chunk_id": i,
                            "mtime": current_mtime
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
            d_embedding = doc.get('embedding')
            if d_embedding is None:
                continue
            d_vec = np.array(d_embedding)
            norm_d = np.linalg.norm(d_vec)
            
            if norm_q == 0 or norm_d == 0:
                similarity = 0
            else:
                similarity = np.dot(q_vec, d_vec) / (norm_q * norm_d)
            
            results.append({
                "text": doc.get('text', ""),
                "source": doc.get('source', "unknown"),
                "score": float(similarity)
            })

        # Sort by similarity desc
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:k]

    def list_documents(self) -> List[Dict[str, Any]]:
        """Lists all supported documents in docs folders with metadata and status."""
        docs_list = []
        indexed_sources = {doc.get('source') for doc in self.vector_store if doc.get('source')}
        
        # Scan directories
        for directory in [DOCS_DIR, COMPAGNIE_DOCS_DIR, SRC_DIR, LIBRARY_UPLOADS]:
            if not os.path.exists(directory):
                continue
            for root, _, filenames in os.walk(directory):
                # Skip __pycache__ and hidden dirs
                if '__pycache__' in root or '/.' in root or '\\.' in root:
                    continue
                    
                for filename in filenames:
                    if not filename.lower().endswith(SUPPORTED_EXTENSIONS):
                        continue
                        
                    file_path = os.path.join(root, filename)
                    try:
                        stat = os.stat(file_path)
                        is_indexed = file_path in indexed_sources
                        
                        relative_path = os.path.relpath(file_path, os.getcwd())
                        # Normalize slashes for URL
                        url_path = relative_path.replace("\\", "/")
                        web_path = None
                        
                        if url_path.startswith("docs/"):
                            web_path = "/" + url_path
                        elif url_path.startswith("CompagnieDocs/"):
                            web_path = "/" + url_path
                        elif url_path.startswith("uploads/library/"):
                            web_path = "/" + url_path

                        # Sanitize SRC_DIR metadata
                        is_src_file = file_path.startswith(SRC_DIR + os.sep)
                        
                        docs_list.append({
                            "doc_id": hashlib.sha256(file_path.encode()).hexdigest()[:16],
                            "title": "[CODE] " + os.path.basename(file_path) if is_src_file else filename,
                            "ext": os.path.splitext(filename)[1].lower().replace('.', '').upper(),
                            "status": "processed" if is_indexed else "pending_conversion", 
                            "size_bytes": 0 if is_src_file else stat.st_size,
                            "updated_at": None if is_src_file else str(stat.st_mtime),
                            "sanitized": True if is_src_file else False,
                            "raw_path": web_path
                        })
                    except Exception as e:
                        logger.error(f"Error listing {file_path}: {e}")
        return docs_list

rag_service = RAGService()
