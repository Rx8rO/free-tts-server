from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import edge_tts
import uuid
import os
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

app = FastAPI()

@app.get("/tts")
async def text_to_speech(text: str):
    filename = f"{uuid.uuid4()}.mp3"
    communicate = edge_tts.Communicate(text, voice="en-US-GuyNeural")
    await communicate.save(filename)
    return FileResponse(filename, media_type="audio/mpeg", filename="speech.mp3")


@app.post("/render-video")
async def render_video(audio: UploadFile = File(...), images: list[UploadFile] = File(...)):

    temp_audio = f"{uuid.uuid4()}.mp3"
    with open(temp_audio, "wb") as f:
        f.write(await audio.read())

    clips = []

    for img in images:
        temp_img = f"{uuid.uuid4()}.png"
        with open(temp_img, "wb") as f:
            f.write(await img.read())

        clip = ImageClip(temp_img).set_duration(4).resize((1080, 1920))
        clips.append(clip)

    final_video = concatenate_videoclips(clips, method="compose")

    audio_clip = AudioFileClip(temp_audio)
    final_video = final_video.set_audio(audio_clip)

    output_file = f"{uuid.uuid4()}.mp4"
    final_video.write_videofile(output_file, fps=24)

    return FileResponse(output_file, media_type="video/mp4", filename="final.mp4")
