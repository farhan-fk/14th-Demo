"""
Tests for CourseSearchTool execute method.
Validates search functionality, result formatting, and source tracking.
"""
import pytest
from search_tools import CourseSearchTool
from vector_store import SearchResults


class TestCourseSearchToolExecute:
    """Test suite for CourseSearchTool.execute() method"""
    
    def test_execute_basic_query_success(self, course_search_tool):
        """Test successful search with basic query"""
        result = course_search_tool.execute(query="machine learning")
        
        # Assertions
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Machine learning" in result
        assert "[Test Course: Introduction to AI - Lesson 1]" in result
        
        # Verify sources were tracked
        assert len(course_search_tool.last_sources) > 0
        assert course_search_tool.last_sources[0]["text"] == "Test Course: Introduction to AI"
        assert course_search_tool.last_sources[0]["lesson_number"] == 1
        assert course_search_tool.last_sources[0]["link"] == "https://example.com/lesson/1"
    
    def test_execute_with_course_filter(self, course_search_tool):
        """Test search with course name filter"""
        result = course_search_tool.execute(
            query="neural networks",
            course_name="Test Course"
        )
        
        assert "Neural networks" in result
        assert len(course_search_tool.last_sources) >= 1
    
    def test_execute_with_lesson_filter(self, course_search_tool):
        """Test search with lesson number filter"""
        result = course_search_tool.execute(
            query="neural networks",
            lesson_number=2
        )
        
        assert "neural" in result.lower()
        # Verify all sources are from lesson 2
        for source in course_search_tool.last_sources:
            assert source["lesson_number"] == 2
    
    def test_execute_no_results_found(self, course_search_tool, mock_vector_store):
        """Test behavior when search returns no results"""
        # Configure mock to return empty results
        mock_vector_store.search.return_value = SearchResults(
            documents=[], metadata=[], distances=[]
        )
        
        result = course_search_tool.execute(query="nonexistent topic")
        
        assert "No relevant content found" in result
        assert len(course_search_tool.last_sources) == 0
    
    def test_execute_course_not_found_error(self, course_search_tool, mock_vector_store):
        """Test error handling when course name doesn't match any course"""
        mock_vector_store.search.return_value = SearchResults.empty(
            "No course found matching 'Nonexistent Course'"
        )
        
        result = course_search_tool.execute(
            query="test",
            course_name="Nonexistent Course"
        )
        
        assert "No course found matching" in result
        assert "Nonexistent Course" in result


class TestCourseSearchToolDefinition:
    """Test suite for CourseSearchTool.get_tool_definition()"""
    
    def test_get_tool_definition_structure(self, course_search_tool):
        """Test that tool definition has correct structure for Anthropic"""
        definition = course_search_tool.get_tool_definition()
        
        assert isinstance(definition, dict)
        assert "name" in definition
        assert "description" in definition
        assert "input_schema" in definition
        
        assert definition["name"] == "search_course_content"
        assert isinstance(definition["description"], str)


class TestToolManager:
    """Test suite for ToolManager"""
    
    def test_register_tool(self, tool_manager, course_search_tool):
        """Test tool registration"""
        # Tool should already be registered from fixture
        assert "search_course_content" in tool_manager.tools
    
    def test_get_tool_definitions(self, tool_manager):
        """Test getting all tool definitions"""
        definitions = tool_manager.get_tool_definitions()
        
        assert isinstance(definitions, list)
        assert len(definitions) == 1
        assert definitions[0]["name"] == "search_course_content"
    
    def test_execute_tool_success(self, tool_manager):
        """Test executing a registered tool"""
        result = tool_manager.execute_tool(
            "search_course_content",
            query="machine learning"
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_get_last_sources(self, tool_manager):
        """Test retrieving sources from last search"""
        # Execute a search first
        tool_manager.execute_tool("search_course_content", query="machine learning")
        
        sources = tool_manager.get_last_sources()
        assert isinstance(sources, list)
        assert len(sources) > 0
    
    def test_reset_sources(self, tool_manager):
        """Test resetting sources"""
        # Execute a search
        tool_manager.execute_tool("search_course_content", query="machine learning")
        assert len(tool_manager.get_last_sources()) > 0
        
        # Reset
        tool_manager.reset_sources()
        assert len(tool_manager.get_last_sources()) == 0
