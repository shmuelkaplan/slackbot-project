# bedrock_kb_handler.py
import json
import os
import logging
from typing import Tuple
import uuid
from botocore.exceptions import BotoCoreError, ClientError

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
    
def save_answer_to_s3(question, answer, session):
    try:
        s3_client = session.client('s3')
        bucket_name = os.getenv('S3_BUCKET_NAME')
        knowledge_base_key = os.getenv('S3_KB_FILE_KEY')

        # Retrieve the existing knowledge base from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=knowledge_base_key)
        knowledge_base = json.loads(response['Body'].read().decode('utf-8'))

        # Add the new question and answer
        knowledge_base.append({"question": question, "answer": answer})

        # Save the updated knowledge base back to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=knowledge_base_key,
            Body=json.dumps(knowledge_base),
            ContentType='application/json'
        )
        logger.info(f"Successfully added question and answer to S3: {question} | {answer}")
    except Exception as e:
        logger.error(f"Failed to save answer to S3: {str(e)}", exc_info=True)
        raise

def sync_knowledge_base(session):
    """
    Synchronizes the Amazon Bedrock knowledge base with the specified data source.

    :param session: A boto3 session with the necessary AWS credentials and configuration.
    :return: True if the sync is initiated successfully, False otherwise.
    """
    try:
        # Initialize the bedrock-agent client
        client = session.client('bedrock-agent')

        # Retrieve environment variables
        knowledge_base_id = os.getenv('BEDROCK_KB_ID')
        data_source_id = os.getenv('BEDROCK_DATA_SOURCE_ID')

        if not knowledge_base_id or not data_source_id:
            logger.error("Environment variables 'BEDROCK_KB_ID' or 'BEDROCK_DATA_SOURCE_ID' are not set.")
            return False

        # Generate a unique client token for idempotency
        client_token = str(uuid.uuid4())  # Generates a 36-character UUID

        # Start the ingestion job
        response = client.start_ingestion_job(
            clientToken=client_token,
            dataSourceId=data_source_id,
            description='Synchronizing knowledge base with S3 data source',
            knowledgeBaseId=knowledge_base_id
        )

        ingestion_job_id = response.get('ingestionJob', {}).get('ingestionJobId', 'N/A')
        logger.info(f"Knowledge base sync triggered successfully. Ingestion Job ID: {ingestion_job_id}")
        return True

    except (BotoCoreError, ClientError) as error:
        logger.error(f"Failed to sync knowledge base: {error}", exc_info=True)
        return False