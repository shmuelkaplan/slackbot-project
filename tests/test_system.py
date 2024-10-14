import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import json
from unittest.mock import patch, MagicMock
import signal
from src.server import flask_app, main
from src.assume_role import get_session, assume_role, check_assumed_role
from src.bedrock_kb_handler import get_bedrock_agent_runtime_client, query_bedrock_kb, get_kb_info
from src.bedrock_handler import get_bedrock_client, query_claude
from src.bot_handler import BotHandler
import logging 
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAssumeRole(unittest.TestCase):
    @patch('boto3.Session')
    def test_get_session(self, mock_session):
        mock_session.return_value.client.return_value.get_caller_identity.return_value = {}
        session = get_session()
        self.assertIsNotNone(session)

    @patch('assume_role.get_session')
    @patch('boto3.Session')
    def test_assume_role(self, mock_boto_session, mock_get_session):
        mock_get_session.return_value.client.return_value.get_caller_identity.return_value = {"Account": "123456789012"}
        mock_get_session.return_value.client.return_value.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "test_key",
                "SecretAccessKey": "test_secret",
                "SessionToken": "test_token"
            }
        }
        assumed_session = assume_role()
        self.assertIsNotNone(assumed_session)

    def test_check_assumed_role(self):
        mock_session = MagicMock()
        mock_session.client.return_value.get_caller_identity.return_value = {"Arn": "test_arn"}
        self.assertTrue(check_assumed_role(mock_session))

class TestBedrockKBHandler(unittest.TestCase):
    def test_get_bedrock_agent_runtime_client(self):
        mock_session = MagicMock()
        client = get_bedrock_agent_runtime_client(mock_session)
        self.assertIsNotNone(client)

    def test_query_bedrock_kb(self):
        mock_session = MagicMock()
        mock_session.client().retrieve_and_generate.return_value = {
        "output": {"text": "Test response"}
        }
        response, valid = query_bedrock_kb(mock_session, "test query")
        self.assertEqual(response, "Test response")
        self.assertTrue(valid)

    def test_get_kb_info(self):
       mock_session = MagicMock()
       mock_session.client().get_knowledge_base.return_value = {"test": "data"}
       info = get_kb_info(mock_session)
       self.assertIsInstance(info, str)
       self.assertIn("test", info)
     
class TestBedrockHandler(unittest.TestCase):
    def test_get_bedrock_client(self):
        mock_session = MagicMock()
        client = get_bedrock_client(mock_session)
        self.assertIsNotNone(client)

    @patch('bedrock_handler.get_bedrock_client')
    def test_query_claude(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.invoke_model.return_value = {
            'body': MagicMock(read=lambda: json.dumps({
                'content': [{'text': 'Test response'}]
            }))
        }
        mock_session = MagicMock()
        response = query_claude(mock_session, json.dumps([{"role": "user", "content": "Test message"}]))
        self.assertEqual(response, 'Test response')

class TestBotHandler(unittest.TestCase):
    @patch('bot_handler.App')
    def test_bot_handler_initialization(self, mock_app):
        handler = BotHandler("test_token", "test_secret")
        self.assertIsNotNone(handler)
        self.assertIsNotNone(handler.get_handler())

    @patch('bot_handler.App')
    def test_set_aws_session(self, mock_app):
        handler = BotHandler("test_token", "test_secret")
        mock_session = MagicMock()
        handler.set_aws_session(mock_session)
        self.assertEqual(handler.aws_session, mock_session)



class TestServer(unittest.TestCase):
    def setUp(self):
        self.app = flask_app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_health_check(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "healthy"})

    @patch('server.assume_role')
    @patch('server.check_assumed_role')
    @patch('server.BotHandler')
    @patch('server.flask_app.run')
    def test_main_success(self, mock_run, mock_bot_handler_class, mock_check_assumed_role, mock_assume_role):
        mock_assume_role.return_value = MagicMock()
        mock_check_assumed_role.return_value = True

        mock_handler = MagicMock()
        mock_handler.handle = lambda: None
        mock_handler.handle.__name__ = 'handle'

        mock_bot_handler = MagicMock()
        mock_bot_handler.get_handler.return_value = mock_handler
        mock_bot_handler_class.return_value = mock_bot_handler

        main()

        mock_run.assert_called_once()
        flask_app.add_url_rule.assert_called_once_with(
            '/slack/events', 
            view_func=mock_handler.handle, 
            methods=['POST']
        )

    @patch('server.assume_role', return_value=None)
    @patch('server.check_assumed_role', return_value=False)
    @patch('server.BotHandler')
    @patch('server.flask_app.run')
    def test_main_role_assumption_failure(self, mock_run, mock_bot_handler_class, mock_check_assumed_role, mock_assume_role):
        with patch('sys.exit') as mock_exit:
            main()
            mock_exit.assert_called_once_with(1)
            mock_run.assert_not_called()

    @patch('server.assume_role')
    @patch('server.check_assumed_role')
    @patch('server.BotHandler')
    @patch('server.flask_app.run')
    def test_main_exception_handling(self, mock_run, mock_bot_handler_class, mock_check_assumed_role, mock_assume_role):
        mock_assume_role.side_effect = Exception("Test exception")

        with patch('sys.exit') as mock_exit:
            main()
            mock_exit.assert_called_once_with(1)
            mock_run.assert_not_called()

    def test_signal_handling(self):
        with patch('server.signal.signal') as mock_signal:
            import server  # This will trigger the signal handlers to be set up
            mock_signal.assert_any_call(signal.SIGINT, server.signal_handler)
            mock_signal.assert_any_call(signal.SIGTERM, server.signal_handler)

    def test_aws_connection(self):
        try:
            assumed_session = assume_role()
            self.assertIsNotNone(assumed_session, "Failed to assume role")

            # Try to use the assumed role to list S3 buckets
            s3_client = assumed_session.client('s3')
            response = s3_client.list_buckets()
            
            # Check if we can access the 'Buckets' key in the response
            self.assertIn('Buckets', response, "Unable to list S3 buckets")
            
            logger.info(f"Successfully listed {len(response['Buckets'])} S3 buckets")

        except ClientError as e:
            self.fail(f"AWS API call failed: {str(e)}")
        except Exception as e:
            self.fail(f"Unexpected error occurred: {str(e)}")

if __name__ == '__main__':
    unittest.main()