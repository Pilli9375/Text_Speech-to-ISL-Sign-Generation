"""A small real-human-speech smoke evaluation, not an accent/noise benchmark."""
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from text_to_sign.speech import transcribe

URL = 'https://raw.githubusercontent.com/QwenLM/Qwen-Audio/main/assets/audio/1272-128104-0000.flac'
REFERENCE = 'MISTER QUILTER IS THE APOSTLE OF THE MIDDLE CLASSES AND WE ARE GLAD TO WELCOME HIS GOSPEL'
SHA256 = '4e25e22555cd16e90edb0a3b49fdcf1fe652b2a1250ab643634db33895c75b41'


def words(text):
    text = re.sub(r'\bmr\.', 'mister', text.lower())
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text)


def distance(a, b):
    previous = list(range(len(b) + 1))
    for i, left in enumerate(a, 1):
        current = [i]
        for j, right in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[-1] + 1, previous[j-1] + (left != right)))
        previous = current
    return previous[-1]


def evaluate():
    target = ROOT / 'artifacts/librispeech-1272-128104-0000.flac'
    target.parent.mkdir(exist_ok=True)
    if not target.exists():
        with urllib.request.urlopen(URL, timeout=45) as response:
            data = response.read(2 * 1024 * 1024)
        target.write_bytes(data)
    if hashlib.sha256(target.read_bytes()).hexdigest() != SHA256:
        raise ValueError('Speech sample checksum changed; inspect the source before evaluating')
    result = transcribe(target)
    reference, observed = words(REFERENCE), words(result['text'])
    edits = distance(reference, observed)
    report = {'sample_id': 'LibriSpeech dev-clean 1272-128104-0000', 'sample_count': 1,
              'source_url': URL, 'dataset_url': 'https://www.openslr.org/12',
              'reference_source': 'https://huggingface.co/datasets/hf-internal-testing/librispeech_asr_demo/viewer/',
              'attribution': 'Vassil Panayotov, Guoguo Chen, Daniel Povey and Sanjeev Khudanpur, LibriSpeech (2015)',
              'license': 'CC BY 4.0', 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
              'reference': REFERENCE, 'observed': result['text'], 'reference_words': len(reference),
              'word_edits': edits, 'wer_percent': round(edits / len(reference) * 100, 2),
              'normalization': 'Case/punctuation ignored; Mr. normalized to mister; no other lexical substitutions.',
              'transcription': result,
              'limitation': 'One clean audiobook speaker/utterance. Not representative of conversational or Indian-accented speech, microphone/noise conditions, or deployed accuracy.'}
    (ROOT / 'text_to_sign/docs/human_speech_smoke.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    evaluate()
