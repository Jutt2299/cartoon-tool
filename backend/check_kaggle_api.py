import modal
import sqlite3
import requests
import os

app = modal.App("cartoon-backend")
volume = modal.NetworkFileSystem.from_name("cartoon-db-nfs", create_if_missing=True)

@app.function(
    network_file_systems={"/data": volume},
    image=modal.Image.debian_slim().pip_install("requests")
)
def check_kaggle_api():
    conn = sqlite3.connect('/data/cartoon_v2.db')
    cur = conn.cursor()
    cur.execute('SELECT username, token FROM kaggle_accounts')
    accounts = cur.fetchall()
    conn.close()
    
    for username, token in accounts:
        print(f"\n--- Checking: {username} ---")
        
        # Check kernel status via Kaggle API directly
        url = f"https://www.kaggle.com/api/v1/kernels/{username}/cartoon-video-generator"
        resp = requests.get(url, auth=(username, token))
        print(f"cartoon-video-generator: {resp.status_code} => {resp.text[:500]}")
        
        url2 = f"https://www.kaggle.com/api/v1/kernels/{username}/cartoon-backend-server"
        resp2 = requests.get(url2, auth=(username, token))
        print(f"cartoon-backend-server: {resp2.status_code} => {resp2.text[:500]}")
        
        # List all kernels
        url3 = "https://www.kaggle.com/api/v1/kernels/list?mine=true&pageSize=5"
        resp3 = requests.get(url3, auth=(username, token))
        print(f"All kernels: {resp3.status_code} => {resp3.text[:1000]}")

if __name__ == "__main__":
    with app.run():
        check_kaggle_api.remote()
