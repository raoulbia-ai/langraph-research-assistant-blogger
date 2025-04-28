from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Paper:
    """Represents a research paper with metadata"""
    id: str
    title: str
    authors: List[str]
    abstract: str
    published_date: str
    url: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Paper':
        """Create a Paper object from a dictionary
        
        Args:
            data: Dictionary containing paper metadata
            
        Returns:
            Paper: A new Paper instance
        """
        return cls(
            id=data.get('id', ''),
            title=data.get('title', ''),
            authors=data.get('authors', []),
            abstract=data.get('summary', ''),
            published_date=data.get('published', ''),
            url=data.get('url', '')
        )

@dataclass
class WorkflowState:
    """Represents the state of the research assistant workflow"""
    topic: str
    papers: List[dict] = None
    selected_paper: Optional[dict] = None
    analysis: str = ""
    blog_post: str = ""
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.papers is None:
            self.papers = []