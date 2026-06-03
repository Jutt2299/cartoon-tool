import httpx
from database import Session, ElevenLabsKey, Character

class ElevenLabsManager:

    def get_active_key(self) -> str:
        """Active key lo — rotation ke saath"""
        db = Session()
        
        key = db.query(ElevenLabsKey).filter(
            ElevenLabsKey.is_active == 1,
            ElevenLabsKey.chars_used < 9500
        ).first()
        
        if not key:
            db.close()
            raise Exception("Sari ElevenLabs keys khatam!")
        
        api_key = key.api_key
        db.close()
        return api_key

    def update_char_count(self, text: str):
        """Characters use hone ke baad count update karo"""
        db = Session()
        
        key = db.query(ElevenLabsKey).filter(
            ElevenLabsKey.is_active == 1,
            ElevenLabsKey.chars_used < 9500
        ).first()
        
        if key:
            key.chars_used += len(text)
            
            # 9500 se zyada ho gaye to next key pe jao
            if key.chars_used >= 9500:
                key.is_active = 0
                
                # Next key activate karo
                next_key = db.query(ElevenLabsKey).filter(
                    ElevenLabsKey.chars_used < 9500
                ).first()
                
                if next_key:
                    next_key.is_active = 1
            
            db.commit()
        
        db.close()

    def generate_audio(self, text: str, character_name: str) -> bytes:
        """Character ke liye audio generate karo"""
        
        # Character ki voice ID lo
        db = Session()
        character = db.query(Character).filter_by(
            name=character_name
        ).first()
        db.close()
        
        if not character or not character.voice_id:
            raise Exception(f"{character_name} ki voice nahi mili!")
        
        api_key = self.get_active_key()
        
        response = httpx.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{character.voice_id}",
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json"
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            # Char count update karo
            self.update_char_count(text)
            return response.content
        
        elif response.status_code == 401:
            # Key khatam — next pe jao
            self.update_char_count("x" * 9999)
            return self.generate_audio(text, character_name)
        
        else:
            raise Exception(f"Audio generation failed: {response.status_code}")

    def process_scene_audio(self, scene: dict) -> list:
        """Ek scene ke sare dialogues ka audio banao"""
        
        audio_files = []
        
        for i, dialogue in enumerate(scene["dialogues"]):
            character = dialogue["character"]
            text = dialogue["text"]
            
            print(f"Audio ban raha hai: {character} - {text[:30]}...")
            
            audio_bytes = self.generate_audio(text, character)
            
            audio_files.append({
                "dialogue_index": i,
                "character": character,
                "text": text,
                "audio": audio_bytes
            })
        
        return audio_files

    def get_keys_status(self) -> list:
        """Sari keys ka status lo"""
        db = Session()
        keys = db.query(ElevenLabsKey).all()
        
        result = []
        for key in keys:
            result.append({
                "id": key.id,
                "api_key": key.api_key,
                "chars_used": key.chars_used,
                "chars_remaining": 10000 - key.chars_used,
                "is_active": key.is_active
            })
        
        db.close()
        return result

    def verify_key(self, api_key: str) -> dict:
        """Verify API key and return characters remaining"""
        try:
            response = httpx.get(
                "https://api.elevenlabs.io/v1/user",
                headers={"xi-api-key": api_key},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                # ElevenLabs returns character count in subscription tier limits
                # Typically data["subscription"]["character_count"] and data["subscription"]["character_limit"]
                subscription = data.get("subscription", {})
                char_count = subscription.get("character_count", 0)
                char_limit = subscription.get("character_limit", 10000)
                
                remaining = char_limit - char_count
                return {
                    "valid": True, 
                    "chars_used": char_count, 
                    "chars_remaining": remaining
                }
            else:
                return {"valid": False, "error": f"Invalid key (Status: {response.status_code})"}
        except Exception as e:
            return {"valid": False, "error": str(e)}

elevenlabs_manager = ElevenLabsManager()