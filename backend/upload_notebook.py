import requests
import json
import subprocess
import os
import sys
import tempfile

BACKEND_URL = "https://irfangull2288--cartoon-backend-fastapi-modal-app.modal.run"

def get_global_tokens():
    """Fetch tokens from backend database"""
    try:
        resp = requests.get(f"{BACKEND_URL}/settings/global")
        data = resp.json()
        return data.get("ngrok_token", ""), data.get("hf_token", "")
    except Exception as e:
        print(f"Failed to fetch global tokens: {e}")
        return "", ""

KAGGLE_CMD = [os.path.join(os.path.dirname(sys.executable), "Scripts", "kaggle.exe")]

def get_kaggle_accounts():
    print("Fetching Kaggle accounts from backend...")
    resp = requests.get(f"{BACKEND_URL}/settings/status")
    if resp.status_code != 200:
        print("Failed to fetch accounts:", resp.text)
        return []
    data = resp.json()
    return data.get("kaggle_accounts", [])

def build_notebook(username):
    """Build notebook JSON with tokens injected"""
    ngrok_token, hf_token = get_global_tokens()
    nb_path = os.path.join(os.path.dirname(__file__), "..", "kaggle_notebook", "notebook.ipynb")
    nb_path = os.path.abspath(nb_path)
    with open(nb_path, "r") as f:
        content = f.read()
    content = content.replace("[HF_TOKEN]", hf_token)
    content = content.replace("[NGROK_TOKEN]", ngrok_token)
    return json.loads(content)

def upload_to_account(username, token):
    print(f"\n--- Uploading to Kaggle Account: {username} ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Write kernel-metadata.json
        metadata = {
            "id": f"{username}/cartoon-video-generator",
            "title": "Cartoon Video Generator",
            "code_file": "notebook.ipynb",
            "language": "python",
            "kernel_type": "notebook",
            "is_private": True,
            "enable_gpu": True,
            "enable_internet": True
        }
        with open(os.path.join(tmpdir, "kernel-metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)

        # 2. Write injected notebook
        try:
            notebook = build_notebook(username)
        except Exception as e:
            print(f"  Failed to build notebook: {e}")
            return False

        with open(os.path.join(tmpdir, "notebook.ipynb"), "w") as f:
            json.dump(notebook, f, indent=2)

        # 3. Set Kaggle credentials and push
        env = os.environ.copy()
        env["KAGGLE_USERNAME"] = username
        env["KAGGLE_KEY"] = token

        try:
            print(f"  Pushing notebook for {username}...")
            result = subprocess.run(
                KAGGLE_CMD + ["kernels", "push", "-p", tmpdir],
                capture_output=True, text=True, check=False, env=env,
                encoding="utf-8", errors="replace"
            )
            if result.returncode == 0:
                print(f"  [OK] Success! {result.stdout.strip()}")
                return True
            else:
                print(f"  [FAIL] Kaggle error:")
                print(result.stderr.strip())
                print(result.stdout.strip())
                return False
        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            return False

if __name__ == "__main__":
    accounts = get_kaggle_accounts()
    if not accounts:
        print("No Kaggle accounts found in backend.")
        exit(0)

    print(f"\nFound {len(accounts)} accounts. Starting batch upload...\n")
    
    success_count = 0
    for acc in accounts:
        username = acc.get("username")
        token = acc.get("token")
        if not username or not token:
            print(f"  Skipping {username} - missing credentials")
            continue
        if upload_to_account(username, token):
            success_count += 1
    
    print(f"\n{'='*40}")
    print(f"Batch upload complete: {success_count}/{len(accounts)} accounts updated.")
