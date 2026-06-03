from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import httpx
import os
import json
from datetime import datetime

from database import Session, KaggleAccount, ElevenLabsKey, get_db, EpisodeHistory
from kaggle_manager import kaggle_manager
from script_parser import script_parser
from elevenlabs import elevenlabs_manager

app = FastAPI()

# ─────────────────────────────────────
# Modal Cloud Deployment Wrapper
# ─────────────────────────────────────
import modal

modal_app = modal.App("cartoon-backend")
image = modal.Image.debian_slim().apt_install(
    "ffmpeg", "imagemagick"
).pip_install(
    "fastapi", "uvicorn", "sqlalchemy", "httpx", 
    "kaggle", "requests", "python-dotenv", "aiofiles", "pydantic",
    "moviepy==1.0.3", "Pillow", "googletrans==4.0.0-rc1"
).add_local_dir(".", remote_path="/root")
volume = modal.Volume.from_name("cartoon-db-volume", create_if_missing=True)

@modal_app.function(image=image, volumes={"/data": volume})
@modal.asgi_app()
def fastapi_modal_app():
    return app
# ─────────────────────────────────────

# CORS — Frontend se connection allow karo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────
# Models
# ─────────────────────────────────────

class ScriptRequest(BaseModel):
    script_text: str
    episode_name: str

class KaggleAccountRequest(BaseModel):
    username: str
    token: str

class ElevenLabsKeyRequest(BaseModel):
    api_key: str

class RegisterURLRequest(BaseModel):
    account_username: str
    url: str

# ─────────────────────────────────────
# Session Routes
# ─────────────────────────────────────

@app.post("/session/start")
async def start_session():
    """Best Kaggle account pe session start karo"""
    try:
        result = kaggle_manager.start_session()
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/session/stop")
async def stop_session():
    """Active session band karo"""
    try:
        result = kaggle_manager.stop_session()
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/session/status")
async def session_status():
    """Sare accounts ka status lo"""
    try:
        accounts = kaggle_manager.check_time_remaining()
        return {"accounts": accounts}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/session/register-url")
