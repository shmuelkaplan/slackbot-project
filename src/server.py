#server.py
import sys
from flask import Flask, request, jsonify
from bot_handler import bot_handler
import logging
import os
from dotenv import load_dotenv
from assume_role import assume_role

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

load_dotenv()

flask_app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    try:
        if "challenge" in request.json:
            logger.info("Received Slack challenge request")
            return jsonify({"challenge": request.json["challenge"]})
        
        logger.info("Received Slack event")
        return bot_handler.handle(request)
    
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@flask_app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

assume_role()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    flask_app.run(host="0.0.0.0", port=port, debug=debug)