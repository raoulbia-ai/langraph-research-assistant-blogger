from utils.arxiv_client import ArxivClient
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from typing import Dict, Any, List

# Load OpenAI API key from environment
openai_api_key = os.environ.get("OPENAI_API_KEY")

# Initialize LLM with proper error handling
def get_llm():
    """Get LLM instance with error handling for API key"""
    try:
        return ChatOpenAI(model="gpt-3.5-turbo", api_key=openai_api_key)
    except Exception as e:
        print(f"Error initializing LLM: {str(e)}")
        return None

llm = get_llm()

def search_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node to search for papers
    
    Args:
        state: Current workflow state with 'topic' key
        
    Returns:
        Dict with 'papers' key or error
    """
    topic = state.get("topic", "")
    if not topic:
        return {"papers": [], "error": "No search topic provided"}
    
    try:
        arxiv_client = ArxivClient()
        papers = arxiv_client.search_recent_papers(topic)
        return {"papers": papers}
    except Exception as e:
        return {"papers": [], "error": f"Error searching papers: {str(e)}"}

def select_paper_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node to select a paper based on the paper_index
    
    Args:
        state: Current workflow state with 'papers' key and 'paper_index' key
        
    Returns:
        Dict with 'selected_paper' key or error
    """
    papers = state.get("papers", [])
    paper_index = state.get("paper_index", 0)
    
    if not papers:
        return {"selected_paper": None, "error": "No papers found"}
    
    # Ensure index is within bounds
    if paper_index < 0 or paper_index >= len(papers):
        paper_index = 0
        
    return {"selected_paper": papers[paper_index]}

def analyze_paper_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node to analyze the selected paper
    
    Args:
        state: Current workflow state with 'selected_paper' key
        
    Returns:
        Dict with 'analysis' key or error
    """
    paper = state.get("selected_paper")
    if not paper:
        return {"analysis": "", "error": "No paper selected"}
    
    if not llm:
        return {"analysis": "", "error": "LLM initialization failed. Check API key."}

    try:
        prompt = ChatPromptTemplate.from_template("""
        Analyze the following research paper:

        Title: {title}
        Authors: {authors}
        Summary: {summary}

        Provide a concise analysis covering:
        1. Main research question
        2. Key methodology
        3. Primary findings
        4. Implications for the field

        Analysis:
        """)

        chain = prompt | llm

        analysis = chain.invoke({
            "title": paper["title"],
            "authors": ", ".join(paper["authors"]),
            "summary": paper["summary"]
        })

        return {"analysis": analysis.content}
    except Exception as e:
        return {"analysis": "", "error": f"Error analyzing paper: {str(e)}"}

def generate_blog_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node to generate a blog post
    
    Args:
        state: Current workflow state with 'selected_paper' and 'analysis' keys
        
    Returns:
        Dict with 'blog_post' key or error
    """
    paper = state.get("selected_paper")
    analysis = state.get("analysis", "")

    if not analysis:
        return {"blog_post": "", "error": "No analysis available"}
    
    if not llm:
        return {"blog_post": "", "error": "LLM initialization failed. Check API key."}

    try:
        prompt = ChatPromptTemplate.from_template("""
        Write a technical blog post based on this paper analysis:

        Paper: {title}
        Authors: {authors}
        URL: {url}
        Analysis: {analysis}

        Create a 500-word technical blog post with:
        1. A catchy title
        2. Brief introduction to the problem
        3. Summary of the approach
        4. Key findings and their significance
        5. Conclusion with future implications
        6. Include a "References" section at the end with the paper URL 

        Format the blog as Markdown with proper headers, links, and styling.

        Blog Post:
        """)

        chain = prompt | llm

        blog = chain.invoke({
            "title": paper["title"],
            "authors": ", ".join(paper["authors"]),
            "url": paper.get("url", "No URL available"),
            "analysis": analysis
        })

        return {"blog_post": blog.content}
    except Exception as e:
        return {"blog_post": "", "error": f"Error generating blog: {str(e)}"}