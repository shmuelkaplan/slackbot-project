#bot.py
import json 
import os
import requests
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from dotenv import load_dotenv
from bedrock_handler import query_claude
from typing import Optional

load_dotenv()

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

def download_image(client, file: dict) -> Optional[str]:
    image_url = file['url_private']
    image_path = f"temp_image_{file['id']}.jpg"
    response = client.web_client.api_call(
        "files.sharedPublicURL",
        file=file['id']
    )
    with open(image_path, 'wb') as f:
        f.write(requests.get(image_url, headers={'Authorization': f"Bearer {client.token}"}).content)
    return image_path

@app.message("")
def handle_message(message, say, client):
    text = message['text']
    image_path = None

    if 'files' in message and message['files']:
        for file in message['files']:
            if file['mimetype'].startswith('image/'):
                image_path = download_image(client, file)
                break  # Only process the first image

    system_message = "You are a helpful AI assistant integrated into a Slack bot. Respond concisely and professionally."
    user_message = f"User message: {text}"
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]

    response = query_claude(json.dumps(messages), image_path)

    if image_path and os.path.exists(image_path):
        os.remove(image_path)

    say(response)


handler = SlackRequestHandler(app)