from fastapi import FastAPI
from fastapi.responses import FileResponse
import edge_tts
import uuid
import os

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
