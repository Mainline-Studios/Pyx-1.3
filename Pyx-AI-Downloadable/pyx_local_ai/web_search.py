"""DuckDuckGo HTML search — no API keys (same idea as Pyx Talk local web)."""

from __future__ import annotations

import html
import os
import re
import urllib.parse
import urllib.request


def _strip_html_fragment(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    return html.unescape(re.sub(r"\s+", " ", s).strip())


def _ddg_is_ad_link(href: str) -> bool:
    h = (href or "").lower()
    return "duckduckgo.com/y.js" in h or "ad_provider=" in h or "ad_domain=" in h


def _unwrap_duck_redirect(href: str) -> str:
    href = (href or "").strip()
    if not href:
        return ""
    href = html.unescape(href)
    if href.startswith("//"):
        href = "https:" + href
    if "duckduckgo.com/l/?" in href or "duckduckgo.com/l?" in href:
        try:
            q = urllib.parse.urlparse(href).query
            params = urllib.parse.parse_qs(q)
            if "uddg" in params:
                return urllib.parse.unquote(params["uddg"][0])
        except Exception:
            pass
    return href


def fetch_snippets(query: str) -> tuple[str, str | None, str | None]:
    """
    Returns (context_text, provider, error).
    context_text is markdown-ish lines for the model — not the final user reply.
    """
    query = (query or "").strip()[:500]
    if not query:
        return "", None, "empty query"

    max_results = 6
    try:
        max_results = max(1, min(int(os.environ.get("PYX13_WEB_MAX_RESULTS", "6")), 12))
    except ValueError:
        pass
    cap = min(max(int(os.environ.get("PYX13_WEB_CONTEXT_CHARS", "8000")), 2000), 32000)
    timeout = max(5, min(int(os.environ.get("PYX13_WEB_TIMEOUT", "22")), 45))

    ddg_url = (os.environ.get("PYX13_WEB_HTML_URL") or "https://html.duckduckgo.com/html/").strip()
    ua = (os.environ.get("PYX13_USER_AGENT") or "").strip() or (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
    form = urllib.parse.urlencode({"q": query, "b": ""}).encode("utf-8")
    req = urllib.request.Request(
        ddg_url,
        data=form,
        headers={
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://duckduckgo.com/",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            page = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return "", "local-web", str(e)[:300]

    blocks = re.findall(
        r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>(?s:.*?)class="result__snippet"[^>]*>(.*?)</a>',
        page,
        re.IGNORECASE | re.DOTALL,
    )
    lines: list[str] = []
    for href, title_html, snip_html in blocks:
        if _ddg_is_ad_link(href):
            continue
        url = _unwrap_duck_redirect(href)
        if _ddg_is_ad_link(url):
            continue
        title = _strip_html_fragment(title_html)
        snippet = _strip_html_fragment(snip_html)
        if not title and not snippet:
            continue
        lines.append(f"- {title}\n  {url}\n  {snippet[:1200]}")
        if len(lines) >= max_results:
            break

    if not lines:
        for m in re.finditer(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            page,
            re.IGNORECASE | re.DOTALL,
        ):
            href = m.group(1)
            if _ddg_is_ad_link(href):
                continue
            url = _unwrap_duck_redirect(href)
            if _ddg_is_ad_link(url):
                continue
            title = _strip_html_fragment(m.group(2))
            if title or url:
                lines.append(f"- {title}\n  {url}\n  ")
            if len(lines) >= max_results:
                break

    text = "\n".join(lines).strip()
    if not text:
        return "", "local-web", "no results (blocked, empty query, or page layout changed)"
    if len(text) > cap:
        text = text[:cap] + "\n…"
    return text, "local-web", None


def should_auto_search(user_text: str) -> bool:
    """Lightweight heuristic similar to Pyx Talk auto-web."""
    t = (user_text or "").strip().lower()
    if len(t) < 8:
        return False
    needles = (
        "latest", "news", "today", "yesterday", "this week", "2024", "2025", "2026",
        "price", "release date", "when did", "who won", "score", "weather",
    )
    if any(n in t for n in needles):
        return True
    if "?" in user_text and len(t) > 12:
        return any(
            k in t
            for k in ("when", "where", "who is", "what is the", "how many", "why did")
        )
    return False
