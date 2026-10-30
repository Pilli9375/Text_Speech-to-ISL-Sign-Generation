import importlib

import pytest
from fastapi.testclient import TestClient

module = importlib.import_module('text_to_sign.app')


@pytest.fixture
def client():
    return TestClient(module.app)


def test_health_and_home(client):
    assert client.get('/api/health').json()['status'] == 'ok'
    assert 'SignBridge' in client.get('/').text


@pytest.mark.parametrize('payload', [{}, {'text': ''}, {'text': '!!!'}, {'text': 'नमस्ते'}, {'text': 'x' * 4001}])
def test_conversion_validation(client, payload):
    assert client.post('/api/convert', json=payload).status_code == 422


def test_unknown_media(client):
    assert client.get('/api/media/not-a-sign').status_code == 404


def test_audio_rejects_format_and_empty(client):
    assert client.post('/api/transcribe', files={'audio': ('test.txt', b'hello')}).status_code == 422
    assert client.post('/api/transcribe', files={'audio': ('test.wav', b'')}).status_code == 422


def test_audio_size_limit(client):
    response = client.post('/api/transcribe', files={'audio': ('big.wav', b'x' * (20 * 1024 * 1024 + 1))})
    assert response.status_code == 413


def test_transcription_contract(client, monkeypatch):
    monkeypatch.setattr(module.speech, 'transcribe', lambda path: {'text': 'hello friend', 'model': 'fixture'})
    response = client.post('/api/transcribe', files={'audio': ('sample.wav', b'fixture')})
    assert response.json()['text'] == 'hello friend'


@pytest.mark.parametrize('error,code', [(ValueError('No speech detected'), 422), (module.speech.SpeechBusyError('Busy'), 409), (RuntimeError('Model failure'), 503), (OSError('Bad container'), 503)])
def test_transcription_errors(client, monkeypatch, error, code):
    def fail(path): raise error
    monkeypatch.setattr(module.speech, 'transcribe', fail)
    assert client.post('/api/transcribe', files={'audio': ('sample.wav', b'fixture')}).status_code == code
