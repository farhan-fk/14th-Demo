"""
End-to-end integration tests for the RAG system.
Tests the complete flow from query to response.
"""
import pytest
from unittest.mock import patch, Mock
from rag_system import RAGSystem


class TestRAGSystemInitialization:
    """Tests for RAG system initialization"""
    
    @patch('rag_system.AIGenerator')
    @patch('rag_system.VectorStore')
    def test_rag_system_initializes_all_components(
        self,
        mock_vector_store_class,
        mock_ai_generator_class,
        test_config
    ):
        """Test that RAG system initializes all required components"""
        rag = RAGSystem(test_config)
        
        assert rag.document_processor is not None
        assert rag.vector_store is not None
        assert rag.ai_generator is not None
        assert rag.session_manager is not None
        assert rag.tool_manager is not None
        assert rag.search_tool is not None


class TestRAGSystemQuery:
    """Tests for RAG system query processing"""
    
    @patch('rag_system.AIGenerator')
    @patch('rag_system.VectorStore')
    def test_query_without_session(
        self,
        mock_vector_store_class,
        mock_ai_generator_class,
        test_config
    ):
        """Test querying without a session ID"""
        # Setup mocks
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store
        
        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "Machine learning is a branch of AI."
        mock_ai_generator_class.return_value = mock_ai_gen
        
        rag = RAGSystem(test_config)
        rag.search_tool.last_sources = [{"text": "Test Course", "lesson_number": 1, "link": "http://test.com"}]
        
        response, sources = rag.query("What is machine learning?")
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert isinstance(sources, list)
    
    @patch('rag_system.AIGenerator')
    @patch('rag_system.VectorStore')
    def test_query_with_session(
        self,
        mock_vector_store_class,
        mock_ai_generator_class,
        test_config
    ):
        """Test querying with a session ID for conversation context"""
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store
        
        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "That's an interesting question."
        mock_ai_generator_class.return_value = mock_ai_gen
        
        rag = RAGSystem(test_config)
        session_id = rag.session_manager.create_session()
        
        # First query
        response1, sources1 = rag.query("What is machine learning?", session_id)
        
        # Second query in same session
        response2, sources2 = rag.query("Tell me more", session_id)
        
        # Verify conversation history was used
        assert mock_ai_gen.generate_response.call_count == 2
        second_call_args = mock_ai_gen.generate_response.call_args_list[1]
        assert second_call_args.kwargs["conversation_history"] is not None
