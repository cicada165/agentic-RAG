"""
Example usage of the Agentic RAG system
"""
from agentic_rag import create_agentic_rag_agent, query_agent


def example_basic_query():
    """Basic query example"""
    print("=" * 60)
    print("Example 1: Basic Query")
    print("=" * 60)
    
    agent = create_agentic_rag_agent()
    query = "什么情况会被退学?"
    
    answer, response = query_agent(agent, query)
    print(f"Query: {query}")
    print(f"Answer: {answer}")


def example_simple_question():
    """Example of a simple question that shouldn't use RAG"""
    print("\n" + "=" * 60)
    print("Example 2: Simple Question (No RAG)")
    print("=" * 60)
    
    agent = create_agentic_rag_agent()
    query = "你是谁?"
    
    answer, response = query_agent(agent, query)
    print(f"Query: {query}")
    print(f"Answer: {answer}")


def example_multiple_queries():
    """Example with multiple queries"""
    print("\n" + "=" * 60)
    print("Example 3: Multiple Queries")
    print("=" * 60)
    
    agent = create_agentic_rag_agent()
    
    queries = [
        "两周未参加学校活动会被退学吗?",
        "学生可以转专业吗?",
        "休学有什么规定?",
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        answer, response = query_agent(agent, query)
        print(f"Answer: {answer}\n")
        print("-" * 60)


if __name__ == "__main__":
    print("Agentic RAG System - Example Usage\n")
    
    try:
        # Example 1: Basic query
        example_basic_query()
        
        # Example 2: Simple question
        example_simple_question()
        
        # Example 3: Multiple queries
        example_multiple_queries()
        
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure you have:")
        print("1. Built the knowledge base: python main.py --build")
        print("2. Set DEEPSEEK_API_KEY in config.py or as environment variable")
