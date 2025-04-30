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

def run_workflow(topic: str, paper_index: int = 0, search_source: str = "arxiv") -> Dict[str, Any]:
    """Run the research assistant workflow.

    Args:
        topic: Research topic to search for
        paper_index: Index of the paper to analyze (0-based)
        search_source: Source to search ("arxiv" or "google_scholar")

    Returns:
        Final workflow state
    """
    # Create the workflow
    workflow = create_workflow()

    # Initial state with topic, paper index, and search source
    initial_state = {
        "topic": topic,
        "paper_index": paper_index,
        "search_source": search_source,  # Set from parameter now
        "search_source_raw_input": None, # Not needed, but keep for compatibility
        "interrupt_action": None,
        "question_details": None,
        "papers": [],
        "selected_paper": None,
        "analysis": "",
        "blog_post": "",
        "error": None
    }

    final_state = {}
    try:
        # Use stream to handle potential interruptions
        for event in workflow.stream(initial_state):
            if not event:
                print("Warning: Received empty event from workflow")
                continue
                
            try:
                # The event key is the node name, event value is the node's output
                event_key = list(event.keys())[0]
                event_value = event[event_key]
                
                # Validate event value
                if event_value is None:
                    print(f"Warning: Node '{event_key}' returned None")
                    continue
                
                # Update the conceptual final state with the latest output
                final_state.update(event_value)
            except (KeyError, TypeError, IndexError) as e:
                print(f"Warning: Could not process event: {str(e)}")
                print(f"Event type: {type(event)}")
                continue

            # Check if the graph signaled an interruption to ask a question
            if final_state.get("interrupt_action") == "ask_question":
                details = final_state.get("question_details", {})
                question = details.get("question", "Missing question")
                suggestions = details.get("suggestions", [])
                target_key = details.get("target_state_key", "user_response") # Key to store raw response

                # Display prompt and suggestions
                print(f"\n{question}")
                for suggestion in suggestions:
                    print(suggestion)

                # Get user input
                user_response = input("Your choice: ").strip()

                # Update state with the user's response
                initial_state[target_key] = user_response # Update state for next implicit step
                final_state[target_key] = user_response # Keep track for final output if needed
                final_state["interrupt_action"] = None # Clear the interrupt flag
                final_state["question_details"] = None

                print("Processing your selection...")

        # After the stream finishes
        print("\nWorkflow finished.")
        
        # Verify we have expected state fields
        required_fields = ["papers", "selected_paper"]
        for field in required_fields:
            if field not in final_state or final_state[field] is None:
                print(f"Warning: Expected field '{field}' missing or None in final state")
        
        return final_state

    except Exception as e:
        import traceback
        error_msg = f"Error running workflow stream: {str(e)}"
        print(error_msg)
        print(f"Error type: {type(e).__name__}")
        print(f"Error trace: {traceback.format_exc()}")
        
        # Try to return a meaningful error state
        if not final_state:
            final_state = {}
        final_state["error"] = (final_state.get("error", "") + "\n" + error_msg).strip()
        return final_state

def display_graph(query: str, search_source: str = "arxiv") -> int:
    """Display the paper graph for a query
    
    Args:
        query: Search query for papers
        search_source: Source to search ("arxiv" or "google_scholar")
        
    Returns:
        int: Number of papers found
    """
    try:
        # Create appropriate client and GraphBuilder
        if search_source.lower() == "google_scholar":
            from utils.google_scholar_client import GoogleScholarClient
            search_client = GoogleScholarClient()
            source_name = "Google Scholar"
        else:
            search_client = ArxivClient()
            source_name = "arXiv"
            
        graph_builder = GraphBuilder(search_client, search_source)
        
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
        print(f"\n{source_name} results for query '{query}':")
        print(f"Found {paper_count} papers")
        
        if paper_count > 0:
            # Display numbered list with publication dates
            for i, node in enumerate(paper_nodes, 1):
                # Format publication date or use fallback
                pub_date = node.paper.published_date
                date_str = ""
                if pub_date:
                    try:
                        # Try to parse and format the date (handle different formats)
                        from datetime import datetime
                        if 'T' in pub_date:  # ISO format
                            dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                            date_str = f" ({dt.strftime('%b %d, %Y')})"
                        elif '-' in pub_date:  # YYYY-MM-DD format
                            dt = datetime.strptime(pub_date.split()[0], '%Y-%m-%d')
                            date_str = f" ({dt.strftime('%b %d, %Y')})"
                        else:
                            date_str = f" ({pub_date})"
                    except Exception:
                        # If date parsing fails, just show it as-is
                        date_str = f" ({pub_date})"
                        
                print(f"{i}. {node.paper.title} by {', '.join(node.paper.authors[:3])}{date_str}")
                
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
    
    # Ask user to select search source
    print("\nSelect search source:")
    print("1. arXiv (scientific papers)")
    print("2. Google Scholar (broader academic content)")
    
    search_source = "arxiv"  # Default
    while True:
        source_choice = input("Enter your choice (1-2) [1]: ").strip()
        if not source_choice or source_choice == "1":
            search_source = "arxiv"
            break
        elif source_choice == "2":
            search_source = "google_scholar"
            break
        else:
            print("Invalid selection. Please choose 1 for arXiv or 2 for Google Scholar.")
    
    # Display graph and check if papers were found
    paper_count = display_graph(topic, search_source)
    
    # If no papers found, prompt for a new search
    while paper_count == 0:
        print("\nNo papers found. Try a different search term or source.")
        retry_choice = input("Try again with: [1] New search term, [2] Different source, [3] Exit: ").strip()
        
        if retry_choice == "1":
            topic = input("Enter new research topic: ")
            if not topic:
                print("Empty search. Exiting.")
                return
            # Keep the same search source
            paper_count = display_graph(topic, search_source)
            
        elif retry_choice == "2":
            # Switch source
            search_source = "google_scholar" if search_source == "arxiv" else "arxiv"
            print(f"Switching to {search_source}...")
            paper_count = display_graph(topic, search_source)
            
        else:
            print("Exiting.")
            return
    
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
        # Pass selected paper index and search source to workflow
        try:
            final_state = run_workflow(topic, paper_index, search_source)
            
            # Display results
            if final_state and final_state.get("error"):
                print(f"\nError: {final_state['error']}")
                return  # Exit if there's an error
            elif final_state:
                print("\n=== Analysis ===")
                print(final_state.get("analysis", "No analysis generated"))
                
                print("\n=== Blog Post ===")
                print(final_state.get("blog_post", "No blog post generated"))
                
                # Offer to save only if we have content
                if final_state.get("blog_post"):
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
            else:
                print("\nError: Workflow did not return any results. There might be an issue with the search source.")
                return
        except Exception as e:
            import traceback
            print(f"\nError running workflow: {str(e)}")
            print(traceback.format_exc())
            return

if __name__ == "__main__":
    main()