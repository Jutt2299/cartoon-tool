from sqlalchemy import create_engine, Column, String, Integer, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Character(Base):
    __tablename__ = "characters"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    gender = Column(String)
    voice_id = Column(String)
    reference_image = Column(String)

class KaggleAccount(Base):
    __tablename__ = "kaggle_accounts"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    token = Column(String)
    hours_used = Column(Float, default=0)
    last_reset = Column(String)
    ngrok_url = Column(String)
    is_active = Column(Integer, default=0)

class ElevenLabsKey(Base):
    __tablename__ = "elevenlabs_keys"
    id = Column(Integer, primary_key=True)
    api_key = Column(String)
    chars_used = Column(Integer, default=0)
    is_active = Column(Integer, default=1)

class EpisodeHistory(Base):
    __tablename__ = "episode_history"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    video_url = Column(String)
    thumbnail_url = Column(String)
    shorts_urls = Column(String)
    created_at = Column(String)

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)      # job_id like "job_1717403123"
    episode_name = Column(String)
    status = Column(String, default="pending") # pending / processing / done / error
    progress = Column(Integer, default=0)      # 0-100
    progress_msg = Column(String, default="Starting...")
    video_url = Column(String)
    thumbnail_url = Column(String)
    shorts_urls = Column(String)
    error = Column(String)
    created_at = Column(String)
    updated_at = Column(String)

class GlobalSettings(Base):
    __tablename__ = "global_settings"
    id = Column(Integer, primary_key=True)
    ngrok_token = Column(String)
    hf_token = Column(String)


import os
db_url = "sqlite:////data/cartoon_v2.db" if os.path.exists("/data") or os.environ.get("MODAL_IMAGE_ID") else "sqlite:///cartoon_v2.db"
engine = create_engine(db_url, connect_args={"timeout": 15})
try:
    Base.metadata.create_all(engine)
except Exception:
    pass
Session = sessionmaker(bind=engine)

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()