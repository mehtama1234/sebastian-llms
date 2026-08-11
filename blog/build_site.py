#!/usr/bin/env python3
"""Render the blog markdown into a small, self-contained static site.

No third-party dependencies. Handles the markdown subset the posts use:
headings, paragraphs, bold, inline code, fenced code, tables, bullet and
numbered lists, blockquotes, and links. Intra-series `.md` links are rewritten
to the generated `.html` pages.

Usage:
    python build_site.py            # build into ./site
    python build_site.py --serve    # build, then serve on http://localhost:8000
"""

from __future__ import annotations

import argparse
import html
import re
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BLOG_DIR = Path(__file__).resolve().parent
SITE_DIR = BLOG_DIR / "site"

# Page order and titles for the nav rail.
PAGES: list[tuple[str, str]] = [
    ("README.md", "Home"),
    ("01-why-this-lab-exists.md", "1. Why this lab exists"),
    ("02-how-the-benchmark-works.md", "2. How the benchmark works"),
    ("03-retrieval-grep-vs-vector.md", "3. Retrieval: grep vs vector"),
    ("04-context-delivery.md", "4. Context delivery"),
    ("05-repo-instructions.md", "5. Repo instructions"),
    ("06-verifier-and-bluffing.md", "6. The verifier"),
    ("07-test-time-scaling.md", "7. Test-time scaling"),
    ("08-putting-it-together.md", "8. Putting it together"),
]

# Hand-authored rich HTML pages (with inline SVG) copied verbatim into the site
# and linked in the nav. These are not markdown — they carry their own styling.
EXTRA_HTML: list[tuple[str, str]] = [
    ("deepseek-illustrated.html", "DeepSeek V3 → V3.2 · illustrated"),
]

_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
_CODE_RE = re.compile(r"`([^`]+)`")


def out_name(md_name: str) -> str:
    return "index.html" if md_name == "README.md" else md_name.replace(".md", ".html")


_NAME_MAP = {md: out_name(md) for md, _ in PAGES}


def render_inline(text: str) -> str:
    """Escape HTML then apply inline code, bold, and links. Code spans are
    protected with a placeholder so their contents are never re-parsed."""
    spans: list[str] = []

    def stash(match: re.Match) -> str:
        spans.append(f"<code>{html.escape(match.group(1))}</code>")
        return f"\x00{len(spans) - 1}\x00"

    text = _CODE_RE.sub(stash, text)
    text = html.escape(text)

    def link(match: re.Match) -> str:
        label, href = match.group(1), match.group(2)
        if not href.startswith(("http://", "https://", "#")):
            href = _NAME_MAP.get(href, href)
        return f'<a href="{href}">{label}</a>'

    # `label`/`href` were escaped above; unescape the couple of entities links use.
    text = _LINK_RE.sub(link, text)
    text = _BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], text)
    return text


