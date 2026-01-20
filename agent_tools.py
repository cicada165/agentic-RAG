"""
Agent tools for Agentic RAG system
"""
from langchain.tools import tool
from pydantic import BaseModel, Field
from config import (
    VECTOR_SEARCH_K,
    FINAL_RETRIEVAL_K,
    KEYWORD_BOOST_SCORE,
    SUMMARY_THRESHOLD
)


# Pydantic models for structured output
class ExpandAndKeywordFormat(BaseModel):
    """Result of query expansion and keyword extraction"""
    expand_query: str = Field(..., description="The expanded/rewritten query result, can be unchanged")
    keyword: str = Field(..., description="The most important short keyword extracted from the query")


class SummaryRelatedDocFormat(BaseModel):
    """Result of document summarization/filtering"""
    summary_related_doc_res: str = Field(..., description="Filtered fragments related to the user query")


def expand_and_keyword(query: str, model=None):
    """
    Rewrite the user's input query and extract the most important keyword.
    
    :param query: str, required - User's input, based on which to expand and extract keywords
    :return: tuple (expand_query: str, keyword: str)
    """
    if model is None:
        raise ValueError("Model must be provided")
    
    expand_and_keyword_conversation = [
        {
            "role": "system",
            "content": "你是一个乐于助人的助手,负责给用户的query进行改写和提取关键词。如果query已经很清晰,可以不改写。"
        },
        {
            "role": "user",
            "content": f"请对以下query进行改写(如果需要)并提取一个最重要的关键词:\n{query}"
        }
    ]
    
    model_with_structure = model.with_structured_output(ExpandAndKeywordFormat)
    response = model_with_structure.invoke(expand_and_keyword_conversation)
    
    expand_query = response.expand_query
    keyword = response.keyword
    
    return expand_query, keyword


def retrieval_augment(query: str, keyword: str, vectorstore=None) -> str:
    """
    [RAG Retrieval Augmentation] Retrieve relevant documents from the knowledge base based on 
    user query and core keywords, and enhance the results.
    
    Core logic: First retrieve Top K documents by query → If keyword exists, adjust matching score 
    (documents containing keyword get score -0.1, making them more similar).
    
    :param query: str, required - User's natural language query, as the basic retrieval condition
    :param keyword: str, required - Core keyword extracted from user input, used to optimize retrieval result weights
    :return: related_doc: str - Retrieval results of repository document content sorted by optimized score, 
             concatenated with double newlines
    """
    if vectorstore is None:
        raise ValueError("Vectorstore must be provided")
    
    # Perform retrieval
    docs = vectorstore.similarity_search_with_score(query, k=VECTOR_SEARCH_K)
    docs = [list(item) for item in docs]  # Convert tuples to lists for score modification
    
    # Keyword-based re-ranking
    if keyword:
        for doc in docs:
            # If keyword is in text, make score smaller (more similar)
            if keyword in doc[0].page_content:
                doc[-1] -= KEYWORD_BOOST_SCORE
    
    # Sort retrieved snippets after keyword search
    docs = sorted(docs, key=lambda x: x[-1])  # Sort by score (lower = more similar)
    
    # Only take top K fragments
    docs = docs[:FINAL_RETRIEVAL_K]
    
    # Concatenate results
    related_doc = '\n\n'.join([text[0].page_content for text in docs])
    
    return related_doc


def summary_related_doc(query: str, related_doc: str, model=None) -> str:
    """
    Deep read fragments. Based on the user query, extract fragments related to the query 
    from the original related_doc fragments, without inventing information.
    
    :param query: str, required - User's natural language query, as the basic retrieval condition
    :param related_doc: str, required - Original document fragments
    :return: summary_related_doc_res: str - Filtered fragments
    """
    if model is None:
        raise ValueError("Model must be provided")
    
    # Only summarize if document is longer than threshold
    if len(related_doc) <= SUMMARY_THRESHOLD:
        return related_doc
    
    query_and_related_doc = f'这是用户的query:{query}\n\n这是原文的众多片段:{related_doc}'
    
    summary_related_doc_conversation = [
        {
            "role": "system",
            "content": "你是一个乐于助人的助手,现在有很多原文片段。请根据用户的query,从这些片段中筛选出与query最相关的部分,不要编造信息。"
        },
        {
            "role": "user",
            "content": query_and_related_doc
        }
    ]
    
    model_with_structure = model.with_structured_output(SummaryRelatedDocFormat)
    response = model_with_structure.invoke(summary_related_doc_conversation)
    
    summary_related_doc_res = response.summary_related_doc_res
    return summary_related_doc_res
