"""Minimal self-contained HTML report renderer — standard library only.

Both modules in this repo render their human-readable report through this
helper, so the two reports share one visual language. No CSS framework, no
network fetch: the page is a single offline .html file.

API
---
    from report_html import esc, html_page, table

    body = [
        html_h2("Verdict"),
        html_p("A sentence of prose."),
        table(["Field", "Value"], [["vector_id", "70cbcb3d..."]]),
    ]
    html = html_page("ACS Verdict Evidence", body)
    open("reports/x.html", "w", encoding="utf-8").write(html)
"""
from __future__ import annotations

import html as _html
from typing import Iterable, Sequence


def esc(text: object) -> str:
    """HTML-escape any scalar; None renders as the literal 'null'."""
    if text is None:
        return "null"
    return _html.escape(str(text), quote=True)


def html_h2(text: str) -> str:
    return "<h2>%s</h2>" % esc(text)


def html_h3(text: str) -> str:
    return "<h3>%s</h3>" % esc(text)


def html_p(text: str) -> str:
    return "<p>%s</p>" % esc(text)


def html_code_block(text: str) -> str:
    return "<pre><code>%s</code></pre>" % esc(text)


def table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    """Build an HTML table; cells are escaped scalars."""
    out = ["<table>", "<thead><tr>"]
    out += ["<th>%s</th>" % esc(h) for h in headers]
    out += ["</tr></thead>", "<tbody>"]
    for row in rows:
        out.append("<tr>")
        out += ["<td>%s</td>" % esc(c) for c in row]
        out.append("</tr>")
    out += ["</tbody></table>"]
    return "".join(out)


_CSS = """
body { font-family: -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
       max-width: 960px; margin: 2rem auto; padding: 0 1rem; color: #1f2328; line-height: 1.55; }
h1 { border-bottom: 2px solid #d0d7de; padding-bottom: .3rem; }
h2 { margin-top: 2rem; color: #0a3069; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
th, td { border: 1px solid #d0d7de; padding: .45rem .7rem; text-align: left; vertical-align: top; }
th { background: #f6f8fa; }
pre { background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px;
      padding: .8rem; overflow-x: auto; font-size: .85rem; }
.badge { display: inline-block; padding: .1rem .6rem; border-radius: 1em;
         font-size: .85rem; font-weight: 600; }
.rejected, .quarantined, .rejected-cell { background: #ffebe9; color: #a40e26; }
.pass, .none, .verified-cell { background: #dafbe1; color: #116329; }
.unresolved, .moderate { background: #fff8c5; color: #9a6700; }
.muted { color: #59636e; font-size: .9rem; }
"""


def html_page(page_title: str, body_blocks: Sequence[str]) -> str:
    """Wrap body blocks into a complete standalone HTML document."""
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n"
        "<h1>%s</h1>\n%s\n"
        "<p class=\"muted\">Generated offline by agent-evidence-kit; no network required.</p>\n"
        "</body>\n</html>\n"
        % (esc(page_title), _CSS, esc(page_title), "\n".join(body_blocks))
    )
