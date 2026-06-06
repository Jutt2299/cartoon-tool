import requests

BACKEND = 'https://irfangull2288--cartoon-backend-fastapi-modal-app.modal.run'

print("Starting session...")
r = requests.post(f'{BACKEND}/session/start')
print(f"Status: {r.status_code}")
print(f"Response: {r.text}")

print("\nChecking status after start...")
r2 = requests.get(f'{BACKEND}/settings/status')
data = r2.json()
for a in data.get('kaggle_accounts', []):
    print(f"  {a['username']}: is_active={a['is_active']}, ngrok_url={a['ngrok_url']}")
