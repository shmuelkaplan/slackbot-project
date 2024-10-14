# bedrock_kb_handler.py
import json
import os
import logging
from typing import Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_bedrock_agent_runtime_client(session):
    """
    Returns a boto3 client for the Bedrock Agent Runtime service using the provided session.

    :param session: A boto3 session with assumed role credentials
    :return: A Bedrock Agent Runtime client or None if an error occurred
    """
    try:
        return session.client('bedrock-agent-runtime')
    except Exception as e:
        logger.error(f"Error creating Bedrock Agent Runtime client: {str(e)}", exc_info=True)
        return None

def query_bedrock_kb(session, query: str) -> Tuple[str, bool]:
    """
    Queries the Bedrock knowledge base with the given query using the provided session.

    :param session: A boto3 session with assumed role credentials
    :param query: The query to send to Bedrock
    :return: The response from Bedrock as a tuple (string, bool)
    """
    bedrock_agent_runtime = get_bedrock_agent_runtime_client(session)
    if not bedrock_agent_runtime:
        logger.error("Bedrock Agent Runtime client is not initialized")
        return "Error: Unable to connect to AWS Bedrock. Please check your credentials and try again.", False

    try:
        knowledge_base_id = os.environ.get("BEDROCK_KB_ID")
        model_arn = os.environ.get("BEDROCK_MODEL_ARN", "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0")
        
        response = bedrock_agent_runtime.retrieve_and_generate(
            input={
                'text': query
            },
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': knowledge_base_id,
                    'modelArn': model_arn
                }
            }
        )

        if 'output' in response and 'text' in response['output']:
            return response['output']['text'], True
        else:
            logger.error(f"Unexpected response structure: {response}")
            return "", False

    except Exception as e:
        logger.error(f"Error querying Bedrock KB: {str(e)}", exc_info=True)
        return "", False

def get_kb_info(session):
    """
    Retrieves information about the Bedrock knowledge base using the provided session.

    :param session: A boto3 session with assumed role credentials
    :return: The information about the knowledge base as a JSON string
    """
    bedrock_agent_runtime = get_bedrock_agent_runtime_client(session)
    if not bedrock_agent_runtime:
        logger.error("Bedrock Agent Runtime client is not initialized")
        return "Error: Unable to connect to AWS Bedrock. Please check your credentials and try again."

    try:
        knowledge_base_id = os.environ.get("BEDROCK_KB_ID")
        response = bedrock_agent_runtime.get_knowledge_base(
            knowledgeBaseId=knowledge_base_id
        )
        return json.dumps(response, indent=2)
    except Exception as e:
        logger.error(f"Error retrieving KB info: {str(e)}", exc_info=True)
        return f"Error retrieving KB info: {str(e)}"