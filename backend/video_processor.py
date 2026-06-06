import os
import subprocess
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import json

# ─────────────────────────────────────────────────────────────────────────────
# QUALITY SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
# Target output resolution
OUTPUT_WIDTH  = 1920
OUTPUT_HEIGHT = 1080
OUTPUT_FPS    = 60

# FFmpeg CRF — 12 = near-lossless (lower = better quality)
VIDEO_CRF     = 12
AUDIO_BITRATE = "320k"
VIDEO_PRESET  = "slow"      # slow = better compression/quality
VIDEO_CODEC   = "libx264"

# Shorts (vertical)
SHORTS_WIDTH  = 1080
SHORTS_HEIGHT = 1920

# Thumbnail
THUMB_WIDTH   = 1280
THUMB_HEIGHT  = 720
THUMB_DPI     = 300

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_demo_video():
    """Generates a dummy 2-second blue video if it doesn't exist."""
    path = "/tmp/demo_video.mp4"
    if not os.path.exists(path):
        print("Generating dummy demo video...")
        cmd = [
            "ffmpeg", "-f", "lavfi", "-i", "color=c=blue:s=1280x720:d=2",
            "-c:v", "libx264", "-y", path
        ]
        import subprocess
        subprocess.run(cmd, check=True)
    return path


def run_ffmpeg(cmd: list):
    """Run an FFmpeg command and raise on failure."""
    print("FFmpeg:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFmpeg stderr:", result.stderr[-1000:])
        raise RuntimeError(f"FFmpeg failed: {result.returncode}")
    return result


def upscale_video_4k(input_path: str, output_path: str):
    """
    Upscale video to 1080p (or 4K-friendly) with:
    - libx264, CRF 12, preset slow
    - 60fps (or source fps if lower)
    - Cartoon-style sharpening + contrast boost
    - AAC 320k audio
    """
    vf_filters = ",".join([
        f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:flags=lanczos",   # high-quality upscale
        "unsharp=5:5:1.2:5:5:0.5",                               # sharpening filter
        "eq=contrast=1.15:saturation=1.3:brightness=0.02",        # vibrant colors + contrast
        "format=yuv420p",
    ])
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", vf_filters,
        "-r", str(OUTPUT_FPS),
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-crf", str(VIDEO_CRF),
        "-c:a", "aac",
        "-b:a", AUDIO_BITRATE,
        "-movflags", "+faststart",
        output_path,
    ]
    run_ffmpeg(cmd)


def translate_to_english(text: str) -> str:
    """Translate Urdu/Hindi text to English using googletrans."""
    try:
        from googletrans import Translator
        translator = Translator()
        detection = translator.detect(text)
        if detection and detection.lang in ['ur', 'hi']:
            translation = translator.translate(text, dest='en')
            return translation.text
        return text
    except Exception as e:
        print("Translation error:", e)
        return text


def estimate_duration(text: str, words_per_second: float = 2.5) -> float:
    """Estimate speaking duration of a dialogue line."""
    word_count = max(1, len(text.split()))
    duration = word_count / words_per_second
    return max(2.0, min(duration, 10.0))


def _load_font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

# ─────────────────────────────────────────────────────────────────────────────
# Caption Rendering — HD-quality per-dialogue subtitles
# ─────────────────────────────────────────────────────────────────────────────

