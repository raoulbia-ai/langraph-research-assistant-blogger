# Comprehensive Implementation Plan: Research Paper Assistant with LangGraph

This document outlines a complete implementation strategy for building a research paper discovery and blogging system using LangGraph, with clear Git versioning milestones.

## Development Tooling Overview

### LangGraph Ecosystem

1. **LangGraph Core Library**
   - Primary framework for building our agent workflow
   - Used to define state machines, nodes, and transitions
   - Installed via pip: `pip install langgraph`

2. **LangGraph Studio** (optional)
   - Visual workflow designer for LangGraph
   - Useful for visualizing complex workflows
   - Can be used later in development for debugging
   - Install: `pip install langgraph-studio`
   - Run: `langraph studio serve`

3. **LangGraph CLI**
   - Useful for managing deployments and project structure
   - Optional for MVP but helpful for later stages
   - Install: `pip install langgraph-cli`

4. **Development Environment**
   - Python 3.9+ required
   - Conda recommended for environment management
   - Virtual environment strongly advised

## Implementation Plan by Git Version

### v0.1.0: Core Functionality

#### Requirements Specification

- Create a basic paper discovery workflow with LangGraph
- Implement ArXiv API integration for paper search
- Develop simple analysis and blog generation using LLMs
- Build a basic CLI interface
- Follow LangGraph best practices for state management

#### Implementation Steps

1. **Project Setup**
   ```bash
   # Initialize project
   mkdir research-assistant
   cd research-assistant
   git init
   
   # Setup Conda environment
   conda create -n research-env python=3.9
   conda activate research-env
   
   # Initial dependencies
   pip install langgraph langchain langchain-openai arxiv python-dotenv
   pip freeze > requirements.txt
   
   # Create basic structure
   mkdir -p graph utils tests
   touch README.md .gitignore .env
   ```

2. **Environment Configuration**
   ```bash
   # .env file
   echo "OPENAI_API_KEY=your-key-here" > .env
   
   # .gitignore
   cat << EOF > .gitignore
   .env
   __pycache__/
   *.py[cod]
   *$py.class
   .pytest_cache/
   .coverage
   htmlcov/
   venv/
   *.db
   *.sqlite
   EOF
   ```

3. **ArXiv Integration**
   ```python
   # utils/arxiv_client.py
   import arxiv
   
   def search_recent_papers(topic, max_results=5):
       """Search for recent papers on ArXiv"""
       client = arxiv.Client()
       search = arxiv.Search(
           query=topic,
           max_results=max_results,
           sort_by=arxiv.SortCriterion.SubmittedDate
       )
       
       results = []
       for paper in client.results(search):
           results.append({
               "id": paper.entry_id,
               "title": paper.title,
               "summary": paper.summary,
               "authors": [author.name for author in paper.authors],
               "published": paper.published,
               "url": paper.pdf_url
           })
       
       return results
   ```

4. **Basic LangGraph Nodes**
   ```python
   # graph/nodes.py
   from utils.arxiv_client import search_recent_papers
   from langchain_openai import ChatOpenAI
   from langchain_core.prompts import ChatPromptTemplate
   
   # Initialize LLM
   llm = ChatOpenAI(model="gpt-3.5-turbo")
   
   def search_node(state):
       """Node to search for papers"""
       topic = state["topic"]
       papers = search_recent_papers(topic)
       return {"papers": papers}
       // TEST: Should return list of papers for valid topic
       // TEST: Should return empty list if no papers found
   
   def select_paper_node(state):
       """Node to select the first paper"""
       papers = state["papers"]
       if not papers:
           return {"selected_paper": None, "error": "No papers found"}
       return {"selected_paper": papers[0]}
       // TEST: Should select first paper in list
       // TEST: Should return error if papers list empty
   
   def analyze_paper_node(state):
       """Node to analyze the selected paper"""
       paper = state["selected_paper"]
       if not paper:
           return {"analysis": "", "error": "No paper selected"}
       
       prompt = ChatPromptTemplate.from_template("""
       Analyze the following research paper:
       
       Title: {title}
       Authors: {authors}
       Summary: {summary}
       
       Provide a concise analysis covering:
       1. Main research question
       2. Key methodology
       3. Primary findings
       4. Implications for the field
       
       Analysis:
       """)
       
       chain = prompt | llm
       
       analysis = chain.invoke({
           "title": paper["title"],
           "authors": ", ".join(paper["authors"]),
           "summary": paper["summary"]
       })
       
       return {"analysis": analysis.content}
       // TEST: Should generate analysis for valid paper
       // TEST: Should return error if no paper provided
   
   def generate_blog_node(state):
       """Node to generate a blog post"""
       paper = state["selected_paper"]
       analysis = state["analysis"]
       
       if not analysis:
           return {"blog_post": "", "error": "No analysis available"}
       
       prompt = ChatPromptTemplate.from_template("""
       Write a technical blog post based on this paper analysis:
       
       Paper: {title}
       Authors: {authors}
       Analysis: {analysis}
       
       Create a 500-word technical blog post with:
       1. A catchy title
       2. Brief introduction to the problem
       3. Summary of the approach
       4. Key findings and their significance
       5. Conclusion with future implications
       
       Blog Post:
       """)
       
       chain = prompt | llm
       
       blog = chain.invoke({
           "title": paper["title"],
           "authors": ", ".join(paper["authors"]),
           "analysis": analysis
       })
       
       return {"blog_post": blog.content}
       // TEST: Should generate blog post from valid analysis
       // TEST: Should return error if no analysis provided
   ```

