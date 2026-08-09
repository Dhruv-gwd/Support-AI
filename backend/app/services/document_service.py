import os
import shutil
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
from pypdf import PdfReader
import docx

IMAGE_STORE_DIR = Path("images")
IMAGE_STORE_DIR.mkdir(exist_ok=True)


def extract_text(file_path: str, filename: str) -> str:
    """Extract raw text from a pdf, docx, txt, csv, xlsx, md, or html file on disk."""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext == "pdf":
        return _extract_pdf(file_path)
    elif ext == "docx":
        return _extract_docx(file_path)
    elif ext == "txt":
        return _extract_txt(file_path)
    elif ext == "csv":
        return _extract_csv(file_path)
    elif ext in {"xlsx", "xls"}:
        return _extract_excel(file_path)
    elif ext == "md":
        return _extract_md(file_path)
    elif ext == "html":
        return _extract_html(file_path)
    else:
        raise ValueError(f"Unsupported file type: .{ext}")


def _extract_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)


def _extract_docx(file_path: str) -> str:
    document = docx.Document(file_path)
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def _extract_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _extract_csv(file_path: str) -> str:
    df = pd.read_csv(file_path)
    return df.to_string(index=False)


def _extract_excel(file_path: str) -> str:
    df = pd.read_excel(file_path)
    return df.to_string(index=False)


def _extract_md(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _extract_html(file_path: str) -> str:
    try:
        from bs4 import BeautifulSoup
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
            return soup.get_text(separator="\n\n", strip=True)
    except ImportError:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()


def extract_images(file_path: str, filename: str) -> list[str]:
    """Extract images from a document and save them to IMAGE_STORE_DIR.
    Returns a list of filenames relative to IMAGE_STORE_DIR.
    """
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    saved = []

    if ext == "docx":
        saved = _extract_images_from_docx(file_path)
    elif ext == "pdf":
        saved = _extract_images_from_pdf(file_path)

    return saved


def _extract_images_from_docx(file_path: str) -> list[str]:
    saved = []
    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            media_files = [name for name in zf.namelist() if name.startswith("word/media/")]
            for media_name in media_files:
                ext = media_name.rsplit(".", 1)[-1].lower()
                if ext not in {"png", "jpg", "jpeg", "gif", "bmp", "webp"}:
                    continue
                data = zf.read(media_name)
                out_name = f"{Path(file_path).stem}_{media_name.replace('/', '_')}"
                out_path = IMAGE_STORE_DIR / out_name
                out_path.write_bytes(data)
                saved.append(out_name)
    except Exception as e:
        print(f"Warning: failed to extract images from DOCX: {e}")
    return saved


def _extract_images_from_pdf(file_path: str) -> list[str]:
    saved = []
    try:
        reader = PdfReader(file_path)
        for page_index, page in enumerate(reader.pages):
            for image_index, image in enumerate(page.images):
                ext = image.name.lower().rsplit(".", 1)[-1] if "." in image.name else "bin"
                if ext not in {"png", "jpg", "jpeg", "gif", "bmp", "webp"}:
                    ext = "bin"
                out_name = f"{Path(file_path).stem}_page{page_index + 1}_img{image_index + 1}.{ext}"
                out_path = IMAGE_STORE_DIR / out_name
                out_path.write_bytes(image.data)
                saved.append(out_name)
    except Exception as e:
        print(f"Warning: failed to extract images from PDF: {e}")
    return saved
