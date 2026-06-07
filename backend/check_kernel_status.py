import modal
import sqlite3
import os
import subprocess

app = modal.App("cartoon-backend")
volume = modal.NetworkFileSystem.from_name("cartoon-db-nfs", create_if_missing=True)

@app.function(
    network_file_systems={"/data": volume},
    image=modal.Image.debian_slim().pip_install("kaggle")
)
def check_kaggle_list():
    conn = sqlite3.connect('/data/cartoon_v2.db')
    cur = conn.cursor()
    cur.execute('SELECT username, token FROM kaggle_accounts WHERE is_active=1')
    account = cur.fetchone()
    conn.close()
    
    if not account:
        print("No active Kaggle account found in DB.")
        return
        
    username, token = account
    print(f"Active account: {username}")
    
    os.environ["KAGGLE_USERNAME"] = username
    os.environ["KAGGLE_KEY"] = token
    
    print("\n--- Running Kaggle kernels list ---")
    result = subprocess.run(["kaggle", "kernels", "list", "--mine", "-v"], capture_output=True, text=True)
    print("Stdout:")
    print(result.stdout)
    if result.stderr:
        print("Stderr:", result.stderr)

if __name__ == "__main__":
    with app.run():
        check_kaggle_list.remote()
