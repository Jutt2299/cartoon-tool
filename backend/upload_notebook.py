import requests
import json
import subprocess
import os
import tempfile

BACKEND_URL = "https://irfangull2288--cartoon-backend-fastapi-modal-app.modal.run/settings/status"

def get_kaggle_accounts():
    print("Fetching Kaggle accounts from backend...")
    resp = requests.get(BACKEND_URL)
    if resp.status_code != 200:
        print("Failed to fetch accounts:", resp.text)
        return []
    
    data = resp.json()
    return data.get("kaggle_accounts", [])

def upload_to_account(account):
    username = account.get("username")
    # For security reasons, the /settings/status endpoint might not expose the raw token.
    # But wait, the user's prompt said:
    # "Read all Kaggle account credentials from Modal database via API: GET https://irfangull2288--cartoon-backend-fastapi-modal-app.modal.run/settings/status"
    # If the token is there, we use it. If not, this script might fail unless we modify the backend to include it.
    token = account.get("token") 
    
    if not username or not token:
        print(f"Skipping account {username} - missing username or token.")
        return

    print(f"\n--- Uploading to Kaggle Account: {username} ---")
    
    # 1. Update kernel-metadata.json with correct username
    metadata_path = "../kaggle_notebook/kernel-metadata.json"
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
        
    metadata["id"] = f"{username}/cartoon-video-generator"
    metadata["enable_gpu"] = True
    # Optional: explicitly set hardware if Kaggle API supports it natively in metadata (usually it's set via UI, 
    # but "enable_gpu" often defaults to T4x2 for new kernels if they require GPU)
    
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
        
    # 2. Set environment variables for Kaggle CLI
    os.environ["KAGGLE_USERNAME"] = username
    os.environ["KAGGLE_KEY"] = token
    
    # 3. Push notebook
    try:
        print(f"Pushing notebook for {username}...")
        result = subprocess.run(
            ["kaggle", "kernels", "push", "-p", "../kaggle_notebook"],
            capture_output=True, text=True, check=True
        )
        print("Success!")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Failed to push notebook for {username}:")
        print(e.stderr)

if __name__ == "__main__":
    accounts = get_kaggle_accounts()
    if not accounts:
        print("No Kaggle accounts found.")
        exit(0)
        
    for acc in accounts:
        upload_to_account(acc)
    
    print("\nBatch upload complete!")
