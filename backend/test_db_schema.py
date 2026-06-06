import modal
import sqlite3
import os

app = modal.App("cartoon-backend")
volume = modal.NetworkFileSystem.from_name("cartoon-db-nfs", create_if_missing=True)

@app.function(network_file_systems={"/data": volume})
def check_db():
    print(f"/data exists: {os.path.exists('/data')}")
    print(f"MODAL_IMAGE_ID: {os.environ.get('MODAL_IMAGE_ID')}")
    try:
        conn = sqlite3.connect('/data/cartoon_v2.db')
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(kaggle_accounts)")
        columns = cur.fetchall()
        print("kaggle_accounts columns:", [c[1] for c in columns])
        
        cur.execute("PRAGMA table_info(global_settings)")
        columns = cur.fetchall()
        print("global_settings columns:", [c[1] for c in columns])
        conn.close()
    except Exception as e:
        print("Error checking /data/cartoon_v2.db:", e)

    try:
        conn = sqlite3.connect('cartoon_v2.db')
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(kaggle_accounts)")
        columns = cur.fetchall()
        print("LOCAL cartoon_v2.db columns:", [c[1] for c in columns])
        conn.close()
    except Exception as e:
        print("Error checking local cartoon_v2.db:", e)

if __name__ == "__main__":
    with app.run():
        check_db.remote()
