# ArXiv Search Improvement Plan

## Problem
The current ArXiv search implementation returns papers that are not always relevant to the search terms. This happens because:

1. The ArXiv API doesn't provide built-in relevance sorting
2. We're using a simple query string without advanced search syntax
3. There's no post-processing filtering of results based on relevance

## Proposed Changes

### 1. Improve Query Construction
- Implement proper query term extraction (remove stop words)
- Use exact phrase matching with quotes for multi-word terms
- Utilize ArXiv's search operators (AND, OR, etc.) more effectively
- Add category filtering when appropriate

### 2. Add Post-Processing Relevance Scoring
- Score each paper based on:
  - Title matches (highest weight)
  - Abstract/summary matches (medium weight)
  - Author matches (if searching for specific researchers)
  - Recent publication dates (time relevance)
- Sort results by this relevance score
- Filter out papers below a relevance threshold

### 3. Enhance Result Count and Filtering
- Request more results than needed initially (e.g., 2-3x)
- Apply post-filtering to select the most relevant ones
- Implement optional category filtering

### 4. Implementation Approach
- Update the `search_recent_papers` method 
- Add helper methods for term extraction and relevance scoring
- Ensure backward compatibility

## Technical Details

### Query Construction Improvements
```python
# Extract key terms from topic
key_terms = self._extract_key_terms(topic)

# Build a more precise query with quotes and AND operators
search_query = ' AND '.join([f'"{term}"' for term in key_terms if len(term) > 2])
```

### Relevance Scoring Formula
```python
def _calculate_relevance(self, paper, key_terms, topic):
    score = 0.0
    
    # Exact phrase matches (highest weight)
    if topic.lower() in paper["title"].lower():
        score += 10.0
    if topic.lower() in paper["summary"].lower():
        score += 5.0
    
    # Individual term matches
    for term in key_terms:
        # Title matches (high weight)
        if term in paper["title"].lower():
            score += 3.0
        # Summary matches (medium weight)
        if term in paper["summary"].lower():
            score += 1.0
            
    return score
```

### Result Processing
```python
# Get more results than needed for filtering
search = arxiv.Search(query=search_query, max_results=max_results * 2)

# Score all results and sort by relevance
scored_papers = [(paper, self._calculate_relevance(paper, key_terms)) 
                 for paper in results]
scored_papers.sort(key=lambda x: x[1], reverse=True)

# Return only the top results
return [paper for paper, score in scored_papers[:max_results]]
```

## Future Extensions
- Add category filtering to focus on specific ArXiv categories
- Integrate with domain-specific terminology for better matching
- Consider implementing a simple cache for frequent searches