def create_dialogue_caption_image(character: str, text: str, size: tuple):
    """
    Renders a subtitle frame at full OUTPUT_WIDTH×OUTPUT_HEIGHT:
      • semi-transparent gradient bar at the bottom
      • character name in bold yellow
      • dialogue text in white with black outline
    """
    w, h = size
    # Scale font sizes relative to video height
    name_size = max(28, h // 28)
    text_size = max(32, h // 24)

    img  = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    bold_font  = _load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", name_size)
    light_font = _load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",      text_size)

    # Gradient bar height — proportional to frame height
    bar_h = h // 8
    bar_y = h - bar_h - 20

    for y_off in range(bar_h):
        alpha = int(200 * (y_off / bar_h))
        draw.line([(0, bar_y + y_off), (w, bar_y + y_off)], fill=(0, 0, 0, alpha))

    margin = w // 25

    # ── Character name ──────────────────────────────────────────────────────
    name_y   = bar_y + int(bar_h * 0.08)
    name_lbl = f"{character}:"
    outline  = 2
    for dx in range(-outline, outline + 1):
        for dy in range(-outline, outline + 1):
            draw.text((margin + dx, name_y + dy), name_lbl, font=bold_font, fill="black")
    draw.text((margin, name_y), name_lbl, font=bold_font, fill="#FFD700")

    # ── Dialogue text ────────────────────────────────────────────────────────
    # Wrap to fit width
    approx_char_w = max(1, text_size // 2)
    max_chars     = max(10, (w - 2 * margin) // approx_char_w)
    if len(text) > max_chars:
        text = text[:max_chars - 3] + "…"

    text_y = name_y + name_size + 6
    for dx in range(-outline, outline + 1):
        for dy in range(-outline, outline + 1):
            draw.text((margin + dx, text_y + dy), text, font=light_font, fill="black")
    draw.text((margin, text_y), text, font=light_font, fill="white")

    img_path = f"/tmp/cap_{abs(hash(character + text))}.png"
    img.save(img_path, dpi=(THUMB_DPI, THUMB_DPI))
    return img_path


def add_captions(video_path: str, scenes: list, output_path: str):
    """
    Burns per-dialogue captions onto the video.
    Each character's line appears only during its estimated speaking window.
    Uses moviepy for composition, then FFmpeg for final high-quality export.
    """
    import moviepy.editor as mp
    video         = mp.VideoFileClip(video_path)
    total_duration = video.duration

    # Flatten all dialogues
    all_dialogues = []
    for scene in scenes:
        dialogues = scene.get("dialogues", [])
        if not dialogues:
            action = scene.get("action", scene.get("video_prompt", ""))[:80]
            if action:
                all_dialogues.append({"character": "Narrator", "text": action})
        else:
            for d in dialogues:
                char = d.get("character", "Character")
                text = d.get("text", "")
                if text.strip():
                    all_dialogues.append({"character": char, "text": text})

    if not all_dialogues:
        video.write_videofile(output_path, codec=VIDEO_CODEC, audio_codec="aac")
        return output_path

    # Scale estimated durations to video length
    raw_durs  = [estimate_duration(d["text"]) for d in all_dialogues]
    total_raw = sum(raw_durs)
    scale     = total_duration / total_raw if total_raw > 0 else 1.0
    durations = [d * scale for d in raw_durs]

    # Build caption overlay clips
    clips        = [video]
    current_time = 0.0
    caption_size = (OUTPUT_WIDTH, OUTPUT_HEIGHT)

    for i, dialogue in enumerate(all_dialogues):
        char       = dialogue["character"]
        raw_text   = dialogue["text"]
        translated = translate_to_english(raw_text)

        dur      = durations[i]
        img_path = create_dialogue_caption_image(char, translated, caption_size)

        txt_clip = (
            mp.ImageClip(img_path)
            .set_start(current_time)
            .set_duration(dur)
        )
        clips.append(txt_clip)
        current_time += dur

    # Intermediate composite (uncompressed-ish)
    tmp_path = output_path.replace(".mp4", "_tmp.mp4")
    final    = mp.CompositeVideoClip(clips, size=caption_size)
    final.write_videofile(
        tmp_path,
        fps=OUTPUT_FPS,
        codec=VIDEO_CODEC,
        audio_codec="aac",
        preset=VIDEO_PRESET,
    )

    # Final FFmpeg pass — apply cartoon filters + high-quality encode
    vf = ",".join([
        f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:flags=lanczos",
        "unsharp=5:5:1.2:5:5:0.5",
        "eq=contrast=1.15:saturation=1.3:brightness=0.02",
        "format=yuv420p",
    ])
    run_ffmpeg([
        "ffmpeg", "-y",
        "-i", tmp_path,
        "-vf", vf,
        "-r", str(OUTPUT_FPS),
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-crf", str(VIDEO_CRF),
        "-c:a", "aac",
        "-b:a", AUDIO_BITRATE,
        "-movflags", "+faststart",
        output_path,
    ])

    # Cleanup temp
    try:
        os.remove(tmp_path)
    except Exception:
        pass

    return output_path

# ─────────────────────────────────────────────────────────────────────────────
# Thumbnail — 1280×720, vibrant, sharp, 300 DPI
# ─────────────────────────────────────────────────────────────────────────────

def generate_thumbnail(video_path: str, title: str, output_path: str):
    """
    Extracts the mid-frame, upscales to 1280×720 at 300 DPI,
    applies saturation + sharpening, then overlays bold title text.
    """
    import moviepy.editor as mp
    video = mp.VideoFileClip(video_path)
    frame = video.get_frame(video.duration / 2)
    video.close()

    img = Image.fromarray(frame).resize((THUMB_WIDTH, THUMB_HEIGHT), Image.LANCZOS)

    # Enhance for vibrant cartoon look
    img = ImageEnhance.Contrast(img).enhance(1.2)
    img = ImageEnhance.Color(img).enhance(1.4)
    img = ImageEnhance.Sharpness(img).enhance(2.0)

    draw = ImageDraw.Draw(img)

    # Dark gradient at bottom (for text legibility)
    for y in range(THUMB_HEIGHT - 220, THUMB_HEIGHT):
        alpha = int((y - (THUMB_HEIGHT - 220)) / 220 * 210)
        draw.line([(0, y), (THUMB_WIDTH, y)], fill=(0, 0, 0, alpha))

    title_font = _load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    sub_font   = _load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",      36)

    # Outer glow / shadow for title
    tx, ty = 50, THUMB_HEIGHT - 160
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            draw.text((tx + dx, ty + dy), title, font=title_font, fill=(0, 0, 0, 200))
    draw.text((tx, ty), title, font=title_font, fill="#FFD700")

    # Sub-label
    sub_label = "Watch Full Episode ▶"
    draw.text((tx + 2, ty + 90), sub_label, font=sub_font, fill=(200, 200, 200))

    img.save(output_path, dpi=(THUMB_DPI, THUMB_DPI), quality=95)
    return output_path

# ─────────────────────────────────────────────────────────────────────────────
# Shorts — 1080×1920 vertical, 60fps, high-bitrate
# ─────────────────────────────────────────────────────────────────────────────

def generate_shorts(video_path: str, output_dir: str, num_shorts: int = 2):
    """
    Cuts the video into vertical 9:16 shorts at 1080×1920,
    using FFmpeg for full quality encode.
    """
    import moviepy.editor as mp
    video = mp.VideoFileClip(video_path)
    w, h  = video.size
    total = video.duration
    video.close()

    short_duration = min(58, total / num_shorts)
    shorts_paths   = []

    for i in range(num_shorts):
        start  = i * short_duration
        end    = min(start + short_duration, total)
        out    = f"{output_dir}/short_{i}.mp4"

        # Crop center 9:16 and scale to 1080×1920
        crop_w = int(h * 9 / 16)
        x1     = (w - crop_w) // 2
        vf     = ",".join([
            f"crop={crop_w}:{h}:{x1}:0",
            f"scale={SHORTS_WIDTH}:{SHORTS_HEIGHT}:flags=lanczos",
            "unsharp=5:5:0.8:5:5:0.4",
            "eq=contrast=1.1:saturation=1.25",
            "format=yuv420p",
        ])
        run_ffmpeg([
            "ffmpeg", "-y",
            "-i", video_path,
            "-ss", str(start),
            "-to", str(end),
            "-vf", vf,
            "-r", str(OUTPUT_FPS),
            "-c:v", VIDEO_CODEC,
            "-preset", VIDEO_PRESET,
            "-crf", str(VIDEO_CRF),
            "-c:a", "aac",
            "-b:a", AUDIO_BITRATE,
            "-movflags", "+faststart",
            out,
        ])
        shorts_paths.append(out)

    return shorts_paths

# ─────────────────────────────────────────────────────────────────────────────
# Main Pipeline
# ─────────────────────────────────────────────────────────────────────────────

def generate_scene_video_from_kaggle(ngrok_url: str, prompt: str, scene_id: str, output_path: str) -> bool:
    """Kaggle Wan2.1 se asli video generate karo"""
    import httpx
    import base64
    try:
        print(f"Calling Kaggle for scene {scene_id}: {prompt[:60]}...")
        resp = httpx.post(
            f"{ngrok_url}/generate",
            json={"prompt": prompt, "scene_id": scene_id, "account_id": "main"},
            timeout=300  # 5 minute timeout per scene
        )
        if resp.status_code == 200:
            data = resp.json()
            video_b64 = data.get("video_data", "")
            if video_b64:
                video_bytes = base64.b64decode(video_b64)
                with open(output_path, 'wb') as f:
                    f.write(video_bytes)
                print(f"Scene video saved: {output_path}")
                return True
        print(f"Kaggle returned {resp.status_code}: {resp.text[:200]}")
        return False
    except Exception as e:
        print(f"Kaggle call failed for scene {scene_id}: {e}")
        return False


def generate_scene_audio_from_elevenlabs(dialogue_text: str, voice_id: str, api_key: str, output_path: str) -> bool:
    """ElevenLabs se audio generate karo"""
    import httpx
    try:
        # Default voices if voice_id is a placeholder
        if not voice_id or voice_id in ["default_male", "default_female"]:
            voice_id = "ErXwobaYiN019PkySvjV" if "female" not in str(voice_id) else "EXAVITQu4vr4xnSDxMaL"
        
        resp = httpx.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": api_key, "Content-Type": "application/json"},
            json={
                "text": dialogue_text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}
            },
            timeout=60
        )
        if resp.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(resp.content)
            return True
        print(f"ElevenLabs error: {resp.status_code}: {resp.text[:200]}")
        return False
    except Exception as e:
        print(f"ElevenLabs call failed: {e}")
        return False


def merge_video_audio(video_path: str, audio_path: str, output_path: str):
    """Video aur audio merge karo"""
    run_ffmpeg([
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        output_path
    ])


def process_full_pipeline(episode_name: str, scenes: list, output_dir: str):
    """Full pipeline: Kaggle AI video + ElevenLabs audio + assembly"""
    os.makedirs(output_dir, exist_ok=True)

    # Kaggle ngrok URL lo database se
    from database import Session, KaggleAccount, ElevenLabsKey
    db = Session()
    active_account = db.query(KaggleAccount).filter_by(is_active=1).first()
    ngrok_url = active_account.ngrok_url if active_account else None
    
    # ElevenLabs key lo
    el_key_obj = db.query(ElevenLabsKey).filter(
        ElevenLabsKey.is_active == 1,
        ElevenLabsKey.chars_used < 9500
    ).first()
    elevenlabs_key = el_key_obj.api_key if el_key_obj else None
    db.close()
    
    scene_video_clips = []
    
    for i, scene in enumerate(scenes):
        scene_id = f"scene_{i}"
        prompt = scene.get("video_prompt", f"Animated cartoon scene: {scene.get('action', '')}")
        
        scene_video_path = f"{output_dir}/{scene_id}_raw.mp4"
        
        # Kaggle se asli AI video lo
        if ngrok_url:
            success = generate_scene_video_from_kaggle(ngrok_url, prompt, scene_id, scene_video_path)
            if not success:
                print(f"Kaggle failed for scene {i}, using demo video...")
                import shutil
                shutil.copy(get_demo_video(), scene_video_path)
        else:
            print(f"No ngrok URL — using demo video for scene {i}")
            import shutil
            shutil.copy(get_demo_video(), scene_video_path)
        
        # Dialogues ke liye audio banao aur merge karo
        if scene.get("dialogues") and elevenlabs_key:
            merged_parts = []
            for j, dialogue in enumerate(scene["dialogues"]):
                audio_path = f"{output_dir}/{scene_id}_dialogue_{j}.mp3"
                merged_path = f"{output_dir}/{scene_id}_part_{j}.mp4"
                
                # Ek dialogue ka audio lo
                audio_ok = generate_scene_audio_from_elevenlabs(
                    dialogue["text"],
                    dialogue.get("voice_id", "default_male"),
                    elevenlabs_key,
                    audio_path
                )
                
                if audio_ok and os.path.exists(audio_path):
                    try:
                        merge_video_audio(scene_video_path, audio_path, merged_path)
                        merged_parts.append(merged_path)
                    except:
                        merged_parts.append(scene_video_path)
                else:
                    merged_parts.append(scene_video_path)
            
            scene_video_clips.append(merged_parts[-1] if merged_parts else scene_video_path)
        else:
            scene_video_clips.append(scene_video_path)
    
    # Sab scenes concatenate karo
    if len(scene_video_clips) > 1:
        concat_list_path = f"{output_dir}/concat_list.txt"
        with open(concat_list_path, 'w') as f:
            for clip in scene_video_clips:
                f.write(f"file '{clip}'\n")
        
        combined_path = f"{output_dir}/combined.mp4"
        run_ffmpeg([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_list_path,
            "-c", "copy",
            combined_path
        ])
    else:
        combined_path = scene_video_clips[0] if scene_video_clips else get_demo_video()
    
    # Captions add karo
    print("Adding captions (1080p 60fps)...")
    final_video_path = f"{output_dir}/final_video.mp4"
    add_captions(combined_path, scenes, final_video_path)

    print("Generating thumbnail...")
    thumbnail_path = f"{output_dir}/thumbnail.jpg"
    generate_thumbnail(final_video_path, episode_name, thumbnail_path)

    print("Generating vertical shorts...")
    shorts_paths = generate_shorts(final_video_path, output_dir, num_shorts=2)

    return {
        "video_url":     final_video_path,
        "thumbnail_url": thumbnail_path,
        "shorts_urls":   shorts_paths,
    }

