"""
Offline pipeline for processing documents and building the knowledge base
"""
import os
import pickle
from pathlib import Path
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import jieba
from rank_bm25 import BM25Okapi
from config import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_MODEL_PATH,
    RAG_CACHE_DIR,
    BM25_MODEL_PATH,
    CHROMA_DB_PATH,
    DEFAULT_DOCUMENT_PATH
)


def load_documents(file_path: str = None):
    """Load documents from file"""
    if file_path is None:
        file_path = DEFAULT_DOCUMENT_PATH
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Document file not found: {file_path}")
    
    print(f"Loading documents from: {file_path}")
    loader = TextLoader(file_path, encoding='utf-8')
    documents = loader.load()
    print(f"Loaded {len(documents)} document(s)")
    return documents


def chunk_documents(documents, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
    """Split documents into chunks"""
    print(f"Chunking documents with size={chunk_size}, overlap={chunk_overlap}")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    doc_splits = text_splitter.split_documents(documents)
    print(f"Created {len(doc_splits)} chunks")
    return doc_splits


def create_bm25_model(doc_splits):
    """Create and return BM25 model"""
    print("Creating BM25 model...")
    # Tokenize documents using jieba for Chinese text
    pdf_content_words = [jieba.lcut(doc.page_content) for doc in doc_splits]
    bm25_model = BM25Okapi(pdf_content_words)
    print("BM25 model created successfully")
    return bm25_model


def create_embeddings():
    """Create embedding model"""
    print(f"Loading embedding model: {EMBEDDING_MODEL_PATH}")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_PATH,
        model_kwargs={'device': 'cpu'},  # Use 'cuda' if GPU available
        encode_kwargs={'normalize_embeddings': True}
    )
    print("Embedding model loaded successfully")
    return embeddings


def create_vectorstore(doc_splits, embeddings):
    """Create and persist vector store"""
    print("Creating vector store...")
    vectorstore = Chroma.from_documents(
        documents=doc_splits,
        embedding=embeddings,
        persist_directory=CHROMA_DB_PATH
    )
    print(f"Vector store created and persisted to: {CHROMA_DB_PATH}")
    return vectorstore


def save_bm25_model(bm25_model, save_path: str = BM25_MODEL_PATH):
    """Save BM25 model to disk"""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'wb') as f:
        pickle.dump(bm25_model, f)
    print(f"BM25 model saved to: {save_path}")


def build_knowledge_base(document_path: str = None):
    """
    Complete offline pipeline to build the knowledge base
    """
    print("=" * 50)
    print("Starting offline knowledge base construction...")
    print("=" * 50)
    
    # Step 1: Load documents
    documents = load_documents(document_path)
    
    # Step 2: Chunk documents
    doc_splits = chunk_documents(documents)
    
    # Step 3: Create BM25 model
    bm25_model = create_bm25_model(doc_splits)
    
    # Step 4: Create embeddings
    embeddings = create_embeddings()
    
    # Step 5: Create vector store
    vectorstore = create_vectorstore(doc_splits, embeddings)
    
    # Step 6: Save BM25 model
    save_bm25_model(bm25_model)
    
    print("=" * 50)
    print("Knowledge base construction completed!")
    print("=" * 50)
    
    return {
        'doc_splits': doc_splits,
        'bm25_model': bm25_model,
        'embeddings': embeddings,
        'vectorstore': vectorstore
    }


if __name__ == "__main__":
    # Create cache directory
    os.makedirs(RAG_CACHE_DIR, exist_ok=True)
    
    # Build knowledge base
    build_knowledge_base()
