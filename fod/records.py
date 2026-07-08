"""JSON-backed session log for FOD clearance records."""
import json
import os
import uuid

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
LOG_PATH = os.path.join(DATA_DIR, "clearance_log.json")


def _ensure_dirs() -> None:
    os.makedirs(IMAGES_DIR, exist_ok=True)


def load_records() -> list:
    _ensure_dirs()
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_records(records: list) -> None:
    _ensure_dirs()
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def save_image(image_bytes: bytes, suffix: str) -> str:
    """Save an image to disk and return its relative path."""
    _ensure_dirs()
    filename = f"{uuid.uuid4().hex}_{suffix}.jpg"
    path = os.path.join(IMAGES_DIR, filename)
    with open(path, "wb") as f:
        f.write(image_bytes)
    return os.path.join("images", filename)


def add_record(record: dict) -> dict:
    """Append a finalized clearance record and persist it. Returns the record with an id."""
    records = load_records()
    record = dict(record)
    record["id"] = uuid.uuid4().hex
    records.append(record)
    _save_records(records)
    return record
