import requests
import os
import sys
import json
import subprocess
import tempfile

BACKEND_URL = "https://irfangull2288--cartoon-backend-fastapi-modal-app.modal.run"
KAGGLE_CMD = [os.path.join(os.path.dirname(sys.executable), "Scripts", "kaggle.exe")]

print("Step 1: Fetching global tokens...")
r = requests.get(f"{BACKEND_URL}/settings/global", timeout=30)
data = r.json()
ngrok_token = data.get("ngrok_token", "")
hf_token = data.get("hf_token", "")
print(f"  ngrok_token: {'OK' if ngrok_token else 'MISSING'}")
print(f"  hf_token: {'OK' if hf_token else 'MISSING'}")

print("Step 2: Fetching accounts...")
r2 = requests.get(f"{BACKEND_URL}/settings/status", timeout=30)
accounts = r2.json().get("kaggle_accounts", [])
usernames = [a.get("username") for a in accounts]
print(f"  Found {len(accounts)} accounts: {usernames}")

if not accounts:
    print("No accounts found! Exiting.")
    sys.exit(0)

print("Step 3: Pushing notebook to first account as test...")
acc = accounts[0]
username = acc.get("username")
token = acc.get("token")
print(f"  Account: {username}")

env = os.environ.copy()
env["KAGGLE_USERNAME"] = username
env["KAGGLE_KEY"] = token

with tempfile.TemporaryDirectory() as tmpdir:
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
        json.dump(metadata, f)

    nb_path = os.path.abspath("../kaggle_notebook/notebook.ipynb")
    with open(nb_path, "r") as f:
        content = f.read()
    content = content.replace("[HF_TOKEN]", hf_token)
    content = content.replace("[NGROK_TOKEN]", ngrok_token)
    with open(os.path.join(tmpdir, "notebook.ipynb"), "w") as f:
        f.write(content)

    print(f"  Pushing now...")
    result = subprocess.run(
        KAGGLE_CMD + ["kernels", "push", "-p", tmpdir],
        capture_output=True, text=True, check=False, env=env,
        encoding="utf-8", errors="replace", timeout=60
    )
    if result.returncode == 0:
        print(f"  [OK] {result.stdout.strip()}")
    else:
        print(f"  [FAIL] {result.stderr.strip() or result.stdout.strip()}")
