#bot_handler.py
import json
import os
import logging
from slack_bolt import App, Say
from slack_bolt.adapter.flask import SlackRequestHandler
from dotenv import load_dotenv
from bedrock_handler import query_claude
from bedrock_kb_handler import query_bedrock_kb

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# @app.event("app_mention")
@app.message("")
def handle_message(message, say):
    try:
        text = message['text']
        
        # First, query the Bedrock knowledge base
        kb_response, valid = query_bedrock_kb(text)
        
        if not valid or not kb_response.strip():
            # If no valid response or empty response, fallback to Claude model directly
            system_message = "You are a helpful AI assistant integrated into a Slack bot. Respond concisely and professionally."
            user_message = f"User message: {text}"
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]

            # Query Claude model directly
            response = query_claude(json.dumps(messages))
            say(response)
        else:
            say(kb_response)

    except Exception as e:
        logger.error(f"Error in handle_message: {str(e)}", exc_info=True)
        say("I'm sorry, I encountered an error while processing your message.")

bot_handler = SlackRequestHandler(app)