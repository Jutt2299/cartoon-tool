import re
import httpx
import json
from database import Session, Character, ElevenLabsKey

class ScriptParser:

    def parse_script(self, script_text: str):
        """Script ko scenes mein todo"""
        scenes = []
        current_scene = {
            "scene_number": 0,
            "location": "",
            "dialogues": [],
            "action": ""
        }

        lines = script_text.strip().split('\n')
        scene_number = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Scene heading detect karo
            # Format: SCENE 1: [Location]
            if line.upper().startswith("SCENE"):
                if current_scene["dialogues"] or current_scene["action"]:
                    scenes.append(current_scene)
                
                scene_number += 1
                location = line.split(":", 1)[1].strip() if ":" in line else ""
                current_scene = {
                    "scene_number": scene_number,
                    "location": location,
                    "dialogues": [],
                    "action": ""
                }

            # Action/description detect karo
            # Format: [Ahmed walks into room]
            elif line.startswith("[") and line.endswith("]"):
                current_scene["action"] += " " + line[1:-1]

            # Dialogue detect karo
            # Format: Ahmed: "Yaar kya ho raha hai!"
            elif ":" in line:
                parts = line.split(":", 1)
                character_name = parts[0].strip()
                dialogue = parts[1].strip().strip('"')

                if character_name and dialogue:
                    current_scene["dialogues"].append({
                        "character": character_name,
                        "text": dialogue
                    })

        # Last scene add karo
        if current_scene["dialogues"] or current_scene["action"]:
            scenes.append(current_scene)

        return scenes

    def detect_gender(self, name: str, context: str = "") -> str:
        """Character ka gender detect karo naam se"""
        
        # Claude API se gender detect karwao
        prompt = f"""
        Character name: {name}
        Context: {context}
        
        Is this character male or female?
        Reply with only one word: "male" or "female"
        Consider Pakistani/Urdu names as well.
        """
        
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": "TUMHARI_CLAUDE_API_KEY",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-opus-4-5",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        
        gender = response.json()["content"][0]["text"].strip().lower()
        return gender if gender in ["male", "female"] else "male"

    def get_or_create_character(self, name: str, context: str = ""):
        """Character database mein check karo — nahi hai to banao"""
        db = Session()
        
        # Pehle check karo database mein hai ya nahi
        character = db.query(Character).filter_by(name=name).first()
        
        if character:
            db.close()
            return character
        
        # Naya character — gender detect karo
        gender = self.detect_gender(name, context)
        
        # ElevenLabs se unique voice banao
        voice_id = self.create_unique_voice(name, gender)
        
        # Database mein save karo
        new_character = Character(
            name=name,
            gender=gender,
            voice_id=voice_id,
            reference_image=""
        )
        db.add(new_character)
        db.commit()
        db.close()
        
        return new_character

    def create_unique_voice(self, name: str, gender: str) -> str:
        """ElevenLabs se unique voice banao"""
        
        # Active ElevenLabs key lo
        api_key = self.get_active_elevenlabs_key()
        
        # Gender ke hisaab se voice settings
        if gender == "male":
            voice_settings = {
                "name": name,
                "gender": "male",
                "age": "young",
                "accent": "american",
                "accent_strength": 0.5
            }
        else:
            voice_settings = {
                "name": name,
                "gender": "female",
                "age": "young", 
                "accent": "american",
                "accent_strength": 0.5
            }
        
        response = httpx.post(
            "https://api.elevenlabs.io/v1/voice-generation/generate-voice",
            headers={"xi-api-key": api_key},
            json=voice_settings
        )
        
        if response.status_code == 200:
            voice_id = response.json().get("voice_id")
            return voice_id
        
        # Fallback — default voice use karo
        return "default_male" if gender == "male" else "default_female"

    def get_active_elevenlabs_key(self) -> str:
        """Active ElevenLabs key lo — rotation ke saath"""
        db = Session()
        
        # Pehli active key lo jisme chars bacha ho
        key = db.query(ElevenLabsKey).filter(
            ElevenLabsKey.is_active == 1,
            ElevenLabsKey.chars_used < 9500  # 500 buffer rakho
        ).first()
        
        if not key:
            # Sari keys khatam
            db.close()
            raise Exception("Sari ElevenLabs keys khatam ho gayi!")
        
        api_key = key.api_key
        db.close()
        return api_key

    def generate_video_prompt(self, scene: dict) -> str:
        """Scene se video generation prompt banao"""
        
        location = scene.get("location", "")
        action = scene.get("action", "")
        characters = [d["character"] for d in scene.get("dialogues", [])]
        characters = list(set(characters))  # Duplicates hatao
        
        prompt = f"""
        2D flat cartoon animation style, Pakistani setting.
        Location: {location}.
        Characters: {', '.join(characters)}.
        Action: {action}.
        Vibrant colors, clear outlines, family friendly.
        """
        
        return prompt.strip()

    def process_script(self, script_text: str):
        """Complete script process karo"""
        
        # Scenes mein todo
        scenes = self.parse_script(script_text)
        
        processed_scenes = []
        
        for scene in scenes:
            # Har character ko process karo
            for dialogue in scene["dialogues"]:
                char_name = dialogue["character"]
                self.get_or_create_character(
                    char_name, 
                    context=dialogue["text"]
                )
            
            # Video prompt banao
            video_prompt = self.generate_video_prompt(scene)
            
            processed_scenes.append({
                "scene_number": scene["scene_number"],
                "location": scene["location"],
                "action": scene["action"],
                "dialogues": scene["dialogues"],
                "video_prompt": video_prompt
            })
        
        return processed_scenes

script_parser = ScriptParser()