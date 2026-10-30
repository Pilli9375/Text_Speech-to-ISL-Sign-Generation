import wave

import pytest

from text_to_sign import speech


def test_duration_limit_before_model_load(tmp_path):
    path = tmp_path / 'long.wav'
    with wave.open(str(path), 'wb') as output:
        output.setnchannels(1); output.setsampwidth(2); output.setframerate(16000)
        output.writeframes(b'\0\0' * 16000 * 61)
    with pytest.raises(ValueError, match='60 seconds'):
        speech.transcribe(path)
    assert not speech.status()['busy']


def test_too_short_audio_releases_lock(tmp_path):
    path = tmp_path / 'short.wav'
    with wave.open(str(path), 'wb') as output:
        output.setnchannels(1); output.setsampwidth(2); output.setframerate(16000)
        output.writeframes(b'\0\0' * 100)
    with pytest.raises(ValueError, match='too short'):
        speech.transcribe(path)
    assert not speech.status()['busy']


def test_busy_transcription_rejected():
    speech._busy.acquire()
    try:
        with pytest.raises(RuntimeError, match='Another recording'):
            speech.transcribe(None)
    finally:
        speech._busy.release()


def test_invalid_media_is_a_user_error_and_releases_lock(tmp_path):
    path = tmp_path / 'invalid.wav'; path.write_bytes(b'not an audio container')
    with pytest.raises(ValueError, match='could not be decoded'):
        speech.transcribe(path)
    assert not speech.status()['busy']
