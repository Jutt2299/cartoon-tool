import requests

r = requests.get('https://irfangull2288--cartoon-backend-fastapi-modal-app.modal.run/settings/status')
data = r.json()
accounts = data.get('kaggle_accounts', [])
print(f'Total accounts: {len(accounts)}')
for a in accounts:
    print(f"  {a['username']}: hours_used={a['hours_used']}, is_active={a['is_active']}")
