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
    "moviepy==1.0.3", "Pillow", "googletrans==4.0.0-rc1", "google-generativeai"
).add_local_dir(".", remote_path="/root"
).add_local_dir("../kaggle_notebook", remote_path="/kaggle_notebook")
volume = modal.NetworkFileSystem.from_name("cartoon-db-nfs", create_if_missing=True)

@modal_app.function(image=image, network_file_systems={"/data": volume})
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

@app.on_event("startup")
def startup_event():
    from database import Base, engine
    try:
        Base.metadata.create_all(engine)
        print("Database tables initialized successfully on mounted volume.")
    except Exception as e:
        print(f"Failed to initialize database tables: {e}")

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

class GlobalSettingsRequest(BaseModel):
    ngrok_token: str
    hf_token: str
    gemini_api_key: str = ""

class RegisterURLRequest(BaseModel):
    account_username: str
    url: str

# ─────────────────────────────────────
# Global Settings Routes
# ─────────────────────────────────────
@app.post("/settings/global")
async def save_global_settings(request: GlobalSettingsRequest):
    from database import GlobalSettings
    db = Session()
    settings = db.query(GlobalSettings).first()
    if not settings:
        settings = GlobalSettings(
            ngrok_token=request.ngrok_token,
            hf_token=request.hf_token,
            gemini_api_key=request.gemini_api_key
        )
        db.add(settings)
    else:
        settings.ngrok_token = request.ngrok_token
        settings.hf_token = request.hf_token
        settings.gemini_api_key = request.gemini_api_key
    db.commit()
    db.close()
    return {"status": "saved"}

@app.get("/settings/global")
async def get_global_settings():
    from database import GlobalSettings
    db = Session()
    settings = db.query(GlobalSettings).first()
    db.close()
    if settings:
        return {
            "ngrok_token": settings.ngrok_token, 
            "hf_token": settings.hf_token,
            "gemini_api_key": settings.gemini_api_key or ""
        }
    return {"ngrok_token": "", "hf_token": "", "gemini_api_key": ""}

# ─────────────────────────────────────
# Session Routes
# ─────────────────────────────────────

@app.post("/session/start")
async def start_session():
    """Best Kaggle account (most GPU hours remaining) pe session start karo"""
    try:
        from datetime import datetime, timedelta
        import time
        db = Session()
        accounts = db.query(KaggleAccount).all()
        
        # Weekly reset check (Kaggle har Sunday reset karta hai)
        now = datetime.now()
        for acc in accounts:
            if acc.last_reset:
                try:
                    last_reset_dt = datetime.fromisoformat(acc.last_reset)
                    # 7 din se zyada ho gaya toh reset
                    if (now - last_reset_dt).days >= 7:
                        acc.hours_used = 0
                        acc.last_reset = now.isoformat()
                except:
                    pass
            else:
                acc.last_reset = now.isoformat()
        db.commit()
        
        # Best account choose karo (sabse zyada hours remaining)
        best_account = None
        best_hours_left = -1
        for acc in accounts:
            hours_left = max(0, 30 - (acc.hours_used or 0))
            if hours_left > best_hours_left:
                best_hours_left = hours_left
                best_account = acc
        
        db.close()
        
        if not best_account:
            raise HTTPException(status_code=400, detail="Koi Kaggle account nahi mila!")
        
        if best_hours_left < 0.5:
            raise HTTPException(status_code=400, detail="Tamam Kaggle accounts ka GPU quota khatam ho gaya! (Weekly reset Sunday ko hoga)")
        
        result = kaggle_manager.start_session(preferred_username=best_account.username)
        return result
    except HTTPException:
        raise
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

@modal_app.function(image=image, network_file_systems={"/data": volume}, timeout=86400) # 24 hours timeout
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
    import time
    db = Session()
    job = None
    for _ in range(3):
        try:
            job = db.query(Job).filter_by(id=job_id).first()
            break
        except Exception as e:
            db.close()
            db = Session()
            time.sleep(1)
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

@app.delete("/history/{episode_id}")
async def delete_history_episode(episode_id: int):
    """Ek specific history episode delete karo"""
    import shutil
    db = Session()
    episode = db.query(EpisodeHistory).filter_by(id=episode_id).first()
    if not episode:
        db.close()
        raise HTTPException(status_code=404, detail="Episode nahi mila!")
    
    # Delete media files from volume
    if episode.video_url:
        parts = episode.video_url.split("/")
        if len(parts) >= 3:
            folder_name = parts[2]
            folder_path = f"/data/media/{folder_name}"
            if os.path.exists(folder_path):
                try:
                    shutil.rmtree(folder_path)
                except:
                    pass
    
    db.delete(episode)
    db.commit()
    db.close()
    return {"status": "deleted", "id": episode_id}

