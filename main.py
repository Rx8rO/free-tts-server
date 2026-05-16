from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import edge_tts
import uuid
import os
import subprocess

app = FastAPI()


# ✅ TTS ENDPOINT
@app.get("/tts")
async def text_to_speech(text: str):
    filename = f"{uuid.uuid4()}.mp3"

    communicate = edge_tts.Communicate(
        text,
        voice="en-US-GuyNeural"
    )

    await communicate.save(filename)

    return FileResponse(filename, media_type="audio/mpeg", filename="speech.mp3")


# ✅ VIDEO RENDER ENDPOINT (NO MOVIEPY)
@app.post("/render-video")
async def render_video(audio: UploadFile = File(...), images = File(...)):

    # Save audio file
    temp_audio = f"{uuid.uuid4()}.mp3"
    with open(temp_audio, "wb") as f:
        f.write(await audio.read())

    # Save images
    image_files = []
    for img in images:
        temp_img = f"{uuid.uuid4()}.png"
        with open(temp_img, "wb") as f:
            f.write(await img.read())
        image_files.append(temp_img)

    # Create ffmpeg input list
    input_txt = "inputs.txt"
    with open(input_txt, "w") as f:
        for img in image_files:
            f.write(f"file '{img}'\n")
            f.write("duration 4\n")

    output_file = f"{uuid.uuid4()}.mp4"

    # Run FFmpeg slideshow
    subprocess.run([
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", input_txt,
        "-i", temp_audio,
        "-vsync", "vfr",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_file
    ])

    return FileResponse(output_file, media_type="video/mp4", filename="final.mp4")
