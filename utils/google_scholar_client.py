import re
from typing import List, Dict, Any, Optional
from scholarly import scholarly, ProxyGenerator

class GoogleScholarClient:
    """Client for interacting with Google Scholar via the scholarly library"""

    def __init__(self, use_proxy: bool = False):
        """Initialize the Google Scholar client

        Args:
            use_proxy (bool): Whether to use a proxy generator for requests.
                              Helps avoid getting blocked by Google Scholar.
        """
        if use_proxy:
            # Configure a proxy generator if needed
            # This might require additional setup depending on the proxy service
            pg = ProxyGenerator()
            # Example: Using a free proxy (less reliable)
            # success = pg.FreeProxies()
            # Or configure with premium proxies if available
            # success = pg.ScraperAPI(YOUR_SCRAPER_API_KEY)
            # scholarly.use_proxy(pg)
            print("Proxy usage requested, but no specific proxy configured in this basic client.")
            # For now, we'll proceed without a proxy, but note it might lead to blocks.
            pass # Add actual proxy setup here if required and configured

    def search_papers(self, topic: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search for papers on Google Scholar

        Args:
            topic (str): The search query topic
            max_results (int, optional): Maximum number of results to attempt to fetch
                                         and process. Defaults to 5. Note: scholarly
                                         might return fewer depending on search results.

        Returns:
            List[Dict[str, Any]]: List of paper metadata dictionaries, normalized.
        """
        papers = []
        try:
            print(f"Searching Google Scholar for: {topic}")
            # The scholarly.search_pubs returns a generator
            search_results = scholarly.search_pubs(topic)

            count = 0
            for result in search_results:
                if count >= max_results:
                    break

                # Normalize the result into the expected dictionary format
                paper_dict = self._normalize_result(result)
                if paper_dict:
                    papers.append(paper_dict)
                    count += 1

            print(f"Found and processed {len(papers)} papers from Google Scholar.")
            return papers

        except Exception as e:
            print(f"Error searching Google Scholar: {str(e)}")
            # Consider more specific error handling based on scholarly exceptions
            return [] # Return empty list on error

    def _normalize_result(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize a single result from scholarly into the standard format"""
        try:
            # Extract fields, providing defaults or None if not available
            title = result.get('bib', {}).get('title', 'No Title Available')
            summary = result.get('bib', {}).get('abstract', 'No Summary Available')
            authors = result.get('bib', {}).get('author', [])
            # Ensure authors are strings if the library returns structured author info
            if authors and not isinstance(authors[0], str):
                 authors = [author.get('name', 'Unknown Author') for author in authors if isinstance(author, dict)]
            elif isinstance(authors, str): # Handle case where authors might be a single string
                authors = [authors]


            published_year = result.get('bib', {}).get('pub_year', None)
            # Construct a simple published date string if year is available
            published_date_str = f"{published_year}-01-01T00:00:00Z" if published_year else None

            # URL: scholarly provides 'pub_url' (publisher link) or 'eprint_url' (often PDF)
            url = result.get('eprint_url', result.get('pub_url', None))

            # ID: Use the publication ID if available, otherwise generate one (less ideal)
            # Google Scholar IDs are not as standard as arXiv IDs
            paper_id = result.get('gs_id', f"gs_{result.get('cid', title[:20])}") # Fallback ID

            return {
                "id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors if isinstance(authors, list) else [str(authors)],
                "published": published_date_str, # Note: Only year is usually available
                "url": url
            }
        except Exception as e:
            print(f"Error normalizing Google Scholar result: {str(e)} - Result: {result}")
            return None

# Example usage (for testing)
if __name__ == '__main__':
    client = GoogleScholarClient()
    search_topic = "large language models for code generation"
    found_papers = client.search_papers(search_topic, max_results=3)
    print("\nFound Papers:")
    for i, p in enumerate(found_papers):
        print(f"\n--- Paper {i+1} ---")
        print(f"  ID: {p.get('id')}")
        print(f"  Title: {p.get('title')}")
        print(f"  Authors: {', '.join(p.get('authors', []))}")
        print(f"  Published: {p.get('published')}")
        print(f"  URL: {p.get('url')}")
        # print(f"  Summary: {p.get('summary', '')[:150]}...") # Keep summary short for printing