5. **Basic Workflow Definition**
   ```python
   # graph/workflow.py
   from langgraph.graph import StateGraph, END
   from graph.nodes import (
       search_node, 
       select_paper_node, 
       analyze_paper_node, 
       generate_blog_node
   )
   
   def create_workflow():
       """Create basic linear workflow"""
       # Define our state
       workflow = StateGraph(name="research-assistant")
       
       # Add all nodes
       workflow.add_node("search", search_node)
       workflow.add_node("select", select_paper_node)
       workflow.add_node("analyze", analyze_paper_node)
       workflow.add_node("blog", generate_blog_node)
       
       # Add linear edges
       workflow.add_edge("search", "select")
       workflow.add_edge("select", "analyze")
       workflow.add_edge("analyze", "blog")
       workflow.add_edge("blog", END)
       // TEST: Workflow should execute nodes in correct order
       // TEST: Should handle edge cases like no papers found
       
       # Compile the graph
       return workflow.compile()
   ```

6. **CLI Application**
   ```python
   # app.py
   import os
   import json
   from dotenv import load_dotenv
   from graph.workflow import create_workflow
   
   # Load environment variables
   load_dotenv()
   
   def main():
       # Create the workflow
       workflow = create_workflow()
       
       # Get user input
       topic = input("Enter research topic: ")
       
       # Initial state
       initial_state = {
           "topic": topic,
           "papers": [],
           "selected_paper": None,
           "analysis": "",
           "blog_post": "",
           "error": None
       }
       
       # Run the workflow
       try:
           result = workflow.invoke(initial_state)
           
           # Display results
           if result.get("error"):
               print(f"Error: {result['error']}")
           else:
               print("\n=== Generated Blog Post ===\n")
               print(result["blog_post"])
               
               # Optionally save result
               save = input("\nSave blog post to file? (y/n): ")
               if save.lower() == "y":
                   filename = f"blog_{topic.replace(' ', '_')}.md"
                   with open(filename, "w") as f:
                       f.write(result["blog_post"])
                   print(f"Blog saved to {filename}")
       
       except Exception as e:
           print(f"Workflow error: {str(e)}")
   
   if __name__ == "__main__":
       main()
   ```

7. **Basic Testing**
   ```python
   # tests/test_basic.py
   import pytest
   from graph.workflow import create_workflow
   
   def test_workflow_creation():
       """Test that workflow can be created"""
       workflow = create_workflow()
       assert workflow is not None
   
   def test_basic_execution():
       """Test basic workflow execution with mocked inputs"""
       workflow = create_workflow()
       
       # Create test state with pre-populated values
       test_state = {
           "topic": "test topic",
           "papers": [{
               "id": "test",
               "title": "Test Paper",
               "summary": "This is a test summary.",
               "authors": ["Test Author"],
               "published": "2023-01-01",
               "url": "https://example.com"
           }],
           "selected_paper": None,
           "analysis": "",
           "blog_post": "",
           "error": None
       }
       
       # Run workflow starting from select node
       result = workflow.invoke(test_state, {"configurable": {"start_from": "select"}})
       
       # Check results
       assert "blog_post" in result
       assert len(result["blog_post"]) > 0
   ```

8. **README Documentation**
   ```markdown
   # Research Assistant

   A LangGraph-powered tool that discovers research papers and generates blog posts.

   ## Features

   - Search for recent papers on ArXiv
   - Analyze paper content
   - Generate technical blog posts

   ## Setup

   1. Clone this repository
   2. Create a conda environment: `conda create -n research-env python=3.9`
   3. Activate it: `conda activate research-env`
   4. Install dependencies: `pip install -r requirements.txt`
   5. Create a `.env` file with your OpenAI API key: `OPENAI_API_KEY=your-key-here`

   ## Usage

   Run: `python app.py`

   Follow the prompts to enter a research topic and generate a blog post.
   ```

#### Git Commands

```bash
# Initial commit with project structure
git add .
git commit -m "chore: Initial project setup"

# Add ArXiv integration
git add utils/arxiv_client.py
git commit -m "feat: Add ArXiv API integration"

# Add core LangGraph nodes
git add graph/nodes.py
git commit -m "feat: Implement basic workflow nodes"

# Add workflow definition
git add graph/workflow.py
git commit -m "feat: Create linear workflow graph"

# Add CLI application
git add app.py
git commit -m "feat: Add CLI interface"

# Add tests
git add tests
git commit -m "test: Add basic tests"

# Add documentation
git add README.md
git commit -m "docs: Add initial documentation"

# Tag the v0.1.0 release
git tag -a v0.1.0 -m "Basic LangGraph implementation with linear workflow"