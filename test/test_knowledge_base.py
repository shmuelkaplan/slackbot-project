import os
import sys
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from bedrock_kb_handler import query_bedrock_kb

load_dotenv()

def test_knowledge_base():
    test_queries = [
        "How many minus vacation days can I get?",
        "What are the office hours in Israel?",
        "How do I submit an expense report?",
        "What is the policy for remote work?",
        "Who do I contact for IT support?"
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        result = query_bedrock_kb(query)
        if result:
            print(f"Response: {result}")
        else:
            print("No response from the knowledge base.")

if __name__ == "__main__":
    test_knowledge_base()