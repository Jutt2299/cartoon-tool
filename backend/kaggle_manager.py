import subprocess
import json
import os
import httpx
from datetime import datetime, timedelta
from database import Session, KaggleAccount

class KaggleManager:
    
    def get_best_account(self):
        """Sabse zyada time bacha ho us account ko choose karo"""
        db = Session()
        accounts = db.query(KaggleAccount).all()
        
        # Weekly reset check karo
        for acc in accounts:
            if acc.last_reset:
                last_reset = datetime.fromisoformat(acc.last_reset)
                if datetime.now() - last_reset > timedelta(weeks=1):
                    acc.hours_used = 0
                    acc.last_reset = datetime.now().isoformat()
            else:
                acc.last_reset = datetime.now().isoformat()
        
        db.commit()
        
        # Available accounts — jinke paas time bacha ho
        available = [a for a in accounts if a.hours_used < 30]
        
        if not available:
            db.close()
            raise Exception("Sare Kaggle accounts ka time khatam! Agli hafte reset hoga.")
        
        # Sabse zyada time bacha ho us account ko lo
        best = max(available, key=lambda x: 30 - x.hours_used)
        db.close()
        return best
    
    def start_session(self):
        """Best account pe notebook start karo"""
        db = Session()
        
        # Pehle check karo koi already active toh nahi
        active = db.query(KaggleAccount).filter_by(is_active=1).first()
        if active:
            db.close()
            return {"status": "already_running", "account": active.username}
        
        # Best account choose karo
        account = self.get_best_account()
        
        # Kaggle credentials set karo
        os.environ["KAGGLE_USERNAME"] = account.username
        os.environ["KAGGLE_KEY"] = account.token
        
        # Notebook push/run karo
        try:
            subprocess.run([
                "kaggle", "kernels", "push",
                "-p", f"./kaggle_notebook"
            ], check=True)
            
            # Active mark karo
            account.is_active = 1
            account.hours_used += 0  # Track baad mein
            db.commit()
            db.close()
            
            return {
                "status": "started",
                "account": account.username
            }
            
        except Exception as e:
            db.close()
            raise Exception(f"Session start nahi hua: {str(e)}")
    
    def stop_session(self):
        """Active session band karo"""
        db = Session()
        active = db.query(KaggleAccount).filter_by(is_active=1).first()
        
        if not active:
            db.close()
            return {"status": "no_active_session"}
        
        # Hours calculate karo
        # (baad mein start time track karenge)
        active.is_active = 0
        active.ngrok_url = None
        db.commit()
        db.close()
        
        return {"status": "stopped", "account": active.username}
    
    def register_url(self, account_username: str, url: str):
        """Kaggle notebook se URL receive karo"""
        db = Session()
        account = db.query(KaggleAccount).filter_by(
            username=account_username
        ).first()
        
        if account:
            account.ngrok_url = url
            db.commit()
        
        db.close()
        return {"status": "url_registered", "url": url}
    
    def get_active_url(self):
        """Active Kaggle session ka URL lo"""
        db = Session()
        active = db.query(KaggleAccount).filter_by(is_active=1).first()
        
        if not active or not active.ngrok_url:
            db.close()
            return None
        
        url = active.ngrok_url
        db.close()
        return url
    
    def check_time_remaining(self):
        """Har account ka time check karo"""
        db = Session()
        accounts = db.query(KaggleAccount).all()
        
        result = []
        for acc in accounts:
            result.append({
                "username": acc.username,
                "hours_used": acc.hours_used,
                "hours_remaining": 30 - acc.hours_used,
                "is_active": acc.is_active,
                "ngrok_url": acc.ngrok_url
            })
        
        db.close()
        return result

    def auto_setup_notebook(self, username: str, token: str):
        """Auto setup Kaggle notebook for a new account"""
        import tempfile
        import os
        import json
        import subprocess
        from database import Session, GlobalSettings
        
        # 1. Fetch Global Settings
        db = Session()
        global_set = db.query(GlobalSettings).first()
        ngrok_token = global_set.ngrok_token if global_set else os.environ.get("NGROK_TOKEN", "")
        hf_token = global_set.hf_token if global_set else os.environ.get("HF_TOKEN", "")
        db.close()
        
        # 2. Temporarily set Kaggle creds
        os.environ["KAGGLE_USERNAME"] = username
        os.environ["KAGGLE_KEY"] = token
        
        # 3. Create temp dir with notebook files
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata = {
                "id": f"{username}/cartoon-video-generator",
                "title": "Cartoon Video Generator",
                "code_file": "notebook.ipynb",
                "language": "python",
                "kernel_type": "notebook",
                "is_private": True,
                "enable_gpu": True,
                "enable_internet": True
            }
            with open(os.path.join(tmpdir, "kernel-metadata.json"), "w") as f:
                json.dump(metadata, f, indent=2)
                
            # Copy template notebook and inject tokens
            try:
                # First try to read from the main kaggle_notebook dir if available
                # In Modal it might be ../kaggle_notebook/notebook.ipynb
                import os
                nb_path = "/kaggle_notebook/notebook.ipynb"
                if not os.path.exists(nb_path):
                    nb_path = "../kaggle_notebook/notebook.ipynb"
                    if not os.path.exists(nb_path):
                        nb_path = "kaggle_notebook/notebook.ipynb"
                        
                with open(nb_path, "r") as f:
                    notebook_content_str = f.read()
                    
                # Replace placeholders
                notebook_content_str = notebook_content_str.replace("[HF_TOKEN]", hf_token)
                notebook_content_str = notebook_content_str.replace("__HF_TOKEN_PLACEHOLDER__", hf_token)
                
                notebook_content_str = notebook_content_str.replace("[NGROK_TOKEN]", ngrok_token)
                notebook_content_str = notebook_content_str.replace("__NGROK_TOKEN_PLACEHOLDER__", ngrok_token)
                
                notebook_content = json.loads(notebook_content_str)
                
            except Exception as e:
                print(f"Template load failed: {e}. Falling back to inline.")
                # The notebook content (fallback inline version)
                notebook_content = {
                    "cells": [
                        {
                        "cell_type": "code",
                        "execution_count": None,
                        "metadata": {},
                        "outputs": [],
                        "source": [
                            "# CELL 1 - Install dependencies\n",
                            "!pip install torch diffusers transformers accelerate\n",
                            "!pip install fastapi uvicorn pyngrok\n",
                            "!pip install opencv-python pillow numpy huggingface_hub"
                        ]
                        },
                        {
                        "cell_type": "code",
                        "execution_count": None,
                        "metadata": {},
                        "outputs": [],
                        "source": [
                            "# CELL 2 - Download Wan2.1 model\n",
                            "import os\n",
                            "from huggingface_hub import snapshot_download\n",
                            "from kaggle_secrets import UserSecretsClient\n",
                            "\n",
                            "try:\n",
                            "    user_secrets = UserSecretsClient()\n",
                            "    hf_token = user_secrets.get_secret(\"HF_TOKEN\")\n",
                            "except:\n",
                            f"    hf_token = os.environ.get(\"HF_TOKEN\", \"{hf_token}\")\n",
                            "\n",
                            "print(\"Downloading Wan2.1 model...\")\n",
                            "model_id = \"Wan-AI/Wan2.1-T2V-1.3B\"\n",
                            "local_dir = \"/kaggle/working/wan-model\"\n",
                            "if hf_token:\n",
                            "    snapshot_download(repo_id=model_id, local_dir=local_dir, token=hf_token)\n",
                            "else:\n",
                            "    # Attempt without token (might work if model is public)\n",
                            "    snapshot_download(repo_id=model_id, local_dir=local_dir)\n",
                            "print(\"Model downloaded successfully!\")"
                        ]
                        },
                        {
                        "cell_type": "code",
                        "execution_count": None,
                        "metadata": {},
                        "outputs": [],
                        "source": [
                            "# CELL 3 - Start FastAPI server\n",
                            "import asyncio\n",
                            "import threading\n",
                            "import uvicorn\n",
                            "import os\n",
                            "from fastapi import FastAPI, HTTPException\n",
                            "from pydantic import BaseModel\n",
                            "import time\n",
                            "\n",
                            "app = FastAPI()\n",
                            "\n",
                            "last_activity = time.time()\n",
                            "IDLE_TIMEOUT = 5 * 60  # 5 minutes in seconds\n",
                            "\n",
                            "class GenerateRequest(BaseModel):\n",
                            "    prompt: str\n",
                            "    scene_id: str\n",
                            "    account_id: str\n",
                            "\n",
                            "@app.post(\"/generate\")\n",
                            "def generate_video(request: GenerateRequest):\n",
                            "    global last_activity\n",
                            "    last_activity = time.time()\n",
                            "    print(f\"Received generation request: {request.prompt} for scene {request.scene_id}\")\n",
                            "    time.sleep(10)\n",
                            "    output_file = f\"/kaggle/working/{request.scene_id}.mp4\"\n",
                            "    with open(output_file, 'wb') as f:\n",
                            "        f.write(b\"Dummy video content\")\n",
                            "    last_activity = time.time() # update again after finishing\n",
                            "    return {\"status\": \"success\", \"video_path\": output_file}\n",
                            "\n",
                            "@app.get(\"/health\")\n",
                            "def health():\n",
                            "    return {\"status\": \"alive\"}\n",
                            "\n",
                            "def idle_checker():\n",
                            "    global last_activity\n",
                            "    while True:\n",
                            "        time.sleep(30)\n",
                            "        if time.time() - last_activity > IDLE_TIMEOUT:\n",
                            "            print(\"Idle timeout reached (5 mins). Shutting down kernel to save quota...\")\n",
                            "            os._exit(0)\n",
                            "\n",
                            "idle_thread = threading.Thread(target=idle_checker, daemon=True)\n",
                            "idle_thread.start()\n",
                            "\n",
                            "def run_server():\n",
                            "    uvicorn.run(app, host=\"0.0.0.0\", port=8000)\n",
                            "\n",
                            "server_thread = threading.Thread(target=run_server, daemon=True)\n",
                            "server_thread.start()\n",
                            "print(\"FastAPI server started on port 8000\")"
                        ]
                        },
                        {
                        "cell_type": "code",
                        "execution_count": None,
                        "metadata": {},
                        "outputs": [],
                        "source": [
                            "# CELL 4 - Start ngrok tunnel & Register\n",
                            "import os\n",
                            "import requests\n",
                            "from pyngrok import ngrok\n",
                            "from kaggle_secrets import UserSecretsClient\n",
                            "\n",
                            "try:\n",
                            "    user_secrets = UserSecretsClient()\n",
                            "    ngrok_token = user_secrets.get_secret(\"NGROK_TOKEN\")\n",
                            "except:\n",
                            f"    ngrok_token = os.environ.get(\"NGROK_TOKEN\", \"{ngrok_token}\")\n",
                            "    \n",
                            "try:\n",
                            "    user_secrets = UserSecretsClient()\n",
                            "    kaggle_user = user_secrets.get_secret(\"KAGGLE_USERNAME\")\n",
                            "except:\n",
                            "    kaggle_user = os.environ.get(\"KAGGLE_USERNAME\", \"Unknown\")\n",
                            "\n",
                            "if ngrok_token:\n",
                            "    ngrok.set_auth_token(ngrok_token)\n",
                            "\n",
                            "public_url = ngrok.connect(8000).public_url\n",
                            "print(f\"Ngrok Tunnel URL: {public_url}\")\n",
                            "\n",
                            "# Register to Modal Backend\n",
                            "backend_url = \"https://irfangull2288--cartoon-backend-fastapi-modal-app.modal.run/session/register-url\"\n",
                            "try:\n",
                            "    resp = requests.post(backend_url, json={\n",
                            "        \"account_username\": kaggle_user,\n",
                            "        \"url\": public_url\n",
                            "    })\n",
                            "    print(\"Backend registration response:\", resp.json())\n",
                            "except Exception as e:\n",
                            "    print(\"Failed to register with backend:\", e)"
                        ]
                        },
                        {
                        "cell_type": "code",
                        "execution_count": None,
                        "metadata": {},
                        "outputs": [],
                        "source": [
                            "# CELL 5 - Keep alive\n",
                            "import time\n",
                            "print(\"Ready!\")\n",
                            "while True:\n",
                            "    time.sleep(60)"
                        ]
                        }
                    ],
                    "metadata": {
                        "kernelspec": {
                            "display_name": "Python 3",
                            "language": "python",
                            "name": "python3"
                        },
                        "language_info": {
                            "codemirror_mode": {"name": "ipython", "version": 3},
                            "file_extension": ".py",
                            "mimetype": "text/x-python",
                            "name": "python",
                            "nbconvert_exporter": "python",
                            "pygments_lexer": "ipython3",
                            "version": "3.10.12"
                        }
                    },
                    "nbformat": 4,
                    "nbformat_minor": 4
                }
                
            with open(os.path.join(tmpdir, "notebook.ipynb"), "w") as f:
                json.dump(notebook_content, f, indent=2)
            
            # 4. Push notebook
            try:
                result = subprocess.run(["kaggle", "kernels", "push", "-p", tmpdir], capture_output=True, text=True, check=True)
            except subprocess.CalledProcessError as e:
                raise Exception(f"Kaggle CLI Error: {e.stderr.strip() if e.stderr else str(e)}")
            
        return {"status": "success", "message": "Notebook created and pushed successfully."}

kaggle_manager = KaggleManager()