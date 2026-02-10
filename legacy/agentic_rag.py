"""
Agentic RAG System - Main agent implementation
"""
import os
import pickle
from langchain.agents import create_agent
from langchain_deepseek import ChatDeepSeek
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from pydantic import BaseModel, Field
from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    EMBEDDING_MODEL_PATH,
    CHROMA_DB_PATH,
    BM25_MODEL_PATH,
    MAX_ITERATIONS
)
from agent_tools import expand_and_keyword, retrieval_augment, summary_related_doc


class AgentResult(BaseModel):
    """Agent response format"""
    agent_answer: str = Field(..., description="Answer to user query")


def load_vectorstore():
    """Load vector store from disk"""
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_PATH,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    vectorstore = Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embeddings
    )
    return vectorstore


def load_bm25_model():
    """Load BM25 model from disk"""
    if not os.path.exists(BM25_MODEL_PATH):
        return None
    
    with open(BM25_MODEL_PATH, 'rb') as f:
        bm25_model = pickle.load(f)
    return bm25_model


def create_agentic_rag_agent(model=None, vectorstore=None):
    """
    Create the Agentic RAG agent with all necessary tools
    """
    # Initialize model if not provided
    if model is None:
        model = ChatDeepSeek(
            model=DEEPSEEK_MODEL,
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )
    
    # Load vectorstore if not provided
    if vectorstore is None:
        vectorstore = load_vectorstore()
    
    # Create tool instances with dependencies using closures
    from langchain.tools import tool
    
    @tool
    def expand_and_keyword_tool(query: str) -> str:
        """Rewrite the user's input query and extract the most important keyword. Returns formatted string with expanded query and keyword."""
        expand_query, keyword = expand_and_keyword(query, model=model)
        return f"Expanded query: {expand_query}\nExtracted keyword: {keyword}"
    
    @tool
    def retrieval_augment_tool(query: str, keyword: str) -> str:
        """Retrieve relevant documents from the knowledge base based on user query and keywords. Returns retrieved document content."""
        return retrieval_augment(query, keyword, vectorstore=vectorstore)
    
    @tool
    def summary_related_doc_tool(query: str, related_doc: str) -> str:
        """Deep read and filter document fragments based on the user query. Returns filtered and summarized document fragments."""
        return summary_related_doc(query, related_doc, model=model)
    
    # Set up tools
    tools = [
        expand_and_keyword_tool,
        retrieval_augment_tool,
        summary_related_doc_tool
    ]
    
    # System prompt for the agent
    system_prompt = f"""你是一名助人为乐的助手,你会根据用户的问题进行判断:

如果用户问题与知识库不相关,那么就直接进行回答,不要调用工具。

如果用户问题与知识库相关,就需要进行RAG检索,然后根据检索到的相关文档进行回答,具体步骤如下:

1. 可选择:如果用户描述不清楚,你需要调用expand_and_keyword_tool工具对用户问题进行改写并提取关键词。

2. 必须进行:调用retrieval_augment_tool工具,基于用户输入的查询语句和核心关键词,从知识库中检索相关文档。注意:如果之前调用了expand_and_keyword_tool,请使用提取的关键词。

3. 可选择:若retrieval_augment_tool检索后的文章大于{1000}字,可调用summary_related_doc_tool工具对文档进行精读和筛选。

4. 根据精读的内容对用户的原始query进行回答;若没有找到答案,请再次对问题进行改写和关键词提取,然后重新检索。

5. 若重复{MAX_ITERATIONS}次还没找到答案,请回答:没有在文档中检索到相关内容,所以无法准确回答。

请基于检索到的文档内容进行回答,并给出引用。如果文档中没有相关信息,请诚实地说不知道,不要编造答案。"""

    # Create agent
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        response_format=AgentResult
    )
    
    return agent


def query_agent(agent, query: str):
    """
    Query the agentic RAG agent
    """
    response = agent.invoke({
        "messages": [{"role": "user", "content": query}]
    })
    
    # Extract the final answer
    if hasattr(response, 'structured_response'):
        answer = response.structured_response.agent_answer
    elif 'structured_response' in response:
        answer = response['structured_response'].agent_answer
    else:
        # Fallback: try to extract from messages
        messages = response.get('messages', [])
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, 'content'):
                answer = last_message.content
            elif isinstance(last_message, dict):
                answer = last_message.get('content', 'No answer found')
            else:
                answer = str(messages[-1])
        else:
            answer = "No response generated"
    
    return answer, response


if __name__ == "__main__":
    # Example usage
    print("Initializing Agentic RAG Agent...")
    agent = create_agentic_rag_agent()
    
    # Test queries
    test_queries = [
        "你是谁?",  # Simple question (should not use RAG)
        "什么情况会被退学?",  # Knowledge base question
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"Query: {query}")
        print(f"{'='*50}")
        answer, response = query_agent(agent, query)
        print(f"Answer: {answer}")
