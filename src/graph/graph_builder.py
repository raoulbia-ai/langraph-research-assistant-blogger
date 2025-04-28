from src.graph.core_nodes import Node, PaperNode
from src.graph.domain import Paper
from utils.arxiv_client import ArxivClient
from typing import Dict, List, Optional, Any

class GraphBuilder:
    """Builds a graph of nodes based on paper metadata"""
    
    def __init__(self, arxiv_client: Optional[ArxivClient] = None):
        """Initialize the graph builder
        
        Args:
            arxiv_client: ArxivClient instance for fetching papers
        """
        self.root_node = None
        self.nodes = {}
        self.arxiv_client = arxiv_client or ArxivClient()
        
    def build_graph(self, query: str) -> Dict[str, Node]:
        """Build a graph from a search query
        
        Args:
            query: Search query for ArXiv
            
        Returns:
            Dict mapping node IDs to Node objects
        """
        try:
            # Search for papers
            papers = self.arxiv_client.search_recent_papers(query)
            if not papers:
                # Create an empty root node if no papers found
                self.root_node = Node("root", {"name": "Root", "type": "root"})
                self.nodes["root"] = self.root_node
                return self.nodes
                
            # Create the root node
            self.root_node = Node("root", {"name": "Root", "type": "root", "query": query})
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