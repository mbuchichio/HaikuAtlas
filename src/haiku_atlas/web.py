"""Small local web UI for browsing a Haiku Atlas index."""

from __future__ import annotations

from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse
import sqlite3
import webbrowser

from haiku_atlas.db import initialize_database
from haiku_atlas.query import (
    ContainedSymbol,
    KitSymbol,
    get_index_status,
    get_symbol_page,
    list_kit_symbols,
    list_kits,
    search_symbols,
)

MAX_SEARCH_RESULTS = 50
MAX_KIT_SYMBOLS = 200


def serve(
    db_path: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser: bool = True,
) -> None:
    initialize_database(db_path)
    handler = _make_handler(db_path)
    server = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{server.server_port}/"
    print(f"atlas web: {url}")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\natlas web: stopped")
    finally:
        server.server_close()


def _make_handler(db_path: Path) -> type[BaseHTTPRequestHandler]:
    class AtlasWebHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            try:
                with sqlite3.connect(db_path) as connection:
                    status_code, body = _route(connection, parsed.path, parse_qs(parsed.query))
            except Exception as error:
                status_code = 500
                body = _page("Atlas error", f"<main><h1>Atlas error</h1><pre>{escape(str(error))}</pre></main>")

            self.send_response(status_code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            try:
                self.wfile.write(body.encode("utf-8"))
            except BrokenPipeError:
                return

        def log_message(self, format: str, *args: object) -> None:
            return

    return AtlasWebHandler


def _route(
    connection: sqlite3.Connection,
    path: str,
    query: dict[str, list[str]],
) -> tuple[int, str]:
    if path == "/":
        return 200, _render_home(connection)
    if path == "/search":
        term = query.get("q", [""])[0].strip()
        return 200, _render_search(connection, term)
    if path.startswith("/kit/"):
        kit_name = unquote(path.removeprefix("/kit/"))
        return _render_kit(connection, kit_name)
    if path.startswith("/symbol/"):
        symbol_name = unquote(path.removeprefix("/symbol/"))
        return _render_symbol(connection, symbol_name)
    return 404, _page("Not found", "<main><h1>Not found</h1></main>")


def _render_home(connection: sqlite3.Connection) -> str:
    status = get_index_status(connection)
    kits = list_kits(connection)
    kit_items = "\n".join(
        f'<a class="row" href="/kit/{quote(kit.name)}">'
        f"<span>{escape(kit.display_name)}</span>"
        f"<small>{kit.top_level_symbol_count} types · {kit.symbol_count} symbols</small>"
        "</a>"
        for kit in kits
    )
    if not kit_items:
        kit_items = '<p class="empty">No kits indexed. Run ./atlas-indexer /path/to/haiku.</p>'

    body = f"""
    <main>
      <section class="toolbar">
        <div>
          <h1>Haiku Atlas</h1>
          <p>{status.header_count} headers · {status.kit_count} kits · {status.symbol_count} symbols</p>
        </div>
        {_search_form()}
      </section>
      <section class="list">
        <section class="group">
          <h2>Kits</h2>
          {kit_items}
        </section>
      </section>
      {_recent_section()}
    </main>
    """
    return _page("Haiku Atlas", body)


def _render_search(connection: sqlite3.Connection, term: str) -> str:
    results = search_symbols(connection, term, limit=MAX_SEARCH_RESULTS) if term else []
    items = "\n".join(
        f'<a class="row" href="/symbol/{quote(result.qualified_name)}">'
        f"<span>{escape(result.qualified_name)}</span>"
        f"<small>{escape(_search_subtitle(result.kind, result.kit_display_name, result.file_path))}</small>"
        "</a>"
        for result in results
    )
    if not items:
        items = '<p class="empty">No matches.</p>' if term else '<p class="empty">Type a symbol name.</p>'

    body = f"""
    <main>
      <section class="toolbar">
        <div>
          <a class="crumb" href="/">Atlas</a>
          <h1>Search</h1>
        </div>
        {_search_form(term)}
      </section>
      <section class="list">
        {items}
      </section>
    </main>
    """
    return _page(f"Search {term}", body)


def _render_kit(connection: sqlite3.Connection, kit_name: str) -> tuple[int, str]:
    result = list_kit_symbols(connection, kit_name, limit=MAX_KIT_SYMBOLS)
    if result is None:
        return 404, _page("Kit not found", "<main><h1>Kit not found</h1></main>")

    kit, symbols = result
    grouped_symbols = _render_kit_symbol_groups(symbols)
    hidden = kit.top_level_symbol_count - len(symbols)
    more = f'<p class="empty">{hidden} more not shown.</p>' if hidden > 0 else ""
    body = f"""
    <main>
      <section class="toolbar">
        <div>
          <a class="crumb" href="/">Atlas</a>
          <h1>{escape(kit.display_name)}</h1>
          <p>{kit.top_level_symbol_count} top-level types · {kit.symbol_count} symbols</p>
        </div>
        {_search_form()}
      </section>
      <section class="list">
        {grouped_symbols}
        {more}
      </section>
    </main>
    """
    return 200, _page(kit.display_name, body)


def _render_symbol(connection: sqlite3.Connection, symbol_name: str) -> tuple[int, str]:
    page = get_symbol_page(connection, symbol_name)
    if page is None:
        return 404, _page("Symbol not found", "<main><h1>Symbol not found</h1></main>")

    detail = page.detail
    contained_groups = _render_contained_groups(page.contained_symbols)
    inherits = ", ".join(escape(base) for base in page.inherits)
    source_context = _doc_body(detail.docs, "source_context")
    body = f"""
    <main>
      <section class="toolbar">
        <div>
          <a class="crumb" href="/">Atlas</a>
          <h1>{escape(detail.display_name)}</h1>
          <p>{escape(detail.kind)} · {escape(detail.kit_display_name or "unknown kit")}</p>
        </div>
        {_search_form()}
      </section>
      <section class="detail">
        <dl>
          <dt>qualified</dt><dd>{escape(detail.qualified_name)}</dd>
          <dt>location</dt><dd>{escape(_location(detail.file_path, detail.line_start))}</dd>
          <dt>inherits</dt><dd>{inherits or "none"}</dd>
          <dt>context</dt><dd>{escape(source_context or "none")}</dd>
        </dl>
        {_declaration_block(detail.raw_declaration)}
      </section>
      <section class="list">
        {contained_groups or '<p class="empty">No child symbols indexed.</p>'}
      </section>
    </main>
    """
    return 200, _page(
        detail.display_name,
        body,
        recent_title=detail.display_name,
        recent_url=f"/symbol/{quote(detail.qualified_name)}",
    )


def _render_kit_symbol_groups(symbols: tuple[KitSymbol, ...]) -> str:
    sections = [
        ("class", "Classes"),
        ("struct", "Structs"),
        ("enum", "Enums"),
    ]
    rendered: list[str] = []
    for kind, title in sections:
        rows = [symbol for symbol in symbols if symbol.kind == kind]
        if not rows:
            continue
        items = "\n".join(
            f'<a class="row" href="/symbol/{quote(symbol.qualified_name)}">'
            f"<span>{escape(symbol.qualified_name)}</span>"
            f"<small>{escape(_location(symbol.file_path, symbol.line_start))}</small>"
            "</a>"
            for symbol in rows
        )
        rendered.append(f'<section class="group"><h2>{title}</h2>{items}</section>')
    return "\n".join(rendered)


def _render_contained_groups(symbols: tuple[ContainedSymbol, ...]) -> str:
    sections = [
        ("constructor", "Constructors"),
        ("destructor", "Destructors"),
        ("method", "Methods"),
    ]
    rendered: list[str] = []
    for kind, title in sections:
        rows = tuple(symbol for symbol in symbols if symbol.kind == kind)
        if not rows:
            continue
        rendered.append(f'<section class="group"><h2>{title}</h2>{_render_method_rows(rows)}</section>')
    return "\n".join(rendered)


def _render_method_rows(methods: tuple[ContainedSymbol, ...]) -> str:
    rows: list[str] = []
    for method in methods:
        display = method.qualified_name.rsplit("::", 1)[-1]
        subtitle = method.raw_declaration or method.qualified_name
        location = _location(method.file_path, method.line_start)
        context = _doc_body(method.docs, "source_context")
        meta = " · ".join(part for part in (context, location) if part)
        rows.append(
            f'<a class="method-row" href="/symbol/{quote(method.qualified_name)}">'
            f'<span class="method-name">{escape(display)}</span>'
            f'<span class="method-signature">{escape(subtitle)}</span>'
            f'<small>{escape(meta)}</small>'
            "</a>"
        )
    return "\n".join(rows)


def _search_form(term: str = "") -> str:
    return (
        '<form class="search" action="/search" method="get">'
        f'<input name="q" value="{escape(term)}" placeholder="Search symbols" autofocus>'
        '<button type="submit">Search</button>'
        "</form>"
    )


def _recent_section() -> str:
    return """
      <section class="list recent" data-recent-section hidden>
        <section class="group">
          <h2>Recent</h2>
          <div data-recent-list></div>
        </section>
      </section>
    """


def _declaration_block(raw_declaration: str | None) -> str:
    if not raw_declaration:
        return ""
    return f"<pre>{escape(raw_declaration)}</pre>"


def _doc_body(docs: tuple[tuple[str, str], ...], source: str) -> str | None:
    for doc_source, body in docs:
        if doc_source == source:
            return body
    return None


def _search_subtitle(kind: str, kit: str | None, file_path: str | None) -> str:
    parts = [kind]
    if kit:
        parts.append(kit)
    if file_path:
        parts.append(file_path)
    return " · ".join(parts)


def _location(file_path: str | None, line_start: int | None) -> str:
    if not file_path:
        return "unknown"
    if line_start is None:
        return file_path
    return f"{file_path}:{line_start}"


def _page(
    title: str,
    body: str,
    *,
    recent_title: str | None = None,
    recent_url: str | None = None,
) -> str:
    recent_attrs = ""
    if recent_title and recent_url:
        recent_attrs = (
            f' data-recent-title="{escape(recent_title)}"'
            f' data-recent-url="{escape(recent_url)}"'
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #182026;
      --muted: #66727c;
      --line: #d7dde2;
      --paper: #f7f8f5;
      --panel: #ffffff;
      --accent: #0b6f7c;
      --accent-ink: #ffffff;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font: 15px/1.45 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 28px 20px 48px; }}
    h1 {{ margin: 0; font-size: 32px; line-height: 1.1; }}
    h2 {{ margin: 0 0 12px; font-size: 18px; }}
    p {{ margin: 8px 0 0; color: var(--muted); }}
    a {{ color: inherit; text-decoration: none; }}
    .nav {{
      display: flex;
      gap: 8px;
      max-width: 1120px;
      margin: 0 auto;
      padding: 14px 20px 0;
    }}
    .nav button, .nav a {{
      min-height: 32px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 5px 9px;
      background: var(--panel);
      color: var(--ink);
      font: inherit;
    }}
    .toolbar {{
      display: flex;
      gap: 18px;
      justify-content: space-between;
      align-items: end;
      padding: 0 0 20px;
      border-bottom: 1px solid var(--line);
    }}
    .crumb {{ display: inline-block; margin-bottom: 8px; color: var(--accent); font-weight: 700; }}
    .search {{ display: flex; gap: 8px; min-width: min(440px, 100%); }}
    input {{
      width: 100%;
      min-height: 40px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 10px;
      font: inherit;
      background: var(--panel);
    }}
    button {{
      min-height: 40px;
      border: 0;
      border-radius: 6px;
      padding: 8px 14px;
      background: var(--accent);
      color: var(--accent-ink);
      font: inherit;
      font-weight: 700;
    }}
    .list, .detail {{ margin-top: 22px; }}
    .group + .group {{ margin-top: 30px; }}
    .group h2 {{
      margin-bottom: 10px;
      padding-top: 2px;
      color: var(--muted);
      font-size: 13px;
      letter-spacing: 0;
      text-transform: uppercase;
    }}
    .row {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 16px;
      align-items: baseline;
      padding: 7px 8px;
      border-radius: 6px;
    }}
    .row:hover, .method-row:hover {{ background: rgba(11, 111, 124, 0.08); }}
    .group .row, .group .method-row {{ margin-left: 18px; }}
    .row span {{ overflow-wrap: anywhere; font-weight: 700; }}
    small {{ color: var(--muted); text-align: right; }}
    dl {{
      display: grid;
      grid-template-columns: 110px minmax(0, 1fr);
      gap: 8px 18px;
      margin: 0;
    }}
    dt {{ color: var(--muted); }}
    dd {{ margin: 0; overflow-wrap: anywhere; }}
    pre {{
      margin: 18px 0 0;
      padding: 14px;
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel);
    }}
    .method-row {{
      display: grid;
      grid-template-columns: 190px minmax(0, 1fr) auto;
      gap: 14px;
      align-items: baseline;
      padding: 7px 8px;
      border-radius: 6px;
    }}
    .method-name {{ color: var(--accent); font-weight: 700; overflow-wrap: anywhere; }}
    .method-signature {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 13px;
      overflow-wrap: anywhere;
    }}
    .recent .row {{ grid-template-columns: minmax(0, 1fr) auto; }}
    .empty {{ color: var(--muted); }}
    @media (max-width: 720px) {{
      .nav {{ padding: 10px 14px 0; }}
      main {{ padding: 20px 14px 36px; }}
      h1 {{ font-size: 26px; }}
      .toolbar {{ display: block; }}
      .search {{ margin-top: 16px; min-width: 0; }}
      .row {{ grid-template-columns: 1fr; gap: 2px; }}
      .method-row {{ grid-template-columns: 1fr; gap: 2px; }}
      .group .row, .group .method-row {{ margin-left: 0; }}
      small {{ text-align: left; }}
      dl {{ grid-template-columns: 1fr; gap: 2px; }}
      dd {{ margin-bottom: 8px; }}
    }}
  </style>
