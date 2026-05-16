from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from typing import List
import edge_tts
import uuid
import os
import subprocess

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


# ✅ VIDEO RENDER ENDPOINT (FFMPEG BASED)
@app.post("/render-video")
async def render_video(
    audio: UploadFile = File(...),
    images: List[UploadFile] = File(...)
):

    try:
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

        # Run ffmpeg slideshow
        process = subprocess.run(
            [
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
            ],
