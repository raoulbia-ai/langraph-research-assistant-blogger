from src.graph.domain import Paper
from typing import Dict, List, Any, Optional

class Node:
    """Base node class for the graph"""
    
    def __init__(self, id: str, data: Dict[str, Any]):
        """Initialize a node
        
        Args:
            id: Unique identifier for the node
            data: Data associated with this node
        """
        self.id = id
        self.data = data
        self.children: List[Node] = []
        
    def add_child(self, node: 'Node') -> None:
        """Add a child node to this node
        
        Args:
            node: Child node to add
        """
        if node not in self.children:
            self.children.append(node)
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert the node to a dictionary
        
        Returns:
            Dictionary representation of this node and its children
        """
        result = {
            "id": self.id,
            "data": self.data,
            "children": [child.to_dict() for child in self.children]
        }
        return result
        
    def __repr__(self) -> str:
        return f"Node(id={self.id}, data={self.data}, children={len(self.children)})"

class PaperNode(Node):
    """Node representing a research paper"""
    
    def __init__(self, paper: Paper):
        """Initialize a paper node
        
        Args:
            paper: Paper object
        """
        super().__init__(paper.id, {
            "title": paper.title,
            "authors": paper.authors,
            "abstract": paper.abstract,
            "published_date": paper.published_date,
            "url": paper.url,
            "type": "paper"
        })
        self.paper = paper
            
    def __repr__(self) -> str:
        return f"PaperNode(id={self.id}, title='{self.paper.title}')"