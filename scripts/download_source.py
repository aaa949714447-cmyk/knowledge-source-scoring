#!/usr/bin/env python3
"""Download and score a web source for beginner knowledge-note synthesis.

This helper intentionally does not call any LLM, OCR, or multimodal model.
It captures source evidence, applies a conservative rule-based score, and
prints JSON that the agent can use in a single Markdown knowledge note.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


BLOCK_TAGS = {
    "address",
    "article",
    "blockquote",
    "br",
    "dd",
    "div",
    "dl",
    "dt",
    "figcaption",
    "figure",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "li",
    "main",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "td",
    "th",
    "tr",
    "ul",
}
SKIP_TAGS = {"script", "style", "noscript", "svg", "canvas", "iframe", "nav", "header", "footer", "aside"}
NOISE_LINE_PATTERNS = [
    r"^github(?: \(opens in a new tab\))?$",
    r"^discord(?: \(opens in a new tab\))?$",
    r"^services$",
    r"^enroll now",
    r"^learn to build apps",
    r"^previous$",
    r"^next$",
    r"^edit this page",
    r"^on this page$",
    r"^提示技术$",
]


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in SKIP_TAGS:
            self.skip_stack.append(tag)
            return
        if self.skip_stack:
            return
        if tag in BLOCK_TAGS:
            self.parts.append("\n")
        if tag == "li":
            self.parts.append("- ")

    def handle_endtag(self, tag: str) -> None:
        if self.skip_stack:
            if self.skip_stack[-1] == tag:
                self.skip_stack.pop()
            return
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_stack:
            return
        text = data.strip()
        if text:
            self.parts.append(text)
            self.parts.append(" ")

    def text(self) -> str:
        raw = html.unescape("".join(self.parts))
        raw = re.sub(r"[ \t\r\f\v]+", " ", raw)
        raw = re.sub(r" *\n *", "\n", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        lines = []
        seen: set[str] = set()
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                if lines and lines[-1]:
                    lines.append("")
                continue
            low = line.lower().strip(" -*•")
            if any(re.search(pattern, low) for pattern in NOISE_LINE_PATTERNS):
                continue
            dedupe_key = re.sub(r"\s+", " ", low)
            if len(dedupe_key) < 80 and dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            lines.append(line)
        return "\n".join(lines).strip()


def env_proxy() -> str:
    for key in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    return ""


def should_use_proxy(url: str, proxy: str, no_proxy: bool) -> bool:
    if no_proxy or not proxy:
        return False
    host = urllib.parse.urlparse(url).hostname or ""
    return not urllib.request.proxy_bypass(host)


def fetch(url: str, timeout: int = 30, proxy: str = "", no_proxy: bool = False) -> tuple[str, bytes, dict[str, str]]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "KnowledgeSourceScoring/1.1 (+local research)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    if no_proxy:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    elif should_use_proxy(url, proxy, no_proxy):
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    else:
        opener = urllib.request.build_opener()
    with opener.open(req, timeout=timeout) as resp:
        final_url = resp.geturl()
        headers = {k.lower(): v for k, v in resp.headers.items()}
        data = resp.read()
    return final_url, data, headers


def decode_html(data: bytes, headers: dict[str, str]) -> str:
    content_type = headers.get("content-type", "")
    match = re.search(r"charset=([^;]+)", content_type, re.I)
    encodings = [match.group(1).strip()] if match else []
    encodings.extend(["utf-8", "gb18030", "latin-1"])
    for encoding in encodings:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def clean_inline(text: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_meta(html_text: str, name: str) -> str:
    patterns = [
        rf"<meta\b[^>]*(?:name|property)=[\"']{re.escape(name)}[\"'][^>]*content=[\"']([^\"']+)[\"'][^>]*>",
        rf"<meta\b[^>]*content=[\"']([^\"']+)[\"'][^>]*(?:name|property)=[\"']{re.escape(name)}[\"'][^>]*>",
    ]
    for pattern in patterns:
        match = re.search(pattern, html_text, re.I | re.S)
        if match:
            return html.unescape(match.group(1)).strip()
    return ""


def extract_title(html_text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.I | re.S)
    document_title = clean_inline(match.group(1)).strip() if match else ""
    meta_title = extract_meta(html_text, "og:title") or extract_meta(html_text, "twitter:title")
    if document_title and "nextra" not in document_title.lower():
        return document_title
    if meta_title and "nextra" not in meta_title.lower():
        return meta_title
    return document_title or meta_title or "untitled"


def extract_section(html_text: str) -> str:
    candidates = []
    for tag in ("article", "main"):
        for match in re.finditer(rf"<{tag}\b[^>]*>(.*?)</{tag}>", html_text, re.I | re.S):
            candidates.append(match.group(1))
    if candidates:
        return max(candidates, key=len)
    body = re.search(r"<body\b[^>]*>(.*?)</body>", html_text, re.I | re.S)
    return body.group(1) if body else html_text


def extract_text(html_text: str) -> str:
    extractor = TextExtractor()
    extractor.feed(extract_section(html_text))
    text = extractor.text()
    if len(text) > 200:
        return text
    fallback = clean_inline(html_text)
    return re.sub(r"\s+", " ", fallback).strip()


def extract_images(text: str, base_url: str) -> list[dict[str, str]]:
    images: list[dict[str, str]] = []
    for match in re.finditer(r"<img\b[^>]*>", text, re.I | re.S):
        tag = match.group(0)
        src_match = re.search(r"\bsrc=[\"']([^\"']+)[\"']", tag, re.I)
        if not src_match:
            continue
        alt_match = re.search(r"\balt=[\"']([^\"']*)[\"']", tag, re.I)
        src = urllib.parse.urljoin(base_url, html.unescape(src_match.group(1)))
        alt = html.unescape(alt_match.group(1)).strip() if alt_match else ""
        reason = classify_image(src, alt)
        images.append({"url": src, "alt": alt, "default_action": reason})
    return images


def classify_image(url: str, alt: str) -> str:
    low = f"{url} {alt}".lower()
    if any(x in low for x in ["logo", "avatar", "icon", "banner", "ads", "tracking", "pixel", "social"]):
        return "skip_by_default"
    if any(x in low for x in ["diagram", "chart", "table", "architecture", "workflow", "formula", "screenshot"]):
        return "may_need_multimodal_review"
    return "inventory_only"


def extract_author(html_text: str) -> str:
    return extract_meta(html_text, "author") or extract_meta(html_text, "article:author")


def extract_author_from_text(body_text: str) -> str:
    match = re.search(r"^Authors?:\s*(.+)$", body_text, re.I | re.M)
    if match:
        return match.group(1).strip()
    return ""


def extract_date(html_text: str) -> str:
    for key in ["article:modified_time", "article:published_time", "dateModified", "datePublished", "last-modified", "ms.date", "updated_at", "date"]:
        value = extract_meta(html_text, key)
        if value:
            return value
    match = re.search(r"<time\b[^>]*(?:datetime=[\"']([^\"']+)[\"'])?[^>]*>(.*?)</time>", html_text, re.I | re.S)
    if match:
        return (match.group(1) or clean_inline(match.group(2))).strip()
    return ""


def extract_date_from_text(body_text: str) -> str:
    match = re.search(r"\[Submitted on ([^\]]+)\]", body_text, re.I)
    if match:
        return match.group(1).strip()
    match = re.search(r"Last Updated:\s*([^\n]+)", body_text, re.I)
    if match:
        return match.group(1).strip()
    return ""


def infer_source_type(url: str, html_text: str, body_text: str) -> str:
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    combined = f"{host} {path} {extract_title(html_text).lower()} {body_text[:2000].lower()}"
    if ".edu" in host or "university" in combined:
        return "university_course"
    if any(x in host for x in ["arxiv.org", "acm.org", "ieee.org", "nature.com", "science.org"]):
        return "peer_reviewed_or_preprint"
    if any(x in host for x in ["w3.org", "ietf.org", "iso.org", "rfc-editor.org"]):
        return "standards_or_spec"
    if any(x in host for x in ["platform.openai.com", "docs.anthropic.com", "learn.microsoft.com", "cloud.google.com", "ai.google.dev", "docs.aws.amazon.com"]):
        return "official_docs"
    if "docs" in host or "/docs" in path or "documentation" in combined:
        return "official_docs"
    if "promptingguide.ai" in host or "developer.mozilla.org" in host or "web.dev" in host:
        return "reputable_technical_reference"
    if "github.com" in host:
        return "reputable_project_docs"
    if any(x in combined for x in ["buy now", "discount", "coupon", "enroll now", "limited offer"]):
        return "marketing_or_course_sales"
    if any(x in host for x in ["stackoverflow.com", "reddit.com", "quora.com"]):
        return "qna_or_forum"
    if "blog" in host or "/blog" in path:
        return "engineering_blog"
    return "unknown"


def score_source(source_type: str, title: str, url: str, body_text: str, author: str, published_at: str) -> dict[str, object]:
    type_authority = {
        "official_docs": 28,
        "standards_or_spec": 30,
        "peer_reviewed_or_preprint": 28,
        "university_course": 27,
        "reputable_technical_reference": 26,
        "reputable_project_docs": 22,
        "engineering_blog": 18,
        "community_blog": 13,
        "qna_or_forum": 10,
        "marketing_or_course_sales": 8,
        "aggregator_or_scraper": 5,
        "unknown": 5,
    }
    authority = type_authority.get(source_type, 5)
    publisher = urllib.parse.urlparse(url).netloc
    traceability = 6
    if publisher:
        traceability += 4
    if author:
        traceability += 4
    if published_at:
        traceability += 5
    if re.search(r"https?://|doi\.org|arxiv|references|参考|引用", body_text, re.I):
        traceability += 1
    traceability = min(traceability, 20)

    text_len = len(body_text)
    technical_depth = 5
    if text_len > 1500:
        technical_depth += 4
    if text_len > 5000:
        technical_depth += 4
    if re.search(r"示例|example|步骤|algorithm|方法|公式|代码|实验|evaluation|case study", body_text, re.I):
        technical_depth += 4
    if re.search(r"\b(19|20)\d{2}\b|等人|et al\.", body_text, re.I):
        technical_depth += 2
    if re.search(r"\n#{1,3} |\n- |\n\d+\. |```", body_text):
        technical_depth += 2
    technical_depth = min(technical_depth, 20)

    freshness = 6 if not published_at and source_type in {"official_docs", "reputable_technical_reference", "reputable_project_docs"} else 5 if not published_at else 8
    date_match = re.search(r"(20\d{2}|19\d{2})", published_at)
    if date_match:
        year = int(date_match.group(1))
        current_year = dt.datetime.now(dt.timezone.utc).year
        freshness = 10 if current_year - year <= 2 else 7 if current_year - year <= 5 else 4

    cross_validation = 0
    low = f"{title} {body_text[:3000]}".lower()
    bias_penalty = 0
    if any(x in low for x in ["discount", "coupon", "enroll now", "buy now", "sponsored"]):
        bias_penalty -= 5
    if source_type == "marketing_or_course_sales":
        bias_penalty -= 5

    breakdown = {
        "authority": authority,
        "traceability": traceability,
        "technical_depth": technical_depth,
        "freshness": freshness,
        "cross_validation": cross_validation,
        "bias_penalty": bias_penalty,
    }
    raw_score = sum(breakdown.values())
    score = max(0, min(100, raw_score))
    level = score_to_level(score)
    cap_reasons = []
    if not published_at and level == "A":
        level = "B"
        cap_reasons.append("缺少发布时间或更新时间，最高 B 级。")
    if source_type in {"engineering_blog", "community_blog"} and level in {"A", "B"}:
        level = "C"
        cap_reasons.append("单一博客来源按规则最高 C 级。")
    if source_type in {"unknown", "marketing_or_course_sales", "aggregator_or_scraper"} and level != "D":
        level = "C" if score >= 55 else "D"
        cap_reasons.append("来源类型权威性不足，需要人工复核。")
    return {"breakdown": breakdown, "score": score, "level": level, "cap_reasons": cap_reasons}


def score_to_level(score: int) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    return "D"


def first_evidence(text: str, max_chars: int = 1200) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    chosen: list[str] = []
    for line in lines:
        if len(line) < 20 and chosen:
            continue
        chosen.append(line)
        if len("\n".join(chosen)) >= max_chars:
            break
    return "\n".join(chosen)[:max_chars].strip()


def safe_slug(url: str, title: str) -> str:
    parsed = urllib.parse.urlparse(url)
    base = f"{parsed.netloc}{parsed.path}".strip("/") or title
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", base).strip("-._")[:80]
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:10]
    return f"{base}-{digest}" if base else digest


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Download and score a source for beginner knowledge-note synthesis.")
    parser.add_argument("--url", required=True)
    parser.add_argument("--out", default="~/knowledge-source-scoring-workspace")
    parser.add_argument("--query", default="")
    parser.add_argument("--proxy", default=env_proxy(), help="HTTP(S) proxy for external web fetches. Defaults to HTTPS_PROXY/HTTP_PROXY env vars.")
    parser.add_argument("--no-proxy", action="store_true", help="Disable proxy use for this fetch.")
    parser.add_argument("--obsidian-vault", default="", help="Optional Obsidian vault root path. Creates topic folders only; source artifacts are not written to Obsidian.")
    parser.add_argument("--obsidian-folder", default="AI_Knowledge_Base", help="Folder inside the Obsidian vault.")
    args = parser.parse_args()

    out_root = Path(args.out).expanduser()
    proxy_used = should_use_proxy(args.url, args.proxy, args.no_proxy)
    final_url, data, headers = fetch(args.url, proxy=args.proxy, no_proxy=args.no_proxy)
    html_text = decode_html(data, headers)
    title = extract_title(html_text)
    body_text = extract_text(html_text)
    images = extract_images(html_text, final_url)
    author = extract_author(html_text) or extract_author_from_text(body_text)
    published_at = extract_date(html_text) or extract_date_from_text(body_text)
    source_type = infer_source_type(final_url, html_text, body_text)
    scoring = score_source(source_type, title, final_url, body_text, author, published_at)
    slug = safe_slug(final_url, title)
    collected_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    evidence = first_evidence(body_text)

    source_dir = out_root / "sources" / slug
    for directory in [source_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    review_status = "needs_review"
    allowed_for_formal_kb = False
    reason_parts = list(scoring["cap_reasons"])
    if scoring["level"] in {"A", "B"}:
        reason_parts.append("来源达到 A/B，但单来源未满足 2 个独立来源交叉验证，写笔记前仍需交叉验证。")
        allowed_for_formal_kb = False
    elif scoring["level"] == "C":
        reason_parts.append("C 级来源只能作为例子或线索，需要人工复核或补充独立来源。")
    else:
        review_status = "rejected"
        reason_parts.append("D 级来源默认拒绝进入知识笔记。")
    review_reason = " ".join(reason_parts) if reason_parts else "需要人工确认知识点和交叉验证状态。"

    (source_dir / "raw.html").write_bytes(data)
    (source_dir / "text.txt").write_text(body_text, encoding="utf-8")
    write_json(source_dir / "images.json", images)
    metadata = {
        "title": title,
        "source_url": final_url,
        "requested_url": args.url,
        "publisher": urllib.parse.urlparse(final_url).netloc,
        "author": author,
        "published_or_updated_at": published_at,
        "source_type": source_type,
        "source_score": scoring["score"],
        "source_level": scoring["level"],
        "review_status": review_status,
        "allowed_for_formal_kb": allowed_for_formal_kb,
        "content_type": headers.get("content-type", ""),
        "collected_at": collected_at,
        "text_chars": len(body_text),
        "image_count": len(images),
        "multimodal_used": False,
        "multimodal_note": "Images are inventoried only. Use multimodal/OCR only after policy review.",
        "proxy_used": proxy_used,
    }
    write_json(source_dir / "metadata.json", metadata)

    source_entry = {
        "source_url": final_url,
        "source_title": title,
        "source_type": source_type,
        "publisher": metadata["publisher"],
        "author": author,
        "published_or_updated_at": published_at,
        "claim_supported": args.query,
        "evidence_excerpt": evidence,
        "scoring_breakdown": scoring["breakdown"],
        "source_score": scoring["score"],
        "source_level": scoring["level"],
        "image_inventory": {
            "total_images": len(images),
            "skipped_images": [img for img in images if img["default_action"] == "skip_by_default"],
            "images_requiring_multimodal": [img for img in images if img["default_action"] == "may_need_multimodal_review"],
        },
        "multimodal_usage": {"used": False, "model": "", "reason": ""},
        "risk_notes": review_reason,
    }
    scorecard = {
        "query": args.query,
        "retrieved_at": collected_at[:10],
        "candidate_sources": [source_entry],
        "cross_validation": {"matched_claims": [], "conflicts": []},
        "decision": {
            "review_status": review_status,
            "reason": review_reason,
            "allowed_for_formal_kb": allowed_for_formal_kb,
        },
    }
    obsidian_output: dict[str, str] = {}
    if args.obsidian_vault:
        base = Path(args.obsidian_vault).expanduser() / (args.obsidian_folder.strip("/\\") or "AI_Knowledge_Base")
        for topic in ["提示词工程", "大模型基础", "RAG知识", "Agent知识"]:
            (base / topic).mkdir(parents=True, exist_ok=True)
        obsidian_output = {"obsidian_base": str(base)}

    print(
        json.dumps(
            {
                "ok": True,
                "source_dir": str(source_dir),
                "scorecard": scorecard,
                **obsidian_output,
                **metadata,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
