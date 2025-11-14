"""
Pytest configuration and shared fixtures for RAG system tests.
"""
import pytest
import os
import sys
import tempfile
import shutil
from typing import Generator
from unittest.mock import Mock, MagicMock

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Course, Lesson, CourseChunk
from vector_store import VectorStore, SearchResults
from search_tools import CourseSearchTool, ToolManager
from config import Config


@pytest.fixture
def temp_chroma_dir() -> Generator[str, None, None]:
    """Create a temporary directory for ChromaDB testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_config(temp_chroma_dir: str) -> Config:
    """Create a test configuration with temporary paths."""
    config = Config()
    config.CHROMA_PATH = temp_chroma_dir
    config.MAX_RESULTS = 3
    config.ANTHROPIC_API_KEY = "test-key-123"
    return config


@pytest.fixture
def sample_course() -> Course:
    """Create a sample course for testing."""
    return Course(
        title="Test Course: Introduction to AI",
        course_link="https://example.com/course/ai-intro",
        instructor="Dr. Test Instructor",
        lessons=[
            Lesson(
                lesson_number=0,
                title="Introduction",
                lesson_link="https://example.com/lesson/0"
            ),
            Lesson(
                lesson_number=1,
                title="Machine Learning Basics",
                lesson_link="https://example.com/lesson/1"
            ),
            Lesson(
                lesson_number=2,
                title="Neural Networks",
                lesson_link="https://example.com/lesson/2"
            )
        ]
    )


@pytest.fixture
def sample_course_chunks(sample_course: Course) -> list[CourseChunk]:
    """Create sample course chunks for testing."""
    return [
        CourseChunk(
            content="Course Test Course: Introduction to AI Lesson 0 content: This course covers the fundamentals of artificial intelligence and machine learning.",
            course_title=sample_course.title,
            lesson_number=0,
            lesson_link="https://example.com/lesson/0",
            chunk_index=0
        ),
        CourseChunk(
            content="Machine learning is a subset of AI that focuses on algorithms that can learn from data.",
            course_title=sample_course.title,
            lesson_number=1,
            lesson_link="https://example.com/lesson/1",
            chunk_index=1
        ),
        CourseChunk(
            content="Neural networks are computing systems inspired by biological neural networks. They consist of layers of interconnected nodes.",
            course_title=sample_course.title,
            lesson_number=2,
            lesson_link="https://example.com/lesson/2",
            chunk_index=2
        ),
        CourseChunk(
            content="Deep learning uses multiple layers of neural networks to extract higher-level features from raw input.",
            course_title=sample_course.title,
            lesson_number=2,
            lesson_link="https://example.com/lesson/2",
            chunk_index=3
        )
    ]


@pytest.fixture
def mock_vector_store() -> Mock:
    """Create a mock vector store for testing without ChromaDB."""
    mock_store = Mock(spec=VectorStore)
    
    # Configure default search behavior
    def mock_search(query: str, course_name=None, lesson_number=None, limit=None):
        # Simulate different responses based on query
        if "machine learning" in query.lower():
            return SearchResults(
                documents=[
                    "Machine learning is a subset of AI that focuses on algorithms that can learn from data."
                ],
                metadata=[
                    {
                        "course_title": "Test Course: Introduction to AI",
                        "lesson_number": 1,
                        "lesson_link": "https://example.com/lesson/1"
                    }
                ],
                distances=[0.2]
            )
        elif "neural" in query.lower():
            return SearchResults(
                documents=[
                    "Neural networks are computing systems inspired by biological neural networks.",
                    "Deep learning uses multiple layers of neural networks."
                ],
                metadata=[
                    {
                        "course_title": "Test Course: Introduction to AI",
                        "lesson_number": 2,
                        "lesson_link": "https://example.com/lesson/2"
                    },
                    {
                        "course_title": "Test Course: Introduction to AI",
                        "lesson_number": 2,
                        "lesson_link": "https://example.com/lesson/2"
                    }
                ],
                distances=[0.1, 0.15]
            )
        elif course_name and "nonexistent" in course_name.lower():
            return SearchResults.empty(f"No course found matching '{course_name}'")
        else:
            # Empty result
            return SearchResults(documents=[], metadata=[], distances=[])
    
    mock_store.search.side_effect = mock_search
    return mock_store


@pytest.fixture
def course_search_tool(mock_vector_store: Mock) -> CourseSearchTool:
    """Create a CourseSearchTool with mocked vector store."""
    return CourseSearchTool(mock_vector_store)


@pytest.fixture
def tool_manager(course_search_tool: CourseSearchTool) -> ToolManager:
    """Create a ToolManager with registered CourseSearchTool."""
    manager = ToolManager()
    manager.register_tool(course_search_tool)
    return manager


@pytest.fixture
def mock_anthropic_client() -> Mock:
    """Create a mock Anthropic client for testing AI generator."""
    mock_client = Mock()
    
    # Create a mock message response
    mock_response = Mock()
    mock_response.content = [Mock(text="This is a test response about AI.")]
    mock_response.stop_reason = "end_turn"
    
    mock_client.messages.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_anthropic_client_with_tool_use() -> Mock:
    """Create a mock Anthropic client that simulates tool usage."""
    mock_client = Mock()
    
    # First response: Claude decides to use the search tool
    mock_tool_use = Mock()
    mock_tool_use.type = "tool_use"
    mock_tool_use.id = "tool_use_123"
    mock_tool_use.name = "search_course_content"
    mock_tool_use.input = {"query": "machine learning basics"}
    
    initial_response = Mock()
    initial_response.content = [mock_tool_use]
    initial_response.stop_reason = "tool_use"
    
    # Second response: Claude's final answer after tool use
    final_response = Mock()
    final_response.content = [Mock(text="Machine learning is a subset of AI that enables computers to learn from data.")]
    final_response.stop_reason = "end_turn"
    
    # Configure the mock to return different responses on subsequent calls
    mock_client.messages.create.side_effect = [initial_response, final_response]
    
    return mock_client
