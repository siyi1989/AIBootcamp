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
