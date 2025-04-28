# Phase 0.1.0: Core Functionality Specifications

## Functional Requirements
1. **Paper Discovery**
   - Search ArXiv for papers by topic (MAX_RESULTS=5)
   - Return paper metadata including title, authors, summary, and URL
   - // TEST: Should return ≥1 paper for valid topics
   - // TEST: Should handle empty result sets gracefully

2. **Workflow Execution**
   - Define linear workflow sequence: SEARCH → SELECT → ANALYZE → BLOG
   - Maintain state across workflow steps
   - // TEST: Workflow execution order must be enforced
   - // TEST: State variables must persist between nodes

3. **Analysis Module**
   - Generate structured analysis of selected paper
   - Include main question, methodology, findings, and implications
   - // TEST: Analysis must be ≥100 words
   - // TEST: Must return error if no paper selected

4. **Blog Generation**
   - Create technical blog post from analysis
   - Follow specified structure (title, intro, methodology, findings, conclusion)
   - // TEST: Blog must be ≥500 words
   - // TEST: Must return error if no analysis provided

5. **CLI Interface**
   - Accept user input for research topic
   - Display generated blog content
   - Option to save output to file
   - // TEST: Must handle invalid user input
   - // TEST: File saving must work with valid filenames

## Edge Cases
1. **No Papers Found**
   - SELECT node must return error state
   - Workflow must terminate gracefully
   - // TEST: SELECT node returns error when papers=[]

2. **API Failures**
   - Handle connection errors/HTTP 5xx
   - // TEST: Simulated API failure triggers error handling

3. **Empty Analysis**
   - BLOG node must validate analysis content
   - // TEST: Empty analysis triggers error

4. **Invalid User Input**
   - CLI must handle empty/null topic input
   - // TEST: Empty topic input shows error message

## Constraints
- NO hardcoded API keys/secrets
- Use .env for environment variables
- Follow LangGraph state management patterns
- Maintain ≤300 lines/module
- Use pytest for unit tests
- CLI must have clear error messages

## Pseudocode Design

### Domain Model
```python
class WorkflowState:
    topic: str
    papers: List[PaperData]
    selected_paper: Optional[PaperData]
    analysis: str
    blog_post: str
    error: Optional[str]

PaperData = {
    id: str
    title: str
    authors: List[str]
    summary: str
    published: datetime
    url: str
}
```

### Core Nodes (graph/nodes.py)
```python
def search_node(state: WorkflowState) -> WorkflowState:
    """Search ArXiv for papers"""
    papers = arxiv_search(state.topic)
    state.papers = papers
    // TEST: Returns ≥1 paper for "machine learning"
    // TEST: Returns empty list for invalid topics
    return state

def select_node(state: WorkflowState) -> WorkflowState:
    """Select first valid paper"""
    if not state.papers:
        state.error = "NO_PAPERS_FOUND"
        return state
    state.selected_paper = state.papers[0]
    // TEST: Selects first paper in list
    // TEST: Sets error when papers empty
    return state

def analyze_node(state: WorkflowState) -> WorkflowState:
    """Generate paper analysis"""
    if not state.selected_paper:
        state.error = "NO_PAPER_SELECTED"
        return state
    analysis = llm_analyze(state.selected_paper)
    state.analysis = analysis
    // TEST: Analysis length ≥100 words
    // TEST: Returns error when no paper selected
    return state

def blog_node(state: WorkflowState) -> WorkflowState:
    """Generate blog post from analysis"""
    if not state.analysis:
        state.error = "NO_ANALYSIS_AVAILABLE"
        return state
    blog = llm_blog(state.selected_paper, state.analysis)
    state.blog_post = blog
    // TEST: Blog length ≥500 words
    // TEST: Returns error when no analysis
    return state
```

### Workflow Definition (graph/workflow.py)
```python
def create_workflow() -> LangGraphWorkflow:
    workflow = LangGraphWorkflow("Research Assistant")
    
    workflow.add_node("SEARCH", search_node)
    workflow.add_node("SELECT", select_node)
    workflow.add_node("ANALYZE", analyze_node)
    workflow.add_node("BLOG", blog_node)
    
    workflow.add_edge("SEARCH", "SELECT")
    workflow.add_edge("SELECT", "ANALYZE")
    workflow.add_edge("ANALYZE", "BLOG")
    
    // TEST: Workflow executes nodes in correct order
    // TEST: Handles errors at each node gracefully
    return workflow
```

### CLI Implementation (app.py)
```python
def main():
    load_dotenv()  # Load environment variables
    workflow = create_workflow()
    
    topic = input("Enter research topic: ")
    if not topic.strip():
        print("Error: Topic cannot be empty")
        return
    
    initial_state = WorkflowState(topic=topic)
    final_state = workflow.run(initial_state)
    
    if final_state.error:
        print(f"Error: {final_state.error}")
    else:
        print(final_state.blog_post)
        save = input("Save to file? [Y/n]: ").lower()
        if save != "n":
            save_to_file(final_state.blog_post)
    
    // TEST: CLI handles empty topic input
    // TEST: File saving functionality works
```

## Validation Checklist
1. All requirements have corresponding TDD anchors
2. No hardcoded secrets/environment variables
3. Clear error handling at each workflow stage
4. Modular code structure with <300 lines per file
5. Test coverage for happy paths and edge cases