</head>
<body{recent_attrs}>
<nav class="nav">
  <button type="button" data-back>Back</button>
  <button type="button" data-forward>Forward</button>
  <a href="/">Home</a>
</nav>
{body}
<script>
(function () {{
  const maxRecent = 12;
  const key = "haiku-atlas:recent";
  const readRecent = () => {{
    try {{
      return JSON.parse(localStorage.getItem(key) || "[]");
    }} catch (_) {{
      return [];
    }}
  }};
  const writeRecent = (items) => localStorage.setItem(key, JSON.stringify(items.slice(0, maxRecent)));
  const currentTitle = document.body.dataset.recentTitle;
  const currentUrl = document.body.dataset.recentUrl;
  if (currentTitle && currentUrl) {{
    const next = [{{ title: currentTitle, url: currentUrl }}, ...readRecent().filter((item) => item.url !== currentUrl)];
    writeRecent(next);
  }}
  document.querySelector("[data-back]")?.addEventListener("click", () => history.back());
  document.querySelector("[data-forward]")?.addEventListener("click", () => history.forward());
  const section = document.querySelector("[data-recent-section]");
  const list = document.querySelector("[data-recent-list]");
  if (section && list) {{
    const items = readRecent();
    if (items.length > 0) {{
      section.hidden = false;
      list.innerHTML = items.map((item) =>
        `<a class="row" href="${{item.url}}"><span>${{escapeHtml(item.title)}}</span><small>symbol</small></a>`
      ).join("");
    }}
  }}
  function escapeHtml(value) {{
    return value.replace(/[&<>"']/g, (char) => ({{
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    }}[char]));
  }}
}}());
</script>
</body>
</html>
"""
