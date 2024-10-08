# bedrock_handler.py

import boto3
import json
import os
import logging
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_bedrock_client():
    try:
        return boto3.client(
            service_name='bedrock-runtime',
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            # We don't need to explicitly set the AWS access key, secret, and session
            # token as environment variables because we're using the assume_role.py
            # script to set them before running this script. This script is intended
            # to be run locally with the same permissions as the deployed version,
            # so we can use the AWS Security Token Service (STS) to assume the IAM
            
            # role specified in the role_arn variable and set the corresponding AWS
            # access key, secret, and session token as environment variables.
        )
    except Exception as e:
        logger.error(f"Error creating Bedrock client: {str(e)}", exc_info=True)
        return None

bedrock = get_bedrock_client()

def query_claude(messages: str) -> str:
    """
    Queries the Claude AI model with the given list of messages and returns the response as a string.

    The input messages should be a JSON-formatted string containing a list of message objects, each with the following keys:

    - role (string): The role of the message sender (either 'user', 'assistant', or 'system')
    - content (string): The content of the message

    The function returns the response from the Claude AI model as a string, or an error message if an error occurs.

    The function also logs an error if the Bedrock Agent Runtime client is not initialized.
    """
    if not bedrock:
        logger.error("Bedrock client is not initialized")
        return "Error: Unable to connect to AWS Bedrock. Please check your credentials and try again."

    try:
        parsed_messages = json.loads(messages)
        
        # Convert 'system' role to 'user' and prepend it to the user's message
        if parsed_messages[0]['role'] == 'system':
            system_content = parsed_messages.pop(0)['content']
            parsed_messages[0]['content'] = f"{system_content}\n\nUser: {parsed_messages[0]['content']}"
        
        # Ensure all messages have 'role' set to 'user' or 'assistant'
        for msg in parsed_messages:
            if msg['role'] not in ['user', 'assistant']:
                msg['role'] = 'user'

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 10000,
            "messages": parsed_messages
        })

        try:
            response = bedrock.invoke_model(
                modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response.get('body').read())
            logger.info(f"Raw response from Bedrock: {json.dumps(response_body, indent=2)}")
            
            if 'content' in response_body and response_body['content']:
                return response_body['content'][0]['text']
            else:
                logger.error(f"Unexpected response structure: {response_body}")
                return "I'm sorry, I received an unexpected response format."

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"AWS Bedrock ClientError: {error_code} - {error_message}", exc_info=True)
            return f"AWS Bedrock Error: {error_code} - {error_message}"

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing messages JSON: {str(e)}", exc_info=True)
        return "Error: Invalid message format."
    except Exception as e:
        logger.error(f"Error querying Claude: {str(e)}", exc_info=True)
        return "I'm sorry, I encountered an error while processing your request."