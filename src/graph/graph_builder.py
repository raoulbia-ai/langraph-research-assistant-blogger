from src.graph.core_nodes import Node, PaperNode
from src.graph.domain import Paper
from utils.arxiv_client import ArxivClient
from utils.google_scholar_client import GoogleScholarClient
from typing import Dict, List, Optional, Any, Union

class GraphBuilder:
    """Builds a graph of nodes based on paper metadata"""
    
    def __init__(self, search_client: Optional[Union[ArxivClient, GoogleScholarClient]] = None, 
                 search_source: str = "arxiv"):
        """Initialize the graph builder
        
        Args:
            search_client: Search client instance for fetching papers
            search_source: Source to search ("arxiv" or "google_scholar"), defaults to "arxiv"
        """
        self.root_node = None
        self.nodes = {}
        self.search_source = search_source.lower()
        
        # Create appropriate client if none provided
        if search_client is None:
            if self.search_source == "google_scholar":
                search_client = GoogleScholarClient()
            else:
                search_client = ArxivClient()
                
        self.search_client = search_client
        
    def build_graph(self, query: str) -> Dict[str, Node]:
        """Build a graph from a search query
        
        Args:
            query: Search query for papers
            
        Returns:
            Dict mapping node IDs to Node objects
        """
        try:
            # Search for papers using the appropriate client
            papers = []
            if isinstance(self.search_client, GoogleScholarClient):
                papers = self.search_client.search_papers(query)
            else:  # Assume ArxivClient or compatible interface
                papers = self.search_client.search_recent_papers(query)
                
            if not papers:
                # Create an empty root node if no papers found
                self.root_node = Node("root", {"name": "Root", "type": "root", 
                                              "source": self.search_source})
                self.nodes["root"] = self.root_node
                return self.nodes
                
            # Create the root node
            self.root_node = Node("root", {"name": "Root", "type": "root", 
                                          "query": query, "source": self.search_source})
            self.nodes["root"] = self.root_node
            
            # Add paper nodes
            for paper in papers:
                paper_node = PaperNode(Paper(
                    id=paper['id'],
                    title=paper['title'],
                    authors=paper['authors'],
                    abstract=paper.get('summary', ''),
                    published_date=paper.get('published', ''),
                    url=paper.get('url', '')
                ))
                self.nodes[paper['id']] = paper_node
                self.root_node.add_child(paper_node)
            
            return self.nodes
        except Exception as e:
            print(f"Error building graph: {str(e)}")
            # Return at least a root node on error
            self.root_node = Node("root", {"name": "Root", "type": "root", "error": str(e)})
            self.nodes["root"] = self.root_node
            return self.nodes
            
    def __repr__(self):
        return f"GraphBuilder(nodes={len(self.nodes) if self.nodes else 0})"
        
    def to_dict(self):
        """Convert the graph to a dictionary
        
        Returns:
            Dictionary representation of the graph
        """
        if self.root_node:
            return self.root_node.to_dict()
        return {}