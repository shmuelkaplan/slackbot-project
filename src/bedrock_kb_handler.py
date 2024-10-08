import boto3
import json
import os
import logging
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from typing import Tuple

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_bedrock_agent_runtime_client():
    """
    Returns a boto3 client for the Bedrock Agent Runtime service.

    :return: A Bedrock Agent Runtime client or None if an error occurred
    :rtype: boto3.client or None
    """
    
    try:
        return boto3.client(
            service_name='bedrock-agent-runtime',
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            # aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            # aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
        )
    except Exception as e:
        logger.error(f"Error creating Bedrock Agent Runtime client: {str(e)}", exc_info=True)
        return None

bedrock_agent_runtime = get_bedrock_agent_runtime_client()

def query_bedrock_kb(query: str) -> Tuple[str, bool]:
    """
    Queries the Bedrock knowledge base with the given query and returns the response as a tuple (string, bool).

    :param query: The query to send to Bedrock
    :type query: str
    :return: The response from Bedrock as a tuple (string, bool)
    :rtype: Tuple[str, bool]

    If an error occurs, the function returns an empty string and False.

    The function queries the knowledge base with the given query and returns the response as a string. If the response
    is not in the expected format, the function logs an error and returns an empty string and False.

    The function also logs an error if the Bedrock Agent Runtime client is not initialized.
    """

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

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"AWS Bedrock ClientError: {error_code} - {error_message}", exc_info=True)
        return "", False
    except Exception as e:
        logger.error(f"Error querying Bedrock KB: {str(e)}", exc_info=True)
        return "", False

def get_kb_info():
    """
    Retrieves information about the Bedrock knowledge base specified by the BEDROCK_KB_ID environment variable.

    :return: The information about the knowledge base as a JSON string
    :rtype: str

    If an error occurs, the function logs an error and returns an error message as a string.

    The function also logs an error if the Bedrock Agent Runtime client is not initialized.
    """
    if not bedrock_agent_runtime:
        logger.error("Bedrock Agent Runtime client is not initialized")
        return "Error: Unable to connect to AWS Bedrock. Please check your credentials and try again."

    try:
        knowledge_base_id = os.environ.get("BEDROCK_KB_ID")
        response = bedrock_agent_runtime.get_knowledge_base(
            knowledgeBaseId=knowledge_base_id
        )
        return json.dumps(response, indent=2)
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"AWS Bedrock ClientError: {error_code} - {error_message}", exc_info=True)
        return f"Error retrieving KB info: {error_code} - {error_message}"
    except Exception as e:
        logger.error(f"Error retrieving KB info: {str(e)}", exc_info=True)
        return f"Error retrieving KB info: {str(e)}"

# Example usage
if __name__ == "__main__":
    # Test querying the knowledge base
    query = "What are the office hours?"
    response, valid = query_bedrock_kb(query)
    if valid:
        print(f"Query: {query}")
        print(f"Response: {response}")
    else:
        print("Failed to get a valid response from the knowledge base.")

    # Test getting knowledge base info
    print("\nKnowledge Base Info:")
    print(get_kb_info())