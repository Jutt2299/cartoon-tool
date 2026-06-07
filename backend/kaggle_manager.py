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
    
    def start_session(self, preferred_username: str = None):
        """Best account pe notebook start karo"""
        db = Session()
        
        # Pehle check karo koi already active toh nahi
        active = db.query(KaggleAccount).filter_by(is_active=1).first()
        if active:
            db.close()
            return {"status": "already_running", "account": active.username}
        
        # preferred_username diya gaya hai toh wahi use karo
        if preferred_username:
            best = db.query(KaggleAccount).filter_by(username=preferred_username).first()
            if not best:
                db.close()
                best = self.get_best_account()
        else:
            db.close()
            best = self.get_best_account()
            db = Session()
        
        username = best.username
        token = best.token
        
        # Notebook push/run karo
        try:
            self.auto_setup_notebook(username, token)
            # Re-query within THIS session to properly save is_active and clear old ngrok URL
            import time
            account = db.query(KaggleAccount).filter_by(username=username).first()
            account.is_active = 1
            account.ngrok_url = None
            account.last_poll_time = time.time()
            db.commit()
            db.close()
            
            return {
                "status": "started",
                "account": username
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
        
        # Actually stop the notebook on Kaggle
        username = active.username
        token = active.token
        
        import tempfile
        import json
        with tempfile.TemporaryDirectory() as temp_dir:
            metadata = {
                "id": f"{username}/cartoon-backend-server",
                "title": "Cartoon Backend Server",
                "code_file": "stop.ipynb",
                "language": "python",
                "kernel_type": "notebook",
                "is_private": "true",
                "enable_gpu": "true",
                "enable_internet": "true"
            }
            with open(os.path.join(temp_dir, "kernel-metadata.json"), "w") as f:
                json.dump(metadata, f)
            
            # Empty notebook that finishes instantly
            notebook_content = {
                "cells": [{"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": ["print('Session stopped.')"]}],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5
            }
            with open(os.path.join(temp_dir, "stop.ipynb"), "w") as f:
                json.dump(notebook_content, f)
            
            # Use current credentials
            os.environ["KAGGLE_USERNAME"] = username
            os.environ["KAGGLE_KEY"] = token
            
            # Execute push
            subprocess.run(
                ["kaggle", "kernels", "push", "-p", temp_dir],
                capture_output=True, text=True
            )
            
        # Reset DB status
        active.is_active = 0
        active.ngrok_url = None
        active.last_poll_time = 0
        db.commit()
        db.close()
        
        return {"status": "stopped", "account": username}
    
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
                
                # Inject the Kaggle username so notebook knows which account to register URL for
                notebook_content_str = notebook_content_str.replace("__KAGGLE_USERNAME_PLACEHOLDER__", username)
                
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
                            "!pip install -U diffusers transformers accelerate sentencepiece\n",
                            "!pip install fastapi uvicorn pyngrok imageio[ffmpeg]\n",
                            "!pip install opencv-python pillow numpy huggingface_hub"
                        ]
                        },
                        {
                        "cell_type": "code",
                        "execution_count": None,
                        "metadata": {},
                        "outputs": [],
                        "source": [
                            "# CELL 2 - Download LTX Video 2.3 model (~2GB only)\n",
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
                            "print(\"Downloading LTX-Video model (~2GB)...\")\n",
                            "model_id = \"Lightricks/LTX-Video\"\n",
                            "local_dir = \"/kaggle/working/ltx-model\"\n",
                            "if hf_token:\n",
                            "    snapshot_download(repo_id=model_id, local_dir=local_dir, token=hf_token)\n",
                            "else:\n",
                            "    snapshot_download(repo_id=model_id, local_dir=local_dir)\n",
                            "print(\"LTX-Video model downloaded successfully!\")"
                        ]
                        },
                        {
                        "cell_type": "code",
                        "execution_count": None,
                        "metadata": {},
                        "outputs": [],
                        "source": [
                            "# CELL 3 - Load LTX model and Start FastAPI server\n",
                            "# CELL 3 - Load LTX model and start FastAPI server\n",
                            "import threading, uvicorn, os, torch, time, base64, traceback, requests\n",
                            "from fastapi import FastAPI\n",
                            "from fastapi.responses import JSONResponse\n",
                            "from pydantic import BaseModel\n",
                            "from diffusers import LTXVideoPipeline\n",
                            "from diffusers.utils import export_to_video\n",
                            "from pyngrok import ngrok\n",
                            "\n",
                            "try:\n",
                            "    from kaggle_secrets import UserSecretsClient\n",
                            "    user_secrets = UserSecretsClient()\n",
                            "    kaggle_user = user_secrets.get_secret('KAGGLE_USERNAME')\n",
                            "except:\n",
                            "    kaggle_user = os.environ.get('KAGGLE_USERNAME', '__KAGGLE_USERNAME_PLACEHOLDER__')\n",
                            "\n",
                            "backend_url = 'https://irfangull2288--cartoon-backend-fastapi-modal-app.modal.run/session/register-url'\n",
                            "\n",
                            "try:\n",
                            "    print('Loading LTX-Video pipeline...')\n",
                            "    MODEL_DIR = '/kaggle/working/ltx-model'\n",
                            "    pipe = LTXVideoPipeline.from_pretrained(MODEL_DIR, torch_dtype=torch.bfloat16)\n",
                            "    pipe = pipe.to('cuda')\n",
                            "    print('LTX-Video pipeline loaded on GPU!')\n",
                            "\n",
                            "    app = FastAPI()\n",
                            "    last_activity = time.time()\n",
                            "    IDLE_TIMEOUT = 10 * 60\n",
                            "\n",
                            "    class GenerateRequest(BaseModel):\n",
                            "        prompt: str\n",
                            "        scene_id: str\n",
                            "        account_id: str\n",
                            "\n",
                            "    @app.post('/generate')\n",
                            "    def generate_video(request: GenerateRequest):\n",
                            "        global last_activity\n",
                            "        last_activity = time.time()\n",
                            "        print(f'Generating: {request.prompt}')\n",
                            "        try:\n",
                            "            result = pipe(\n",
                            "                prompt=request.prompt,\n",
                            "                negative_prompt='worst quality, blurry, jittery',\n",
                            "                width=512, height=288, num_frames=49,\n",
                            "                num_inference_steps=30,\n",
                            "            )\n",
                            "            frames = result.frames[0]\n",
                            "            output_file = f'/kaggle/working/{request.scene_id}.mp4'\n",
                            "            export_to_video(frames, output_file, fps=24)\n",
                            "            with open(output_file, 'rb') as f:\n",
                            "                video_b64 = base64.b64encode(f.read()).decode()\n",
                            "            last_activity = time.time()\n",
                            "            return {'status': 'success', 'video_path': output_file, 'video_b64': video_b64}\n",
                            "        except Exception as e:\n",
                            "            return JSONResponse(status_code=500, content={'status': 'error', 'message': str(e)})\n",
                            "\n",
                            "    @app.get('/health')\n",
                            "    def health():\n",
                            "        return {'status': 'alive', 'model': 'LTX-Video'}\n",
                            "\n",
                            "    def idle_checker():\n",
                            "        global last_activity\n",
                            "        while True:\n",
                            "            time.sleep(30)\n",
                            "            if time.time() - last_activity > IDLE_TIMEOUT:\n",
                            "                print('Idle 10 min. Shutting down...')\n",
                            "                os._exit(0)\n",
                            "\n",
                            "    threading.Thread(target=idle_checker, daemon=True).start()\n",
                            "    threading.Thread(target=lambda: uvicorn.run(app, host='0.0.0.0', port=8000), daemon=True).start()\n",
                            "    print('FastAPI server started on port 8000')\n",
                            "\n",
                            "    try:\n",
                            "        from kaggle_secrets import UserSecretsClient\n",
                            "        user_secrets = UserSecretsClient()\n",
                            "        ngrok_token = user_secrets.get_secret('NGROK_TOKEN')\n",
                            "    except:\n",
                            "        ngrok_token = os.environ.get('NGROK_TOKEN', '__NGROK_TOKEN_PLACEHOLDER__')\n",
                            "\n",
                            "    if ngrok_token:\n",
                            "        ngrok.set_auth_token(ngrok_token)\n",
                            "\n",
                            "    public_url = ngrok.connect(8000).public_url\n",
                            "    print(f'Ngrok URL: {public_url}')\n",
                            "\n",
                            "    resp = requests.post(backend_url, json={'account_username': kaggle_user, 'url': public_url})\n",
                            "    print('Registered URL with backend:', resp.json())\n",
                            "\n",
                            "    while True:\n",
                            "        time.sleep(60)\n",
                            "\n",
                            "except Exception as e:\n",
                            "    error_msg = traceback.format_exc()\n",
                            "    print('CRASH ERROR:', error_msg)\n",
                            "    requests.post(backend_url, json={'account_username': kaggle_user, 'url': f'ERROR: {str(e)} - {error_msg[-200:]}'})\n",
                            "    raise e\n"
                        ]
                        },
                        {
                        "cell_type": "code",
                        "execution_count": None,
                        "metadata": {},
                        "outputs": [],
                        "source": [
                            "# CELL 4 - Keep alive\n",
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