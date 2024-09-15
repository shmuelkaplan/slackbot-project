# bot.py
import json 
import os
import requests
import logging
from slack_bolt import App, Say
from slack_bolt.adapter.flask import SlackRequestHandler
from dotenv import load_dotenv
from bedrock_handler import query_claude
from typing import Optional

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

@app.message("hello")
def message_hello(message: dict, say: Say) -> None:
    """Respond to 'hello' messages."""
    say(f"Hey there <@{message['user']}>!")

@app.message("help")
def message_help(message: dict, say: Say) -> None:
    """Provide help information."""
    help_text = """
    Here are the commands I understand:
    • `hello`: I'll say hello back!
    • `help`: I'll show this help message
    • `echo [message]`: I'll repeat your message
    """
    say(help_text)

@app.message("echo")
def message_echo(message: dict, say: Say) -> None:
    """Echo the user's message."""
    text = message['text'].replace('echo', '', 1).strip()
    if text:
        say(f"You said: {text}")
    else:
        say("You didn't provide anything to echo!")

@app.event("app_mention")
def handle_app_mention(body: dict, say: Say) -> None:
    """Respond to app mentions."""
    say(f"You mentioned me in <#{body['event']['channel']}>. How can I help?")

def download_image(client, file: dict) -> Optional[str]:
    try:
        image_url = file['url_private']
        image_path = f"temp_image_{file['id']}.jpg"
        response = client.web_client.api_call(
            "files.sharedPublicURL",
            file=file['id']
        )
        with open(image_path, 'wb') as f:
            image_response = requests.get(image_url, headers={'Authorization': f"Bearer {client.token}"})
            image_response.raise_for_status()  # Raise an exception for bad status codes
            f.write(image_response.content)
        return image_path
    except requests.RequestException as e:
        logger.error(f"Error downloading image: {str(e)}", exc_info=True)
        return None
    except IOError as e:
        logger.error(f"Error saving image: {str(e)}", exc_info=True)
        return None

@app.message("")
def handle_message(message, say, client):
    try:
        text = message['text']
        image_path = None

        if 'files' in message and message['files']:
            for file in message['files']:
                if file['mimetype'].startswith('image/'):
                    image_path = download_image(client, file)
                    if image_path:
                        break
                    else:
                        say("I'm sorry, I couldn't process the attached image.")
                        return

        system_message = "You are a helpful AI assistant integrated into a Slack bot. Respond concisely and professionally."
        user_message = f"User message: {text}"
        
        messages = [
            {"role": "user", "content": f"{system_message}\n\nUser: {user_message}"}
        ]

        response = query_claude(json.dumps(messages), image_path)

        say(response)
    except Exception as e:
        logger.error(f"Error in handle_message: {str(e)}", exc_info=True)
        say("I'm sorry, I encountered an error while processing your message.")
    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
            
handler = SlackRequestHandler(app)