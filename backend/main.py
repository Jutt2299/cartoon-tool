from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import httpx
import os
import json
from datetime import datetime

from database import Session, KaggleAccount, ElevenLabsKey, get_db
from kaggle_manager import kaggle_manager
from script_parser import script_parser
from elevenlabs import elevenlabs_manager

app = FastAPI()

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
# Video Generation Routes
# ─────────────────────────────────────

@app.post("/generate")
async def generate_episode(request: ScriptRequest):
    """Complete episode generate karo"""
    
    try:
        # Step 1: Script parse karo
        print("Script parse ho rahi hai...")
        scenes = script_parser.process_script(request.script_text)
        print(f"Total scenes: {len(scenes)}")
        
        # Step 2: Active Kaggle URL lo
        kaggle_url = kaggle_manager.get_active_url()
        if not kaggle_url:
            raise HTTPException(
                status_code=400,
                detail="Kaggle session active nahi hai! Pehle Start Session dabao."
            )
        
        results = []
        
        for scene in scenes:
            print(f"Scene {scene['scene_number']} process ho rahi hai...")
            
            # Step 3: Video generate karo (Kaggle se)
            video_response = await httpx.AsyncClient().post(
                f"{kaggle_url}/generate",
                json={
                    "prompt": scene["video_prompt"],
                    "scene_id": scene["scene_number"]
                },
                timeout=300  # 5 min per scene
            )
            
            # Step 4: Audio generate karo (ElevenLabs se)
            audio_files = elevenlabs_manager.process_scene_audio(scene)
            
            results.append({
                "scene_number": scene["scene_number"],
                "video_status": video_response.json(),
                "audio_count": len(audio_files)
            })
        
        return {
            "status": "success",
            "episode": request.episode_name,
            "total_scenes": len(scenes),
            "scenes": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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