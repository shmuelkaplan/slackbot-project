import os
import boto3
from slack_bolt import App
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_aws_credentials():
    try:
        # Create a Bedrock client
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
        )
        
        # Try to invoke a model (using Claude-3 Sonnet as an example)
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hello, world!"}]
            }),
            contentType='application/json',
            accept='application/json'
        )
        logger.info("AWS Bedrock credentials are valid.")
        return True
    except Exception as e:
        logger.error(f"AWS Bedrock credential test failed: {str(e)}")
        return False