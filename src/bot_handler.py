#bot_handler.py
import json
import logging
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from bedrock_handler import query_claude
from bedrock_kb_handler import query_bedrock_kb
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BotHandler:
    def __init__(self, slack_bot_token, slack_signing_secret):
        logger.info("Initializing BotHandler")
        self.app = App(token=slack_bot_token, signing_secret=slack_signing_secret)
        self.handler = SlackRequestHandler(self.app)
        self.aws_session = None
        self.setup_listeners()
        logger.info("BotHandler initialized successfully")

    def set_aws_session(self, session):
        logger.info("Setting AWS session")
        self.aws_session = session

    def setup_listeners(self):
        logger.info("Setting up Slack event listeners")

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

            logger.info("Querying Bedrock knowledge base")
            kb_response, valid = query_bedrock_kb(self.aws_session, text)
            
            if not valid or not kb_response.strip():
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

    def get_handler(self):
        return self.handler

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
                    'text': 'What are the office hours?'  # Use a query that's likely to be in your KB
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