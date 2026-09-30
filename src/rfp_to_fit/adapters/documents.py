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


def hwpx_text(xml: str) -> list[str]:
    """section XML → 문단 텍스트 목록. <hp:t> 안의 줄바꿈·탭·중첩 태그는 걷어낸다."""
    out = []
    for p in re.findall(r"<hp:p\b.*?</hp:p>", xml, re.S):
        runs = []
        for t in re.findall(r"<hp:t(?:\s[^>]*)?>(.*?)</hp:t>", p, re.S):
            t = re.sub(r"<hp:lineBreak\s*/>", "\n", t)
            t = re.sub(r"<hp:tab[^>]*/>", " ", t)
            t = re.sub(r"<[^>]+>", "", t)
            runs.append(t)
        line = "".join(runs).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").strip()
        if line:
            out.append(line)
    return out


def paginate(paras: list[str], size: int = 3000) -> list[str]:
    """쪽 개념이 없는 문서(HWPX·텍스트)는 문단 경계에서 약 size자씩 끊어 「구간」을 쪽처럼 쓴다."""
    pages, buf, n = [], [], 0
    for para in paras:
        if buf and n + len(para) > size:
            pages.append("\n".join(buf))
            buf, n = [], 0
        buf.append(para)
        n += len(para)
    if buf:
        pages.append("\n".join(buf))
    return pages or [""]


def load_hwpx(data: bytes, doc_id: str) -> Document:
    z = zipfile.ZipFile(io.BytesIO(data))
    names = sorted((n for n in z.namelist() if re.match(r"Contents/section\d+\.xml", n)),
                   key=lambda n: int(re.findall(r"\d+", n)[0]))
    paras = []
    for n in names:
        paras += hwpx_text(z.read(n).decode("utf-8", "ignore"))
    return Document(doc_id, paginate(paras))


def load_text(data: bytes, doc_id: str) -> Document:
    return Document(doc_id, paginate(data.decode("utf-8", "ignore").split("\n")))


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
