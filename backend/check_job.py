import requests

BACKEND = 'https://irfangull2288--cartoon-backend-fastapi-modal-app.modal.run'

# Check latest job status
r = requests.get(f'{BACKEND}/job/job_1780515884/status')
print("Job status:", r.json())
