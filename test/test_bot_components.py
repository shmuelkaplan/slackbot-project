import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from bedrock_handler import query_claude
from bedrock_kb_handler import query_bedrock_kb
from bot_handler import handle_message

class TestBedrockHandler(unittest.TestCase):

    @patch('bedrock_handler.bedrock')
    def test_query_claude_success(self, mock_bedrock):
        mock_response = MagicMock()
        mock_response.get.return_value.read.return_value = json.dumps({
            "content": [{"text": "This is a test response from Claude."}]
        })
        mock_bedrock.invoke_model.return_value = mock_response

        messages = json.dumps([
            {"role": "user", "content": "Hello, Claude!"}
        ])

        result = query_claude(messages)
        self.assertEqual(result, "This is a test response from Claude.")
        mock_bedrock.invoke_model.assert_called_once()

    @patch('bedrock_handler.bedrock')
    def test_query_claude_error(self, mock_bedrock):
        mock_bedrock.invoke_model.side_effect = Exception("Test error")

        messages = json.dumps([
            {"role": "user", "content": "Hello, Claude!"}
        ])

        result = query_claude(messages)
        self.assertTrue(result.startswith("I'm sorry, I encountered an error"))

class TestBedrockKBHandler(unittest.TestCase):

    @patch('bedrock_kb_handler.bedrock_agent_runtime')
    def test_query_bedrock_kb_success(self, mock_agent_runtime):
        mock_agent_runtime.retrieve_and_generate.return_value = {
            "output": {"text": "This is a test response from the knowledge base."}
        }

        result, valid = query_bedrock_kb("Test query")
        self.assertEqual(result, "This is a test response from the knowledge base.")
        self.assertTrue(valid)
        mock_agent_runtime.retrieve_and_generate.assert_called_once()

    @patch('bedrock_kb_handler.bedrock_agent_runtime')
    def test_query_bedrock_kb_error(self, mock_agent_runtime):
        mock_agent_runtime.retrieve_and_generate.side_effect = Exception("Test error")

        result, valid = query_bedrock_kb("Test query")
        self.assertEqual(result, "")
        self.assertFalse(valid)

class TestBotHandler(unittest.TestCase):

    @patch('bot_handler.query_bedrock_kb')
    @patch('bot_handler.query_claude')
    def test_handle_message_kb_success(self, mock_query_claude, mock_query_bedrock_kb):
        mock_query_bedrock_kb.return_value = ("KB response", True)
        mock_say = MagicMock()

        handle_message({"text": "Test query"}, mock_say)

        mock_say.assert_called_once_with("KB response")
        mock_query_claude.assert_not_called()

    @patch('bot_handler.query_bedrock_kb')
    @patch('bot_handler.query_claude')
    def test_handle_message_claude_fallback(self, mock_query_claude, mock_query_bedrock_kb):
        mock_query_bedrock_kb.return_value = ("", False)
        mock_query_claude.return_value = "Claude response"
        mock_say = MagicMock()

        handle_message({"text": "Test query"}, mock_say)

        mock_say.assert_called_once_with("Claude response")
        mock_query_claude.assert_called_once()

    @patch('bot_handler.query_bedrock_kb')
    @patch('bot_handler.query_claude')
    def test_handle_message_error(self, mock_query_claude, mock_query_bedrock_kb):
        mock_query_bedrock_kb.side_effect = Exception("Test error")
        mock_say = MagicMock()

        handle_message({"text": "Test query"}, mock_say)

        mock_say.assert_called_once_with("I'm sorry, I encountered an error while processing your message.")

if __name__ == '__main__':
    unittest.main()