@app.delete("/history")
async def delete_all_history():
    """Saari history delete karo"""
    import shutil
    db = Session()
    all_episodes = db.query(EpisodeHistory).all()
    
    for episode in all_episodes:
        if episode.video_url:
            parts = episode.video_url.split("/")
            if len(parts) >= 3:
                folder_name = parts[2]
                folder_path = f"/data/media/{folder_name}"
                if os.path.exists(folder_path):
                    try:
                        shutil.rmtree(folder_path)
                    except:
                        pass
        db.delete(episode)
    
    db.commit()
    db.close()
    return {"status": "all_deleted"}

# ─────────────────────────────────────
# Settings Routes
# ─────────────────────────────────────

@app.post("/settings/kaggle/add")
async def add_kaggle_account(request: KaggleAccountRequest):
    """Naya Kaggle account add karo aur auto-setup karo"""
    db = Session()
    
    # Check karo already hai ya nahi
    existing = db.query(KaggleAccount).filter_by(
        username=request.username
    ).first()
    
    if existing:
        db.close()
        raise HTTPException(status_code=400, detail="Account already exists!")
        
    try:
        # Auto Setup: Create and push Kaggle notebook
        kaggle_manager.auto_setup_notebook(request.username, request.token)
    except Exception as e:
        db.close()
        raise HTTPException(status_code=400, detail=f"Kaggle Setup Failed: {str(e)}")
    
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
    
    return {"status": "added", "username": request.username, "message": "Notebook auto-setup complete!"}

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
    """Naya ElevenLabs key add karo and verify karo"""
    db = Session()
    
    existing = db.query(ElevenLabsKey).filter_by(
        api_key=request.api_key
    ).first()
    
    if existing:
        db.close()
        raise HTTPException(status_code=400, detail="API Key already exists!")
        
    # Verify the key using the manager
    from elevenlabs import elevenlabs_manager
    verification = elevenlabs_manager.verify_key(request.api_key)
    
    if not verification.get("valid"):
        db.close()
        raise HTTPException(status_code=400, detail=f"Invalid API Key: {verification.get('error', 'Unknown error')}")
    
    # Save with character counts from verification
    chars_used = verification.get("chars_used", 0)
    
    key = ElevenLabsKey(
        api_key=request.api_key,
        chars_used=chars_used,
        is_active=1
    )
    db.add(key)
    db.commit()
    db.close()
    
    return {
        "status": "added", 
        "chars_remaining": verification.get("chars_remaining", 10000 - chars_used),
        "message": "Key verified successfully!"
    }

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
async def get_status():
    from elevenlabs import elevenlabs_manager
    from database import GlobalSettings
    import time
    db = Session()
    
    # Kaggle accounts
    kaggle_accounts = []
    records = db.query(KaggleAccount).all()
    current_time = time.time()
    
    for r in records:
        # Weekly reset check
        if r.last_reset:
            try:
                from datetime import datetime as dt2
                last_reset_dt = dt2.fromisoformat(r.last_reset)
                if (dt2.now() - last_reset_dt).days >= 7:
                    r.hours_used = 0
                    r.last_reset = dt2.now().isoformat()
            except:
                pass
        
        if r.is_active == 1:
            # Calculate elapsed time since last poll
            if r.last_poll_time and r.last_poll_time > 0:
                elapsed_secs = current_time - r.last_poll_time
                elapsed_hours = elapsed_secs / 3600.0
                r.hours_used = (r.hours_used or 0) + elapsed_hours
            
            r.last_poll_time = current_time
            db.commit()
            
        hours_used = r.hours_used or 0
        hours_remaining = max(0, 30 - hours_used)
        kaggle_accounts.append({
            "username": r.username,
            "token": r.token,
            "hours_used": round(hours_used, 2),
            "hours_remaining": round(hours_remaining, 2),
            "is_active": r.is_active,
            "ngrok_url": r.ngrok_url
        })
        
    # Global settings
    global_set = db.query(GlobalSettings).first()
    global_settings = {}
    if global_set:
        global_settings = {
            "ngrok_token": global_set.ngrok_token,
            "hf_token": global_set.hf_token,
            "gemini_api_key": global_set.gemini_api_key or ""
        }
    
    db.close()
    
    # Live fetch for ElevenLabs
    db2 = Session()
    from database import ElevenLabsKey
    keys = db2.query(ElevenLabsKey).all()
    for k in keys:
        live_stats = elevenlabs_manager.verify_key(k.api_key)
        if live_stats.get("valid"):
            k.chars_used = live_stats.get("chars_used", k.chars_used)
    db2.commit()
    db2.close()
    
    elevenlabs_keys = elevenlabs_manager.get_keys_status()
    
    return {
        "status": "ok",
        "kaggle_accounts": kaggle_accounts,
        "elevenlabs_keys": elevenlabs_keys,
        "global_settings": global_settings
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