import modal
from main import app as fastapi_app

app = modal.App("cartoon-backend")

image = modal.Image.debian_slim().apt_install(
    "ffmpeg", "imagemagick"
).pip_install(
    "fastapi", "uvicorn", "sqlalchemy", "httpx", 
    "kaggle", "requests", "python-dotenv", "aiofiles", "pydantic",
    "moviepy==1.0.3", "Pillow", "googletrans==4.0.0-rc1", "openai-whisper"
)

volume = modal.Volume.from_name("cartoon-db-volume", create_if_missing=True)

@app.function(image=image, volumes={"/data": volume})
@modal.asgi_app()
def fastapi_modal_app():
    return fastapi_app
