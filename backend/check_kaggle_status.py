import modal
import os
import subprocess
import sqlite3

app = modal.App("cartoon-backend")
volume = modal.NetworkFileSystem.from_name("cartoon-db-nfs", create_if_missing=True)

@app.function(
    network_file_systems={"/data": volume},
    image=modal.Image.debian_slim().pip_install("kaggle")
)
def check_status():
    conn = sqlite3.connect('/data/cartoon_v2.db')
    cur = conn.cursor()
    cur.execute('SELECT username, token FROM kaggle_accounts WHERE is_active=1')
    row = cur.fetchone()
    conn.close()
    
    if not row:
        print("No active account.")
        return
        
    username, token = row
    os.environ["KAGGLE_USERNAME"] = username
    os.environ["KAGGLE_KEY"] = token
    
    print(f"Checking status for: {username}")
    res = subprocess.run(
        ["kaggle", "kernels", "status", f"{username}/cartoon-video-generator"],
        capture_output=True, text=True
    )
    print("Status Output:")
    print(res.stdout)
    print("Status Error:")
    print(res.stderr)

if __name__ == "__main__":
    with app.run():
        check_status.remote()
