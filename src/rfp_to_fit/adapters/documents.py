"""문서 로더 — PDF(pdfplumber) · HWPX(ZIP+XML 직접 파싱) · 텍스트/마크다운."""
from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

from ..application.ports import Document


def load_pdf(data: bytes, doc_id: str) -> Document:
    import pdfplumber
    pages = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for p in pdf.pages:
            text = p.extract_text() or ""
            tables = []
            try:
                for t in p.extract_tables():
                    rows = [" | ".join((c or "").replace("\n", " ") for c in row) for row in t if any(row)]
                    if rows:
                        tables.append("\n".join(rows))
            except Exception:
                pass
            if tables:   # 표는 셀 순서가 섞이므로 행 단위로 한 번 더 붙인다
                text += "\n\n[표]\n" + "\n\n".join(tables)
            pages.append(text)
    return Document(doc_id, pages)


def load_hwpx(data: bytes, doc_id: str) -> Document:
    z = zipfile.ZipFile(io.BytesIO(data))
    names = sorted(n for n in z.namelist() if re.match(r"Contents/section\d+\.xml", n))
    pages = []
    for n in names:
        xml = z.read(n).decode("utf-8", "ignore")
        paras = re.findall(r"<hp:p\b.*?</hp:p>", xml, re.S)
        lines = ["".join(re.findall(r"<hp:t[^>]*>(.*?)</hp:t>", p, re.S)) for p in paras]
        pages.append("\n".join(l for l in lines if l.strip()))
    return Document(doc_id, pages)


def load_text(data: bytes, doc_id: str) -> Document:
    return Document(doc_id, [data.decode("utf-8", "ignore")])


def load_bytes(data: bytes, filename: str, doc_id: str | None = None) -> Document:
    doc_id = doc_id or Path(filename).stem
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return load_pdf(data, doc_id)
    if ext == ".hwpx":
        return load_hwpx(data, doc_id)
    return load_text(data, doc_id)


def load_path(path: str | Path, doc_id: str | None = None) -> Document:
    p = Path(path)
    return load_bytes(p.read_bytes(), p.name, doc_id)
