"""
Configuration file for Agentic RAG system
"""
import os

# Model Configuration
EMBEDDING_MODEL_PATH = os.getenv(
    "EMBEDDING_MODEL_PATH", 
    "sentence-transformers/all-MiniLM-L6-v2"  # Default to a lightweight model
)

# DeepSeek API Configuration
# Note: DEEPSEEK_API_KEY must be set via environment variable
# No default value to prevent accidental API calls with invalid key
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError(
        "DEEPSEEK_API_KEY is required. Set it as an environment variable or in .env file."
    )
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# Chunking Configuration
CHUNK_SIZE = 300
CHUNK_OVERLAP = 50

# Retrieval Configuration
VECTOR_SEARCH_K = 10  # Number of documents to retrieve initially
FINAL_RETRIEVAL_K = 5  # Number of documents after re-ranking
KEYWORD_BOOST_SCORE = 0.1  # Score reduction for keyword matches (lower = more similar)

# Storage Paths
RAG_CACHE_DIR = "./rag_cache"
BM25_MODEL_PATH = f"{RAG_CACHE_DIR}/bm25_model.pkl"
CHROMA_DB_PATH = f"{RAG_CACHE_DIR}/chroma_db"

# Document Path
DEFAULT_DOCUMENT_PATH = "./documents/sample_document.txt"

# Agent Configuration
MAX_ITERATIONS = 3  # Maximum number of query rewriting attempts
SUMMARY_THRESHOLD = 1000  # Character threshold for document summarization
