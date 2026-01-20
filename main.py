"""
Main entry point for Agentic RAG system
"""
import argparse
import os
from agentic_rag import create_agentic_rag_agent, query_agent
from offline_pipeline import build_knowledge_base
from config import DEFAULT_DOCUMENT_PATH


def build_kb_mode(document_path: str):
    """Build knowledge base from documents"""
    print("Building knowledge base...")
    if not os.path.exists(document_path):
        print(f"Error: Document file not found: {document_path}")
        print("Please create a document file or update DEFAULT_DOCUMENT_PATH in config.py")
        return
    
    build_knowledge_base(document_path)
    print("\nKnowledge base built successfully!")
    print("You can now run the agent with: python main.py --query 'your question here'")


def query_mode(query: str):
    """Query the agentic RAG system"""
    print("Initializing Agentic RAG Agent...")
    try:
        agent = create_agentic_rag_agent()
        print("Agent initialized successfully!\n")
        
        print(f"{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        answer, response = query_agent(agent, query)
        
        print(f"\nAnswer:\n{answer}")
        print(f"\n{'='*60}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have:")
        print("1. Built the knowledge base (run: python main.py --build)")
        print("2. Set your DEEPSEEK_API_KEY in config.py or as environment variable")


def interactive_mode():
    """Interactive query mode"""
    print("Initializing Agentic RAG Agent...")
    try:
        agent = create_agentic_rag_agent()
        print("Agent initialized successfully!")
        print("Enter your queries (type 'exit' or 'quit' to stop):\n")
        
        while True:
            query = input("Query: ").strip()
            
            if query.lower() in ['exit', 'quit', 'q']:
                print("Goodbye!")
                break
            
            if not query:
                continue
            
            print(f"\n{'='*60}")
            answer, response = query_agent(agent, query)
            print(f"\nAnswer:\n{answer}")
            print(f"{'='*60}\n")
            
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have:")
        print("1. Built the knowledge base (run: python main.py --build)")
        print("2. Set your DEEPSEEK_API_KEY in config.py or as environment variable")


def main():
    parser = argparse.ArgumentParser(description="Agentic RAG System")
    parser.add_argument(
        '--build',
        action='store_true',
        help='Build the knowledge base from documents'
    )
    parser.add_argument(
        '--document',
        type=str,
        default=DEFAULT_DOCUMENT_PATH,
        help='Path to document file for building knowledge base'
    )
    parser.add_argument(
        '--query',
        type=str,
        help='Query to ask the agent'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode'
    )
    
    args = parser.parse_args()
    
    if args.build:
        build_kb_mode(args.document)
    elif args.query:
        query_mode(args.query)
    elif args.interactive:
        interactive_mode()
    else:
        # Default to interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
