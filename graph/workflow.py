from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional, Dict, Any
from graph.nodes import (
    search_node, 
    select_paper_node, 
    analyze_paper_node, 
    generate_blog_node
)

# Define a TypedDict for our state
class WorkflowState(TypedDict, total=False):
    topic: str
    papers: List[Dict[str, Any]]
    paper_index: int
    selected_paper: Optional[Dict[str, Any]]
    analysis: str
    blog_post: str
    error: Optional[str]

def create_workflow():
    """Create basic linear workflow"""
    # Define our state with schema
    workflow = StateGraph(WorkflowState)

    # Add all nodes
    workflow.add_node("search", search_node)
    workflow.add_node("select", select_paper_node)
    workflow.add_node("analyze", analyze_paper_node)
    workflow.add_node("blog", generate_blog_node)

    # Add linear edges
    workflow.add_edge("search", "select")
    workflow.add_edge("select", "analyze")
    workflow.add_edge("analyze", "blog")
    workflow.add_edge("blog", END)

    # Set the entry point
    workflow.set_entry_point("select")

    # Compile the graph
    return workflow.compile()