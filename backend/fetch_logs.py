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
def fetch_logs():
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
    
    print(f"Fetching logs for: {username}")
    res = subprocess.run(
        ["kaggle", "kernels", "output", f"{username}/cartoon-video-generator", "-p", "/tmp/logs"],
        capture_output=True, text=True
    )
    print("Download Output:", res.stdout)
    print("Download Error:", res.stderr)
    
    if os.path.exists("/tmp/logs/cartoon-video-generator.log"):
        with open("/tmp/logs/cartoon-video-generator.log", "r") as f:
            log_content = f.read()
        print("--- KERNEL LOG ---")
        print(log_content[-2000:])
    else:
        print("Log file not found. Files in /tmp/logs:")
        os.system("ls -la /tmp/logs")

if __name__ == "__main__":
    with app.run():
        fetch_logs.remote()
