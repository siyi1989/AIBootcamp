from qdrant_client import QdrantClient

#  ADD QDRANT CLOUD ENDPOINT CONFIGURATION:
client = QdrantClient(
    url="https://701a7901-4482-409e-811a-2a37bfafdc5d.sa-east-1-0.aws.cloud.qdrant.io",  # Copy your endpoint from cloud.qdrant.io
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6ZDViNzI5OTQtYzU0MC00MDc2LWJlMzQtZjc1YjdmMjRjMWE3In0.nSR0aCkfR29QvinCwt37uBp1LQ4-TTHj30bw8cgz0Vc",            # Input your cluster API Key
)

# 1. List all collections
collections = client.get_collections()
print("--- Existing Collections ---")
print(collections)

# 2. Get specific collection details (Replace with your actual collection name)
# Typically it matches what is in your get_qdrant_config()
COLLECTION_NAME = "caas-documents" 

try:
    info = client.get_collection(collection_name=COLLECTION_NAME)
    print(f"\n--- Info for '{COLLECTION_NAME}' ---")
    print(f"Status: {info.status}")
    print(f"Total Vectors Stored: {info.vectors_count}")
except Exception as e:
    print(f"\nCould not read collection '{COLLECTION_NAME}': {e}")


import requests
import json

# Your exact Qdrant Cloud credentials
CLUSTER_URL = "https://701a7901-4482-409e-811a-2a37bfafdc5d.sa-east-1-0.aws.cloud.qdrant.io"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6ZDViNzI5OTQtYzU0MC00MDc2LWJlMzQtZjc1YjdmMjRjMWE3In0.nSR0aCkfR29QvinCwt37uBp1LQ4-TTHj30bw8cgz0Vc"

url = f"{CLUSTER_URL}/audit/logs"
headers = {
    "api-key": API_KEY,
    "Content-Type": "application/json"
}

# Fetch the last 10 log entries
response = requests.post(url, headers=headers, json={"limit": 10})

if response.status_code == 200:
    logs = response.json()
    print("--- Recent Database Access History ---")
    for entry in logs.get("result", []):
        # Look for search or query actions
        print(f"Time: {entry.get('timestamp')} | Action: {entry.get('request_path')}")
else:
    print(f"Failed to fetch logs: {response.status_code} - {response.text}")
