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


def hwp5_paragraphs(data: bytes) -> list[str]:
    """구형 한글(HWP 5.0, OLE 복합문서) 본문 — BodyText/SectionN 레코드 중 PARA_TEXT(태그 67)의 UTF-16 텍스트."""
    import olefile
    import struct
    import zlib
    ole = olefile.OleFileIO(io.BytesIO(data))
    header = ole.openstream("FileHeader").read()
    compressed = bool(header[36] & 1)
    sections = sorted((e for e in ole.listdir() if e[0] == "BodyText"), key=lambda e: int(re.sub(r"\D", "", e[1]) or 0))
    paras = []
    for e in sections:
        raw = ole.openstream("/".join(e)).read()
        if compressed:
            raw = zlib.decompress(raw, -15)
        i = 0
        while i + 4 <= len(raw):
            h = struct.unpack_from("<I", raw, i)[0]
            tag, size = h & 0x3FF, (h >> 20) & 0xFFF
            i += 4
            if size == 0xFFF:
                size = struct.unpack_from("<I", raw, i)[0]
                i += 4
            if tag == 67:
                chars, j, buf = raw[i:i + size], 0, []
                while j + 2 <= len(chars):
                    c = struct.unpack_from("<H", chars, j)[0]
                    if c < 32:   # 제어 문자: 확장 제어는 16바이트(8글자) 차지
                        j += 16 if c in (1, 2, 3, 11, 12, 14, 15, 16, 17, 18, 21, 22, 23) else 2
                        if c in (10, 13):
                            buf.append("\n")
                        continue
                    buf.append(chr(c))
                    j += 2
                line = "".join(buf).strip()
                if line:
                    paras.append(line)
            i += size
    return paras


def load_hwp5(data: bytes, doc_id: str) -> Document:
    return Document(doc_id, paginate(hwp5_paragraphs(data)))


def sniff(data: bytes, filename: str = "") -> str:
    """확장자가 아니라 내용으로 형식을 판별한다(실측: NST 첨부 .hwp가 실제로는 HWPX zip)."""
    if data[:5] == b"%PDF-":
        return "pdf"
    if data[:4] == b"PK\x03\x04":
        return "hwpx"
    if data[:8] == bytes.fromhex("D0CF11E0A1B11AE1"):
        return "hwp5"
    head = data[:2048].lstrip().lower()
    if head.startswith(b"<!doctype html") or head.startswith(b"<html"):
        return "html"
    return Path(filename).suffix.lower().lstrip(".") or "txt"


def load_text(data: bytes, doc_id: str) -> Document:
    return Document(doc_id, paginate(data.decode("utf-8", "ignore").split("\n")))


def load_bytes(data: bytes, filename: str, doc_id: str | None = None) -> Document:
    doc_id = doc_id or Path(filename).stem
    kind = sniff(data, filename)
    if kind == "pdf":
        return load_pdf(data, doc_id)
    if kind == "hwpx":
        return load_hwpx(data, doc_id)
    if kind == "hwp5":
        return load_hwp5(data, doc_id)
    if kind == "html":
        from .fetch import html_text
        return Document(doc_id, paginate(html_text(data.decode("utf-8", "ignore")).split("\n")))
    return load_text(data, doc_id)


def load_path(path: str | Path, doc_id: str | None = None) -> Document:
    p = Path(path)
    return load_bytes(p.read_bytes(), p.name, doc_id)
