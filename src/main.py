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

def run_workflow(topic: str, paper_index: int = 0) -> Dict[str, Any]:
    """Run the research assistant workflow
    
    Args:
        topic: Research topic to search for
        paper_index: Index of the paper to analyze (0-based)
        
    Returns:
        Final workflow state
    """
    # Create the workflow
    workflow = create_workflow()
    
    # Get papers first to ensure we have data before running workflow
    try:
        arxiv_client = ArxivClient()
        papers = arxiv_client.search_recent_papers(topic)
        
        # Validate paper_index before running workflow
        if paper_index < 0 or paper_index >= len(papers):
            return {"error": f"Invalid paper index: {paper_index+1}. Only {len(papers)} papers available."}
        
        # Create initial state with pre-loaded papers
        initial_state = {
            "topic": topic,
            "papers": papers,
            "paper_index": paper_index,
            "selected_paper": None,
            "analysis": "",
            "blog_post": "",
            "error": None
        }
        
        # Run the workflow
        final_state = workflow.invoke(initial_state)
        return final_state
    except Exception as e:
        error_msg = f"Error running workflow: {str(e)}"
        print(error_msg)
        return {"error": error_msg}

def display_graph(query: str) -> int:
    """Display the paper graph for a query
    
    Args:
        query: Search query for papers
        
    Returns:
        int: Number of papers found
    """
    try:
        # Create ArxivClient and GraphBuilder
        arxiv_client = ArxivClient()
        graph_builder = GraphBuilder(arxiv_client)
        
        # Build the graph
        graph = graph_builder.build_graph(query)
        
        # Collect paper nodes
        paper_nodes = []
        for node_id, node in graph.items():
            if hasattr(node, 'paper'):
                paper_nodes.append(node)
        
        # Get accurate paper count
        paper_count = len(paper_nodes)
        
        # Display graph info
        print(f"\nGraph for query '{query}':")
        print(f"Found {paper_count} papers")
        
        if paper_count > 0:
            # Display numbered list
            for i, node in enumerate(paper_nodes, 1):
                print(f"{i}. {node.paper.title} by {', '.join(node.paper.authors[:3])}")
                
        return paper_count
    except Exception as e:
        print(f"Error displaying graph: {str(e)}")
        return 0

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
    
    # Display graph and check if papers were found
    paper_count = display_graph(topic)
    
    # If no papers found, prompt for a new search
    while paper_count == 0:
        print("\nNo papers found. Try a different search term.")
        topic = input("Enter new research topic: ")
        if not topic:
            print("Empty search. Exiting.")
            return
        paper_count = display_graph(topic)
    
    # Ask user which paper to analyze
    print("\nWhich paper would you like to analyze and generate a blog post for?")
    # Process user selection with error handling
    paper_index = -1 # Initialize with invalid index
    while True: # Loop until valid input is received
        paper_choice = input(f"Enter paper number (1-{paper_count}): ").strip()
        try:
            selected_index = int(paper_choice) - 1
            if 0 <= selected_index < paper_count:
                paper_index = selected_index
                break # Exit loop on valid selection
            else:
                print(f"Invalid paper selection. Please choose a number between 1 and {paper_count}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    # Proceed only if a valid paper_index was set
    if paper_index != -1:
        print("\nRunning workflow...")
        # Pass selected paper index to workflow
        final_state = run_workflow(topic, paper_index)
        
        # Display results
        if final_state.get("error"):
            print(f"\nError: {final_state['error']}")
        else:
            print("\n=== Analysis ===")
            print(final_state.get("analysis", "No analysis generated"))
            
            print("\n=== Blog Post ===")
            print(final_state.get("blog_post", "No blog post generated"))
            
            # Offer to save
            save = input("\nSave blog post to file? (y/n): ").strip()
            if save.lower() == 'y':
                filename = f"blog_{topic.replace(' ', '_')}_{paper_index+1}.md" # Add paper index to filename
                # Save in blog_posts directory
                blog_dir = Path(project_root) / "blog_posts"
                # Create the directory if it doesn't exist
                blog_dir.mkdir(exist_ok=True)
                filepath = blog_dir / filename
                try:
                    with open(filepath, "w") as f:
                        f.write(final_state.get("blog_post", ""))
                    print(f"Blog post saved to {filepath}")
                except Exception as e:
                    print(f"Error saving file: {str(e)}")

if __name__ == "__main__":
    main()