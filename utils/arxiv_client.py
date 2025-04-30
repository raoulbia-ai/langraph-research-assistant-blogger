import arxiv
import re
from typing import List, Dict, Any, Optional

class ArxivClient:
    """Client for interacting with the ArXiv API with improved search relevance"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the ArXiv client
        
        Args:
            api_key (Optional[str]): Not required for ArXiv but kept for consistency
        """
        # ArXiv doesn't require an API key, but we maintain the parameter for consistency
        self.client = arxiv.Client()
    
    def search_recent_papers(self, topic: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search for recent papers on ArXiv with improved relevance
        
        Args:
            topic (str): The search query topic
            max_results (int, optional): Maximum number of results to return. Defaults to 5.
            
        Returns:
            List[Dict[str, Any]]: List of paper metadata dictionaries, filtered for relevance
        """
        try:
            # Extract key terms for better search precision
            key_terms = self._extract_key_terms(topic)
            
            # Construct a more precise query if possible
            if len(key_terms) > 1:
                # Use quotes for exact term matching and AND operator
                search_query = ' AND '.join([f'"{term}"' for term in key_terms if len(term) > 2])
                if not search_query:  # Fallback if no good terms
                    search_query = topic
            else:
                # Use the original topic if we couldn't extract good terms
                search_query = topic
            
            # Try with date filter first (get more results for filtering)
            search = arxiv.Search(
                query=f"{search_query} AND submittedDate:[2025 TO 2099]",
                max_results=max(max_results * 2, 10),  # Get more results for filtering
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            # Check if there are any results
            results = list(self.client.results(search))
            
            # If no results, try without date filter
            if not results:
                search = arxiv.Search(
                    query=search_query,
                    max_results=max(max_results * 2, 10),  # Get more results for filtering
                    sort_by=arxiv.SortCriterion.SubmittedDate
                )
                results = list(self.client.results(search))
                
            # Process and score results for relevance
            scored_papers = []
            
            for paper in results:
                # Create paper dict
                paper_dict = {
                    "id": paper.entry_id,
                    "title": paper.title,
                    "summary": paper.summary,
                    "authors": [author.name for author in paper.authors],
                    "published": paper.published,
                    "url": paper.pdf_url
                }
                
                # Score paper for relevance
                relevance_score = self._calculate_relevance(paper_dict, key_terms, topic)
                scored_papers.append((paper_dict, relevance_score))
            
            # Sort by relevance score and take top max_results
            scored_papers.sort(key=lambda x: x[1], reverse=True)
            processed_results = [paper for paper, score in scored_papers[:max_results]]
                
            return processed_results
        except Exception as e:
            print(f"Error searching ArXiv: {str(e)}")
            return []
    
    def _extract_key_terms(self, topic: str) -> List[str]:
        """Extract key terms from the search topic
        
        Args:
            topic: The search topic
            
        Returns:
            List of key terms
        """
        # Remove special characters and split by spaces
        cleaned_topic = re.sub(r'[^\w\s]', ' ', topic.lower())
        
        # Split into words
        words = cleaned_topic.split()
        
        # Filter out common stop words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "of"}
        key_terms = [word for word in words if word not in stop_words and len(word) > 2]
        
        return key_terms
    
    def _calculate_relevance(self, paper: Dict[str, Any], key_terms: List[str], topic: str) -> float:
        """Calculate relevance score for a paper
        
        Args:
            paper: Paper dictionary
            key_terms: List of key terms from the search topic
            topic: Original search topic
            
        Returns:
            Relevance score (higher is more relevant)
        """
        score = 0.0
        title = paper["title"].lower()
        summary = paper["summary"].lower()
        
        # Check for exact phrase match (highest weight)
        if topic.lower() in title:
            score += 10.0
        if topic.lower() in summary:
            score += 5.0
        
        # Check for key term matches
        for term in key_terms:
            # Title matches (high weight)
            if term in title:
                score += 3.0
            
            # Summary/abstract matches (medium weight)
            if term in summary:
                score += 1.0
        
        return score

# For backward compatibility with existing code
def search_recent_papers(topic, max_results=5):
    """Legacy function for searching papers on ArXiv"""
    client = ArxivClient()
    return client.search_recent_papers(topic, max_results)