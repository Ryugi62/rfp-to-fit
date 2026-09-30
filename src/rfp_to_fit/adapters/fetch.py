"""링크로 공고 가져오기 — 공고 파일 직링크면 그대로, 게시판 공지 페이지면 첨부 중 「공고문」을 골라 내려받는다.
(예선 기획서 약속: [입력] 공고 URL/PDF/HWPX)"""
from __future__ import annotations

import html as H
import re
from dataclasses import dataclass, field
from urllib.parse import unquote, urljoin

import httpx

UA = {"User-Agent": "Mozilla/5.0 (Macintosh) RFP-to-Fit/0.1 (+https://github.com/Ryugi62/rfp-to-fit)"}
_A = re.compile(r"<a\b([^>]*)>(.*?)</a>", re.S | re.I)
_HREF = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.I)
_FILE = re.compile(r"\.(pdf|hwpx|hwp)\b", re.I)


@dataclass
class Attachment:
    name: str
    url: str
    score: float = 0.0


@dataclass
class Fetched:
    url: str
    filename: str
    data: bytes
    page_title: str = ""
    attachments: list[Attachment] = field(default_factory=list)   # 공지 페이지였다면 발견한 첨부 전체
    chosen: Attachment | None = None
    parts: list[tuple[str, bytes]] = field(default_factory=list)   # 공고문이 여러 파일로 나뉜 경우 전부(순서대로)


def html_text(s: str) -> str:
    s = re.sub(r"<(script|style)\b.*?</\1>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</tr>", "\n", s, flags=re.I)
    s = H.unescape(re.sub(r"<[^>]+>", " ", s))
    return "\n".join(l.strip() for l in s.splitlines() if l.strip())


def score_name(name: str) -> float:
    """공고문일수록 높게, 서식·신청서·포스터일수록 낮게. 같은 점수면 PDF > HWPX > HWP."""
    n = name.lower()
    sc = 0.0
    for kw, w in [("공고문", 5), ("공고", 3), ("제안요구서", 4), ("rfp", 4), ("지원 공고", 2), ("시행계획", 1)]:
        if kw in n:
            sc += w
    for kw, w in [("서식", -4), ("양식", -4), ("신청서", -3), ("제출서류", -3), ("가이드", -2), ("매뉴얼", -3),
                  ("포스터", -5), ("동의서", -4), ("서약서", -4), ("faq", -2), ("q&a", -2)]:
        if kw in n:
            sc += w
    ext = _FILE.search(n)
    sc += {"pdf": 0.3, "hwpx": 0.2, "hwp": 0.1}.get(ext.group(1).lower(), -9) if ext else -9
    return sc


_ONCLICK = re.compile(r"""onclick\s*=\s*["'][^"']*?\(\s*'?(\d+)'?\s*,\s*'?(\d+)'?""", re.I)


def find_attachments(page_html: str, base_url: str) -> list[Attachment]:
    """<a href>의 첨부 + 스크립트 다운로드(과기정통부형 onclick="fn(첨부번호, 순번)" → POST /ssm/file/fileDown.do)."""
    from urllib.parse import urlsplit
    out, seen = [], set()
    origin = "{0.scheme}://{0.netloc}".format(urlsplit(base_url))
    for attrs, inner in _A.findall(page_html):
        m = _HREF.search(attrs)
        if not m:
            continue
        href = H.unescape(m.group(1)).strip()
        oc = _ONCLICK.search(attrs)
        if href.startswith("javascript") and oc:
            href = f"POST {origin}/ssm/file/fileDown.do?atchFileNo={oc.group(1)}&fileOrd={oc.group(2)}&fileBtn=A"
        name = re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", inner))).strip()
        target = name if _FILE.search(name) else unquote(href)
        if not _FILE.search(target) or href.startswith(("javascript:", "#", "mailto:")):
            continue
        url = href if href.startswith("POST ") else urljoin(base_url, href)
        if url in seen:
            continue
        seen.add(url)
        fname = _FILE.search(name) and name or unquote(href.rsplit("/", 1)[-1])
        fname = re.sub(r"\s*\[[\d.,]+\s*[KMG]?B\]\s*$", "", fname, flags=re.I)   # 「[140.6 KB]」 꼬리 제거
        out.append(Attachment(fname, url, score_name(fname)))
    return sorted(out, key=lambda a: -a.score)


def _filename(resp: httpx.Response, fallback: str) -> str:
    cd = resp.headers.get("content-disposition", "")
    m = re.search(r"filename\*?=(?:UTF-8'')?\"?([^\";]+)", cd, re.I)
    return unquote(m.group(1)).strip() if m else fallback


def fetch_url(url: str, timeout: float = 30) -> Fetched:
    with httpx.Client(follow_redirects=True, headers=UA, timeout=timeout, verify=False) as c:
        r = c.get(url)
        r.raise_for_status()
        ctype = r.headers.get("content-type", "").lower()
        is_page = "text/html" in ctype and not r.content[:5] == b"%PDF-"
        if not is_page:
            return Fetched(url, _filename(r, unquote(url.rsplit("/", 1)[-1].split("?")[0]) or "rfp"), r.content)
        page = r.text
        title = html_text(re.search(r"<title>(.*?)</title>", page, re.S | re.I).group(1)) if "<title" in page.lower() else ""
        atts = find_attachments(page, str(r.url))
        good = [a for a in atts if a.score >= 0]
        if good:
            top = good[0].score
            # 같은 공고문이 PDF·HWPX로 겹쳐 올라오면 PDF만, 공고문이 (1)(2)로 나뉘면 전부 받는다
            same = [a for a in good if a.score >= top - 0.25]
            base = lambda a: _FILE.sub("", a.name).strip().lower()  # noqa: E731
            pick, bases = [], set()
            for a in sorted(same, key=lambda a: -a.score):
                if base(a) not in bases:
                    bases.add(base(a))
                    pick.append(a)
            parts = []
            for a in sorted(pick, key=lambda a: a.name)[:4]:
                try:
                    if a.url.startswith("POST "):
                        from urllib.parse import parse_qsl, urlsplit
                        u = urlsplit(a.url[5:])
                        f = c.post(f"{u.scheme}://{u.netloc}{u.path}", data=dict(parse_qsl(u.query)),
                                   headers={**UA, "Referer": str(r.url)})
                    else:
                        f = c.get(a.url, headers={**UA, "Referer": str(r.url)})
                    f.raise_for_status()
                    if f.content[:5] == b"%PDF-" or f.content[:4] == b"PK\x03\x04" or f.content[:4] == bytes.fromhex("D0CF11E0"):
                        parts.append((_filename(f, a.name), f.content))
                except httpx.HTTPError:
                    continue
            if parts:
                return Fetched(url, parts[0][0], parts[0][1], title, atts, pick[0], parts)
        # 첨부가 없으면 공지 본문 자체를 공고로 쓴다
        return Fetched(url, "page.html", r.content, title, atts, None)


def load_fetched(f: Fetched, doc_id: str = "url"):
    """여러 첨부면 쪽을 이어 붙인 하나의 문서로. 반환 (Document, 구성 설명)."""
    from ..application.ports import Document
    from .documents import load_bytes
    if not f.parts:
        d = load_bytes(f.data, f.filename, doc_id)
        return d, [(f.filename, 1, len(d.pages))]
    pages, spans = [], []
    for name, data in f.parts:
        d = load_bytes(data, name, doc_id)
        spans.append((name, len(pages) + 1, len(pages) + len(d.pages)))
        pages += d.pages
    return Document(doc_id, pages), spans
