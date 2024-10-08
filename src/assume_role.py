# assume_role.py
import boto3
import os
import subprocess
import logging
from botocore.exceptions import ClientError, NoCredentialsError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_env_vars():
    """
    Validates that the required environment variables are set.

    Raises a ValueError if any of the required variables are not set.
    """
    
    required_vars = ["AWS_DEFAULT_REGION", "AWS_ROLE_ARN"]
    for var in required_vars:
        if not os.environ.get(var):
            raise ValueError(f"Environment variable {var} is not set")

def assume_role():
    """
    Assumes an AWS role and sets the corresponding AWS access key, secret, and session token as environment variables.
    """
    validate_env_vars()
    
    try:
        region = os.environ.get("AWS_DEFAULT_REGION")
        role_arn = os.environ.get("AWS_ROLE_ARN")
        
        sts_client = boto3.client('sts', region_name=region)
        assumed_role_object = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName="LocalDevelopmentSession"
        )
        credentials = assumed_role_object['Credentials']
        
        os.environ['AWS_ACCESS_KEY_ID'] = credentials['AccessKeyId']
        os.environ['AWS_SECRET_ACCESS_KEY'] = credentials['SecretAccessKey']
        os.environ['AWS_SESSION_TOKEN'] = credentials['SessionToken']
        
        logger.info("Role assumed successfully")
        
    except ClientError as e:
        logger.error(f"AWS ClientError occurred: {e}")
        logger.error(f"Error Code: {e.response['Error']['Code']}")
        logger.error(f"Error Message: {e.response['Error']['Message']}")
        raise
    except NoCredentialsError:
        logger.error("AWS credentials not found. Make sure AWS CLI is configured correctly.")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise

def check_assumed_role():
    """
    Checks if the assumed role is still valid.
    """
    try:
        sts_client = boto3.client('sts')
        sts_client.get_caller_identity()
        return True
    except:
        return False

if __name__ == "__main__":
    try:
        assume_role()
        if check_assumed_role():
            logger.info("Assumed role is valid. Starting server...")
            subprocess.run(["python", "server.py"])
        else:
            logger.error("Failed to assume role or role is not valid.")
    except Exception as e:
        logger.error(f"Failed to run the server: {e}")