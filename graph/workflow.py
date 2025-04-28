from langgraph.graph import StateGraph, END
from graph.nodes import (
    search_node, 
    select_paper_node, 
    analyze_paper_node, 
    generate_blog_node
)

def create_workflow():
    """Create basic linear workflow"""
    # Define our state
    workflow = StateGraph(name="research-assistant")

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

    # Compile the graph
    return workflow.compile()