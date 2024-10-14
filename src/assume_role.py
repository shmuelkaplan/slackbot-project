# assume_role.py

import boto3
import logging
import time
from botocore.exceptions import ClientError, NoCredentialsError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_session(max_retries=5, initial_delay=1):
    for attempt in range(max_retries):
        try:
            session = boto3.Session()
            sts = session.client('sts')
            sts.get_caller_identity()
            logger.info(f"Successfully created session on attempt {attempt + 1}")
            return session
        except ClientError as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                logger.error("Failed to create session after maximum retries")
                return None
            time.sleep(initial_delay * (2 ** attempt))  # Exponential backoff

def assume_role(max_retries=5, initial_delay=1):
    for attempt in range(max_retries):
        try:
            session = get_session()
            if not session:
                raise NoCredentialsError("Unable to locate valid credentials")

            sts_client = session.client('sts')
            account_id = sts_client.get_caller_identity()["Account"]
            role_arn = f"arn:aws:iam::{account_id}:role/BedrokLocalDevelopmentRoleTeam5"
            
            logger.info(f"Attempting to assume role: {role_arn}")
            
            assumed_role_object = sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName="LocalDevelopmentSession"
            )
            
            credentials = assumed_role_object['Credentials']
            
            new_session = boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )
            
            logger.info(f"Role assumed successfully on attempt {attempt + 1}")
            return new_session
        except ClientError as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                logger.error("Failed to assume role after maximum retries")
                raise
            time.sleep(initial_delay * (2 ** attempt))  # Exponential backoff
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise

def check_assumed_role(session):
    try:
        sts_client = session.client('sts')
        identity = sts_client.get_caller_identity()
        logger.info(f"Assumed role identity: {identity['Arn']}")
        return True
    except Exception as e:
        logger.error(f"Error checking assumed role: {e}")
        return False

if __name__ == "__main__":
    try:
        assumed_session = assume_role()
        if assumed_session and check_assumed_role(assumed_session):
            logger.info("Assumed role is valid.")
        else:
            logger.error("Failed to assume role or role is not valid.")
    except Exception as e:
        logger.error(f"Failed to assume role: {e}")