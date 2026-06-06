import requests

BACKEND = 'https://irfangull2288--cartoon-backend-fastapi-modal-app.modal.run'
API_KEY = 'sk_90e4776a38453d4208d84c37053641b462a511d6be7f6450'

print("Testing ElevenLabs key directly...")
r = requests.get('https://api.elevenlabs.io/v1/user/subscription',
    headers={'xi-api-key': API_KEY})
print(f"ElevenLabs direct check: {r.status_code}")
print(r.text[:300])

print("\nAdding to backend...")
r2 = requests.post(f'{BACKEND}/settings/elevenlabs/add',
    json={'api_key': API_KEY},
    headers={'Content-Type': 'application/json'})
print(f"Backend status: {r2.status_code}")
print(r2.text[:300])
