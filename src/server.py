from flask import Flask, request, jsonify  # Import Flask, request, and jsonify
from bot import handler  # Import the SlackRequestHandler instance
import logging
flask_app = Flask(__name__)  # Create a new Flask web application instance

logging.basicConfig(level=logging.INFO)

@flask_app.route("/slack/events", methods=["POST"])  # Define a route for POST requests to /slack/events
def slack_events():
    # Check if this is a challenge request
    try:
        
        if "challenge" in request.json:
            return jsonify({"challenge": request.json["challenge"]})  # Respond with the challenge token
        # If not a challenge, process the event as before
        return handler.handle(request)  # Process the request using the SlackRequestHandler
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return jsonify({"error": "An internal error occurred"}), 500

if __name__ == "__main__":  # Run the Flask app only if the script is executed directly
    flask_app.run(port=3000)  # Start the Flask web server on port 3000
