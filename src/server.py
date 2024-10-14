# server.py
import os
import sys
import logging
import signal
from dotenv import load_dotenv
from assume_role import assume_role, check_assumed_role
from slack_handler import SlackHandler
from bedrock_kb_handler import query_bedrock_kb

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Verify that required environment variables are set
required_env_vars = ['SLACK_BOT_TOKEN', 'SLACK_APP_TOKEN', 'SLACK_SIGNING_SECRET', 'AWS_DEFAULT_REGION', 'BEDROCK_KB_ID', 'BEDROCK_MODEL_ARN']
for var in required_env_vars:
    if not os.getenv(var):
        logger.error(f"Missing required environment variable: {var}")
        sys.exit(1)


def signal_handler(sig, frame):
    logger.info('Shutting down gracefully...')
    # Perform any cleanup operations here
    sys.exit(0)

def main():
    try:
        logger.info("Starting the application...")
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        logger.info("Signal handlers set up")

        assumed_session = assume_role()
        if not assumed_session or not check_assumed_role(assumed_session):
            logger.error("Failed to assume role or role is not valid.")
            sys.exit(1)
        logger.info("AWS role assumed successfully")

        logger.info("Setting up Slack handler...")
        slack_handler = SlackHandler(
            os.environ.get("SLACK_BOT_TOKEN"),
            os.environ.get("SLACK_APP_TOKEN")
        )
        slack_handler.set_aws_session(assumed_session)
        logger.info("Slack handler initialized")

        if slack_handler.test_bedrock_access():
            logger.info("Bedrock access test passed")
            # Add a test query to check KB content
            test_response, valid = query_bedrock_kb(assumed_session, "How many minus vacation days can I get into?")
            if valid and test_response.strip() and test_response != "Sorry, I am unable to assist you with this request.":
                logger.info(f"Bedrock KB content test passed. Response: {test_response}")
            else:
                logger.warning("Bedrock KB content test failed. The knowledge base might be empty or not contain relevant information.")
        else:
            logger.error("Bedrock access test failed")

        logger.info(f"Slack handler initialized with bot token: {os.environ.get('SLACK_BOT_TOKEN')[:10]}... and app token: {os.environ.get('SLACK_APP_TOKEN')[:10]}...")

        logger.info("Starting Slack bot in Socket Mode...")
        try:
            slack_handler.start()
        except Exception as e:
            logger.error(f"Failed to start Slack bot: {str(e)}", exc_info=True)
            sys.exit(1)

    except Exception as e:
        logger.error(f"An error occurred during startup: {e}", exc_info=True)
        sys.exit(1)
        
if __name__ == "__main__":
    main()