from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional, Dict, Any
from graph.nodes import (
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

    # Define conditional branching based on whether search_source is already set
    def has_search_source(state: Dict[str, Any]) -> str:
        """Check if search source is already set in the state"""
        if state.get("search_source"):
            # Skip to search directly if source is already provided
            print(f"Using pre-selected search source: {state.get('search_source')}")
            return "search"
        else:
            # Start interactive selection if no source is specified
            return "ask_source"

    # Entry conditional on whether search source is already set
    workflow.add_conditional_edges(
        "ask_source",
        has_search_source,
        {
            "ask_source": "process_source",  # Continue with interactive selection
            "search": "search"               # Skip to search directly
        }
    )

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