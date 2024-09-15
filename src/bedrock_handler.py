#bedrock_handlers.py
import boto3
import json
import base64
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

def get_bedrock_client():
    try:
        return boto3.client(
            service_name='bedrock-runtime',
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
        )
    except Exception as e:
        print(f"Error creating Bedrock client: {str(e)}")
        return None

bedrock = get_bedrock_client()

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def query_claude(messages: str, image_path: Optional[str] = None) -> str:
    if not bedrock:
        return "Error: Unable to connect to AWS Bedrock. Please check your credentials and try again."

    parsed_messages = json.loads(messages)
    
    if image_path:
        base64_image = encode_image(image_path)
        parsed_messages[1]["content"] = [
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
                "text": parsed_messages[1]["content"]
            }
        ]
    else:
        parsed_messages[1]["content"] = [{"type": "text", "text": parsed_messages[1]["content"]}]

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": parsed_messages
    })

    try:
        response = bedrock.invoke_model(
            modelId="arn:aws:bedrock:eu-west-1:976193263418:inference-profile/eu.anthropic.claude-3-5-sonnet-20240620-v1:0",
            body=body,
            contentType="application/json",
            accept="application/json"
        )
        response_body = json.loads(response.get('body').read())
        return response_body['content'][0]['text']
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        return f"AWS Bedrock Error: {error_code} - {error_message}"
    except Exception as e:
        print(f"Error querying Claude: {str(e)}")
        return "I'm sorry, I encountered an error while processing your request."