import json
import os
from pathlib import Path

IMAGE_MAP_PATH = Path(__file__).resolve().parent.parent / "images" / "image_map.json"
_IMAGES_DIR = IMAGE_MAP_PATH.parent
_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def _load_map() -> dict:
    if IMAGE_MAP_PATH.exists():
        return json.loads(IMAGE_MAP_PATH.read_text(encoding="utf-8"))
    return {}


def _save_map(m: dict) -> None:
    IMAGE_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    IMAGE_MAP_PATH.write_text(json.dumps(m, indent=2), encoding="utf-8")


def _key(tenant_id: int, filename: str) -> str:
    # Tenant-scoped key: two tenants uploading a document with the same
    # filename (e.g. "manual.pdf") must not overwrite each other's image
    # list. Filenames alone are not unique across tenants.
    return f"{tenant_id}:{filename}"


def add_document_images(tenant_id: int, filename: str, image_filenames: list[str]) -> None:
    m = _load_map()
    m[_key(tenant_id, filename)] = image_filenames
    _save_map(m)


def get_document_images(tenant_id: int, filename: str) -> list[str]:
    return _load_map().get(_key(tenant_id, filename), [])


def remove_document_images(tenant_id: int, filename: str) -> None:
    m = _load_map()
    key = _key(tenant_id, filename)
    if key in m:
        del m[key]
        _save_map(m)


def cleanup_image_files(image_filenames: list[str]) -> None:
    for name in image_filenames:
        p = _IMAGES_DIR / name
        if p.exists():
            p.unlink()
