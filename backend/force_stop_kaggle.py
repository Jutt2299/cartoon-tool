import modal
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, create_engine
import os
import subprocess
import json
import tempfile

app = modal.App("cartoon-backend")
volume = modal.NetworkFileSystem.from_name("cartoon-db-nfs", create_if_missing=True)

Base = declarative_base()
class KaggleAccount(Base):
    __tablename__ = "kaggle_accounts"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    token = Column(String)
    is_active = Column(Integer, default=0)

@app.function(network_file_systems={"/data": volume})
def force_stop_kaggle():
    db_url = "sqlite:////data/cartoon_v2.db"
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    active = db.query(KaggleAccount).filter_by(is_active=1).first()
    # Alternatively try to stop all just in case
    accounts = db.query(KaggleAccount).all()
    
    for acc in accounts:
        print(f"Stopping kaggle for {acc.username}...")
        os.environ["KAGGLE_USERNAME"] = acc.username
        os.environ["KAGGLE_KEY"] = acc.token
        
        with tempfile.TemporaryDirectory() as temp_dir:
            metadata = {
                "id": f"{acc.username}/cartoon-backend-server",
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
            
            notebook_content = {
                "cells": [{"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": ["print('Stopped.')"]}],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5
            }
            with open(os.path.join(temp_dir, "stop.ipynb"), "w") as f:
                json.dump(notebook_content, f)
                
            subprocess.run(["kaggle", "kernels", "push", "-p", temp_dir], capture_output=True, text=True)
            
            # Additional push to the second kernel name just in case
            metadata["id"] = f"{acc.username}/cartoon-video-generator"
            with open(os.path.join(temp_dir, "kernel-metadata.json"), "w") as f:
                json.dump(metadata, f)
            subprocess.run(["kaggle", "kernels", "push", "-p", temp_dir], capture_output=True, text=True)
            
        acc.is_active = 0
        acc.ngrok_url = None
        db.commit()
    
    db.close()
    print("Force stopped all possible kaggle instances.")

if __name__ == "__main__":
    with app.run():
        force_stop_kaggle.remote()
