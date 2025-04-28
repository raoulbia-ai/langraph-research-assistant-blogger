import pytest
import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# Import only what we can test without OpenAI API key
from utils.arxiv_client import ArxivClient, search_recent_papers
from src.graph.core_nodes import Node, PaperNode
from src.graph.domain import Paper
from src.graph.graph_builder import GraphBuilder

def test_arxiv_client():
    """Test that ArxivClient returns results"""
    client = ArxivClient()
    papers = client.search_recent_papers("machine learning", max_results=2)
    
    # Check that we get some papers
    assert papers
    assert len(papers) > 0
    assert isinstance(papers, list)
    
    # Check paper structure
    paper = papers[0]
    assert "id" in paper
    assert "title" in paper
    assert "authors" in paper
    assert "summary" in paper
    assert "url" in paper

def test_legacy_search_function():
    """Test that legacy search function works"""
    papers = search_recent_papers("machine learning", max_results=2)
    assert papers
    assert len(papers) > 0

def test_node_classes():
    """Test the Node and PaperNode classes"""
    # Test basic Node
    node = Node("test", {"name": "Test Node"})
    assert node.id == "test"
    assert "name" in node.data
    
    # Test add_child method
    child_node = Node("child", {"name": "Child Node"})
    node.add_child(child_node)
    assert len(node.children) == 1
    assert node.children[0].id == "child"
    
    # Test to_dict method
    node_dict = node.to_dict()
    assert "id" in node_dict
    assert "data" in node_dict
    assert "children" in node_dict
    assert len(node_dict["children"]) == 1
    
    # Test PaperNode
    paper = Paper(
        id="test",
        title="Test Paper",
        authors=["Test Author"],
        abstract="Test abstract",
        published_date="2023-01-01",
        url="https://example.com"
    )
    paper_node = PaperNode(paper)
    assert paper_node.id == "test"
    assert paper_node.paper.title == "Test Paper"
    assert paper_node.data["title"] == "Test Paper"

def test_paper_from_dict():
    """Test Paper.from_dict method"""
    paper_data = {
        "id": "1234.5678",
        "title": "Test Paper Title",
        "authors": ["Author One", "Author Two"],
        "summary": "This is a test summary",
        "published": "2023-01-01",
        "url": "https://arxiv.org/abs/1234.5678"
    }
    
    paper = Paper.from_dict(paper_data)
    assert paper.id == "1234.5678"
    assert paper.title == "Test Paper Title"
    assert len(paper.authors) == 2
    assert paper.abstract == "This is a test summary"
    assert paper.published_date == "2023-01-01"
    assert paper.url == "https://arxiv.org/abs/1234.5678"
    
def test_graph_builder():
    """Test GraphBuilder functionality"""
    client = ArxivClient()
    builder = GraphBuilder(client)
    
    # Test graph building
    graph = builder.build_graph("machine learning")
    
    # Should have at least a root node
    assert len(graph) >= 1
    assert "root" in graph
    
    # Check that root node has children (papers)
    root = graph["root"]
    assert hasattr(root, "children")
    
    # If we found papers, check their structure
    if len(graph) > 1:
        # Get any node that's not the root
        paper_id = next(key for key in graph.keys() if key != "root")
        paper_node = graph[paper_id]
        
        # Check that it's a PaperNode
        assert isinstance(paper_node, PaperNode)
        assert hasattr(paper_node, "paper")
        assert paper_node.paper.id == paper_id