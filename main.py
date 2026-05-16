from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from typing import List
import edge_tts
import uuid
import subprocess

app = FastAPI()


@app.get("/tts")
async def text_to_speech(text: str):
    filename = f"{uuid.uuid4()}.mp3"

    communicate = edge_tts.Communicate(
        text,
        voice="en-US-GuyNeural"
    )

    await communicate.save(filename)

    return FileResponse(filename, media_type="audio/mpeg", filename="speech.mp3")


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

    input_txt = "inputs.txt"
    with open(input_txt, "w") as f:
        for img in image_files:
            f.write(f"file '{img}'\n")
            f.write("duration 4\n")

    output_file = f"{uuid.uuid4()}.mp4"

    subprocess.run(
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
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    return FileResponse(output_file, media_type="video/mp4", filename="final.mp4")
