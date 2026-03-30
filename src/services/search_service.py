import io
from typing import List, Tuple
from PyPDF2 import PdfReader
import docx


from src.api.onedrive_client import search_onedrive, download_file_content

def extract_text_from_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def extract_text_from_docx(data: bytes) -> str:
    buf = io.BytesIO(data)
    d = docx.Document(buf)
    return "\n".join(p.text for p in d.paragraphs)

def extract_text_from_bytes(data: bytes, filename: str) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(data)
    if name.endswith(".docx"):
        return extract_text_from_docx(data)
    return data.decode("utf-8", errors="ignore")

def get_context_from_onedrive(access_token: str, query: str, max_files: int = 3) -> Tuple[str, List[str]]:
    items = search_onedrive(access_token, query)

    if not items:
        # No items or Graph error; return empty context
        return "", []

    selected = items[:max_files]

    contexts = []
    filenames = []
    for item in selected:
        # skip folders
        if "file" not in item:
            continue

        item_id = item["id"]
        name = item.get("name", "unknown")
        file_bytes = download_file_content(access_token, item_id)
        text = extract_text_from_bytes(file_bytes, name)
        if text.strip():
            contexts.append(f"--- {name} ---\n{text[:8000]}")
            filenames.append(name)

    if not contexts:
        return "", filenames

    full_context = "\n\n".join(contexts)[:20000]
    return full_context, filenames
