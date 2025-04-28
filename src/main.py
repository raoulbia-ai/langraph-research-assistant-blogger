import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

# Add project root to path so imports work correctly
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from graph.workflow import create_workflow
from utils.arxiv_client import ArxivClient
from src.graph.graph_builder import GraphBuilder
from src.graph.domain import WorkflowState

def load_config() -> Dict[str, Any]:
    """Load configuration from config file
    
    Returns:
        Dict containing configuration values
    """
    try:
        config_path = Path(project_root) / 'config.json'
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
    except Exception as e:
        print(f"Error loading config: {str(e)}")
        return {}

def setup_environment() -> None:
    """Setup environment variables from config"""
    # Load .env file if it exists
    env_path = Path(project_root) / '.env'
    load_dotenv(dotenv_path=env_path)
    
    # Load API key from config if not in environment
    if not os.environ.get('OPENAI_API_KEY'):
        config = load_config()
        api_key = config.get('api_key')
        if api_key and api_key != "YOUR_API_KEY_HERE":
            os.environ['OPENAI_API_KEY'] = api_key
            print("Loaded API key from config.json")
        else:
            print("Warning: No valid API key found. Set OPENAI_API_KEY in environment or config.json")

def run_workflow(topic: str) -> Dict[str, Any]:
    """Run the research assistant workflow
    
    Args:
        topic: Research topic to search for
        
    Returns:
        Final workflow state
    """
    # Create the workflow
    workflow = create_workflow()
    
    # Create initial state
    initial_state = {
        "topic": topic,
        "papers": [],
        "selected_paper": None,
        "analysis": "",
        "blog_post": "",
        "error": None
    }
    
    try:
        # Run the workflow
        final_state = workflow.invoke(initial_state)
        return final_state
    except Exception as e:
        print(f"Error running workflow: {str(e)}")
        return {"error": str(e)}

def display_graph(query: str) -> None:
    """Display the paper graph for a query
    
    Args:
        query: Search query for papers
    """
    try:
        # Create ArxivClient and GraphBuilder
        arxiv_client = ArxivClient()
        graph_builder = GraphBuilder(arxiv_client)
        
        # Build the graph
        graph = graph_builder.build_graph(query)
        
        # Display graph info
        print(f"\nGraph for query '{query}':")
        print(f"Found {len(graph) - 1} papers") # -1 for root node
        
        # Display nodes
        for node_id, node in graph.items():
            if hasattr(node, 'paper'):
                print(f"- {node.paper.title} by {', '.join(node.paper.authors[:3])}")
    except Exception as e:
        print(f"Error displaying graph: {str(e)}")

def main() -> None:
    """Main entry point for the application"""
    # Setup environment
    setup_environment()
    
    # Get query from config or use default
    config = load_config()
    default_query = config.get('query', 'machine learning')
    
    # Get topic from user
    print("Research Assistant")
    print("=================")
    topic = input(f"Enter research topic [{default_query}]: ")
    if not topic:
        topic = default_query
    
    # Display graph
    display_graph(topic)
    
    # Ask if user wants to run workflow
    print("\nDo you want to analyze the first paper and generate a blog post?")
    choice = input("Enter 'y' to continue: ")
    
    if choice.lower() == 'y':
        print("\nRunning workflow...")
        final_state = run_workflow(topic)
        
        # Display results
        if final_state.get("error"):
            print(f"\nError: {final_state['error']}")
        else:
            print("\n=== Analysis ===")
            print(final_state.get("analysis", "No analysis generated"))
            
            print("\n=== Blog Post ===")
            print(final_state.get("blog_post", "No blog post generated"))
            
            # Offer to save
            save = input("\nSave blog post to file? (y/n): ")
            if save.lower() == 'y':
                filename = f"blog_{topic.replace(' ', '_')}.md"
                with open(filename, "w") as f:
                    f.write(final_state.get("blog_post", ""))
                print(f"Blog post saved to {filename}")

if __name__ == "__main__":
    main()