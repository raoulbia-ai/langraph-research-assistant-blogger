import arxiv
from typing import List, Dict, Any, Optional

class ArxivClient:
    """Client for interacting with the ArXiv API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the ArXiv client
        
        Args:
            api_key (Optional[str]): Not required for ArXiv but kept for consistency
        """
        # ArXiv doesn't require an API key, but we maintain the parameter for consistency
        self.client = arxiv.Client()
    
    def search_recent_papers(self, topic: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search for recent papers on ArXiv
        
        Args:
            topic (str): The search query topic
            max_results (int, optional): Maximum number of results to return. Defaults to 5.
            
        Returns:
            List[Dict[str, Any]]: List of paper metadata dictionaries
        """
        try:
            # Try with date filter first
            search = arxiv.Search(
                query=f"{topic} AND submittedDate:[2025 TO 2099]",
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            # Check if there are any results
            results = list(self.client.results(search))
            
            # If no results, try without date filter
            if not results:
                search = arxiv.Search(
                    query=topic,
                    max_results=max_results,
                    sort_by=arxiv.SortCriterion.SubmittedDate
                )
                results = list(self.client.results(search))
                
            # Process results
            processed_results = []
            for paper in results:
                processed_results.append({
                    "id": paper.entry_id,
                    "title": paper.title,
                    "summary": paper.summary,
                    "authors": [author.name for author in paper.authors],
                    "published": paper.published,
                    "url": paper.pdf_url
                })
                
            return processed_results
        except Exception as e:
            print(f"Error searching ArXiv: {str(e)}")
            return []

# For backward compatibility with existing code
def search_recent_papers(topic, max_results=5):
    """Legacy function for searching papers on ArXiv"""
    client = ArxivClient()
    return client.search_recent_papers(topic, max_results)