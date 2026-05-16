from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from typing import List
import edge_tts
import uuid
import subprocess

app = FastAPI()


# ✅ TEXT TO SPEECH
@app.get("/tts")
async def text_to_speech(text: str):
    filename = f"{uuid.uuid4()}.mp3"

    communicate = edge_tts.Communicate(
        text,
        voice="en-US-GuyNeural"
    )

    await communicate.save(filename)

    return FileResponse(filename, media_type="audio/mpeg", filename="speech.mp3")


# ✅ VIDEO RENDER (FULL AUDIO LENGTH MATCH)
@app.post("/render-video")
async def render_video(
    audio: UploadFile = File(...),
    images: List[UploadFile] = File(...)
):

    # Save audio file
    temp_audio = f"{uuid.uuid4()}.mp3"
    with open(temp_audio, "wb") as f:
        f.write(await audio.read())

    # Get audio duration using ffprobe
    probe = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            temp_audio
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    audio_duration = float(probe.stdout.decode().strip())

    # Save images
    image_files = []
    for img in images:
        temp_img = f"{uuid.uuid4()}.png"
        with open(temp_img, "wb") as f:
            f.write(await img.read())
        image_files.append(temp_img)

    # Calculate duration per image
    per_image_duration = audio_duration / len(image_files)

    # Create FFmpeg input list
    input_txt = "inputs.txt"
    with open(input_txt, "w") as f:
        for img in image_files:
            f.write(f"file '{img}'\n")
            f.write(f"duration {per_image_duration}\n")

    output_file = f"{uuid.uuid4()}.mp4"

    # Build vertical slideshow video
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", input_txt,
            "-i", temp_audio,
            "-vf",
            "scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "-pix_fmt", "yuv420p",
            "-shortest",
            output_file
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    return FileResponse(output_file, media_type="video/mp4", filename="final.mp4")
