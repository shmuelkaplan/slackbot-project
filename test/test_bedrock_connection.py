#test_bedrock_connection.py

import boto3
import json
from botocore.exceptions import ClientError

def test_bedrock_connection():
    try:
        # Create a Bedrock Runtime client
        bedrock = boto3.client('bedrock-runtime')

        # Prepare a simple prompt
        prompt = "Hello, Claude. How are you today?"
        
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })

        # Invoke the model
        response = bedrock.invoke_model(
            modelId="eu.anthropic.claude-3-5-sonnet-20240620-v1:0",
            body=body,
            contentType="application/json",
            accept="application/json"
        )

        # Parse and print the response
        response_body = json.loads(response['body'].read())
        print("Bedrock connection successful!")
        print("Claude's response:", response_body['content'][0]['text'])

    except ClientError as e:
        print(f"Error connecting to Bedrock: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    test_bedrock_connection()