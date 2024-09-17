import boto3
import json
import base64
import os
import logging
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_bedrock_client():
    try:
        return boto3.client(
            service_name='bedrock-runtime',
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
        )
    except Exception as e:
        logger.error(f"Error creating Bedrock client: {str(e)}", exc_info=True)
        return None

bedrock = get_bedrock_client()

def encode_image(image_path: str) -> Optional[str]:
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except IOError as e:
        logger.error(f"Error reading image file: {str(e)}", exc_info=True)
        return None

def query_claude(messages: str, image_path: Optional[str] = None) -> str:
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

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing messages JSON: {str(e)}", exc_info=True)
        return "Error: Invalid message format."

    if image_path:
        base64_image = encode_image(image_path)
        if not base64_image:
            return "Error: Unable to process the attached image."
        parsed_messages[0]["content"] = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64_image
                }
            },
            {
                "type": "text",
                "text": parsed_messages[0]["content"]
            }
        ]
    else:
        parsed_messages[0]["content"] = [{"type": "text", "text": parsed_messages[0]["content"]}]

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 10000,
        "messages": parsed_messages
    })

    try:
        response = bedrock.invoke_model(
            modelId="eu.anthropic.claude-3-5-sonnet-20240620-v1:0",
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
    except Exception as e:
        logger.error(f"Error querying Claude: {str(e)}", exc_info=True)
        return "I'm sorry, I encountered an error while processing your request."