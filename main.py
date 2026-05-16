from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from typing import List
import edge_tts
import uuid
import subprocess
import os

# Force FFmpeg to use 1 thread to prevent CPU overload on free tier
os.environ["OMP_NUM_THREADS"] = "1"

app = FastAPI()


# ✅ TEXT TO SPEECH ENDPOINT
@app.get("/tts")
async def text_to_speech(text: str):
    filename = f"{uuid.uuid4()}.mp3"

    communicate = edge_tts.Communicate(
        text,
        voice="en-US-GuyNeural"
    )

    await communicate.save(filename)

    return FileResponse(filename, media_type="audio/mpeg", filename="speech.mp3")


# ✅ VIDEO RENDER ENDPOINT (OPTIMIZED FOR FREE TIER)
@app.post("/render-video")
async def render_video(
    audio: UploadFile = File(...),
    images: List[UploadFile] = File(...)
):

    temp_audio = f"{uuid.uuid4()}.mp3"
    with open(temp_audio, "wb") as f:
        f.write(await audio.read())

    image_files = []
    for img in images:
        temp_img = f"{uuid.uuid4()}.png"
        with open(temp_img, "wb") as f:
            f.write(await img.read())
        image_files.append(temp_img)

    output_file = f"{uuid.uuid4()}.mp4"

    # Build ffmpeg input args
    ffmpeg_cmd = ["ffmpeg", "-y"]

    # Add each image as looping input
    for img in image_files:
        ffmpeg_cmd += ["-loop", "1", "-t", "5", "-i", img]

    # Add audio
    ffmpeg_cmd += ["-i", temp_audio]

    # Build filter to concatenate images
    filter_complex = ""
    for i in range(len(image_files)):
        filter_complex += f"[{i}:v]scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}];"

    filter_complex += "".join([f"[v{i}]" for i in range(len(image_files))])
    filter_complex += f"concat=n={len(image_files)}:v=1:a=0[outv]"

    ffmpeg_cmd += [
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", f"{len(image_files)}:a",
        "-shortest",
        "-pix_fmt", "yuv420p",
        output_file
    ]

    subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return FileResponse(output_file, media_type="video/mp4", filename="final.mp4")
