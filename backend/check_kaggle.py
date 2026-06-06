import requests

BACKEND = 'https://irfangull2288--cartoon-backend-fastapi-modal-app.modal.run'

# Check status
r = requests.get(f'{BACKEND}/settings/status')
data = r.json()
for a in data.get('kaggle_accounts', []):
    print(f"Account: {a['username']}, active={a['is_active']}, ngrok={a['ngrok_url']}")

# Check if ngrok URL actually responds
ngrok_url = None
for a in data.get('kaggle_accounts', []):
    if a['ngrok_url']:
        ngrok_url = a['ngrok_url']

if ngrok_url:
    print(f"\nTesting ngrok: {ngrok_url}")
    try:
        r2 = requests.get(f'{ngrok_url}/health', timeout=10)
        print(f"Kaggle health: {r2.status_code} - {r2.text}")
    except Exception as e:
        print(f"Kaggle NOT reachable: {e}")
else:
    print("No ngrok URL found")
