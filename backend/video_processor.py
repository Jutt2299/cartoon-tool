import os
import urllib.request
from PIL import Image, ImageDraw, ImageFont
import json

DEMO_VIDEO_URL = "https://storage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"

def get_demo_video():
    """Downloads a demo video for processing if it doesn't exist."""
    path = "/tmp/demo_video.mp4"
    if not os.path.exists(path):
        print("Downloading demo video...")
        urllib.request.urlretrieve(DEMO_VIDEO_URL, path)
    return path

def translate_to_english(text: str) -> str:
    """Translate Urdu/Hindi text to English using googletrans."""
    try:
        from googletrans import Translator
        translator = Translator()
        detection = translator.detect(text)
        if detection.lang in ['ur', 'hi']:
            translation = translator.translate(text, dest='en')
            return translation.text
        return text
    except Exception as e:
        print("Translation error:", e)
        return text

def create_text_image(text: str, size: tuple, font_size: int = 40):
    """Creates a transparent image with centered outlined text using Pillow."""
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0,0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = (size[0] - text_w) / 2
    y = size[1] - text_h - 50

    for adj in range(-2, 3):
        for adj2 in range(-2, 3):
            draw.text((x+adj, y+adj2), text, font=font, fill="black")
            
    draw.text((x, y), text, font=font, fill="white")
    
    img_path = f"/tmp/subtitle_{abs(hash(text))}.png"
    img.save(img_path)
    return img_path

def estimate_duration(text: str, words_per_second: float = 2.5) -> float:
    """Estimate how long it takes to speak a line of text."""
    word_count = max(1, len(text.split()))
    duration = word_count / words_per_second
    return max(2.0, min(duration, 10.0))  # min 2s, max 10s per line

def create_dialogue_caption_image(character: str, text: str, size: tuple, font_size: int = 36):
    """Creates a transparent image with character name + dialogue caption at the bottom."""
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size - 4)
        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except:
        name_font = ImageFont.load_default()
        text_font = ImageFont.load_default()

    # Draw semi-transparent background bar at bottom
    bar_height = 90
    bar_y = size[1] - bar_height - 20
    for y_offset in range(bar_height):
        alpha = int(180 * (y_offset / bar_height))
        draw.line([(0, bar_y + y_offset), (size[0], bar_y + y_offset)], fill=(0, 0, 0, alpha))

    # Character name in yellow
    name_y = bar_y + 8
    name_label = f"{character}:"
    # Outline for name
    for adj in range(-1, 2):
        for adj2 in range(-1, 2):
            draw.text((52 + adj, name_y + adj2), name_label, font=name_font, fill="black")
    draw.text((52, name_y), name_label, font=name_font, fill="#FFD700")

    # Dialogue text in white below name
    text_y = name_y + font_size + 2
    # Wrap text to fit screen width
    max_chars = size[0] // (font_size // 2)
    wrapped = text if len(text) <= max_chars else text[:max_chars - 3] + "..."
    # Outline for dialogue
    for adj in range(-1, 2):
        for adj2 in range(-1, 2):
            draw.text((52 + adj, text_y + adj2), wrapped, font=text_font, fill="black")
    draw.text((52, text_y), wrapped, font=text_font, fill="white")

    img_path = f"/tmp/caption_{abs(hash(character + text))}.png"
    img.save(img_path)
    return img_path

