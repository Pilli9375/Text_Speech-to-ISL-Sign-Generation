"""Lazy local ASR: no credentials and no hosted transcription service."""
import os
import threading
import time
from pathlib import Path

_model = None
_lock = threading.Lock()
_busy = threading.Lock()
MODEL = os.getenv("SIGNBRIDGE_ASR_MODEL", "base.en")
MAX_AUDIO_SECONDS = 60


class SpeechBusyError(RuntimeError):
    """An expected busy-worker response, distinct from model runtime failures."""


def status() -> dict:
    return {"model": MODEL, "loaded": _model is not None, "busy": _busy.locked(),
            "max_seconds": MAX_AUDIO_SECONDS, "device": "cpu"}


def transcribe(path: Path) -> dict:
    if not _busy.acquire(blocking=False):
        raise SpeechBusyError("Another recording is being transcribed. Please try again shortly.")
    try:
        import av
        # Decode only up to the duration limit BEFORE loading the model; header metadata can lie.
        seconds = 0.0
        try:
            with av.open(str(path)) as container:
                if not container.streams.audio:
                    raise ValueError("The file contains no audio track.")
                for frame in container.decode(audio=0):
                    seconds += frame.samples / frame.sample_rate
                    if seconds > MAX_AUDIO_SECONDS + 0.1:
                        raise ValueError(f"Please upload recordings of {MAX_AUDIO_SECONDS} seconds or less.")
        except av.error.FFmpegError as exc:
            raise ValueError("The audio file could not be decoded. Choose a valid recording and try again.") from exc
        if seconds < 0.15:
            raise ValueError("The recording is empty or too short. Please try again.")
        global _model
        started = time.perf_counter()
        with _lock:
            if _model is None:
                from faster_whisper import WhisperModel
                _model = WhisperModel(MODEL, device="cpu", compute_type="int8",
                                     cpu_threads=min(4, os.cpu_count() or 2))
        segments, info = _model.transcribe(str(path), language="en", beam_size=3, vad_filter=True,
                                          condition_on_previous_text=False)
        text = " ".join(s.text.strip() for s in segments).strip()
        if not text:
            raise ValueError("No speech was detected. Try a clearer recording or enter text.")
        return {"text": text, "language": info.language, "audio_seconds": round(seconds, 2),
                "elapsed_ms": round((time.perf_counter() - started) * 1000), "model": MODEL}
    finally:
        _busy.release()
