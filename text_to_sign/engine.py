"""Deterministic phrase/word/fingerspelling retrieval with explicit review gates."""
from __future__ import annotations

import json
import hashlib
import re
import unicodedata
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parent
CHECKS = ("playable", "label_checked", "isl_reviewed", "usage_approved")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    if any(c.isalpha() and not ('a' <= c <= 'z') for c in text):
        raise ValueError("Please use English A–Z text. Other writing systems are not supported yet.")
    text = text.replace("’", "'").replace("–", " ").replace("—", " ")
    # Join contractions; treat other punctuation as boundaries so hello,world stays two words.
    text = re.sub(r"(?<=[a-z])'(?=[a-z])", "", text)
    text = re.sub(r"[^a-z0-9\-\s]", " ", text)
    text = re.sub(r"(?<![a-z0-9])-|-(?![a-z0-9])", " ", text)
    return " ".join(text.split())


def safe_asset(path: str, root: Path = ROOT) -> Path:
    if not path or "\\" in path or ":" in path or Path(path).is_absolute():
        raise ValueError("Invalid asset path")
    parts = Path(path).parts
    if not parts or parts[0] != "signs" or ".." in parts:
        raise ValueError("Assets must be inside signs/")
    candidate = (root / path).resolve()
    if not candidate.is_relative_to((root / "signs").resolve()):
        raise ValueError("Asset path escapes signs/")
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError("Asset directory escapes the project")
    if candidate.suffix.lower() not in {".mp4", ".webm"}:
        raise ValueError("Unsupported media type")
    return candidate


def is_ready(entry: dict) -> bool:
    return (
        entry.get("status") == "READY"
        and all(entry.get("checks", {}).get(key) is True for key in CHECKS)
        and bool(entry.get("reviewed_by"))
        and bool(entry.get("reviewed_on"))
        and bool(entry.get("source_url"))
        and bool(entry.get("attribution"))
        and bool(re.fullmatch(r"[a-f0-9]{64}", entry.get("sha256", "")))
    )


