import modal
import sqlite3
import subprocess
import os
import json

app = modal.App("cartoon-backend")
volume = modal.NetworkFileSystem.from_name("cartoon-db-nfs", create_if_missing=True)

@app.function(network_file_systems={"/data": volume})
def check_kaggle_status():
    conn = sqlite3.connect('/data/cartoon_v2.db')
    cur = conn.cursor()
    cur.execute('SELECT username, token FROM kaggle_accounts')
    accounts = cur.fetchall()
    conn.close()
    
    for username, token in accounts:
        print(f"\n--- Checking Kaggle for: {username} ---")
        os.environ["KAGGLE_USERNAME"] = username
        os.environ["KAGGLE_KEY"] = token
        
        # Check kernel status
        result = subprocess.run(
            ["kaggle", "kernels", "list", "--mine", "--csv"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("Kernels found:")
            print(result.stdout[:2000])
        else:
            print("Error:", result.stderr[:500])
            
        # Check specific kernel status
        result2 = subprocess.run(
            ["kaggle", "kernels", "status", f"{username}/cartoon-video-generator"],
            capture_output=True, text=True
        )
        print(f"Kernel status ({username}/cartoon-video-generator):")
        print(result2.stdout or result2.stderr)

if __name__ == "__main__":
    with app.run():
        check_kaggle_status.remote()
