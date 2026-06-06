import re
import httpx
import json
from database import Session, Character, ElevenLabsKey

class ScriptParser:

    def parse_script_manual(self, script_text: str):
        """Purana manual rule-based parsing fallback"""
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

            elif line.startswith("[") and line.endswith("]"):
                current_scene["action"] += " " + line[1:-1]

            elif ":" in line:
                parts = line.split(":", 1)
                character_name = parts[0].strip()
                dialogue = parts[1].strip().strip('"')

                if character_name and dialogue:
                    current_scene["dialogues"].append({
                        "character": character_name,
                        "text": dialogue
                    })

        if current_scene["dialogues"] or current_scene["action"]:
            scenes.append(current_scene)

        return scenes

    def detect_gender(self, name: str, context: str = "") -> str:
        """Character ka gender detect karo naam se (simple offline logic)"""
        name_lower = name.lower()
        female_names = ["sara", "fatima", "ayesha", "zainab", "maryam", "amna", "hira", "sana", "maria", "sadia", "girl", "woman", "mom", "mother", "aunt", "sister", "baji"]
        
        for f_name in female_names:
            if f_name in name_lower:
                return "female"
                
        return "male"

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
        """Complete script process karo using Gemini AI if available"""
        from database import GlobalSettings
        db = Session()
        settings = db.query(GlobalSettings).first()
        gemini_key = settings.gemini_api_key if settings else None
        db.close()
        
        scenes = None
        if gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                You are an expert scriptwriter and prompt engineer for an AI video generation pipeline.
                The user will provide a raw story or script below. It could be in English, Urdu, or Roman Urdu.
                Your task is to parse the story and break it down into sequential scenes.
                
                For each scene, extract:
                1. A brief 'location' (where the scene happens).
                2. The 'action' (what is happening in the scene).
                3. Any 'dialogues' spoken in the scene. For each dialogue, provide the 'character' name and the 'text' they speak.
                4. A highly detailed, Midjourney-style 'video_prompt' for the scene. The prompt should be in English, optimized for 2D flat cartoon animation. Include lighting, mood, camera angle, and detailed character descriptions based on the action. 
                
                Return the output STRICTLY as a valid JSON array of objects. Do not include any markdown formatting like ```json.
                
                Format Example:
                [
                  {{
                    "scene_number": 1,
                    "location": "Bedroom",
                    "action": "Ali is sleeping in his bed when a thief quietly enters.",
                    "dialogues": [],
                    "video_prompt": "2D flat cartoon animation style, Pakistani setting, Bedroom, Ali sleeping on bed, thief entering from window, moonlight, vibrant colors, clear outlines, family friendly."
                  }},
                  {{
                     "scene_number": 2,
                     "location": "Bedroom",
                     "action": "Ali wakes up and shouts at the thief.",
                     "dialogues": [
                         {{"character": "Ali", "text": "Oyee chor!"}}
                     ],
                     "video_prompt": "2D flat cartoon animation style..."
                  }}
                ]
                
                User's Story/Script:
                \"\"\"{script_text}\"\"\"
                """
                response = model.generate_content(prompt)
                raw_text = response.text.strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                scenes = json.loads(raw_text.strip())
                print("Gemini ne successfully script parse kar di!")
            except Exception as e:
                print("Gemini API error (using fallback):", e)
                scenes = None
                
        if not scenes:
            print("Using manual parser fallback...")
            scenes = self.parse_script_manual(script_text)
        
        processed_scenes = []
        for i, scene in enumerate(scenes):
            scene_num = scene.get("scene_number", i+1)
            # Har character ko process karo
            for dialogue in scene.get("dialogues", []):
                char_name = dialogue.get("character", "Unknown")
                self.get_or_create_character(
                    char_name, 
                    context=dialogue.get("text", "")
                )
            
            # Agar Gemini ne video_prompt nahi diya toh fallback use karo
            video_prompt = scene.get("video_prompt")
            if not video_prompt:
                video_prompt = self.generate_video_prompt(scene)
                
            processed_scenes.append({
                "scene_number": scene_num,
                "location": scene.get("location", ""),
                "action": scene.get("action", ""),
                "dialogues": scene.get("dialogues", []),
                "video_prompt": video_prompt
            })
        
        return processed_scenes

script_parser = ScriptParser()