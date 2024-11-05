# slack_handler.py
import os
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from bedrock_kb_handler import query_bedrock_kb
from bedrock_kb_handler import save_answer_to_s3, sync_knowledge_base
from bedrock_handler import query_claude
import json

logger = logging.getLogger(__name__)

class SlackHandler:
    def __init__(self, slack_bot_token, slack_app_token):
        """
        Initializes the SlackHandler with tokens and starts setting up listeners.
        """
        self.app = App(token=slack_bot_token)
        self.socket_mode_handler = SocketModeHandler(self.app, slack_app_token)
        try:
            self.bot_user_id = self.app.client.auth_test()['user_id']
        except Exception as e:
            logger.error(f"Failed to authenticate with Slack API: {str(e)}", exc_info=True)
            raise SystemExit("Critical error: Failed to authenticate with Slack API.")
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
            if event.get("channel_type") == "im" and f"<@{self.bot_user_id}>" not in event.get("text", ""):
                self.handle_message(event, say)

        @self.app.command("/use_claude")
        def handle_use_claude_command(ack, respond, command):
            ack()  # Acknowledge the command request
            try:

                if not self.aws_session:
                    logger.error("AWS session not set for Claude query")
                    respond("I'm not properly configured to answer questions at the moment. Please try again later.")
                    return

                user_message = command.get("text", "")
                if not user_message:
                    respond("Please provide a question or message to process.")
                    return

                system_message = "You are a helpful AI assistant integrated into a Slack bot. Respond concisely and professionally."
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ]
                response = query_claude(self.aws_session, json.dumps(messages))
                if not response:
                    respond("I was unable to generate a response. Please try again or reach out to HR.")
                else:
                    logger.info(f"Claude response: {response}")
                    respond(response)
            except Exception as e:
                logger.error(f"Error in handle_use_claude_command: {str(e)}", exc_info=True)
                respond("I'm sorry, I encountered an error while processing your request.")
            
        @self.app.command("/add_answer")
        def handle_add_answer(ack, respond, command):
            ack()  # Acknowledge the command request
            hr_channel_id = os.getenv('HR_CHANNEL_ID')
            if command.get('channel_id') != hr_channel_id:
                respond("This command is not allowed outside the HR channel.")
                return
            try:
                 
                if not self.aws_session:
                    logger.error("AWS session not set for saving answer")
                    respond("I'm not properly configured to save answers at the moment. Please try again later.")
                    return

                user_message = command.get("text", "").strip()
                if not user_message:
                    respond("Please provide both the question and the answer in the format: `question | answer`.")
                    return

                # Extract question and answer
                parts = user_message.split("|")
                if len(parts) != 2:
                    respond("Invalid format. Please use: `question | answer`.")
                    return

                question = parts[0].strip()
                answer = parts[1].strip()

                # Save the question and answer to S3
                save_answer_to_s3(question, answer, self.aws_session)
                respond("The answer has been successfully added to the knowledge base.")

                # Sync with knowledge base
                if sync_knowledge_base(self.aws_session):
                    respond("The knowledge base has been updated successfully.")
                else:
                    respond("The answer was added, but there was an issue syncing the knowledge base. Please check the logs.")
            except Exception as e:
                logger.error(f"Error in handle_add_answer: {str(e)}", exc_info=True)
                respond("I'm sorry, I encountered an error while processing your request.")

    def handle_message(self, event, say):
        if event.get("bot_id"):
            return
        
        try:
            text = event.get("text", "")
            logger.info(f"Received message: {text}")

            if not text:
                say("Received an empty message. I'm sorry, I can't help with that.")
                return

            if not self.aws_session:
                logger.error("AWS session not set")
                say("I'm sorry, I'm not properly configured to answer questions at the moment. check the logs for more details")
                return
            
            # Remove bot mention from the text
            text = text.replace(f"<@{self.bot_user_id}>", "").strip()
            
            #query the knowledge base
            kb_response, valid = query_bedrock_kb(self.aws_session, text)
            logger.info(f"Knowledge base response: {kb_response}")
            if not valid or not kb_response.strip() or kb_response == "Sorry, I am unable to assist you with this request." or "I'm sorry" in kb_response or "I apologize" in kb_response:
                logger.info("No valid response from knowledge base, notifying HR")
                self.notify_hr_with_question(text, say)
            else:
                logger.info(f"Responding with knowledge base answer: {kb_response}")
                say(kb_response)

        
        except Exception as e:
            logger.error(f"Error in handle_message: {str(e)}", exc_info=True)
            say("I'm sorry, I encountered an error while processing your message.")


    def notify_hr_with_question(self, user_question, say):
        try:
            # Send message to HR channel using Slack Bolt client
            hr_channel_id = os.getenv('HR_CHANNEL_ID')
            if not hr_channel_id:
                logger.error("HR_CHANNEL_ID environment variable is not set")
                say("I'm unable to forward your question to HR because the HR channel is not configured.")
                return
            
            user_question = user_question.replace(f'<@{self.bot_user_id}>', '')
            try:
                self.app.client.chat_postMessage(
                    channel=hr_channel_id,
                    text=f"A new employee question could not be answered by the KB:\n\n"
                         f"*Question:* {user_question}\n\n"
                         f"Please provide an answer and use the /add_answer command to update the KB."
                )
                say("I'm not sure about that, but I've sent your question to HR. They'll respond soon!")
            except Exception as e:
                logger.error(f"Failed to send message to HR channel: {str(e)}", exc_info=True)
                say("I'm sorry, I encountered an error while trying to notify HR. Please contact support if the issue persists.")

            # Notify the user
            say("I'm not sure about that, but I've sent your question to HR. They'll respond soon!")

        except Exception as e:
            logger.error(f"Unexpected error in notify_hr_with_question: {str(e)}", exc_info=True)
            say("I'm sorry, I encountered an unexpected error while trying to notify HR.")



    def start(self):
        try:
            logger.info("Starting Socket Mode handler")
            self.socket_mode_handler.start()
        except Exception as e:
            logger.error(f"Failed to start Socket Mode handler: {str(e)}", exc_info=True)
            raise SystemExit("Critical error: Failed to start Slack Socket Mode handler.")
    
    def test_bedrock_access(self):
        if not self.aws_session:
            logger.error("AWS session not set")
            return False
        try:
            client = self.aws_session.client('bedrock-agent-runtime')
            knowledge_base_id = os.getenv('BEDROCK_KB_ID')
            model_arn = os.getenv('BEDROCK_MODEL_ARN')

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
        except client.exceptions.ClientError as e:
            logger.error(f"Client error while accessing Bedrock knowledge base: {str(e)}", exc_info=True)
            return False
        except client.exceptions.InvalidParameterException as e:
            logger.error(f"Invalid parameters provided: {str(e)}. Please verify the knowledge base ID and model ARN.", exc_info=True)
            return False
        except client.exceptions.AccessDeniedException as e:
            logger.error(f"Access denied: {str(e)}. Please check your AWS permissions.", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Failed to access Bedrock knowledge base: {str(e)}", exc_info=True)
            return False