def render_table(rows: list[str]) -> str:
    def cells(line: str) -> list[str]:
        return [c.strip() for c in line.strip().strip("|").split("|")]

    header = cells(rows[0])
    body = [cells(r) for r in rows[2:]]  # rows[1] is the |---| separator
    out = ["<table>", "<thead><tr>"]
    out += [f"<th>{render_inline(c)}</th>" for c in header]
    out.append("</tr></thead><tbody>")
    for r in body:
        out.append("<tr>" + "".join(f"<td>{render_inline(c)}</td>" for c in r) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def markdown_to_html(md: str) -> str:
    lines = md.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]

        # Fenced code block.
        if line.startswith("```"):
            code: list[str] = []
            i += 1
            while i < n and not lines[i].startswith("```"):
                code.append(html.escape(lines[i]))
                i += 1
            i += 1  # skip closing fence
            out.append(f"<pre><code>{chr(10).join(code)}</code></pre>")
            continue

        # Table: a header row followed by a |---| separator.
        if line.strip().startswith("|") and i + 1 < n and set(lines[i + 1].strip()) <= set("|-: "):
            table: list[str] = []
            while i < n and lines[i].strip().startswith("|"):
                table.append(lines[i])
                i += 1
            out.append(render_table(table))
            continue

        # Heading.
        m = re.match(r"(#{1,6})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            out.append(f"<h{level}>{render_inline(m.group(2))}</h{level}>")
            i += 1
            continue

        # Blockquote (possibly multi-line).
        if line.startswith(">"):
            quote: list[str] = []
            while i < n and lines[i].startswith(">"):
                quote.append(lines[i].lstrip(">").strip())
                i += 1
            out.append(f"<blockquote>{render_inline(' '.join(quote))}</blockquote>")
            continue

        # Unordered list.
        if re.match(r"\s*-\s+", line):
            items: list[str] = []
            while i < n and re.match(r"\s*-\s+", lines[i]):
                items.append(render_inline(re.sub(r"\s*-\s+", "", lines[i], count=1)))
                i += 1
            out.append("<ul>" + "".join(f"<li>{it}</li>" for it in items) + "</ul>")
            continue

        # Ordered list.
        if re.match(r"\s*\d+\.\s+", line):
            items = []
            while i < n and re.match(r"\s*\d+\.\s+", lines[i]):
                items.append(render_inline(re.sub(r"\s*\d+\.\s+", "", lines[i], count=1)))
                i += 1
            out.append("<ol>" + "".join(f"<li>{it}</li>" for it in items) + "</ol>")
            continue

        # Blank line.
        if not line.strip():
            i += 1
            continue

        # Paragraph: gather until a blank line or a block starter.
        para: list[str] = []
        while i < n and lines[i].strip() and not re.match(r"(#{1,6}\s|```|>|\s*-\s|\s*\d+\.\s)", lines[i]) and not lines[i].strip().startswith("|"):
            para.append(lines[i].strip())
            i += 1
        if para:
            out.append(f"<p>{render_inline(' '.join(para))}</p>")

    return "\n".join(out)


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
:root {{ --ink:#1f2328; --muted:#59636e; --line:#d8dee4; --accent:#8a5a2b; --bg:#fbf9f6; --card:#fff; --code:#f3efe9; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink);
  font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif; }}
.wrap {{ display:flex; gap:0; max-width:1100px; margin:0 auto; }}
nav {{ width:260px; flex:none; padding:32px 20px; border-right:1px solid var(--line);
  position:sticky; top:0; align-self:flex-start; height:100vh; overflow:auto; }}
nav h2 {{ font-size:13px; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin:0 0 14px; }}
nav a {{ display:block; padding:6px 10px; margin:2px 0; border-radius:7px; color:var(--ink);
  text-decoration:none; font-size:14px; }}
nav a:hover {{ background:var(--code); }}
nav a.active {{ background:var(--accent); color:#fff; }}
main {{ flex:1; min-width:0; padding:40px 48px 80px; }}
article {{ max-width:720px; }}
h1 {{ font-size:30px; line-height:1.25; margin:0 0 24px; }}
h2 {{ font-size:22px; margin:36px 0 12px; padding-bottom:6px; border-bottom:1px solid var(--line); }}
h3 {{ font-size:17px; margin:26px 0 8px; }}
p {{ margin:14px 0; }}
a {{ color:var(--accent); }}
code {{ background:var(--code); padding:2px 6px; border-radius:5px; font-size:14px;
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
pre {{ background:#2b2620; color:#f5efe6; padding:16px 18px; border-radius:10px; overflow:auto; }}
pre code {{ background:none; color:inherit; padding:0; }}
blockquote {{ margin:18px 0; padding:10px 18px; border-left:4px solid var(--accent);
  background:var(--card); color:var(--muted); border-radius:0 8px 8px 0; }}
table {{ border-collapse:collapse; width:100%; margin:18px 0; font-size:14.5px; }}
th,td {{ border:1px solid var(--line); padding:8px 12px; text-align:left; }}
thead th {{ background:var(--code); }}
ul,ol {{ padding-left:22px; }}
li {{ margin:5px 0; }}
.pager {{ display:flex; justify-content:space-between; margin-top:56px; padding-top:20px;
  border-top:1px solid var(--line); font-size:14px; }}
.pager a {{ text-decoration:none; }}
.pager span {{ color:var(--muted); }}
@media (max-width:820px) {{ .wrap {{ flex-direction:column; }} nav {{ width:auto; height:auto; position:static;
  border-right:none; border-bottom:1px solid var(--line); }} main {{ padding:28px 22px 60px; }} }}
</style>
</head>
<body>
<div class="wrap">
<nav>
<h2>2026 LLM lab</h2>
{navlinks}
</nav>
<main><article>
{body}
<div class="pager">{prev}{next}</div>
</article></main>
</div>
</body>
</html>
"""


def _navlinks(active: str) -> str:
    """Nav order: Home, the illustrated extra pages, then the numbered series."""
    links = [f'<a href="index.html" class="{"active" if active == "README.md" else ""}">Home</a>']
    for name, title in EXTRA_HTML:
        links.append(f'<a href="{name}" class="{"active" if active == name else ""}">{title}</a>')
    for md, title in PAGES[1:]:
        links.append(f'<a href="{out_name(md)}" class="{"active" if md == active else ""}">{title}</a>')
    return "\n".join(links)


def build() -> None:
    SITE_DIR.mkdir(exist_ok=True)
    # Copy hand-authored rich HTML pages verbatim.
    for name, _ in EXTRA_HTML:
        src = BLOG_DIR / name
        if src.exists():
            (SITE_DIR / name).write_text(src.read_text())
    navlinks_for = _navlinks
    for idx, (md, title) in enumerate(PAGES):
        src = BLOG_DIR / md
        if not src.exists():
            continue
        body = markdown_to_html(src.read_text())
        prev_html = ""
        next_html = ""
        if idx > 0:
            pmd, ptitle = PAGES[idx - 1]
            prev_html = f'<a href="{out_name(pmd)}">&larr; {ptitle}</a>'
        else:
            prev_html = "<span></span>"
        if idx < len(PAGES) - 1:
            nmd, ntitle = PAGES[idx + 1]
            next_html = f'<a href="{out_name(nmd)}">{ntitle} &rarr;</a>'
        else:
            next_html = "<span></span>"
        page = PAGE_TEMPLATE.format(
            title=title if md != "README.md" else "Building an experiment lab for 2026 LLM papers",
            navlinks=navlinks_for(md),
            body=body,
            prev=prev_html,
            next=next_html,
        )
        (SITE_DIR / out_name(md)).write_text(page)
    print(f"built {len(PAGES)} pages into {SITE_DIR}")


def serve(port: int = 8000) -> None:
    handler = partial(SimpleHTTPRequestHandler, directory=str(SITE_DIR))
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"serving blog at http://localhost:{port}  (Ctrl+C to stop)")
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true", help="serve after building")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    build()
    if args.serve:
        serve(args.port)
