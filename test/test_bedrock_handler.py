import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os
from botocore.exceptions import ClientError

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from bedrock_handler import query_claude

class TestBedrockHandler(unittest.TestCase):

    @patch('bedrock_handler.bedrock')
    def test_query_claude_success(self, mock_bedrock):
        # Arrange
        mock_response = MagicMock()
        mock_response.get.return_value.read.return_value = json.dumps({
            "content": [{"text": "This is a test response from Claude."}]
        })
        mock_bedrock.invoke_model.return_value = mock_response

        messages = json.dumps([
            {"role": "user", "content": "Hello, Claude!"}
        ])

        # Act
        result = query_claude(messages)

        # Assert
        self.assertEqual(result, "This is a test response from Claude.")
        mock_bedrock.invoke_model.assert_called_once()

    @patch('bedrock_handler.bedrock')
    def test_query_claude_with_system_message(self, mock_bedrock):
        # Arrange
        mock_response = MagicMock()
        mock_response.get.return_value.read.return_value = json.dumps({
            "content": [{"text": "This is a test response from Claude with system message."}]
        })
        mock_bedrock.invoke_model.return_value = mock_response

        messages = json.dumps([
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, Claude!"}
        ])

        # Act
        result = query_claude(messages)

        # Assert
        self.assertEqual(result, "This is a test response from Claude with system message.")
        mock_bedrock.invoke_model.assert_called_once()

    @patch('bedrock_handler.bedrock')
    def test_query_claude_unexpected_response(self, mock_bedrock):
        # Arrange
        mock_response = MagicMock()
        mock_response.get.return_value.read.return_value = json.dumps({
            "unexpected_key": "unexpected_value"
        })
        mock_bedrock.invoke_model.return_value = mock_response

        messages = json.dumps([
            {"role": "user", "content": "Hello, Claude!"}
        ])

        # Act
        result = query_claude(messages)

        # Assert
        self.assertEqual(result, "I'm sorry, I received an unexpected response format.")
        mock_bedrock.invoke_model.assert_called_once()

    @patch('bedrock_handler.bedrock')
    def test_query_claude_client_error(self, mock_bedrock):
        # Arrange
        mock_bedrock.invoke_model.side_effect = ClientError(
            error_response={'Error': {'Code': 'TestErrorCode', 'Message': 'Test error message'}},
            operation_name='InvokeModel'
        )

        messages = json.dumps([
            {"role": "user", "content": "Hello, Claude!"}
        ])

        # Act
        result = query_claude(messages)

        # Assert
        self.assertEqual(result, "AWS Bedrock Error: TestErrorCode - Test error message")
        mock_bedrock.invoke_model.assert_called_once()

    @patch('bedrock_handler.bedrock', None)
    def test_query_claude_client_not_initialized(self):
        # Arrange
        messages = json.dumps([
            {"role": "user", "content": "Hello, Claude!"}
        ])

        # Act
        result = query_claude(messages)

        # Assert
        self.assertEqual(result, "Error: Unable to connect to AWS Bedrock. Please check your credentials and try again.")

if __name__ == '__main__':
    unittest.main()