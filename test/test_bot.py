# test_bot.py

import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.bot_handler import app, handle_message
from src.bedrock_handler import query_claude

class TestSlackBot(unittest.TestCase):

    @patch('src.bot_handler.query_claude')
    def test_handle_message_text_only(self, mock_query_claude):
        # Arrange
        mock_query_claude.return_value = "This is a response from Claude."
        message = {'text': 'Hello, bot!', 'user': 'U123ABC'}
        mock_say = MagicMock()
        mock_client = MagicMock()

        # Act
        handle_message(message, mock_say, mock_client)

        # Assert
        mock_query_claude.assert_called_once()
        mock_say.assert_called_once_with("This is a response from Claude.")

    @patch('src.bot_handler.query_claude')
    @patch('src.bot_handler.download_image')
    def test_handle_message_with_image(self, mock_download_image, mock_query_claude):
        # Arrange
        mock_query_claude.return_value = "This is a response about the image."
        mock_download_image.return_value = "path/to/temp/image.jpg"
        message = {
            'text': 'What\'s in this image?',
            'user': 'U123ABC',
            'files': [{'mimetype': 'image/jpeg', 'id': 'F123XYZ'}]
        }
        mock_say = MagicMock()
        mock_client = MagicMock()

        # Act
        handle_message(message, mock_say, mock_client)

        # Assert
        mock_download_image.assert_called_once()
        mock_query_claude.assert_called_once()
        mock_say.assert_called_once_with("This is a response about the image.")

    @patch('src.bedrock_handler.bedrock')
    def test_query_claude(self, mock_bedrock):
        # Arrange
        mock_response = MagicMock()
        mock_response.get.return_value.read.return_value = json.dumps({
            'content': [{'text': 'This is Claude\'s response.'}]
        })
        mock_bedrock.invoke_model.return_value = mock_response

        messages = json.dumps([{"role": "user", "content": "Hello, Claude!"}])

        # Act
        response = query_claude(messages)

        # Assert
        self.assertEqual(response, "This is Claude's response.")
        mock_bedrock.invoke_model.assert_called_once()

    def test_hello_command(self):
        # Arrange
        client = app.client
        message = {'user': 'U123ABC'}

        # Act
        result = app.get_listener('message', 'hello')(message, client)

        # Assert
        self.assertIn(f"Hey there <@U123ABC>!", result)

    def test_help_command(self):
        # Arrange
        client = app.client
        message = {}

        # Act
        result = app.get_listener('message', 'help')(message, client)

        # Assert
        self.assertIn("Here are the commands I understand:", result)
        self.assertIn("`hello`", result)
        self.assertIn("`help`", result)
        self.assertIn("`echo [message]`", result)

    def test_echo_command(self):
        # Arrange
        client = app.client
        message = {'text': 'echo Hello, World!'}

        # Act
        result = app.get_listener('message', 'echo')(message, client)

        # Assert
        self.assertEqual("You said: Hello, World!", result)

if __name__ == '__main__':
    unittest.main()