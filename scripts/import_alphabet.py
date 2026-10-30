"""Restore the pinned ISLAN signer-1 double-handed alphabet and make browser clips.

Only selected public ZIP members are fetched using HTTP byte ranges. Stills are
rotated upright and shown for one second. The original J video keeps its motion.
No transformation constitutes independent ISL correctness review.
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from text_to_sign.engine import safe_asset

HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; SignBridge research asset fetcher)'}


class RemoteZip(io.RawIOBase):
    def __init__(self, url: str, size: int):
        self.url, self.size, self.pos = url, size, 0
        self.cache_start, self.cache = 0, b''

    def seekable(self):
        return True

    def seek(self, offset, whence=0):
        self.pos = offset if whence == 0 else self.pos + offset if whence == 1 else self.size + offset
        return self.pos

    def tell(self):
        return self.pos

    def read(self, count=-1):
        if count < 0:
            count = self.size - self.pos
        if not count:
            return b''
        if count > 20 * 1024 * 1024:
            raise ValueError('Archive read exceeds bounded member limit')
        if self.cache_start <= self.pos and self.pos + count <= self.cache_start + len(self.cache):
            start = self.pos - self.cache_start
            data = self.cache[start:start + count]
            self.pos += len(data)
            return data
        amount = min(max(count, 65536), self.size - self.pos)
        request = urllib.request.Request(self.url, headers={**HEADERS, 'Range': f'bytes={self.pos}-{self.pos + amount - 1}'})
        with urllib.request.urlopen(request, timeout=90) as response:
            if response.status != 206:
                raise ValueError('Source no longer supports bounded HTTP ranges; no full archive was downloaded')
            data = response.read(amount)
        self.cache_start, self.cache = self.pos, data
        self.pos += len(data[:count])
        return data[:count]


def still_to_video(source: Path, target: Path):
    import av
    from PIL import Image, ImageOps
    with Image.open(source) as original:
        image = ImageOps.exif_transpose(original).convert('RGB').rotate(90, expand=True)
        image.thumbnail((960, 720))
        width, height = image.width // 2 * 2, image.height // 2 * 2
        image = image.resize((width, height))
        with av.open(str(target), 'w', format='mp4', options={'movflags': '+faststart'}) as output:
            stream = output.add_stream('libx264', rate=10)
            stream.width, stream.height, stream.pix_fmt = width, height, 'yuv420p'
            stream.options = {'crf': '20', 'preset': 'medium'}
            for _ in range(10):
                for packet in stream.encode(av.VideoFrame.from_image(image)):
                    output.mux(packet)
            for packet in stream.encode():
                output.mux(packet)


def restore():
    manifest_path = ROOT / 'text_to_sign/data/alphabet_manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    source_path = ROOT / 'text_to_sign/data/source_manifest.json'
    source_manifest = json.loads(source_path.read_text(encoding='utf-8'))
    current = {e['text']: e for e in source_manifest['candidates'] if e.get('type') == 'alphabet'}
    originals = ROOT / 'artifacts/islan-originals'; originals.mkdir(parents=True, exist_ok=True)
    needed = []
    for item in manifest['files']:
        letter = item['letter'].lower()
        target = safe_asset(f'signs/letters/{letter}.mp4')
        if target.exists() and current.get(letter, {}).get('sha256') == hashlib.sha256(target.read_bytes()).hexdigest():
            continue
        needed.append(item)
    if not needed:
        print('A–Z clips are already present with matching checksums.')
        return
    def valid_original(item):
        path = originals / Path(item['source_member']).name
        return path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256']
    missing = [item for item in needed if not valid_original(item)]
    url = None
    if missing:
        request = urllib.request.Request(manifest['archive_url'], headers=HEADERS, method='HEAD')
        with urllib.request.urlopen(request, timeout=45) as response:
            url = response.geturl()
            if int(response.headers['Content-Length']) != manifest['archive_size']:
                raise ValueError('Source archive size changed; inspect the source before importing')

    def import_letter(item):
        original = originals / Path(item['source_member']).name
        if not valid_original(item):
            with zipfile.ZipFile(RemoteZip(url, manifest['archive_size'])) as archive:
                info = archive.getinfo(item['source_member'])
                if info.file_size != item['bytes'] or info.file_size > 20 * 1024 * 1024:
                    raise ValueError('Unexpected alphabet source member size')
                data = archive.read(info)
            if hashlib.sha256(data).hexdigest() != item['sha256']:
                raise ValueError('Alphabet source checksum did not match the pinned version')
            original.write_bytes(data)
        letter = item['letter'].lower()
        target = safe_asset(f'signs/letters/{letter}.mp4'); target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix('.download')
        try:
            if original.suffix.lower() == '.mp4':
                # The selected double-handed J is a genuine moving sign. Keep the source intact.
                temporary.write_bytes(original.read_bytes())
                derivation = 'Original dynamic video copied unchanged; no temporal or spatial edits.'
            else:
                still_to_video(original, temporary)
                derivation = 'Original still rotated 90 degrees counterclockwise to upright, resized to fit 960x720, encoded as a one-second H.264 clip. No synthesized hand motion.'
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        print(f'{letter.upper()}: source restored and browser clip prepared', flush=True)
        return {'text': letter, 'type': 'alphabet', 'provider': 'islan', 'file': f'signs/letters/{letter}.mp4',
                'source_file_name': Path(item['source_member']).name, 'source_member': item['source_member'],
                'source_sha256': item['sha256'], 'source_url': manifest['source_url'],
                'attribution': manifest['attribution'], 'terms_url': 'https://creativecommons.org/licenses/by/4.0/',
                'usage_note': 'CC BY 4.0: retain attribution, source, license and modification notice. ' + derivation,
                'meaning': f'ISLAN author-labelled double-handed English letter {letter.upper()}, signer 1. Independent ISL review pending.',
                'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        updates = list(pool.map(import_letter, needed))
    current.update({item['text']: item for item in updates})
    source_manifest['candidates'] = [e for e in source_manifest['candidates'] if e.get('type') != 'alphabet'] + [current[k] for k in sorted(current)]
    temporary = source_path.with_suffix('.tmp')
    temporary.write_text(json.dumps(source_manifest, indent=2), encoding='utf-8'); temporary.replace(source_path)


if __name__ == '__main__':
    restore()
