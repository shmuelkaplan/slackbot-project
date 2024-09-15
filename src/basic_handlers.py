#basic_handler.py
from slack_bolt import App
from slack_bolt.context.say import Say
from slack_bolt.context.body import BoltContext

def register_basic_handlers(app: App) -> None:
    """
    Register basic message handlers for the Slack bot.
    """
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