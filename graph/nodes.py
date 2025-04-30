from utils.arxiv_client import ArxivClient
from utils.google_scholar_client import GoogleScholarClient # Added import
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
    """Node to search for papers from a specified source (arXiv or Google Scholar)

    Args:
        state: Current workflow state with 'topic' key,
               optionally 'search_source' ('arxiv' or 'google_scholar', defaults to 'arxiv'),
               and optionally 'max_results' (defaults to 5).

    Returns:
        Dict with 'papers' key containing search results, or 'error' key if failed.
    """
    # Skip search if papers are already provided
    if state.get("papers") and state.get("selected_paper"):
        return {"papers": state.get("papers")}
        
    topic = state.get("topic", "")
    search_source = state.get("search_source", "arxiv").lower() # Default to arxiv
    max_results = state.get("max_results", 5)

    if not topic:
        return {"papers": [], "error": "No search topic provided"}

    try:
        if search_source == "google_scholar":
            client = GoogleScholarClient()
            # Note: GoogleScholarClient's search_papers handles max_results internally
            papers = client.search_papers(topic, max_results=max_results)
        elif search_source == "arxiv":
            client = ArxivClient()
            papers = client.search_recent_papers(topic, max_results=max_results)
        else:
            return {"papers": [], "error": f"Invalid search source: {search_source}. Use 'arxiv' or 'google_scholar'."}

        return {"papers": papers}
    except Exception as e:
        return {"papers": [], "error": f"Error searching {search_source}: {str(e)}"}

# --- Node to ask user for search source ---
def ask_search_source_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Checks if search source is set, if not, prepares details for a user prompt."""
    if state.get("search_source"):
        # Source already selected, proceed without interruption
        # Return non-empty dict to avoid warnings
        return {"source_checked": True}
    else:
        # Signal to the agent/runner to ask the user
        return {
            "interrupt_action": "ask_question",
            "question_details": {
                "question": "Select the search source:",
                "suggestions": ["1. arXiv", "2. Google Scholar"],
                # Agent should store the raw user response here
                "target_state_key": "search_source_raw_input"
            }
        }

# --- Node to process the user's selection ---
def process_source_selection_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Processes the user's raw selection and sets the search_source state."""
    raw_input = state.get("search_source_raw_input", "")
    search_source = None
    error_msg = state.get("error") # Preserve existing errors

    if not raw_input:
        # This shouldn't happen if the graph logic is correct, but handle defensively
        error_msg = (error_msg + "\n" if error_msg else "") + "No search source selection received."
        search_source = "arxiv" # Default if something went wrong
    else:
        raw_input_lower = raw_input.lower()
        if "arxiv" in raw_input_lower or "1" in raw_input_lower:
            search_source = "arxiv"
        elif "google scholar" in raw_input_lower or "scholar" in raw_input_lower or "2" in raw_input_lower:
            search_source = "google_scholar"
        else:
            error_msg = (error_msg + "\n" if error_msg else "") + f"Invalid selection: '{raw_input}'. Defaulting to arXiv."
            search_source = "arxiv" # Default on invalid input

    # Prepare state updates, clearing interrupt flags and raw input
    updates = {
        "search_source_raw_input": None,
        "interrupt_action": None,
        "question_details": None,
        "search_source": search_source,
        "error": error_msg
    }
    # Return only non-None values to keep state clean
    return {k: v for k, v in updates.items() if v is not None}


# --- Existing Nodes ---

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
        # Format the publication date if available
        pub_date = paper.get("published", "")
        formatted_date = ""
        if pub_date:
            try:
                from datetime import datetime
                if 'T' in pub_date:  # ISO format
                    dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                    formatted_date = dt.strftime('%B %d, %Y')
                elif '-' in pub_date:  # YYYY-MM-DD format
                    dt = datetime.strptime(pub_date.split()[0], '%Y-%m-%d')
                    formatted_date = dt.strftime('%B %d, %Y')
                else:
                    formatted_date = pub_date
            except Exception:
                formatted_date = pub_date

        prompt = ChatPromptTemplate.from_template("""
        Write a technical blog post based on this paper analysis:

        Paper: {title}
        Authors: {authors}
        Publication Date: {pub_date}
        URL: {url}
        Analysis: {analysis}

        Create a 500-word technical blog post with:
        1. A catchy title
        2. Brief introduction to the problem
        3. Summary of the approach
        4. Key findings and their significance
        5. Conclusion with future implications
        6. Include a "References" section at the end with the paper title, authors, publication date, and URL

        Format the blog as Markdown with proper headers, links, and styling.
        Make sure to include the publication date in the post introduction and in the references.

        Blog Post:
        """)

        chain = prompt | llm

        blog = chain.invoke({
            "title": paper["title"],
            "authors": ", ".join(paper["authors"]),
            "pub_date": formatted_date or "Date not available",
            "url": paper.get("url", "No URL available"),
            "analysis": analysis
        })

        return {"blog_post": blog.content}
    except Exception as e:
        return {"blog_post": "", "error": f"Error generating blog: {str(e)}"}