#aws_credention_test.py
import boto3
from botocore.exceptions import ClientError

def test_aws_credentials():
    try:
        sts = boto3.client('sts')
        response = sts.get_caller_identity()
        print("AWS credentials are valid.")
        print(f"Account ID: {response['Account']}")
        print(f"User ID: {response['UserId']}")
    except ClientError as e:
        print("Error: AWS credentials are invalid or not set.")
        print(f"Error message: {str(e)}")

if __name__ == "__main__":
    test_aws_credentials()