from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the Slack app
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))


@app.message("help")
def message_help(message, say):
    help_text = """
    Here are the commands I understand:
    • `hello`: I'll say hello back!
    • `help`: I'll show this help message
    • `echo [message]`: I'll repeat your message
    """
    say(help_text)

@app.message("echo")
def message_echo(message, say):
    # Remove 'echo' from the beginning of the message
    text = message['text'].replace('echo', '', 1).strip()
    if text:
        say(f"You said: {text}")
    else:
        say("You didn't provide anything to echo!")

# Basic message handler
@app.message("hello")
def message_hello(message, say):
    say(f"Hey there <@{message['user']}>!")

# Event handler for app mentions
@app.event("app_mention")
def handle_app_mention(body, say):
    say(f"You mentioned me in <#{body['event']['channel']}>. How can I help?")

# Get the handler for Flask
handler = SlackRequestHandler(app)