def add_captions(video_path: str, scenes: list, output_path: str):
    """Burns per-dialogue captions — each character's line shows when they speak."""
    import moviepy.editor as mp
    video = mp.VideoFileClip(video_path)
    total_duration = video.duration

    # ── Flatten all dialogues from all scenes ──────────────────────────────
    all_dialogues = []
    for scene in scenes:
        dialogues = scene.get("dialogues", [])
        if not dialogues:
            # Fallback: scene action as narrator caption
            action = scene.get("action", scene.get("video_prompt", ""))[:60]
            if action:
                all_dialogues.append({"character": "Narrator", "text": action})
        else:
            for d in dialogues:
                char = d.get("character", "Character")
                text = d.get("text", "")
                if text:
                    all_dialogues.append({"character": char, "text": text})

    if not all_dialogues:
        video.write_videofile(output_path, codec="libx264", audio_codec="aac")
        return output_path

    # ── Estimate durations and calculate timing ────────────────────────────
    raw_durations = [estimate_duration(d["text"]) for d in all_dialogues]
    total_raw = sum(raw_durations)

    # Scale durations to fit video length
    scale = total_duration / total_raw if total_raw > 0 else 1.0
    durations = [d * scale for d in raw_durations]

    # ── Build caption clips ───────────────────────────────────────────────
    clips = [video]
    current_time = 0.0

    for i, dialogue in enumerate(all_dialogues):
        char = dialogue["character"]
        raw_text = dialogue["text"]
        translated = translate_to_english(raw_text)

        duration = durations[i]
        img_path = create_dialogue_caption_image(char, translated, video.size)

        txt_clip = (
            mp.ImageClip(img_path)
            .set_start(current_time)
            .set_duration(duration)
        )
        clips.append(txt_clip)
        current_time += duration

    final_video = mp.CompositeVideoClip(clips)
    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
    return output_path


def generate_thumbnail(video_path: str, title: str, output_path: str):
    """Extracts a frame, resizes to 1280x720 and overlays bright text."""
    import moviepy.editor as mp
    video = mp.VideoFileClip(video_path)
    frame = video.get_frame(video.duration / 2)
    img = Image.fromarray(frame).resize((1280, 720))
    
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    except:
        font = ImageFont.load_default()
        
    # Dark gradient at bottom
    for y in range(500, 720):
        alpha = int((y - 500) / 220 * 200)
        draw.line([(0, y), (1280, y)], fill=(0, 0, 0, alpha))
        
    # Bold title text
    x, y = 50, 600
    for adj in range(-3, 4):
        for adj2 in range(-3, 4):
            draw.text((x+adj, y+adj2), title, font=font, fill="black")
    draw.text((x, y), title, font=font, fill="#FFD700")
    
    img.save(output_path)
    return output_path

def generate_shorts(video_path: str, output_dir: str, num_shorts: int = 2):
    """Cuts the video into vertical 9:16 shorts."""
    import moviepy.editor as mp
    video = mp.VideoFileClip(video_path)
    w, h = video.size
    
    target_w = int(h * 9 / 16)
    x1 = (w - target_w) / 2
    x2 = x1 + target_w
    
    vertical_video = video.crop(x1=x1, y1=0, x2=x2, y2=h)
    
    shorts_paths = []
    short_duration = min(30, video.duration / num_shorts)
    
    for i in range(num_shorts):
        start = i * short_duration
        end = start + short_duration
        short_clip = vertical_video.subclip(start, end)
        path = f"{output_dir}/short_{i}.mp4"
        short_clip.write_videofile(path, codec="libx264", audio_codec="aac")
        shorts_paths.append(path)
        
    return shorts_paths

def process_full_pipeline(episode_name: str, scenes: list, output_dir: str):
    """Runs the entire pipeline on a demo video."""
    os.makedirs(output_dir, exist_ok=True)
    
    print("Downloading demo video...")
    base_video = get_demo_video()
    
    print("Adding captions...")
    final_video_path = f"{output_dir}/final_video.mp4"
    add_captions(base_video, scenes, final_video_path)
    
    print("Generating thumbnail...")
    thumbnail_path = f"{output_dir}/thumbnail.jpg"
    generate_thumbnail(final_video_path, episode_name, thumbnail_path)
    
    print("Generating shorts...")
    shorts_paths = generate_shorts(final_video_path, output_dir, num_shorts=2)
    
    return {
        "video_url": final_video_path,
        "thumbnail_url": thumbnail_path,
        "shorts_urls": shorts_paths
    }
