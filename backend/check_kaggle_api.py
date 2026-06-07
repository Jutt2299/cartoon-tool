import modal
import sqlite3
import os
import subprocess

app = modal.App("cartoon-backend")
volume = modal.NetworkFileSystem.from_name("cartoon-db-nfs", create_if_missing=True)

@app.function(
    network_file_systems={"/data": volume},
    image=modal.Image.debian_slim().pip_install("kaggle", "requests")
)
def check_gpu_quota():
    conn = sqlite3.connect('/data/cartoon_v2.db')
    cur = conn.cursor()
    cur.execute('SELECT username, token FROM kaggle_accounts WHERE is_active=1')
    account = cur.fetchone()
    if not account:
        cur.execute('SELECT username, token FROM kaggle_accounts LIMIT 1')
        account = cur.fetchone()
    conn.close()
    
    if not account:
        print("No Kaggle account found in DB.")
        return
        
    username, token = account
    print(f"Checking quota for: {username}")
    
    import requests
    from requests.auth import HTTPBasicAuth
    
    # Check kernel quota via Kaggle API
    resp = requests.get(
        "https://www.kaggle.com/api/v1/kernels/list",
        params={"mine": True, "pageSize": 1},
        auth=HTTPBasicAuth(username, token)
    )
    print(f"API Status: {resp.status_code}")
    
    # Check weekly usage via user profile
    resp2 = requests.get(
        f"https://www.kaggle.com/api/v1/users/{username}",
        auth=HTTPBasicAuth(username, token)
    )
    print(f"User API Status: {resp2.status_code}")
    if resp2.status_code == 200:
        data = resp2.json()
        print("User data keys:", list(data.keys()))
        print("Full response:", data)

if __name__ == "__main__":
    with app.run():
        check_gpu_quota.remote()
