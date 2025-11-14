"""
Tests for AIGenerator and its integration with CourseSearchTool.
Validates tool calling, response generation, and error handling.
"""
import pytest
from unittest.mock import Mock, patch
from ai_generator import AIGenerator


class TestAIGeneratorBasic:
    """Basic AIGenerator tests without tool usage"""
    
    @patch('ai_generator.anthropic.Anthropic')
    def test_initialization(self, mock_anthropic_class):
        """Test AIGenerator initialization"""
        generator = AIGenerator(api_key="test-key", model="claude-3-sonnet")
        
        assert generator.model == "claude-3-sonnet"
        assert generator.base_params["model"] == "claude-3-sonnet"
        assert generator.base_params["temperature"] == 0
        assert generator.base_params["max_tokens"] == 800
    
    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_without_tools(self, mock_anthropic_class, mock_anthropic_client):
        """Test generating response without tools"""
        mock_anthropic_class.return_value = mock_anthropic_client
        
        generator = AIGenerator(api_key="test-key", model="claude-3-sonnet")
        response = generator.generate_response(query="What is AI?")
        
        assert isinstance(response, str)
        assert len(response) > 0
        mock_anthropic_client.messages.create.assert_called_once()


class TestAIGeneratorWithToolCalling:
    """Tests for AIGenerator's tool calling capabilities"""
    
    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_triggers_tool_use(
        self, 
        mock_anthropic_class, 
        mock_anthropic_client_with_tool_use,
        tool_manager
    ):
        """Test that AIGenerator correctly triggers tool use"""
        mock_anthropic_class.return_value = mock_anthropic_client_with_tool_use
        
        generator = AIGenerator(api_key="test-key", model="claude-3-sonnet")
        response = generator.generate_response(
            query="What is machine learning?",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        
        # Verify Claude was called twice (initial + after tool use)
        assert mock_anthropic_client_with_tool_use.messages.create.call_count == 2
    
    @patch('ai_generator.anthropic.Anthropic')
    def test_tool_execution_called_correctly(
        self,
        mock_anthropic_class,
        mock_anthropic_client_with_tool_use,
        tool_manager
    ):
        """Test that tools are executed with correct parameters"""
        mock_anthropic_class.return_value = mock_anthropic_client_with_tool_use
        
        # Spy on tool execution
        original_execute = tool_manager.execute_tool
        tool_manager.execute_tool = Mock(side_effect=original_execute)
        
        generator = AIGenerator(api_key="test-key", model="claude-3-sonnet")
        generator.generate_response(
            query="What is machine learning?",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager
        )
        
        # Verify tool was called
        tool_manager.execute_tool.assert_called_once()
        call_args = tool_manager.execute_tool.call_args
        assert call_args.args[0] == "search_course_content"
        assert "query" in call_args.kwargs
