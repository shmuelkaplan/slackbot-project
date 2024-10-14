# slack_handler.py
import os
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from bedrock_kb_handler import query_bedrock_kb
from bedrock_handler import query_claude
import json

logger = logging.getLogger(__name__)

class SlackHandler:
    def __init__(self, slack_bot_token, slack_app_token):
        self.app = App(token=slack_bot_token)
        self.socket_mode_handler = SocketModeHandler(self.app, slack_app_token)
        self.aws_session = None
        self.setup_listeners()

    def set_aws_session(self, session):
        self.aws_session = session

    def setup_listeners(self):
        @self.app.event("app_mention")
        def handle_app_mention(event, say):
            self.handle_message(event, say)

        @self.app.event("message")
        def handle_message_event(event, say):
            self.handle_message(event, say)

    def handle_message(self, event, say):
        try:
            text = event['text']
            logger.info(f"Received message: {text}")

            if not self.aws_session:
                logger.error("AWS session not set")
                say("I'm sorry, I'm not properly configured to answer questions at the moment.")
                return

            kb_response, valid = query_bedrock_kb(self.aws_session, text)
            
            if not valid or not kb_response.strip() or kb_response == "Sorry, I am unable to assist you with this request.":
                logger.info("No valid response from knowledge base, falling back to Claude")
                system_message = "You are a helpful AI assistant integrated into a Slack bot. Respond concisely and professionally."
                user_message = f"User message: {text}"
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ]
                response = query_claude(self.aws_session, json.dumps(messages))
                logger.info(f"Claude response: {response}")
                say(response)
            else:
                logger.info(f"Responding with knowledge base answer: {kb_response}")
                say(kb_response)

        except Exception as e:
            logger.error(f"Error in handle_message: {str(e)}", exc_info=True)
            say("I'm sorry, I encountered an error while processing your message.")

    def start(self):
        try:
            logger.info("Starting Socket Mode handler")
            self.socket_mode_handler.start()
        except Exception as e:
            logger.error(f"Failed to start Socket Mode handler: {str(e)}", exc_info=True)
        raise
    def test_bedrock_access(self):
        if not self.aws_session:
            logger.error("AWS session not set")
            return False
        try:
            client = self.aws_session.client('bedrock-agent-runtime')
            knowledge_base_id = os.environ.get('BEDROCK_KB_ID')
            model_arn = os.environ.get('BEDROCK_MODEL_ARN')
            
            response = client.retrieve_and_generate(
                input={
                    'text': 'Test query'
                },
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': knowledge_base_id,
                        'modelArn': model_arn
                    }
                }
            )
            logger.info(f"Successfully accessed Bedrock knowledge base: {response}")
            return True
        except Exception as e:
            logger.error(f"Failed to access Bedrock knowledge base: {str(e)}")
            return False