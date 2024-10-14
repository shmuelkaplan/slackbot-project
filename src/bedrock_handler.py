# bedrock_handler.py

import json
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_bedrock_client(session):
    """
    Creates and returns a Bedrock runtime client using the provided session.

    :param session: A boto3 session with assumed role credentials
    :return: A Bedrock runtime client or None if an error occurred
    """
    try:
        return session.client('bedrock-runtime')
    except Exception as e:
        logger.error(f"Error creating Bedrock client: {str(e)}", exc_info=True)
        return None

def query_claude(session, messages: str) -> str:
    """
    Queries the Claude AI model with the given list of messages using the provided session.

    :param session: A boto3 session with assumed role credentials
    :param messages: JSON-formatted string of messages
    :return: Response from the Claude AI model or an error message
    """
    bedrock = get_bedrock_client(session)
    if not bedrock:
        logger.error("Bedrock client is not initialized")
        return "Error: Unable to connect to AWS Bedrock. Please check your credentials and try again."

    try:
        parsed_messages = json.loads(messages)
        
        if parsed_messages[0]['role'] == 'system':
            system_content = parsed_messages.pop(0)['content']
            parsed_messages[0]['content'] = f"{system_content}\n\nUser: {parsed_messages[0]['content']}"
        
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