async def register_url(request: RegisterURLRequest):
    """Kaggle notebook se URL receive karo"""
    try:
        result = kaggle_manager.register_url(
            request.account_username,
            request.url
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─────────────────────────────────────
# Media File Serving (Videos, Thumbnails, Shorts)
# ─────────────────────────────────────

@app.get("/media/{episode_id}/{filename}")
async def serve_media(episode_id: str, filename: str):
    """Serve video/thumbnail/shorts files from Modal volume"""
    media_dir = "/data/media" if os.path.exists("/data") else "/tmp/media"
    file_path = os.path.join(media_dir, episode_id, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

# ─────────────────────────────────────
# Video Generation Routes
# ─────────────────────────────────────

from database import Job
import time

@modal_app.function(image=image, volumes={"/data": volume}, timeout=86400) # 24 hours timeout
def background_generate_episode(job_id: str, script_text: str, episode_name: str):
    """Background task running on Modal to generate the video."""
    db = Session()
    job = db.query(Job).filter_by(id=job_id).first()
    if not job:
        db.close()
        return

    try:
        job.status = "processing"
        job.progress = 10
        job.progress_msg = "Parsing script..."
        db.commit()

        print(f"[{job_id}] Script parse ho rahi hai...")
        scenes = script_parser.process_script(script_text)
        
        job.progress = 30
        job.progress_msg = "Generating video (captions & rendering)..."
        db.commit()

        print(f"[{job_id}] Processing full pipeline...")
        episode_id = f"ep_{int(datetime.now().timestamp())}"
        output_dir = f"/data/media/{episode_id}"
        
        import video_processor
        
        # This takes the longest time
        media_results = video_processor.process_full_pipeline(
            episode_name, scenes, output_dir
        )
        
        video_url = f"/media/{episode_id}/final_video.mp4"
        thumbnail_url = f"/media/{episode_id}/thumbnail.jpg"
        shorts_urls = [f"/media/{episode_id}/short_0.mp4", f"/media/{episode_id}/short_1.mp4"]
        
        job.progress = 90
        job.progress_msg = "Saving to database..."
        db.commit()

        # Save to EpisodeHistory
        history = EpisodeHistory(
            title=episode_name,
            video_url=video_url,
            thumbnail_url=thumbnail_url,
            shorts_urls=json.dumps(shorts_urls),
            created_at=datetime.now().isoformat()
        )
        db.add(history)
        
        # Update Job
        job.status = "done"
        job.progress = 100
        job.progress_msg = "Completed successfully!"
        job.video_url = video_url
        job.thumbnail_url = thumbnail_url
        job.shorts_urls = json.dumps(shorts_urls)
        job.updated_at = datetime.now().isoformat()
        db.commit()
        
        # Cleanup old episodes (keep last 5)
        import shutil
        total_episodes = db.query(EpisodeHistory).count()
        if total_episodes > 5:
            episodes_to_delete = db.query(EpisodeHistory).order_by(EpisodeHistory.id.asc()).limit(total_episodes - 5).all()
            for ep in episodes_to_delete:
                if ep.video_url:
                    parts = ep.video_url.split("/")
                    if len(parts) >= 3:
                        folder_name = parts[2]
                        folder_path = f"/data/media/{folder_name}"
                        if os.path.exists(folder_path):
                            try:
                                shutil.rmtree(folder_path)
                            except:
                                pass
                db.delete(ep)
            db.commit()
            
    except Exception as e:
        print(f"[{job_id}] Error: {str(e)}")
        job.status = "error"
        job.error = str(e)
        job.progress_msg = "Failed"
        db.commit()
    finally:
        db.close()


@app.post("/generate")
async def generate_episode(request: ScriptRequest):
    """Start background episode generation"""
    job_id = f"job_{int(datetime.now().timestamp())}"
    
    db = Session()
    new_job = Job(
        id=job_id,
        episode_name=request.episode_name,
        status="pending",
        progress=0,
        progress_msg="Queued...",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    db.add(new_job)
    db.commit()
    db.close()
    
    # Run the generation in the background using Modal
    background_generate_episode.spawn(job_id, request.script_text, request.episode_name)
    
    return {
        "status": "queued",
        "job_id": job_id,
        "message": "Video generation started in the background."
    }

@app.get("/job/{job_id}/status")
async def get_job_status(job_id: str):
    """Check the status of a generation job"""
    db = Session()
    job = db.query(Job).filter_by(id=job_id).first()
    if not job:
        db.close()
        raise HTTPException(status_code=404, detail="Job not found")
        
    response = {
        "job_id": job.id,
        "episode_name": job.episode_name,
        "status": job.status,
        "progress": job.progress,
        "progress_msg": job.progress_msg,
        "error": job.error,
        "video_url": job.video_url,
        "thumbnail_url": job.thumbnail_url,
        "shorts_urls": json.loads(job.shorts_urls) if job.shorts_urls else []
    }
    db.close()
    return response

@app.get("/history")
async def get_history():
    db = Session()
    records = db.query(EpisodeHistory).order_by(EpisodeHistory.id.desc()).all()
    results = []
    for r in records:
        results.append({
            "id": r.id,
            "title": r.title,
            "video_url": r.video_url,
            "thumbnail_url": r.thumbnail_url,
            "shorts_urls": json.loads(r.shorts_urls) if r.shorts_urls else [],
            "created_at": r.created_at
        })
    db.close()
    return {"history": results}

# ─────────────────────────────────────
# Settings Routes
# ─────────────────────────────────────

@app.post("/settings/kaggle/add")
async def add_kaggle_account(request: KaggleAccountRequest):
    """Naya Kaggle account add karo"""
    db = Session()
    
    # Check karo already hai ya nahi
    existing = db.query(KaggleAccount).filter_by(
        username=request.username
    ).first()
    
    if existing:
        db.close()
        raise HTTPException(status_code=400, detail="Account already exists!")
    
    account = KaggleAccount(
        username=request.username,
        token=request.token,
        hours_used=0,
        last_reset=datetime.now().isoformat(),
        is_active=0
    )
    db.add(account)
    db.commit()
    db.close()
    
    return {"status": "added", "username": request.username}

@app.delete("/settings/kaggle/{username}")
async def delete_kaggle_account(username: str):
    """Kaggle account delete karo"""
    db = Session()
    account = db.query(KaggleAccount).filter_by(username=username).first()
    
    if not account:
        db.close()
        raise HTTPException(status_code=404, detail="Account nahi mila!")
    
    db.delete(account)
    db.commit()
    db.close()
    
    return {"status": "deleted"}

@app.post("/settings/elevenlabs/add")
async def add_elevenlabs_key(request: ElevenLabsKeyRequest):
    """Naya ElevenLabs key add karo"""
    db = Session()
    
    key = ElevenLabsKey(
        api_key=request.api_key,
        chars_used=0,
        is_active=1
    )
    db.add(key)
    db.commit()
    db.close()
    
    return {"status": "added"}

@app.delete("/settings/elevenlabs/{key_id}")
async def delete_elevenlabs_key(key_id: int):
    """ElevenLabs key delete karo"""
    db = Session()
    key = db.query(ElevenLabsKey).filter_by(id=key_id).first()
    
    if not key:
        db.close()
        raise HTTPException(status_code=404, detail="Key nahi mili!")
    
    db.delete(key)
    db.commit()
    db.close()
    
    return {"status": "deleted"}

@app.get("/settings/status")
async def get_all_status():
    """Sab kuch ka status ek jagah"""
    
    kaggle_accounts = kaggle_manager.check_time_remaining()
    elevenlabs_keys = elevenlabs_manager.get_keys_status()
    
    return {
        "kaggle_accounts": kaggle_accounts,
        "elevenlabs_keys": elevenlabs_keys
    }

# ─────────────────────────────────────
# Health Check
# ─────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "Cartoon Tool Backend Chal Raha Hai! ✅"}

@app.get("/health")
async def health():
    return {"status": "alive", "time": datetime.now().isoformat()}