class Dictionary:
    def __init__(self, root: Path = ROOT):
        self.root = root
        self._digests = {}
        self._registry_stamp = None
        self._entries = None

    def entries(self) -> list[dict]:
        registry = self.root / "data" / "signs.json"
        stat = registry.stat()
        stamp = (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
        if self._registry_stamp == stamp:
            return self._entries
        raw = json.loads(registry.read_text(encoding="utf-8"))
        entries = raw["entries"]
        seen = set()
        ids = set()
        for entry in entries:
            key = normalize(entry["text"])
            namespace = 'alphabet' if entry.get('type') == 'alphabet' else 'lexical'
            identity = (namespace, key)
            if not key or identity in seen:
                raise ValueError(f"Empty or duplicate dictionary key: {key}")
            seen.add(identity)
            if not re.fullmatch(r"[A-Za-z0-9_-]+", entry.get("id", "")) or entry["id"] in ids:
                raise ValueError("Dictionary IDs must be unique URL-safe identifiers")
            ids.add(entry["id"])
            if entry.get("type") not in {"word", "phrase", "alphabet"}:
                raise ValueError("Unknown dictionary entry type")
            if entry["type"] == "alphabet" and not re.fullmatch(r"[a-z]", key):
                raise ValueError("Alphabet entries must contain a single English letter")
            for alias in entry.get('aliases', []):
                if not isinstance(alias, str) or not normalize(alias):
                    raise ValueError('Dictionary aliases must contain English text')
            safe_asset(entry["file"], self.root)
        self._registry_stamp, self._entries = stamp, entries
        return entries

    def available(self, entry: dict, preview: bool = False) -> bool:
        if entry.get('status') == 'REJECTED':
            return False
        # Source preview is explicit and still requires provenance, usage and playable media.
        checks = entry.get("checks", {})
        allowed = is_ready(entry) or (
            preview and checks.get("playable") is True
            and checks.get("usage_approved") is True
            and bool(entry.get("source_url")) and bool(entry.get("attribution"))
        )
        if not allowed:
            return False
        path = safe_asset(entry["file"], self.root)
        try:
            stat = path.stat()
            if not path.is_file():
                return False
            expected = entry.get("sha256")
            if expected:
                key = (str(path), stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
                digest = self._digests.get(key)
                if digest is None:
                    with path.open("rb") as source:
                        digest = hashlib.file_digest(source, "sha256").hexdigest()
                    # Bound the cache; replaced files need not accumulate indefinitely.
                    if len(self._digests) >= 4096:
                        self._digests.clear()
                    self._digests[key] = digest
                return digest == expected
            return not is_ready(entry)
        except OSError:
            return False

    def inventory(self) -> dict:
        entries = self.entries()
        items = [{
            "id": e["id"], "text": e["text"], "type": e["type"],
            "meaning": e.get("meaning", ""), "ready": self.available(e),
            "previewable": self.available(e, True), "status": e.get("status", "PENDING"),
            "source_url": e.get("source_url", ""), "attribution": e.get("attribution", ""),
            "checks": e.get("checks", {}),
            "category": e.get("category", "Alphabet" if e["type"] == "alphabet" else "Everyday signs"),
            "aliases": e.get('aliases', []),
        } for e in entries]
        return {"entries": items, "total": len(items),
                "alphabet_ready": sum(e["ready"] and e["type"] == "alphabet" for e in items),
                "alphabet_previewable": sum(e["previewable"] and e["type"] == "alphabet" for e in items),
                "ready": sum(e["ready"] for e in items),
                "previewable": sum(e["previewable"] for e in items)}

    def convert(self, text: str, fingerspell: bool = True, preview: bool = False) -> dict:
        started = perf_counter()
        normalized = normalize(text)
        if not normalized:
            raise ValueError("Please enter English text to convert.")
        tokens = normalized.split()
        if len(tokens) > 200:
            raise ValueError("Please use 200 words or fewer per sequence.")
        entries = self.entries()
        index = {normalize(e["text"]): e for e in entries if e["type"] != "alphabet"}
        for entry in entries:
            if entry['type'] != 'alphabet':
                for alias in entry.get('aliases', []):
                    index.setdefault(normalize(alias), entry)
        letters = {normalize(e["text"]): e for e in entries if e["type"] == "alphabet"}
        max_phrase = max((len(k.split()) for k in index), default=1)
        queue, warnings = [], []
        matched = 0

        def item(entry: dict, original: str, spelling: bool = False) -> dict:
            return {"id": entry["id"], "text": entry["text"], "input": original,
                    "type": "alphabet" if spelling else entry["type"],
                    "url": f"/api/media/{entry['id']}", "ready": is_ready(entry),
                    "source_url": entry.get("source_url", ""),
                    "attribution": entry.get("attribution", "")}

        i = 0
        while i < len(tokens):
            found = None
            # Evaluate phrases at every offset, including phrases following ordinary words.
            for size in range(min(max_phrase, len(tokens) - i), 0, -1):
                key = " ".join(tokens[i:i + size])
                entry = index.get(key)
                if entry is not None and self.available(entry, preview):
                    found = (entry, key, size)
                    break
            if found:
                entry, key, size = found
                queue.append(item(entry, key))
                matched += size
                i += size
                continue
            word = tokens[i]
            # Fingerspelling is atomic: never emit a partial spelling or drop digits/hyphens.
            if fingerspell and re.fullmatch(r"[a-z]+", word) and all(
                c in letters and self.available(letters[c], preview) for c in word
            ):
                queue.extend(item(letters[c], word, True) for c in word)
                matched += 1
            else:
                known = word in index
                warnings.append({"term": word, "code": "ASSET_UNAVAILABLE" if known else "UNSUPPORTED_TERM",
                                 "message": f'No available {"approved " if not preview else ""}sign or complete spelling for “{word}”.'})
            i += 1
            if len(queue) > 1000:
                raise ValueError("This message produces over 1,000 signs. Please split it into smaller messages.")
        return {"normalized": normalized, "sequence": queue, "warnings": warnings,
                "input_words": len(tokens), "matched_words": matched,
                "coverage": round(matched / len(tokens) * 100), "preview": preview,
                "elapsed_ms": round((perf_counter() - started) * 1000, 2)}
