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
            search = arxiv.Search(
                query=topic,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            results = []
            for paper in self.client.results(search):
                results.append({
                    "id": paper.entry_id,
                    "title": paper.title,
                    "summary": paper.summary,
                    "authors": [author.name for author in paper.authors],
                    "published": paper.published,
                    "url": paper.pdf_url
                })
                
            return results
        except Exception as e:
            print(f"Error searching ArXiv: {str(e)}")
            return []

# For backward compatibility with existing code
def search_recent_papers(topic, max_results=5):
    """Legacy function for searching papers on ArXiv"""
    client = ArxivClient()
    return client.search_recent_papers(topic, max_results)