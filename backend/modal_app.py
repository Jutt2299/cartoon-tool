import modal
from main import app as fastapi_app

app = modal.App("cartoon-backend")

image = modal.Image.debian_slim().pip_install(
    "fastapi", "uvicorn", "sqlalchemy", "httpx", 
    "kaggle", "requests", "python-dotenv", "aiofiles", "pydantic"
)

volume = modal.Volume.from_name("cartoon-db-volume", create_if_missing=True)

@app.function(image=image, volumes={"/data": volume})
@modal.asgi_app()
def fastapi_modal_app():
    return fastapi_app
