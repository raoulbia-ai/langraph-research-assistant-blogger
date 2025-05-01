from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional, Dict, Any
from src.graph.workflow.nodes import (
    search_node,
    select_paper_node,
    analyze_paper_node,
    generate_blog_node,
    ask_search_source_node,         # Added
    process_source_selection_node   # Added
)

# Define a TypedDict for our state
class WorkflowState(TypedDict, total=False):
    topic: str
    search_source: Optional[str] # Added: 'arxiv' or 'google_scholar'
    search_source_raw_input: Optional[str] # Added: To store user's raw input
    interrupt_action: Optional[str] # Added: Signal for interruption
    question_details: Optional[Dict[str, Any]] # Added: Details for the question
    papers: List[Dict[str, Any]]
    paper_index: int
    selected_paper: Optional[Dict[str, Any]]
    analysis: str
    blog_post: str
    error: Optional[str]

def create_workflow():
    """Create workflow with optional interactive search source selection"""
    # Define our state with schema
    workflow = StateGraph(WorkflowState)

    # Add all nodes
    workflow.add_node("ask_source", ask_search_source_node)
    workflow.add_node("process_source", process_source_selection_node)
    workflow.add_node("search", search_node)
    workflow.add_node("select", select_paper_node)
    workflow.add_node("analyze", analyze_paper_node)
    workflow.add_node("blog", generate_blog_node)

    # First conditional: check if we already have a selected paper to start analyzing
    def has_selected_paper(state: Dict[str, Any]) -> str:
        """Check if we already have a selected paper to skip search and select steps"""
        # Ensure state always has a valid search_source to avoid None returns
        if not state.get("search_source"):
            # Default to arxiv to avoid None issues in conditional nodes
            state["search_source_placeholder"] = True
            
        if state.get("selected_paper") is not None:
            # Ensure papers list exists even if we're skipping the search
            # This prevents warnings about missing fields
            if not state.get("papers") and state.get("selected_paper"):
                papers = [state["selected_paper"]]
                state["papers"] = papers
                
            return "analyze"  # Skip to analysis directly
        elif state.get("search_source"):
            # No selected paper but search source is set, go to search
            return "search"
        else:
            # Neither paper nor source is provided, start with source selection
            return "ask_source"

    # Entry conditional for the whole workflow
    workflow.add_conditional_edges(
        "ask_source",
        has_selected_paper,
        {
            "ask_source": "process_source",  # Start with source selection
            "search": "search",              # Skip to search directly
            "analyze": "analyze"             # Skip to analysis directly
        }
    )
    
    # Simply check for None outputs in each node instead of using set_node_wrapper
    # The set_node_wrapper method isn't available in this version of langgraph

    # Define the rest of the workflow sequence
    workflow.add_edge("process_source", "search")
    workflow.add_edge("search", "select")
    workflow.add_edge("select", "analyze")
    workflow.add_edge("analyze", "blog")
    workflow.add_edge("blog", END)

    # Set the entry point
    workflow.set_entry_point("ask_source")

    # Compile the graph
    return workflow.compile()