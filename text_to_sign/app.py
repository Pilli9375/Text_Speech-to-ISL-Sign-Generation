"""Run with python -m uvicorn text_to_sign.app:app --host 127.0.0.1 --port 8000."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
import os
import tempfile
from typing import Literal
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import speech
from .engine import ROOT, Dictionary, safe_asset
from .sentences import convert_sentence

@asynccontextmanager
async def lifespan(app):
    # Validate source checksums before accepting traffic, rather than charging
    # the first visitor for hashing the complete media bank.
    await run_in_threadpool(dictionary.inventory)
    yield


app = FastAPI(title="SignBridge", version="1.2.0", lifespan=lifespan)
dictionary = Dictionary()
logger = logging.getLogger("signbridge")


class Conversion(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    fingerspell: bool = True
    preview: bool = False
    mode: Literal['dictionary', 'reviewed_sentence'] = 'dictionary'


@app.get("/api/health")
def health():
    return {"status": "ok", "application": "SignBridge", "version": app.version, "speech": speech.status()}


@app.get("/api/dictionary")
def inventory():
    return dictionary.inventory()


@app.post("/api/convert")
def convert(payload: Conversion):
    try:
        if payload.mode == 'reviewed_sentence':
            return convert_sentence(dictionary, payload.text, payload.preview)
        return dictionary.convert(payload.text, payload.fingerspell, payload.preview)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/media/{sign_id}")
def media(sign_id: str):
    entry = next((e for e in dictionary.entries() if e["id"] == sign_id), None)
    if entry is None or not dictionary.available(entry, preview=True):
        raise HTTPException(404, "Sign media is unavailable.")
    return FileResponse(safe_asset(entry["file"], dictionary.root), media_type="video/mp4" if entry["file"].endswith(".mp4") else "video/webm")


@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    path = None
    try:
        if Path(audio.filename or "").suffix.lower() not in {".wav", ".mp3", ".m4a", ".ogg", ".webm", ".mp4", ".flac"}:
            raise HTTPException(422, "Choose WAV, MP3, M4A, OGG, WebM, MP4, or FLAC audio.")
        with tempfile.NamedTemporaryFile(suffix=Path(audio.filename).suffix, delete=False) as target:
            path = Path(target.name)
            size = 0
            while chunk := await audio.read(1024 * 1024):
                size += len(chunk)
                if size > 20 * 1024 * 1024:
                    raise HTTPException(413, "Audio must be smaller than 20 MB.")
                target.write(chunk)
        if size == 0:
            raise HTTPException(422, "The audio file is empty.")
        return await run_in_threadpool(speech.transcribe, path)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except speech.SpeechBusyError as exc:
        raise HTTPException(409, str(exc)) from exc
    except Exception as exc:
        logger.exception("Transcription failed")
        raise HTTPException(503, "Transcription is unavailable. Check the audio format and model download connection, or enter text.") from exc
    finally:
        await audio.close()
        if path:
            path.unlink(missing_ok=True)


if os.getenv("SIGNBRIDGE_DIAGNOSTICS") == "1":
    @app.get("/diagnostics/recorder", include_in_schema=False)
    def recorder_diagnostics():
        return FileResponse(ROOT / "tests/browser_harness.html", media_type="text/html")

app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="web")
