import modal
import sqlite3

app = modal.App("cartoon-backend")
volume = modal.NetworkFileSystem.from_name("cartoon-db-nfs", create_if_missing=True)

@app.function(network_file_systems={"/data": volume})
def check_ngrok():
    conn = sqlite3.connect('/data/cartoon_v2.db')
    cur = conn.cursor()
    cur.execute('SELECT username, is_active, ngrok_url FROM kaggle_accounts')
    for row in cur.fetchall():
        print(row)
    conn.close()

if __name__ == "__main__":
    with app.run():
        check_ngrok.remote()
