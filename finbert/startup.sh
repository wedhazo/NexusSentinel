#!/bin/bash
set -e

# Download model from GCS if needed
if [ "$MODEL_SOURCE" = "GCS" ]; then
  echo "Downloading model from GCS bucket: ${GCS_BUCKET}, path: ${GCS_PATH}"
  python -c "
import os
from google.cloud import storage

# Setup client
storage_client = storage.Client()
bucket = storage_client.bucket(os.environ[\"GCS_BUCKET\"])

# Create model directory
os.makedirs(os.environ[\"MODEL_PATH\"], exist_ok=True)

# List all blobs with the prefix
blobs = list(bucket.list_blobs(prefix=os.environ[\"GCS_PATH\"] + \"/\"))

# Download each file
for blob in blobs:
    # Skip the directory itself
    if blob.name.endswith(\"/\"):
        continue
        
    # Get the relative path
    rel_path = blob.name[len(os.environ[\"GCS_PATH\"]) + 1:]
    if rel_path:
        # Create the directory structure
        dest_file = os.path.join(os.environ[\"MODEL_PATH\"], rel_path)
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
        
        # Download the file
        blob.download_to_filename(dest_file)
        print(f\"Downloaded {blob.name} to {dest_file}\")
"
  echo "Model download complete"
fi

# Start the application
echo "Starting the application..."
exec uvicorn app:app --host 0.0.0.0 --port ${PORT}
