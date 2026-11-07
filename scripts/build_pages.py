"""Makes the site's pages that are made from data/, and sitemap.xml.

Standard library only.  Run from anywhere:

    python scripts/build_pages.py            write every page it makes
    python scripts/build_pages.py --all      the same, named in full
    python scripts/build_pages.py --check    say whether each page is as committed

Pages made here:

    releases.html, releases.xml
                      from data/core/RELEASE_NOTES.md (the page, and its Atom feed)
                      and, for its JSON-LD, data/core/latest.json
    index.html        stays hand-made; its JSON-LD takes the version and the
                      download address from data/core/latest.json
    every page        the dark theme block (THEME_STYLE), last in its head, and
                      every <img> with its width and height, lazy but the first
    gallery.html, examples/NAME.html, img/gallery/...
                      from data/core/examples and data/core/gallery
    fabrication.html, drafting-pro.html
                      from data/core/gui.md and the site's own words
    tutorial.html     from the public docs and the bracket example
    docs/NAME.html    one page for each public SDK doc in data/core (index.md is
                      docs/index.html), through the small Markdown reader below
    search.html, search.json
                      the search page, and the list of every page it searches
    download.html     from data/core/latest.json: the version, its date, its files
    404.html          the page GitHub Pages shows for an address that is not here
    footer            FOOTER, below, is the footer of every page: made pages are
                      given it, and in the hand-made pages it replaces the footer

The look of a made page is the look of the pages that are written by hand: its
style and its header are those of refunds.html, its footer is the index's.
Nothing in data/ is ever written to.
"""

import argparse
import ast
import datetime
import html
import json
import os
import posixpath
import re
import struct
import sys
from html.parser import HTMLParser

SITE = "https://dxcad.designmatix.co.uk/"
SOCIAL_IMAGE = "img/og-dxcad.png"
SOCIAL_IMAGE_ALT = ("DX-CAD: AI-powered 3D CAD for sheet metal, fabrication, industrial "
                    "design and 3D printing. 30-day free trial.")
SKIP_DIRS = {"data", "logs", "prompts", "scripts", "tests", "node_modules", "__pycache__"}

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


# ---------------------------------------------------------------- reading ---

def read_text(path):
    with open(path, "rb") as f:
        return f.read().decode("utf-8").replace("\r\n", "\n")


def esc(text):
    return html.escape(text, quote=False)


def ascii_only(text):
    return text.encode("ascii", "xmlcharrefreplace").decode("ascii")


# --------------------------------------------------------- release notes ---

DATE_RE = re.compile(r"\b(\d{1,2}) (%s) (\d{4})\b" % "|".join(MONTHS))


def parse_release_notes(text):
    """Releases, newest first, as dicts: version, date, blocks.

    A block is ("p", text), ("h3", text) or ("ul", [items]).  Text is as the
    notes give it, with its lines joined.
    """
    releases = []
    current = None
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^## (\S+)\s*$", line)
        if m:
            current = {"version": m.group(1), "blocks": []}
            releases.append(current)
            i += 1
            continue
        if current is None:
            i += 1
            continue
        if line.startswith("### "):
            current["blocks"].append(("h3", line[4:].strip()))
            i += 1
        elif line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                parts = [lines[i][2:].strip()]
                i += 1
                while i < len(lines) and lines[i].startswith("  ") and lines[i].strip():
                    parts.append(lines[i].strip())
                    i += 1
                items.append(" ".join(parts))
            current["blocks"].append(("ul", items))
        elif line.strip():
            parts = []
            while (i < len(lines) and lines[i].strip() and not lines[i].startswith("#")
                   and not lines[i].startswith("- ")):
                parts.append(lines[i].strip())
                i += 1
            current["blocks"].append(("p", " ".join(parts)))
        else:
            i += 1
    for rel in releases:
        rel["date"] = None
        for kind, value in rel["blocks"]:
            if kind == "p":
                m = DATE_RE.search(value)
                if m:
                    rel["date"] = datetime.date(int(m.group(3)),
                                                MONTHS.index(m.group(2)) + 1,
                                                int(m.group(1)))
                    break
        if rel["date"] is None:
            raise ValueError("release %s: no date found in its first paragraph"
                             % rel["version"])
    return releases


def inline(text):
    """Notes text to HTML: `code` is code, [text](file) keeps only its text."""
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    out = []
    for n, piece in enumerate(re.split(r"`", text)):
        out.append("<code>%s</code>" % esc(piece) if n % 2 else esc(piece))
    return "".join(out)


def long_date(d):
    return "%d %s %d" % (d.day, MONTHS[d.month - 1], d.year)


def anchor(version):
    return "v" + re.sub(r"[^0-9A-Za-z]+", "-", version)


# ------------------------------------------------------------------ shell ---

def between(text, start, end, what, source):
    a = text.find(start)
    b = text.find(end, a)
    if a < 0 or b < 0:
        raise ValueError("%s: no %s found" % (source, what))
    return text[a:b + len(end)]


# The footer of every page of the site, written here and nowhere else: a made
# page is given it when it is made, and a hand-made page has its footer
# replaced by it on every run (see build_footers).  Its first line starts at the
# tag, its last line carries the page's own indent.
FOOTER = """<footer class="tb" aria-label="Company details">
    <div><span>Product</span><strong><a href="/">DX-CAD</a></strong></div>
    <div><span>Made by</span><strong>Designmatix Ltd</strong></div>
    <div><span>Company number</span><strong>12697280</strong></div>
    <div><span>Registered in</span><strong>England and Wales</strong></div>
    <div class="wide"><span>Registered office</span><strong>71-75 Shelton Street, London WC2H 9JQ, United Kingdom</strong></div>
    <div><span>Email</span><strong><a href="mailto:support@designmatix.co.uk">support@designmatix.co.uk</a></strong></div>
    <div><span>Telephone</span><strong><a href="tel:+442088651947">+44 (0) 20 8865 1947</a></strong></div>
    <div><span>Licence</span><strong><a href="/eula.html">Licence agreement</a></strong></div>
    <div><span>Refunds</span><strong><a href="/refunds.html">Refund policy</a></strong></div>
    <div><span>Privacy</span><strong><a href="/privacy.html">Privacy notice</a></strong></div>
    <div><span>Releases</span><strong><a href="/releases.html">What is new in each release</a></strong></div>
    <div><span>Learn</span><strong><a href="/docs/">Documentation</a> &middot; <a href="/gallery.html">Examples</a> &middot; <a href="/tutorial.html">Tutorial</a> &middot; <a href="/faq.html">Questions</a> &middot; <a href="/shortcuts.html">Shortcuts</a></strong></div>
    <div><span>Find</span><strong><a href="/search.html">Search</a> &middot; <a href="/download.html">All downloads</a></strong></div>
    <div class="wide"><span>Also from Designmatix</span><strong><a href="https://ai.designmatix.co.uk/texttocad/">Text-to-CAD</a> &middot; <a href="https://dxems.designmatix.co.uk/">DX-EMS</a></strong></div>
    <div class="full">Our order process is conducted by our online reseller Paddle.com. Paddle.com is the Merchant of Record for all our orders. Paddle provides all customer service inquiries and handles returns.</div>
  </footer>"""

FOOTER_RE = re.compile(r'<footer class="tb".*?</footer>', re.S)

# Pages a visitor can reach that are not listed in sitemap.xml (nor searched).
NOT_LISTED = {"404.html"}


# The dark theme: a visitor whose system asks for dark gets the same pages with
# the same variables turned over.  It is one block, last in the head of every
# page (made pages are given it by make_page, hand-made pages on every run, as
# with the footer), so it overrides the page's own colours whatever the page
# is.  Text is held to WCAG AA in both themes by tests/a11ycheck.py.
THEME_STYLE = """<style id="theme">
@media (prefers-color-scheme:dark){
:root{color-scheme:dark;--ink:#E6EAF2;--ink-2:#AEB8CC;--blue:#9DAAFF;--blue-dark:#C2CBFF;--red:#FF8F8D;--line:#3B4766;--paper:#0E1526;--wash:#18223A}
.skip{background:var(--ink);color:var(--paper)}
.btn{background:var(--blue);color:var(--paper)}
.results mark{background:#FFE88A;color:#14213D}
.brand img{background:#FFFFFF;padding:2px 6px}
svg [stroke="#1E2FE0"]{stroke:var(--blue)}
svg [stroke="#C8201F"]{stroke:var(--red)}
}
</style>"""

THEME_RE = re.compile(r'<style id="theme">.*?</style>\n?', re.S)


def with_theme(text):
    """A page with THEME_STYLE as the last thing in its head (one copy)."""
    text = THEME_RE.sub("", text)
    if "</head>" not in text:
        return text
    return text.replace("</head>", THEME_STYLE + "\n</head>", 1)


def read_shell(root):
    """The style, header and icons a made page takes from the hand-made ones."""
    refunds = read_text(os.path.join(root, "refunds.html"))
    icons = [ln for ln in refunds.split("\n")
             if ln.startswith(('<link rel="icon"', '<link rel="apple-touch-icon"'))]
    return {
        "icons": icons,
        "style": between(refunds, "<style>", "</style>", "style", "refunds.html"),
        "header": between(refunds, '<header class="bar">', "</header>", "header",
                          "refunds.html"),
        "footer": FOOTER,
    }


def make_page(shell, path, title, description, body, extra_style="", head_extra="",
              robots="index, follow"):
    """A whole page, as text.  path is the page's file name, e.g. releases.html."""
    url = address(path)
    image = SITE + SOCIAL_IMAGE
    t, d = html.escape(title), html.escape(description)
    head = [
        '<!doctype html>',
        '<html lang="en-GB">',
        '<head>',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<title>%s</title>' % t,
        '<meta name="description" content="%s">' % d,
        '<link rel="canonical" href="%s">' % url,
        '<meta name="robots" content="%s">' % robots,
        '<meta name="theme-color" content="#1E2FE0">',
        '<meta name="author" content="Designmatix Ltd">',
    ]
    head += shell["icons"]
    head += [
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="DX-CAD by Designmatix">',
        '<meta property="og:title" content="%s">' % t,
        '<meta property="og:description" content="%s">' % d,
        '<meta property="og:url" content="%s">' % url,
        '<meta property="og:image" content="%s">' % image,
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta property="og:image:alt" content="%s">' % html.escape(SOCIAL_IMAGE_ALT),
        '<meta property="og:locale" content="en_GB">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<meta name="twitter:title" content="%s">' % t,
        '<meta name="twitter:description" content="%s">' % d,
        '<meta name="twitter:image" content="%s">' % image,
    ]
    if head_extra:
        head.append(head_extra)
    head.append(shell["style"])
    if extra_style:
        head.append("<style>\n%s\n</style>" % extra_style.strip("\n"))
    head.append(THEME_STYLE)
    head.append('</head>')
    page = "\n".join(head) + "\n" + "\n".join([
        '<body>',
        '<a class="skip" href="#main">Skip to content</a>',
        shell["header"],
        '<main class="wrap" id="main">',
        '',
        '  <div class="sheet">',
        '  <article class="doc">',
        body.rstrip("\n"),
        '  </article>',
        '  </div>',
        '',
        '  ' + shell["footer"],
        '</main>',
        '</body>',
        '</html>',
        '',
    ])
    return ascii_only(page)


# ------------------------------------------------------- structured data ---

LD_RE = re.compile(r'(<script type="application/ld\+json">\n)(.*?)(\n</script>)', re.S)


def index_software(root):
    """(whole JSON-LD of index.html, its SoftwareApplication node): the home page's
    own words for what DX-CAD is and which systems it runs on."""
    text = read_text(os.path.join(root, "index.html"))
    m = LD_RE.search(text)
    if not m:
        raise ValueError("index.html has no JSON-LD block")
    data = json.loads(m.group(2))
    for node in data.get("@graph", []):
        if node.get("@type") == "SoftwareApplication":
            return data, node
    raise ValueError("index.html's JSON-LD has no SoftwareApplication")


def index_with_software(text, latest):
    """index.html with its SoftwareApplication's version and download address those
    of data/core/latest.json (the rest of its JSON-LD is left as written)."""
    m = LD_RE.search(text)
    if not m:
        return text
    data = json.loads(m.group(2))
    for node in data.get("@graph", []):
        if node.get("@type") == "SoftwareApplication":
            node["softwareVersion"] = latest["version"]
            if latest.get("url"):
                node["downloadUrl"] = latest["url"]
    body = json.dumps(data, indent=1)
    return text[:m.start(2)] + body + text[m.end(2):]


def releases_software(root):
    """The JSON-LD block of releases.html: the same application, its version and
    download address from latest.json, its systems from the home page."""
    latest = read_latest(root)
    _, node = index_software(root)
    app = {
        "@type": "SoftwareApplication",
        "name": node["name"],
        "url": node["url"],
        "applicationCategory": node["applicationCategory"],
        "operatingSystem": node["operatingSystem"],
        "softwareVersion": latest["version"],
        "releaseNotes": address("releases.html"),
        "publisher": {"@type": "Organization", "name": "Designmatix Ltd",
                      "url": "https://designmatix.co.uk/"},
    }
    if latest.get("url"):
        app["downloadUrl"] = latest["url"]
    data = dict({"@context": "https://schema.org"}, **app)
    return '<script type="application/ld+json">\n%s\n</script>' % json.dumps(data, indent=1)


# --------------------------------------------------------------- releases ---

def releases_body(releases):
    latest = releases[0]
    out = [
        '    <h1>What is new in each release</h1>',
        '    <p class="meta">DX-CAD by Designmatix Ltd. Newest first. The latest is %s, %s.</p>'
        % (esc(latest["version"]), long_date(latest["date"])),
        '    <p>What each release of DX-CAD brings, in plain words. Each one installs over '
        'the one before, and your files, settings and add-ons are kept.</p>',
        '    <nav class="toc" aria-label="Releases"><strong>Releases</strong>',
        '      <ol>',
    ]
    for r in releases:
        out.append('        <li><a href="#%s">DX-CAD %s</a>, %s</li>'
                   % (anchor(r["version"]), esc(r["version"]), long_date(r["date"])))
    out += ['      </ol>', '    </nav>']
    for r in releases:
        out.append('')
        out.append('    <div class="release" id="%s">' % anchor(r["version"]))
        out.append('    <h2>DX-CAD %s</h2>' % esc(r["version"]))
        out.append('    <p class="meta"><time datetime="%s">%s</time></p>'
                   % (r["date"].isoformat(), long_date(r["date"])))
        for kind, value in r["blocks"]:
            if kind == "p":
                out.append('    <p>%s</p>' % inline(value))
            elif kind == "h3":
                out.append('    <h3>%s</h3>' % esc(value))
            else:
                out.append('    <ul>')
                out += ['      <li>%s</li>' % inline(item) for item in value]
                out.append('    </ul>')
        out.append('    </div>')
    return "\n".join(out)


FEED = "releases.xml"


def xml(text):
    return html.escape(text, quote=True)


def feed_content(release):
    """A release's blocks as one string of HTML, for an entry's content."""
    out = []
    for kind, value in release["blocks"]:
        if kind == "p":
            out.append("<p>%s</p>" % inline(value))
        elif kind == "h3":
            out.append("<h3>%s</h3>" % esc(value))
        else:
            out.append("<ul>%s</ul>" % "".join("<li>%s</li>" % inline(i) for i in value))
    return "".join(out)


def plain(text):
    """Notes text without its markup: `code` as code's words, links as their text."""
    return re.sub(r"\s+", " ", inline(text).replace("<code>", "").replace("</code>", "")
                  ).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")


def releases_feed(releases):
    """An Atom feed (RFC 4287) of the releases, newest first."""
    page = SITE + "releases.html"
    stamp = lambda d: "%sT00:00:00Z" % d.isoformat()
    out = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en-GB">',
        '  <id>%s</id>' % (SITE + FEED),
        '  <title>DX-CAD releases</title>',
        '  <subtitle>What each DX-CAD release brought, in plain words, newest first.</subtitle>',
        '  <updated>%s</updated>' % stamp(releases[0]["date"]),
        '  <link rel="self" type="application/atom+xml" href="%s"/>' % (SITE + FEED),
        '  <link rel="alternate" type="text/html" href="%s"/>' % page,
        '  <author><name>Designmatix Ltd</name></author>',
    ]
    for r in releases:
        url = "%s#%s" % (page, anchor(r["version"]))
        first = next((v for k, v in r["blocks"] if k == "p"), "")
        out += [
            '  <entry>',
            '    <id>%s</id>' % url,
            '    <title>DX-CAD %s</title>' % xml(r["version"]),
            '    <updated>%s</updated>' % stamp(r["date"]),
            '    <link rel="alternate" type="text/html" href="%s"/>' % url,
            '    <summary type="text">%s</summary>' % xml(plain(first)),
            '    <content type="html">%s</content>' % xml(feed_content(r)),
            '  </entry>',
        ]
    out += ['</feed>', '']
    return ascii_only("\n".join(out))


def build_releases(root, shell):
    path = os.path.join(root, "data", "core", "RELEASE_NOTES.md")
    releases = parse_release_notes(read_text(path))
    if not releases:
        raise ValueError("data/core/RELEASE_NOTES.md has no release")
    latest = releases[0]
    page = make_page(
        shell, "releases.html",
        "What is new in each DX-CAD release | DX-CAD by Designmatix",
        "What each DX-CAD release brought, in plain words, newest first. The latest is "
        "%s, %s." % (latest["version"], long_date(latest["date"])),
        releases_body(releases),
        head_extra='<link rel="alternate" type="application/atom+xml" '
                   'title="DX-CAD releases" href="/%s">\n%s' % (FEED, releases_software(root)))
    return {"releases.html": (page, latest["date"]),
            FEED: (releases_feed(releases), latest["date"])}


# ---------------------------------------------------------------- gallery ---

GALLERY_STYLE = """
.doc .lead{font-size:19px;max-width:62ch;margin:0 0 24px}
.shots{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:24px;margin:24px 0 0;padding:0;list-style:none}
.shots li{margin:0;max-width:none}
.shots a{display:block;text-decoration:none;color:var(--ink)}
.shots a:hover strong{color:var(--blue)}
.shots img,.shot img{display:block;width:100%;height:auto;border:1px solid var(--line);background:var(--wash)}
.shots strong{display:block;font-family:var(--cond);font-size:18px;margin:8px 0 2px}
.shots span{display:block;font-size:14px;color:var(--ink-2)}
.shot{margin:0 0 24px}.shot figcaption{font-size:14px;color:var(--ink-2);margin-top:6px}
.pair{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin:0 0 24px}.pair .shot{margin:0}
pre.script{overflow-x:auto;border:1px solid var(--ink);background:var(--wash);padding:16px 20px;font-size:14px;line-height:1.5;max-width:none;tab-size:4}
pre.script code{background:none;padding:0;font-size:inherit}
"""

DARK = "dark"


def png_size(data):
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("not a PNG picture")
    return struct.unpack(">II", data[16:24])


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def first_docstring_line(source, name):
    doc = ast.get_docstring(ast.parse(source))
    if not doc or not doc.strip():
        raise ValueError("examples/%s.py has no docstring" % name)
    return doc.strip().split("\n")[0].strip()


def read_examples(root):
    """The examples in data/core/examples, by name: script, description, pictures."""
    base = os.path.join(root, "data", "core", "examples")
    gal = os.path.join(root, "data", "core", "gallery")
    found = []
    for fname in sorted(os.listdir(base)):
        if not fname.endswith(".py"):
            continue
        name = fname[:-3]
        source = read_text(os.path.join(base, fname))
        light = os.path.join(gal, name + ".png")
        dark = os.path.join(gal, DARK, name + ".png")
        if not os.path.exists(light):
            raise ValueError("data/core/gallery/%s.png: no picture for the example" % name)
        companions = sorted(
            f for f in os.listdir(base)
            if f != fname and not f.endswith((".py", ".md", ".jsonl")) and f in source)
        found.append({
            "name": name,
            "source": source,
            "description": first_docstring_line(source, name),
            "light": read_bytes(light),
            "dark": read_bytes(dark) if os.path.exists(dark) else None,
            "companions": companions,
        })
    if not found:
        raise ValueError("data/core/examples has no example")
    return found


def title_of(name):
    words = name.replace("_", " ")
    return words[:1].upper() + words[1:]


def img_tag(src, alt, data, lazy=True):
    w, h = png_size(data)
    return ('<img src="%s" alt="%s" width="%d" height="%d"%s>'
            % (src, html.escape(alt), w, h, ' loading="lazy" decoding="async"' if lazy else ""))


def example_page(shell, ex):
    name, desc = ex["name"], ex["description"]
    pics = ['<figure class="shot">%s<figcaption>Drawn light.</figcaption></figure>'
            % img_tag("/img/gallery/%s.png" % name,
                      "%s: %s" % (title_of(name), desc), ex["light"], lazy=False)]
    if ex["dark"] is not None:
        pics.append('<figure class="shot">%s<figcaption>Drawn dark.</figcaption></figure>'
                    % img_tag("/img/gallery/%s/%s.png" % (DARK, name),
                              "%s: %s (drawn dark)" % (title_of(name), desc), ex["dark"]))
    out = [
        '    <p class="small"><a href="/gallery.html">All the examples</a></p>',
        '    <h1>%s</h1>' % esc(title_of(name)),
        '    <p class="lead">%s</p>' % esc(desc),
        '    <div class="pair">',
    ]
    out += ["    " + p for p in pics]
    out += [
        '    </div>',
        '    <h2>How to open it in DX-CAD</h2>',
        '    <p>This example ships with DX-CAD. Copy it into a folder, then open it in the window:</p>',
        '    <pre class="script"><code>dxcad examples %s\ndxcad gui %s.py</code></pre>' % (name, name),
        '    <p>To build it into a project from the command line instead:</p>',
        '    <pre class="script"><code>dxcad run %s.py --output %s.dxcprt\n'
        'dxcad describe %s.dxcprt</code></pre>' % (name, name, name),
        "    <p>Change a number at the top of the script and run it again: that is the whole of "
        "DX-CAD's parametric model.</p>",
    ]
    if ex["companions"]:
        names = " and ".join("<code>%s</code>" % esc(c) for c in ex["companions"])
        out.append('    <p>This example keeps %s beside the script.</p>' % names)
    out += [
        '    <h2>The whole script: %s.py</h2>' % esc(name),
        '    <pre class="script"><code>%s</code></pre>' % esc(ex["source"].rstrip("\n")),
    ]
    return make_page(
        shell, "examples/%s.html" % name,
        "%s: an example model.py | DX-CAD by Designmatix" % title_of(name),
        "%s The whole model.py, with its picture and how to open it in DX-CAD." % desc,
        "\n".join(out), GALLERY_STYLE)


def gallery_page(shell, examples):
    out = [
        '    <h1>Examples: every part is a script</h1>',
        '    <p class="lead">Every example that ships with DX-CAD is a short Python script, '
        'a model.py, with its numbers at the top. Pick one to see its picture and read the '
        'whole script.</p>',
        '    <p>Open any of them in DX-CAD, change a number and run it again. %d examples:</p>'
        % len(examples),
        '    <ul class="shots">',
    ]
    for ex in examples:
        name = ex["name"]
        out.append(
            '      <li><a href="/examples/%s.html">%s<strong>%s</strong><span>%s</span></a></li>'
            % (name,
               img_tag("/img/gallery/%s.png" % name,
                       "%s: %s" % (title_of(name), ex["description"]), ex["light"]),
               esc(title_of(name)), esc(ex["description"])))
    out.append('    </ul>')
    return make_page(
        shell, "gallery.html",
        "Examples: every DX-CAD part is a script | DX-CAD by Designmatix",
        "%d example parts that ship with DX-CAD, each with its picture and its whole "
        "model.py: sheet metal, assemblies, drawings and whole machines." % len(examples),
        "\n".join(out), GALLERY_STYLE)


def build_gallery(root, shell, date):
    examples = read_examples(root)
    made = {"gallery.html": (gallery_page(shell, examples), date)}
    for ex in examples:
        made["examples/%s.html" % ex["name"]] = (example_page(shell, ex), date)
        made["img/gallery/%s.png" % ex["name"]] = (ex["light"], date)
        if ex["dark"] is not None:
            made["img/gallery/%s/%s.png" % (DARK, ex["name"])] = (ex["dark"], date)
    return made


# ----------------------------------------------------------------- add-ons ---

# Words below are the site's own: the Fabrication ones are those of
# fabrication-layout-software.html, the Drafting Pro ones those of the editions
# table in index.html.  The commands, and the trial and licence words, are read
# from data/core/gui.md every time the pages are made.

FABRICATION = {
    "file": "fabrication.html",
    "name": "Fabrication",
    "title": "Fabrication add-on: cones, transitions, elbows and branches | DX-CAD by Designmatix",
    "description": ("The Fabrication add-on for DX-CAD: the shapes plate and duct fabricators "
                    "cut every day, developed to flat patterns with a marking table, "
                    "and exported to DXF. Free during your 30-day trial."),
    "h1": "The Fabrication add-on",
    "lead": ("The shapes plate and duct fabricators cut every day, developed to flat patterns "
             "with thickness allowance, seams and a marking table for setting out by hand, "
             "and exported to DXF for the cutting table."),
    "pictures": [
        ("fabrication-cone-and-reducer.png",
         "A cone and reducer with their flat patterns, made with the Fabrication add-on"),
        ("fabrication-square-to-round.png",
         "A square-to-round transition and its flat pattern with marking table, "
         "made by DX-CAD Fabrication"),
    ],
    "sections": [
        ("The shapes", [
            ("Cones and reducers", "Concentric and oblique cones and reducers, rolled cylinders "
             "and courses, and cone-on-cone and pipe-on-cone joints."),
            ("Transitions", "Square-to-round, rectangle-to-rectangle and round-to-round "
             "transitions, and hoppers, each with its seams and splits where you choose."),
            ("Elbows and branches", "Segmented (lobster-back) and reducing elbows, tees, "
             "laterals, Y-pieces and breeches, headers, and branches on pipes, cones, elbows "
             "and plates."),
            ("Ducting and press-brake parts", "Rectangular duct elbows, offsets and Y-branches; "
             "trays, boxes, brackets and corner posts for the press brake; dished heads; and "
             "weldments with cut lists."),
        ]),
        ("Flat patterns you can trust", [
            ("Thickness allowance", "Each development allows for the plate's thickness, with "
             "the sizes taken to the face you choose."),
            ("Marking tables", "Every flat comes with a marking table of points to set it out "
             "by hand, for the shop that still marks plate with a rule and a scriber."),
            ("Verified by refolding", "Every shape family is checked over a grid of sizes by "
             "folding its flat pattern back up and comparing it with the 3D surface, and "
             "against closed-form values where they exist."),
            ("Out to the shop", "Flats go out as DXF and SVG, onto drawings, and onto stock "
             "sheets with the nesting tool, each piece kept a gap from the next."),
        ]),
    ],
    "steps_title": "From sizes to the cutting table",
    "steps": [
        "Pick the shape from the Fabrication menu and type its sizes in the dialog.",
        "Choose the plate thickness, where the seam goes and how many pieces.",
        "See the part in 3D and its flat pattern, with the marking table.",
        "Export the DXF, or nest the flats on your stock sheets, and put it on a drawing.",
    ],
    "other": ("drafting-pro.html", "Drafting Pro", "production drawings"),
    "more": ("/fabrication-layout-software.html", "Fabrication layout software"),
}

DRAFTING_PRO = {
    "file": "drafting-pro.html",
    "name": "Drafting Pro",
    "title": "Drafting Pro add-on: dimensions, balloons, GD&T and section views | DX-CAD by Designmatix",
    "description": ("The Drafting Pro add-on for DX-CAD: dimensions, balloons, hole tables, "
                    "tolerances and GD&T, section, detail and exploded views. Free during "
                    "your 30-day trial."),
    "h1": "The Drafting Pro add-on",
    "lead": ("Dimensions, balloons, hole tables, tolerances and GD&T, section, detail and "
             "exploded views, for the drawings DX-CAD makes."),
    "pictures": [
        ("drafting-finished-drawing.png",
         "A finished assembly drawing with sections, a detail view, dimensions, balloons and "
         "a parts list, made with Drafting Pro"),
    ],
    "sections": [
        ("What is in DX-CAD, and what Drafting Pro adds", [
            ("In DX-CAD itself", "Drawing documents, title blocks and parts lists, to PDF "
             "and DXF."),
            ("In Drafting Pro", "Dimensions, balloons, hole tables, tolerances and GD&T, "
             "section, detail and exploded views, revision tables and notes."),
        ]),
    ],
    "steps_title": "",
    "steps": [],
    "other": ("fabrication.html", "Fabrication", "cones, transitions, elbows and branches"),
    "more": None,
}


def gui_section(gui, name):
    """The part of gui.md under '### NAME': its paragraph and its command rows."""
    m = re.search(r"(?ms)^### %s\n\n(.*?)(?=^#{2,3} )" % re.escape(name), gui)
    if not m:
        raise ValueError("data/core/gui.md has no '### %s' section" % name)
    block = m.group(1)
    paragraph = block.split("\n\n")[0].strip()
    commands = []
    for line in block.split("\n"):
        if not line.startswith("| `"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        cmd = cells[0].strip("`")
        what = cells[-1].split(" Greyed:")[0].strip()
        if not cmd.endswith(" - " + name):
            raise ValueError("gui.md: command %r is not named for %s" % (cmd, name))
        commands.append((cmd, what))
    if not commands:
        raise ValueError("data/core/gui.md: no commands under '### %s'" % name)
    return paragraph, commands


def trial_words(gui, name):
    """The trial and licence sentences of gui.md, as it words them, for one add-on."""
    paragraph, _ = gui_section(gui, name)
    m = re.search(r"What a listed command's panel says depends on .*$", paragraph, re.S)
    if not m:
        raise ValueError("gui.md: no licence words in the '%s' section" % name)
    first = re.sub(r" \(item \d+\)", "", paragraph.split(". ")[0]) + "."
    third = re.search(r"The paid add-ons, Fabrication and Drafting Pro, [^.]*\.", gui)
    if not third:
        raise ValueError("gui.md: no licence words about the paid add-ons")
    return first, m.group(0), third.group(0)


def addon_page(root, shell, spec, gui):
    name = spec["name"]
    first, panel, both = trial_words(gui, name)
    _, commands = gui_section(gui, name)
    out = ['    <h1>%s</h1>' % esc(spec["h1"]),
           '    <p class="lead">%s</p>' % esc(spec["lead"])]
    for pic, alt in spec["pictures"]:
        data = read_bytes(os.path.join(root, "img", pic))
        out.append('    <figure class="shot">%s</figure>'
                   % img_tag("/img/" + pic, alt, data, lazy=True))
    out.append('    <p><a class="btn" href="/#download">Download the 30-day free trial</a> '
               '<a class="btn ghost" href="/#pricing">See pricing</a></p>')
    for title, items in spec["sections"]:
        out.append('    <h2>%s</h2>' % esc(title))
        out.append('    <ul>')
        for head, text in items:
            out.append('      <li><strong>%s.</strong> %s</li>' % (esc(head), esc(text)))
        out.append('    </ul>')
    if spec["steps"]:
        out.append('    <h2>%s</h2>' % esc(spec["steps_title"]))
        out.append('    <ol>')
        out += ['      <li>%s</li>' % esc(s) for s in spec["steps"]]
        out.append('    </ol>')
    out.append('    <h2>Its commands</h2>')
    out.append('    <p>These are the commands of %s, as DX-CAD lists them in its menus and in '
               'command search:</p>' % esc(name))
    out.append('    <ul>')
    for cmd, what in commands:
        out.append('      <li><code>%s</code>: %s</li>' % (esc(cmd), esc(what)))
    out.append('    </ul>')
    out.append('    <h2>Trial and licence</h2>')
    out.append('    <div class="box"><p>%s</p><p>%s</p><p>%s</p></div>'
               % (esc(first), esc(panel), esc(both)))
    page_other, other_name, other_what = spec["other"]
    out.append('    <h2>Also an add-on</h2>')
    out.append('    <p><a href="/%s">%s</a> does %s.%s</p>'
               % (page_other, esc(other_name), esc(other_what),
                  (' More on the <a href="%s">%s</a> page.' % (spec["more"][0], esc(spec["more"][1])))
                  if spec["more"] else ""))
    return make_page(shell, spec["file"], spec["title"], spec["description"],
                     "\n".join(out), GALLERY_STYLE)


def build_addons(root, shell, date):
    gui = read_text(os.path.join(root, "data", "core", "gui.md"))
    return {spec["file"]: (addon_page(root, shell, spec, gui), date)
            for spec in (FABRICATION, DRAFTING_PRO)}


# --------------------------------------------------------------- tutorial ---

def need(pattern, text, what, flags=0):
    m = re.search(pattern, text, flags)
    if not m:
        raise ValueError("%s: not found where the tutorial looks for it" % what)
    return m


def release_list(releases, version, heading):
    for r in releases:
        if r["version"] != version:
            continue
        take = False
        for kind, value in r["blocks"]:
            if kind == "h3":
                take = value == heading
            elif kind == "ul" and take:
                return value
    raise ValueError("RELEASE_NOTES.md: no '%s' list under %s" % (heading, version))


def tutorial_page(root, shell):
    """Install to a bracket with four holes, exported as STEP: every command and
    number is read from data/core (release notes, gui.md, the bracket example)."""
    core = os.path.join(root, "data", "core")
    releases = parse_release_notes(read_text(os.path.join(core, "RELEASE_NOTES.md")))
    install = release_list(releases, "0.1.0", "Install")
    gui = read_text(os.path.join(core, "gui.md"))
    story = read_text(os.path.join(core, "examples", "bracket.md"))
    script = read_text(os.path.join(core, "examples", "bracket.py"))

    doctor = [i for i in install if i.startswith("`dxcad doctor`")]
    if not doctor:
        raise ValueError("RELEASE_NOTES.md: no `dxcad doctor` line in 0.1.0's Install")
    windows = [i for i in install if i.startswith("Windows:")]
    others = [i for i in install if i.startswith("macOS")]
    if not windows or not others:
        raise ValueError("RELEASE_NOTES.md: no Windows or macOS install line in 0.1.0")

    trial = need(r"Free for 30 days from first start, then a licence\. "
                 r"Opening, viewing and exporting stay free\.",
                 "\n".join(release_list(releases, "0.1.1", "Licensing")), "trial words").group(0)

    # the numbers: the script's own lines, and the facts bracket.md gives
    numbers = need(r"(?ms)^(LENGTH = .*?^INSET = [^\n]*)$", script, "bracket.py numbers").group(1)
    holes_code = need(r"(?ms)^(pitch = .*?^part\([^\n]*\))$", script, "bracket.py hole lines").group(1)
    flat = re.sub(r"\s+", " ", story)
    vol80 = need(r"The answer is the bracket again: volume ([\d.]+)", flat, "first volume").group(1)
    centres80 = need(r"with centres at x = ([\d., and]+?), y = ([\d.]+)\.", flat, "centres")
    diam = need(r"each of diameter ([\d.]+) and depth ([\d.]+)", flat, "hole size")
    vol100 = need(r"volume of ([\d.]+), which is 420 x 100", flat, "second volume").group(1)
    centres100 = need(r"holes of diameter [\d.]+, now at x = (\d[\d., and]*?\d)\.\s", flat,
                      "second centres").group(1)
    size100 = need(r"the bracket is now ([\d.]+ x [\d.]+ x [\d.]+)", flat, "second size").group(1)
    size80 = need(r"size ([\d.]+ x [\d.]+ x [\d.]+);", flat, "first size").group(1)
    run_key = need(r"\| `Run Script` \| `(F5)` \|", gui, "Run Script key").group(1)
    export = need(r"\| `(Export Parts\.\.\.)` \| \| Write the picked parts, or every part when "
                  r"none is picked, to one (STEP), STL, 3MF or BREP file", gui, "Export Parts")
    need(r"as `dxcad export` writes them", gui, "dxcad export")

    def block(*lines):
        return '    <pre class="script"><code>%s</code></pre>' % esc("\n".join(lines))

    out = [
        '    <p class="small"><a href="/gallery.html">Examples</a></p>',
        '    <h1>Your first part in ten minutes</h1>',
        '    <p class="lead">From installing DX-CAD to a bracket with four holes, exported as a '
        'STEP file. The bracket is one of the examples that ships with DX-CAD: a short script '
        'with its numbers at the top.</p>',
        '    <h2>1. Install DX-CAD</h2>',
        '    <p>%s</p>' % inline(windows[0]),
        '    <p>%s</p>' % inline(others[0]),
        '    <p>Or, with Python:</p>',
        block("pip install dxcad"),
        '    <p>%s</p>' % inline(doctor[0]),
        '    <p>%s <a href="/#download">Download DX-CAD</a>.</p>' % esc(trial),
        '    <h2>2. Get the bracket</h2>',
        '    <p>Copy the example out, then open it in the window:</p>',
        block("dxcad examples bracket", "dxcad gui bracket.py"),
        '    <p>The window shows the model in a pane on the right, and the part it builds '
        'on the left.</p>',
        '    <h2>3. Read the numbers</h2>',
        '    <p>The model is a script, <code>bracket.py</code>, and these are its numbers, '
        'at the top of the file:</p>',
        block(*numbers.split("\n")),
        '    <p>The bracket is an L in section, drawn once and extruded along its length. '
        'Every other size follows from these names.</p>',
        '    <h2>4. Run it</h2>',
        '    <p>In the window, choose Model &gt; Run Script, or press <code>%s</code>. '
        'The same model builds from the command line into a project, and one more command '
        'says in words what was built:</p>' % esc(run_key),
        block("dxcad run bracket.py --output bracket.dxcprt", "dxcad describe bracket.dxcprt"),
        '    <p>It is one valid solid, %s, with a volume of %s: the L\'s area times its length, '
        'less four holes.</p>' % (esc(size80), esc(vol80)),
        '    <h2>5. Four holes from one line</h2>',
        '    <p>The script makes one drill, a cylinder through the base, and repeats it in '
        'a row. The holes are spaced from the length, so they move when the length does:</p>',
        block(*holes_code.split("\n")),
        '    <p>Counting them, the part has four holes, each of diameter %s and depth %s, '
        'with centres at x = %s, y = %s.</p>'
        % (esc(diam.group(1)), esc(diam.group(2)), esc(centres80.group(1)), esc(centres80.group(2))),
        '    <h2>6. Change a number</h2>',
        '    <p>Change <code>LENGTH = 80.0</code> to <code>LENGTH = 100.0</code> in the pane '
        'and run it again with <code>%s</code>. The bracket is now %s with a volume of %s, '
        'and the four holes are at x = %s. That is the whole of DX-CAD\'s parametric model: '
        'change a number and run it again.</p>'
        % (esc(run_key), esc(size100), esc(vol100), esc(centres100)),
        '    <h2>7. Export it as STEP</h2>',
        '    <p>Choose File &gt; <code>%s</code>, pick %s as the file type and give it a name. '
        'It writes the picked parts, or every part when none is picked, to one file; '
        'the command line writes them the same way with <code>dxcad export</code>.</p>'
        % (esc(export.group(1)), esc(export.group(2))),
        '    <p>Save the project, with its model, with File &gt; Save.</p>',
        '    <h2>Where next</h2>',
        '    <ul>',
        '      <li>See the bracket as it ships: <a href="/examples/bracket.html">the bracket '
        'example</a>, with its whole script.</li>',
        '      <li>Every other example, a script each: <a href="/gallery.html">the gallery</a>.</li>',
        '      <li>What each release brought: <a href="/releases.html">release notes</a>.</li>',
        '    </ul>',
    ]
    return make_page(
        shell, "tutorial.html",
        "Your first part in ten minutes: a bracket with four holes | DX-CAD by Designmatix",
        "From installing DX-CAD to a bracket with four holes exported as a STEP file, "
        "from one short script.",
        "\n".join(out), GALLERY_STYLE)


def build_tutorial(root, shell, date):
    return {"tutorial.html": (tutorial_page(root, shell), date)}


# ------------------------------------------------------------------- docs ---

# The public SDK's docs (every .md under data/core except the release notes,
# which have their own page) become docs/NAME.html.  The reader below is small
# and ours: ATX headings, paragraphs, bullet and numbered lists (nested by
# indent), block quotes, fenced code, tables, links, pictures, emphasis and
# `code`.  HTML comments in the source are dropped; other HTML is shown as text.

DOCS_STYLE = """
.doc .tw{overflow-x:auto;margin:8px 0 16px}.doc .tw table{margin:0;min-width:520px}
.doc td,.doc th{overflow-wrap:anywhere}
.doc blockquote{margin:0 0 16px;padding:4px 0 4px 16px;border-left:3px solid var(--line);color:var(--ink-2)}
.doc blockquote p{margin:8px 0}
.doc img.fig{display:block;max-width:100%;height:auto;border:1px solid var(--line);margin:0 0 16px}
.doc .toc p{margin:0}
.doc .toc ol{columns:2;column-gap:32px}.doc .toc li{break-inside:avoid}
@media (max-width:640px){.doc .toc ol{columns:1}}
pre.script{overflow-x:auto;border:1px solid var(--ink);background:var(--wash);padding:16px 20px;font-size:14px;line-height:1.5;max-width:none;tab-size:4}
pre.script code{background:none;padding:0;font-size:inherit}
@media print{
.skip,.bar,.tb,.toc{display:none!important}
body{background:#fff;color:#000;font-size:11pt}
.wrap{max-width:none;padding:0}
.sheet{border:0;margin:0;padding:0}.sheet::before{display:none}
.doc{max-width:none}.doc a{color:#000}
.doc a[href^="http"]::after{content:" (" attr(href) ")";font-size:9pt;overflow-wrap:anywhere}
.doc h1,.doc h2,.doc h3{break-after:avoid}
.doc pre,.doc table,.doc img,.doc blockquote{break-inside:avoid}
pre.script{white-space:pre-wrap;overflow:visible;border:1px solid #000;background:#fff}
}
"""

LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def doc_sources(root):
    """{path under data/core, with '/': text} of every public SDK doc."""
    base = os.path.join(root, "data", "core")
    found = {}
    for folder, dirs, files in os.walk(base):
        dirs[:] = sorted(dirs)
        for name in sorted(files):
            if not name.endswith(".md"):
                continue
            rel = os.path.relpath(os.path.join(folder, name), base).replace(os.sep, "/")
            if rel != "RELEASE_NOTES.md":
                found[rel] = read_text(os.path.join(folder, name))
    return found


def doc_name(src):
    """examples/README.md -> examples; examples/bracket.md -> examples-bracket."""
    stem = src[:-len(".md")]
    if stem.endswith("/README"):
        stem = stem[:-len("/README")]
    return stem.replace("/", "-")


def doc_path(src):
    return "docs/%s.html" % doc_name(src)


def doc_href(src):
    return "/docs/" if doc_name(src) == "index" else "/" + doc_path(src)


def md_plain(text):
    """Markdown text with its marks taken off: what a reader sees, as one line."""
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"`+", "", text)
    text = re.sub(r"\*\*|(?<![\w])_|_(?![\w])", "", text)
    text = re.sub(r"(?<![\w*])\*(?=\S)|(?<=\S)\*(?![\w*])", "", text)
    return " ".join(html.unescape(text).split())


def slugify(text):
    """GitHub's anchor for a heading: lower case, no punctuation, spaces to hyphens."""
    return re.sub(r"[^\w\- ]", "", md_plain(text).lower()).replace(" ", "-")


def md_blocks(lines):
    """Lines of markdown -> blocks: ("h", level, text), ("p", text), ("code", lang, text),
    ("ul"|"ol", [item]), ("quote", blocks), ("table", header, rows), ("hr",).
    A list item is {"text": str, "kids": [list block]}."""
    blocks = []
    i, n = 0, len(lines)

    def starts_block(k):
        s = lines[k]
        return (s.startswith(("```", ">", "<!--")) or HEADING_RE.match(s) is not None
                or LIST_RE.match(s) is not None or re.match(r"^\s*(-{3,}|\*{3,})\s*$", s)
                or (s.lstrip().startswith("|") and k + 1 < n and TABLE_SEP_RE.match(lines[k + 1])))

    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
        elif line.startswith("```"):
            lang = line[3:].strip()
            i += 1
            code = []
            while i < n and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            blocks.append(("code", lang, "\n".join(code)))
        elif line.lstrip().startswith("<!--"):
            while i < n and "-->" not in lines[i]:
                i += 1
            i += 1
        elif HEADING_RE.match(line):
            m = HEADING_RE.match(line)
            blocks.append(("h", len(m.group(1)), m.group(2)))
            i += 1
        elif re.match(r"^\s*(-{3,}|\*{3,})\s*$", line):
            blocks.append(("hr",))
            i += 1
        elif line.startswith(">"):
            inner = []
            while i < n and lines[i].startswith(">"):
                inner.append(re.sub(r"^> ?", "", lines[i]))
                i += 1
            blocks.append(("quote", md_blocks(inner)))
        elif line.lstrip().startswith("|") and i + 1 < n and TABLE_SEP_RE.match(lines[i + 1]):
            header = split_row(line)
            i += 2
            rows = []
            while i < n and lines[i].lstrip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            blocks.append(("table", header, rows))
        elif LIST_RE.match(line):
            items = []
            while i < n:
                s = lines[i]
                m = LIST_RE.match(s)
                if not s.strip():
                    k = i
                    while k < n and not lines[k].strip():
                        k += 1
                    if k < n and (LIST_RE.match(lines[k]) or lines[k].startswith("  ")):
                        i = k
                        continue
                    break
                if (m and items and len(m.group(1)) <= items[0]["indent"]
                        and m.group(2)[0].isdigit() != items[0]["ordered"]):
                    break       # a numbered list after a bullet list, or the other way
                if m:
                    items.append({"indent": len(m.group(1)), "ordered": m.group(2)[0].isdigit(),
                                  "text": m.group(3).strip()})
                elif items and (s.startswith(" ") or not starts_block(i)):
                    items[-1]["text"] += " " + s.strip()
                else:
                    break
                i += 1
            blocks.append(list_tree(items))
        else:
            para = [line.strip()]
            i += 1
            while i < n and lines[i].strip() and not starts_block(i):
                para.append(lines[i].strip())
                i += 1
            blocks.append(("p", "\n".join(para)))
    return blocks


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line)]


def list_tree(items):
    """Flat items with indents -> ("ul"|"ol", [{"text", "kids": [list block]}])."""
    root = {"indent": -1, "kids": [], "ordered": items[0]["ordered"]}
    stack = [root]
    for item in items:
        node = {"indent": item["indent"], "text": item["text"], "kids": [],
                "ordered": item["ordered"]}
        while len(stack) > 1 and stack[-1]["indent"] >= node["indent"]:
            stack.pop()
        stack[-1]["kids"].append(node)
        stack.append(node)

    def freeze(parent):
        kind = "ol" if parent["kids"][0]["ordered"] else "ul"
        return (kind, [{"text": k["text"], "kids": [freeze(k)] if k["kids"] else []}
                       for k in parent["kids"]])
    return freeze(root)


def md_target(url, ctx):
    """Where a link in a doc goes on this site, or None if it goes nowhere here."""
    if re.match(r"https?://", url):
        return url
    path, _, frag = url.partition("#")
    if not path:
        return "#" + frag if frag in ctx["slugs"][ctx["src"]] else None
    target = posixpath.normpath(posixpath.join(posixpath.dirname(ctx["src"]), path))
    if target in ctx["slugs"]:
        href = doc_href(target)
        return href + "#" + frag if frag in ctx["slugs"][target] else href
    m = re.fullmatch(r"examples/([\w-]+)\.py", target)
    if m and m.group(1) in ctx["examples"]:
        return "/examples/%s.html" % m.group(1)
    return None


def md_inline(text, ctx):
    stash = []

    def keep(markup):
        stash.append(markup)
        return "\x00%d\x00" % (len(stash) - 1)

    text = re.sub(r"(`+)(.+?)\1", lambda m: keep("<code>%s</code>" % esc(m.group(2).strip())),
                  text, flags=re.S)
    text = esc(html.unescape(text))

    def picture(m):
        alt, url = m.group(1), html.unescape(m.group(2))
        base = posixpath.normpath(posixpath.join(posixpath.dirname(ctx["src"]), url))
        data = ctx["assets"].get(base)
        if data is None:
            return keep("<em>(Picture: %s)</em>" % alt)
        ctx["used"].add(base)
        return keep('<img class="fig" src="/img/docs/%s" alt="%s" loading="lazy" decoding="async">'
                    % (base, alt))

    def link(m):
        href = md_target(html.unescape(m.group(2)), ctx)
        inner = emphasis(m.group(1))
        return keep('<a href="%s">%s</a>' % (html.escape(href), inner)) if href else inner

    def emphasis(t):
        t = re.sub(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", lambda m: keep("<strong>%s</strong>" % m.group(1)), t)
        t = re.sub(r"(?<![\w*])\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?![\w*])",
                   lambda m: keep("<em>%s</em>" % m.group(1)), t)
        t = re.sub(r"(?<![\w])_(?=[^\s_])(.+?)(?<=[^\s_])_(?![\w])",
                   lambda m: keep("<em>%s</em>" % m.group(1)), t)
        return t

    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", picture, text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, text)
    text = emphasis(text)
    while "\x00" in text:
        text = re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], text)
    return text


def doc_blocks_html(blocks, ctx, out, state):
    """Append HTML lines for blocks.  state: heading levels and the ids used."""
    for b in blocks:
        kind = b[0]
        if kind == "h":
            level = 1 if state["last"] == 0 else max(2, min(b[1], state["last"] + 1))
            state["last"] = level
            sid = slugify(b[2])
            n = state["ids"].get(sid, 0)
            state["ids"][sid] = n + 1
            sid = sid if n == 0 else "%s-%d" % (sid, n)
            state["heading"] = md_plain(b[2])
            if level == 2:
                state["toc"].append((sid, md_inline(b[2], ctx)))
            state["marks"].append(len(out))
            out.append('    <h%d id="%s">%s</h%d>' % (level, sid, md_inline(b[2], ctx), level))
        elif kind == "p":
            out.append("    <p>%s</p>" % md_inline(b[1], ctx))
        elif kind == "code":
            out.append('    <pre class="script"><code>%s</code></pre>' % esc(b[2]))
        elif kind == "hr":
            out.append("    <hr>")
        elif kind == "quote":
            out.append("    <blockquote>")
            doc_blocks_html(b[1], ctx, out, state)
            out.append("    </blockquote>")
        elif kind in ("ul", "ol"):
            out.extend(list_html(b, ctx, "    "))
        elif kind == "table":
            head, rows = b[1], b[2]
            width = len(head)
            out.append('    <div class="tw" role="region" tabindex="0" aria-label="%s">'
                       % html.escape("Table: " + (state["heading"] or "this page")))
            out.append("    <table>")
            out.append("      <thead><tr>%s</tr></thead>" % "".join(
                '<th scope="col">%s</th>' % md_inline(c, ctx) for c in head))
            out.append("      <tbody>")
            for row in rows:
                if dead_page_row(row, ctx):
                    continue
                row = (row + [""] * width)[:width]
                out.append("        <tr>%s</tr>" % "".join(
                    "<td>%s</td>" % md_inline(c, ctx) for c in row))
            out.append("      </tbody>")
            out.append("    </table>")
            out.append("    </div>")


def dead_page_row(row, ctx):
    """A table row that is only a link to another doc this site does not have
    (the index lists pages the public docs do not include): left out."""
    m = re.fullmatch(r"\[[^\]]+\]\(([^)\s#]+\.md)(#[^)\s]*)?\)", row[0].strip()) if row else None
    return bool(m) and md_target(m.group(1) + (m.group(2) or ""), ctx) is None


def list_html(block, ctx, pad):
    kind, items = block
    out = ["%s<%s>" % (pad, kind)]
    for item in items:
        if item["kids"]:
            out.append("%s  <li>%s" % (pad, md_inline(item["text"], ctx)))
            for kid in item["kids"]:
                out.extend(list_html(kid, ctx, pad + "    "))
            out.append("%s  </li>" % pad)
        else:
            out.append("%s  <li>%s</li>" % (pad, md_inline(item["text"], ctx)))
    out.append("%s</%s>" % (pad, kind))
    return out


def doc_description(blocks, title):
    """The first paragraph, in whole sentences up to about 160 characters."""
    for b in blocks:
        if b[0] == "p":
            text = md_plain(b[1])
            if len(text) <= 160:
                return text
            cut = ""
            for sentence in re.findall(r".+?(?:[.!?](?=\s|$)|$)", text):
                if len(cut) + len(sentence) > 160:
                    break
                cut += sentence
            if cut.strip():
                return cut.strip()
            return text[:157].rsplit(" ", 1)[0] + "..."
    return title


def doc_page(shell, src, blocks, ctx):
    out = []
    state = {"last": 0, "ids": {}, "toc": [], "heading": "", "marks": []}
    if doc_name(src) != "index":
        out.append('    <p class="small"><a href="/docs/">DX-CAD documentation</a></p>')
    doc_blocks_html(blocks, ctx, out, state)
    if len(state["toc"]) >= 5:
        toc = ['    <nav class="toc" aria-label="On this page">',
               "    <p><strong>On this page</strong></p>", "    <ol>"]
        toc += ['      <li><a href="#%s">%s</a></li>' % (sid, text) for sid, text in state["toc"]]
        toc += ["    </ol>", "    </nav>"]
        first = next(m for m in state["marks"] if out[m].startswith("    <h2"))
        out[first:first] = toc
    title = next((md_plain(b[2]) for b in blocks if b[0] == "h"), doc_name(src))
    out.append('    <p class="small">From the DX-CAD documentation, <code>%s</code>. '
               '<a href="/docs/">All the pages</a>.</p>' % esc(src))
    return make_page(
        shell, doc_path(src),
        "%s | DX-CAD documentation | DX-CAD by Designmatix" % title,
        doc_description(blocks, title), "\n".join(out), DOCS_STYLE)


def build_docs(root, shell, date):
    sources = doc_sources(root)
    base = os.path.join(root, "data", "core")
    assets = {}
    for folder, dirs, files in os.walk(base):
        dirs[:] = sorted(dirs)
        for name in files:
            if name.lower().endswith((".png", ".svg", ".jpg", ".jpeg", ".gif")):
                rel = os.path.relpath(os.path.join(folder, name), base).replace(os.sep, "/")
                assets[rel] = read_bytes(os.path.join(folder, name))
    parsed = {src: md_blocks(text.split("\n")) for src, text in sources.items()}
    slugs = {}
    for src, blocks in parsed.items():
        seen = {}
        slugs[src] = set()
        for b in blocks:
            if b[0] == "h":
                sid = slugify(b[2])
                n = seen.get(sid, 0)
                seen[sid] = n + 1
                slugs[src].add(sid if n == 0 else "%s-%d" % (sid, n))
    examples = {p[:-3] for p in os.listdir(os.path.join(base, "examples")) if p.endswith(".py")} \
        if os.path.isdir(os.path.join(base, "examples")) else set()
    made = {}
    used = set()
    for src, blocks in parsed.items():
        ctx = {"src": src, "slugs": slugs, "examples": examples, "assets": assets, "used": used}
        made[doc_path(src)] = (doc_page(shell, src, blocks, ctx), date)
    for rel in sorted(used):
        made["img/docs/" + rel] = (assets[rel], date)
    return made


# ----------------------------------------------------------------- search ---

# search.json lists every page with its title, address, headings and words (the
# lines of a whole script are left out: the gallery pages would triple its size).
# search.html reads it with plain JavaScript: no server, no library, nothing
# from elsewhere, so once the two files are loaded it works with no network.

SEARCH_JSON = "search.json"

SEARCH_STYLE = """
.search label{display:block;font-family:var(--cond);font-weight:700;font-size:19px;margin:0 0 6px}
.search input{width:100%;max-width:560px;font:inherit;padding:10px 12px;border:1.5px solid var(--ink);border-radius:0;background:var(--paper);color:var(--ink)}
.search input:focus-visible{outline:3px solid var(--blue);outline-offset:2px}
.search .count{margin:12px 0 0;color:var(--ink-2);font-size:15px}
.results{list-style:none;padding:0;margin:24px 0 0}
.results li{margin:0 0 22px;max-width:none}
.results a{font-family:var(--cond);font-size:20px;font-weight:700}
.results .url{display:block;font-size:13px;color:var(--ink-2)}
.results p{margin:4px 0 0;font-size:15px;max-width:80ch}
.results mark{background:#FFE88A;color:var(--ink);padding:0 1px}
"""

SEARCH_SCRIPT = r"""
(function () {
  var pages = [];
  var box = document.getElementById("q");
  var list = document.getElementById("results");
  var count = document.getElementById("count");
  var MAX = 40;
  var prepared = false;
  var loaded = false;

  function prepare() {
    if (prepared) { return; }
    prepared = true;
    pages.forEach(function (p) {
      p.lt = p.title.toLowerCase();
      p.lh = p.headings.map(function (h) { return h.t.toLowerCase(); });
      p.chunks = p.text.split("\n");
      p.lc = p.chunks.map(function (c) { return c.toLowerCase(); });
    });
  }

  function occurrences(hay, word) {
    var n = 0, at = hay.indexOf(word);
    while (at >= 0 && n < 10) { n += 1; at = hay.indexOf(word, at + word.length); }
    return n;
  }

  function score(p, words) {
    var total = 0;
    for (var i = 0; i < words.length; i += 1) {
      var w = words[i], here = 0;
      if (p.lt.indexOf(w) >= 0) { here += 20; }
      for (var h = 0; h < p.lh.length; h += 1) {
        if (p.lh[h].indexOf(w) >= 0) { here += 8; break; }
      }
      for (var c = 0; c < p.lc.length && here < 60; c += 1) {
        here += occurrences(p.lc[c], w);
      }
      if (here === 0) { return 0; }
      total += here;
    }
    return total;
  }

  function snippets(p, words) {
    var found = [];
    for (var c = 0; c < p.lc.length; c += 1) {
      var hit = 0;
      for (var i = 0; i < words.length; i += 1) {
        if (p.lc[c].indexOf(words[i]) >= 0) { hit += 1; }
      }
      if (hit > 0) { found.push({ at: c, hit: hit }); }
    }
    found.sort(function (a, b) { return b.hit - a.hit || a.at - b.at; });
    return found.slice(0, 2).sort(function (a, b) { return a.at - b.at; });
  }

  function marked(text, words) {
    var low = text.toLowerCase(), spans = [], start = 0, end = text.length;
    words.forEach(function (w) {
      var at = low.indexOf(w);
      while (at >= 0) { spans.push([at, at + w.length]); at = low.indexOf(w, at + w.length); }
    });
    spans.sort(function (a, b) { return a[0] - b[0]; });
    if (spans.length && text.length > 170) {
      start = Math.max(0, spans[0][0] - 60);
      end = Math.min(text.length, start + 170);
    }
    var p = document.createElement("p");
    if (start > 0) { p.appendChild(document.createTextNode("... ")); }
    var pos = start;
    spans.forEach(function (s) {
      if (s[0] < pos || s[0] >= end) { return; }
      var to = Math.min(s[1], end);
      p.appendChild(document.createTextNode(text.slice(pos, s[0])));
      var m = document.createElement("mark");
      m.appendChild(document.createTextNode(text.slice(s[0], to)));
      p.appendChild(m);
      pos = to;
    });
    p.appendChild(document.createTextNode(text.slice(pos, end)));
    if (end < text.length) { p.appendChild(document.createTextNode(" ...")); }
    return p;
  }

  function show() {
    var words = box.value.toLowerCase().split(/\s+/).filter(function (w) { return w; });
    while (list.firstChild) { list.removeChild(list.firstChild); }
    if (!words.length) { count.textContent = "Type a word to search the whole site."; return; }
    if (!loaded) { count.textContent = "Loading the list of pages ..."; return; }
    prepare();
    var hits = [];
    pages.forEach(function (p) {
      var s = score(p, words);
      if (s > 0) { hits.push({ p: p, s: s }); }
    });
    hits.sort(function (a, b) { return b.s - a.s || (a.p.title < b.p.title ? -1 : 1); });
    count.textContent = hits.length
      ? hits.length + (hits.length === 1 ? " page matches." : " pages match.")
        + (hits.length > MAX ? " The first " + MAX + " are shown." : "")
      : "No page matches. Try fewer or shorter words.";
    hits.slice(0, MAX).forEach(function (hit) {
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.href = hit.p.url;
      a.appendChild(document.createTextNode(hit.p.title));
      li.appendChild(a);
      var u = document.createElement("span");
      u.className = "url";
      u.appendChild(document.createTextNode(hit.p.url));
      li.appendChild(u);
      snippets(hit.p, words).forEach(function (s) {
        li.appendChild(marked(hit.p.chunks[s.at], words));
      });
      list.appendChild(li);
    });
  }

  function failed() {
    count.textContent = "The list of pages could not be loaded. Reload the page to try again.";
  }

  var q = /[?&]q=([^&]*)/.exec(window.location.search);
  if (q) {
    try { box.value = decodeURIComponent(q[1].replace(/\+/g, " ")); } catch (e) { box.value = ""; }
  }
  box.addEventListener("input", show);
  var req = new XMLHttpRequest();
  req.open("GET", "search.json");
  req.onload = function () {
    if (req.status >= 400) { failed(); return; }
    try { pages = JSON.parse(req.responseText); } catch (e) { failed(); return; }
    loaded = true;
    show();
  };
  req.onerror = failed;
  req.send();
})();
"""

LONG_CODE = 40     # a code block of more lines than this is a whole script: not indexed
BLOCK_TAGS = {"p", "li", "td", "th", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "pre",
              "figcaption", "figure", "dt", "dd", "div", "section", "article", "blockquote",
              "table", "ul", "ol", "br", "caption", "header", "main"}


class PageText(HTMLParser):
    """A page's title, headings (with their ids) and the text of its main part."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.headings = []
        self.chunks = []
        self._buf = []
        self._in_title = False
        self._in_main = False
        self._skip = 0
        self._pre = 0
        self._pre_at = 0
        self._heading = None

    def _flush(self):
        text = " ".join("".join(self._buf).split())
        self._buf = []
        if text:
            self.chunks.append(text)
        return text

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "main":
            self._in_main = True
        if tag in ("script", "style", "svg", "footer", "template"):
            self._skip += 1
        if not self._in_main or self._skip:
            return
        if tag in BLOCK_TAGS:
            self._flush()
        if tag == "pre":
            self._pre += 1
            self._pre_at = len(self.chunks)
        if re.fullmatch(r"h[1-6]", tag):
            self._heading = a.get("id")
        if tag == "img" and a.get("alt"):
            self._flush()
            self._buf.append(a["alt"])
            self._flush()

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in ("script", "style", "svg", "footer", "template") and self._skip:
            self._skip -= 1
            return
        if not self._in_main or self._skip:
            return
        if re.fullmatch(r"h[1-6]", tag):
            text = self._flush()
            if text:
                entry = {"t": text}
                if self._heading:
                    entry["id"] = self._heading
                self.headings.append(entry)
            self._heading = None
        elif tag in BLOCK_TAGS:
            self._flush()
        if tag == "pre" and self._pre:
            self._pre -= 1
            self._flush()
            if len(self.chunks) - self._pre_at > LONG_CODE:
                del self.chunks[self._pre_at:]   # a whole script is not searched

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if not self._in_main or self._skip:
            return
        if self._pre:
            parts = data.split("\n")
            for k, part in enumerate(parts):
                self._buf.append(part)
                if k < len(parts) - 1:
                    self._flush()
        else:
            self._buf.append(data)


def search_entry(rel, page_html):
    p = PageText()
    p.feed(page_html)
    p.close()
    p._flush()
    url = "/" + rel
    if rel == "index.html":
        url = "/"
    elif rel.endswith("/index.html"):
        url = "/" + rel[:-len("index.html")]
    return {"url": url, "title": " ".join(p.title.split()), "headings": p.headings,
            "text": "\n".join(p.chunks)}


def search_page(shell):
    out = [
        '    <h1>Search the site</h1>',
        '    <p class="lead">Every page of this site, its documentation and its examples. '
        'Matching words are shown in their sentence.</p>',
        '    <div class="search">',
        '    <label for="q">Search for</label>',
        '    <input id="q" type="search" autocomplete="off" spellcheck="false">',
        '    <p class="count" id="count" role="status" aria-live="polite">'
        'Type a word to search the whole site.</p>',
        '    </div>',
        '    <noscript><p>Search needs JavaScript. '
        'Without it, start from the <a href="/docs/">documentation</a>, the '
        '<a href="/gallery.html">examples</a> or the <a href="/releases.html">release notes</a>.</p>'
        '</noscript>',
        '    <ol class="results" id="results"></ol>',
        '    <script>',
        SEARCH_SCRIPT.strip("\n"),
        '    </script>',
    ]
    return make_page(
        shell, "search.html", "Search | DX-CAD by Designmatix",
        "Search every page of the DX-CAD site, its documentation and its examples. "
        "It works with no server and no outside library.",
        "\n".join(out), GALLERY_STYLE + SEARCH_STYLE)


def search_files(root, made):
    """search.json: every page here, newest content (made pages from memory, the
    others from disk), in the order of their addresses."""
    pages = {}
    for rel in page_files(root):
        pages[rel] = read_text(os.path.join(root, rel))
    for rel, (content, _) in made.items():
        if rel.endswith(".html"):
            pages[rel] = content
    for rel in NOT_LISTED:
        pages.pop(rel, None)
    entries = sorted((search_entry(rel, text) for rel, text in pages.items()),
                     key=lambda e: e["url"])
    body = "[\n" + ",\n".join(json.dumps(e, ensure_ascii=True, separators=(",", ":"))
                              for e in entries) + "\n]\n"
    return {SEARCH_JSON: body}


# --------------------------------------------------------------- download ---

DOWNLOAD_STYLE = """
.doc .lead{font-size:19px;max-width:62ch;margin:0 0 24px}
.doc dl.facts{display:grid;grid-template-columns:max-content 1fr;gap:6px 24px;margin:0 0 24px;max-width:none}
.doc dl.facts dt{font-family:var(--cond);font-weight:700}
.doc dl.facts dd{margin:0}
.doc .files{width:100%;border-collapse:collapse;margin:0 0 24px}
.doc .files th,.doc .files td{border:1px solid var(--ink);padding:8px 10px;text-align:left;vertical-align:top}
.doc .files code{word-break:break-all}
pre.script{overflow-x:auto;border:1px solid var(--ink);background:var(--wash);padding:16px 20px;font-size:14px;line-height:1.5;max-width:none;tab-size:4}
pre.script code{background:none;padding:0;font-size:inherit}
"""

LATEST = "latest.json"
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def read_latest(root):
    """data/core/latest.json as a dict, with its files as a list of
    {name, size, sha256, url, what} (a key the file does not give is None)."""
    path = os.path.join(root, "data", "core", LATEST)
    try:
        data = json.loads(read_text(path))
    except (OSError, ValueError) as e:
        raise ValueError("data/core/%s cannot be read: %s" % (LATEST, e))
    if not isinstance(data, dict):
        raise ValueError("data/core/%s is not a JSON object" % LATEST)
    for key in ("version", "date"):
        if not isinstance(data.get(key), str) or not data[key]:
            raise ValueError("data/core/%s has no %r" % (LATEST, key))
    try:
        data["when"] = datetime.date.fromisoformat(data["date"])
    except ValueError:
        raise ValueError("data/core/%s: date %r is not YYYY-MM-DD" % (LATEST, data["date"]))
    raw = data.get("files") or []
    if isinstance(raw, dict):
        raw = [dict(v if isinstance(v, dict) else {"url": v}, name=k) for k, v in raw.items()]
    files = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("data/core/%s: a file entry is not an object" % LATEST)
        name = item.get("name") or item.get("file") or item.get("filename")
        url = item.get("url")
        if not name and url:
            name = url.rstrip("/").rsplit("/", 1)[-1]
        if not name:
            raise ValueError("data/core/%s: a file entry has no name" % LATEST)
        size = item.get("size", item.get("bytes"))
        if size is not None and (isinstance(size, bool) or not isinstance(size, int) or size < 0):
            raise ValueError("data/core/%s: the size of %s is not a whole number of bytes"
                             % (LATEST, name))
        sha = item.get("sha256")
        if sha is not None and not SHA256_RE.match(str(sha)):
            raise ValueError("data/core/%s: the sha256 of %s is not 64 hex digits" % (LATEST, name))
        files.append({"name": str(name), "size": size, "url": url,
                      "sha256": str(sha).lower() if sha else None,
                      "what": item.get("what") or item.get("description")})
    data["files"] = files
    return data


def size_words(n):
    """12345678 -> '12,345,678 bytes (11.8 MB)'."""
    out = "{:,} bytes".format(n)
    for unit, step in (("GB", 1 << 30), ("MB", 1 << 20), ("KB", 1 << 10)):
        if n >= step:
            return "%s (%.1f %s)" % (out, n / step, unit)
    return out


def download_page(root, shell):
    d = read_latest(root)
    version, when = d["version"], d["when"]
    out = [
        '    <h1>Download DX-CAD</h1>',
        '    <p class="lead">The current version is <strong>%s</strong>, released on %s.</p>'
        % (esc(version), long_date(when)),
    ]
    if d.get("note"):
        out.append('    <p>%s</p>' % esc(d["note"]))
    out += ['    <h2>This version</h2>', '    <dl class="facts">',
            '      <dt>Version</dt><dd>%s</dd>' % esc(version),
            '      <dt>Released</dt><dd><time datetime="%s">%s</time></dd>'
            % (when.isoformat(), long_date(when))]
    for key, label in (("licences_from", "Licences from"), ("trial_until", "Trial until")):
        v = d.get(key)
        if isinstance(v, str):
            try:
                v = long_date(datetime.date.fromisoformat(v))
            except ValueError:
                pass
            out.append('      <dt>%s</dt><dd>%s</dd>' % (label, esc(str(v))))
    out.append('    </dl>')
    out += ['    <h2>Install with Python</h2>',
            '    <pre class="script"><code>pip install dxcad</code></pre>']
    if d.get("url"):
        out.append('    <p>This version\'s page on PyPI: <a href="%s">%s</a>.</p>'
                   % (esc(d["url"]), esc(d["url"])))
    out.append('    <p>The installer for Windows, the builds for macOS and Linux and what they need '
               'are on the <a href="/#download">home page</a>; the first steps are in the '
               '<a href="/tutorial.html">tutorial</a>.</p>')
    out.append('    <h2>Files</h2>')
    files = d["files"]
    if not files:
        out.append('    <p>The public record of this release names no downloadable file, so none is '
                   'listed here with a size or a checksum. Use the install above, or the '
                   '<a href="/#download">home page</a>.</p>')
    else:
        out += ['    <table class="files">',
                '      <caption class="vh">Files of DX-CAD %s, with their sizes and SHA-256 '
                'checksums</caption>' % esc(version),
                '      <thead><tr><th scope="col">File</th><th scope="col">Size</th>'
                '<th scope="col">SHA-256</th><th scope="col">What to do with it</th></tr></thead>',
                '      <tbody>']
        for f in files:
            name = esc(f["name"])
            cell = '<a href="%s">%s</a>' % (esc(f["url"]), name) if f["url"] else name
            size = size_words(f["size"]) if f["size"] is not None else "not given"
            sha = "<code>%s</code>" % f["sha256"] if f["sha256"] else "not given"
            what = esc(f["what"]) if f["what"] else (
                "Download it, check its SHA-256 as described below, then run it "
                "or unpack it.")
            out.append('      <tr><th scope="row">%s</th><td>%s</td><td>%s</td><td>%s</td></tr>'
                       % (cell, size, sha, what))
        out += ['      </tbody>', '    </table>']
        out += ['    <h2>Check a download</h2>',
                '    <p>A checksum shows that the file you have is the file listed. On Windows, '
                'run <code>certutil -hashfile FILE SHA256</code>; on macOS or Linux, run '
                '<code>shasum -a 256 FILE</code>. The digits must be the same as the ones above.</p>']
    out.append('    <p>See <a href="/releases.html">what is new in each release</a>.</p>')
    return make_page(
        shell, "download.html", "Download DX-CAD %s | DX-CAD by Designmatix" % version,
        "Download DX-CAD %s, released on %s: the install, and each file with its size and "
        "checksum where the public record gives one." % (version, long_date(when)),
        "\n".join(out), DOWNLOAD_STYLE)


def build_download(root, shell, date):
    return {"download.html": (download_page(root, shell), date)}


# -------------------------------------------------------------------- faq ---

FAQ_STYLE = """
.doc .lead{font-size:19px;max-width:62ch;margin:0 0 24px}
.doc .qa{border-top:1px solid var(--line);padding-top:4px;margin:0 0 8px}
.doc .qa h3{margin:12px 0 6px}
.doc .qa p{margin:0 0 8px}
.doc .qa .more{font-size:15px}
"""

# The questions about gui.md: (question, the heading of its section, which paragraph of the
# section answers it, and which sentences of it, from and up to).  The answer is gui.md's own
# words, nothing added.
FAQ_WINDOW = [
    ("What is the window, and how do I open it?", "The window", 0, (0, 1)),
    ("Does DX-CAD need a display?", "The window", 1, (0, 2)),
    ("Can I have several documents open at once?", "Tabs", 0, (0, 2)),
    ("Where does the model live in the window?", "The model pane", 0, (0, 2)),
    ("Is it safe to open a project someone sent me?", "The model a project carries", 0, (0, 2)),
    ("Can I ask the Assistant to build or change a part?", "The Assistant", 0, (0, 1)),
    ("How do I get help while I work?", "The help window", 0, (0, 1)),
    ("Where do I find the keyboard shortcuts?", "The Keyboard Shortcuts box", 0, (0, 1)),
]

# The questions about limitations.md, by the heading of each section.  A section with no
# question here still gets one, made from its heading, so a limitation added to the doc is
# never left out.
FAQ_LIMITS = {
    "Fillets that would consume a face": "Why is a large fillet refused?",
    "Fillets meeting at a vertex":
        "Why does a fillet fail where several filleted edges meet at a corner?",
    "Variable-radius fillets": "Can a fillet change its radius along an edge?",
    "Booleans on coincident or tangent faces":
        "Why does a boolean fail when two parts only touch?",
    "Shelling and offsets on complex faces": "Why can a part not always be hollowed out?",
    "Persistent naming": "Do face numbers stay the same when an earlier feature changes?",
    "STEP and IGES files that need healing":
        "Does DX-CAD repair STEP files, and does it read IGES?",
    "No simultaneous assembly solver":
        "Can DX-CAD solve all the mates of an assembly at once?",
    "Large assemblies": "Can DX-CAD work with an assembly of thousands of parts?",
    "Pictures without a window on macOS":
        "Can DX-CAD draw a picture of a part on a Mac with no window open?",
    "The robustness suite": "What happens with the hardest cases, such as a fillet that is too big?",
}

ITEM_RE = re.compile(r"\s*\(items? [\d, and]+\)")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z`\"(])")


def faq_sentences(text, first, last):
    """Sentences first..last-1 of a paragraph, with the private item numbers the docs
    carry taken out."""
    text = ITEM_RE.sub("", " ".join(text.split()))
    out = " ".join(SENTENCE_RE.split(text)[first:last]).strip()
    return out[:1].upper() + out[1:]


def faq_sections(blocks, level):
    """{heading: [paragraph text]} of the sections at heading level `level` (the
    paragraphs before the next heading of any level are the section's own)."""
    found, current = {}, None
    for b in blocks:
        if b[0] == "h":
            current = md_plain(b[2]) if b[1] == level else None
            if current is not None:
                found[current] = []
        elif b[0] == "p" and current is not None:
            found[current].append(b[1])
    return found


def faq_entries(root):
    """([(group, question, [answer markdown], doc, heading to link to)], {doc: blocks})."""
    sources = doc_sources(root)
    for name in ("gui.md", "limitations.md"):
        if name not in sources:
            raise ValueError("data/core/%s is missing; the questions page is made from it" % name)
    parsed = {s: md_blocks(sources[s].split("\n")) for s in ("gui.md", "limitations.md")}
    gui, lim = parsed["gui.md"], parsed["limitations.md"]
    gui_sections = {}
    for level in (1, 2, 3):
        for heading, paras in faq_sections(gui, level).items():
            gui_sections.setdefault(heading, paras)
    entries = []
    for question, heading, which, (a, b) in FAQ_WINDOW:
        paras = gui_sections.get(heading, [])
        if len(paras) <= which:
            raise ValueError("data/core/gui.md has no paragraph %d under '%s'" % (which + 1, heading))
        entries.append(("window", question, [faq_sentences(paras[which], a, b)], "gui.md", heading))
    # the first paragraph of limitations.md says what builds the solids
    intro = next(b[1] for b in lim if b[0] == "p")
    entries.append(("limits", "What does DX-CAD build its solids with?",
                    [faq_sentences(intro, 0, 1)], "limitations.md", None))
    for heading, paras in faq_sections(lim, 2).items():
        if not paras:
            raise ValueError("data/core/limitations.md: the section '%s' has no paragraph" % heading)
        question = FAQ_LIMITS.get(heading) or "What should I know about: %s?" % heading.lower()
        text = [" ".join(p.split()) for p in paras]
        cause = next((t for t in text if t.startswith("Cause:")), None)
        work = next((t for t in text if t.startswith("Workaround:")), None)
        if cause and work:
            answer = [faq_sentences(cause[len("Cause:"):], 0, 3),
                      "Workaround: " + faq_sentences(work[len("Workaround:"):], 0, 2)]
        else:
            answer = [faq_sentences(text[0], 0, 2)]
        entries.append(("limits", question, answer, "limitations.md", heading))
    return entries, parsed


def faq_page(root, shell):
    entries, parsed = faq_entries(root)
    slugs, titles = {}, {}
    for src, blocks in parsed.items():
        seen, slugs[src] = {}, set()
        for b in blocks:
            if b[0] == "h":
                sid = slugify(b[2])
                n = seen.get(sid, 0)
                seen[sid] = n + 1
                slugs[src].add(sid if n == 0 else "%s-%d" % (sid, n))
        titles[src] = next(md_plain(b[2]) for b in blocks if b[0] == "h")
    out = [
        '    <h1>Questions and answers</h1>',
        '    <p class="lead">What DX-CAD does and what it does not do, in plain words. Each answer '
        'is taken from the public documentation, and its link goes to the page that says more.</p>',
    ]
    group_titles = {"window": "What DX-CAD does", "limits": "What DX-CAD does not do"}
    shown, used = None, set()
    for group, question, answer, src, heading in entries:
        if group != shown:
            shown = group
            out.append('    <h2>%s</h2>' % group_titles[group])
        ctx = {"src": src, "slugs": slugs, "examples": set(), "assets": {}, "used": set()}
        base = qid = "q-" + slugify(question)
        n = 1
        while qid in used:
            n += 1
            qid = "%s-%d" % (base, n)
        used.add(qid)
        href, label = doc_href(src), titles[src]
        if heading is not None:
            sid = slugify(heading)
            if sid not in slugs[src]:
                raise ValueError("%s has no heading '%s' to link to" % (src, heading))
            href += "#" + sid
            label = md_plain(heading)
        out.append('    <div class="qa" id="%s">' % qid)
        out.append('      <h3>%s</h3>' % esc(question))
        for para in answer:
            out.append('      <p>%s</p>' % md_inline(para, ctx))
        out.append('      <p class="more">More: <a href="%s">%s</a></p>' % (esc(href), esc(label)))
        out.append('    </div>')
    return make_page(
        shell, "faq.html", "Questions and answers | DX-CAD by Designmatix",
        "What DX-CAD does and does not do, in plain words: short answers from the public "
        "documentation, each linked to the page that says more.",
        "\n".join(out), FAQ_STYLE)


def build_faq(root, shell, date):
    return {"faq.html": (faq_page(root, shell), date)}


# --------------------------------------------------------------- shortcuts ---

SHORTCUTS_STYLE = """
.doc .lead{font-size:19px;max-width:62ch;margin:0 0 24px}
.doc .keys{width:100%;max-width:640px;border-collapse:collapse;margin:0 0 24px}
.doc .keys th,.doc .keys td{border:1px solid var(--ink);padding:6px 10px;text-align:left;vertical-align:top}
.doc .keys kbd{font-family:Consolas,"Cascadia Mono",monospace;background:var(--wash);font-size:15px;border:1px solid var(--ink-2);padding:1px 6px;white-space:nowrap}
"""


def shortcut_rows(root):
    """([(menu, action, [key])] in the order gui.md has them, its intro sentences).  The
    rows are the table under '## Keyboard shortcuts' in data/core/gui.md."""
    gui = doc_sources(root).get("gui.md")
    if gui is None:
        raise ValueError("data/core/gui.md is missing; the shortcuts page is made from it")
    blocks = md_blocks(gui.split("\n"))
    start = next((i for i, b in enumerate(blocks)
                  if b[0] == "h" and md_plain(b[2]) == "Keyboard shortcuts"), None)
    if start is None:
        raise ValueError("data/core/gui.md has no '## Keyboard shortcuts' section")
    intro, table = [], None
    for b in blocks[start + 1:]:
        if b[0] == "h":
            break
        if b[0] == "p":
            intro.append(b[1])
        elif b[0] == "table" and table is None:
            table = b
    if table is None:
        raise ValueError("data/core/gui.md: no table under '## Keyboard shortcuts'")
    head = [md_plain(c) for c in table[1]]
    if head != ["Menu", "Action", "Keys"]:
        raise ValueError("data/core/gui.md: the shortcuts table has the columns %s, not "
                         "Menu, Action, Keys" % head)
    rows = []
    for row in table[2]:
        if len(row) != 3:
            raise ValueError("data/core/gui.md: a shortcuts row is not Menu, Action, Keys: %s" % row)
        keys = re.findall(r"`([^`]+)`", row[2]) or [md_plain(row[2])]
        rows.append((md_plain(row[0]), md_plain(row[1]), keys))
    if not rows:
        raise ValueError("data/core/gui.md: the shortcuts table has no rows")
    sentences = []
    for para in intro:
        for s in SENTENCE_RE.split(ITEM_RE.sub("", " ".join(para.split()))):
            if "docsgen" not in s and "a test fails" not in s:
                sentences.append(s)
    return rows, sentences


def shortcuts_page(root, shell):
    rows, sentences = shortcut_rows(root)
    ctx = {"src": "gui.md", "slugs": {"gui.md": set()}, "examples": set(), "assets": {},
           "used": set()}
    out = ['    <h1>Keyboard shortcuts</h1>']
    if sentences:
        out.append('    <p class="lead">%s</p>' % md_inline(" ".join(sentences), ctx))
    out.append('    <p>More about each menu is in <a href="/docs/gui.html">the page of the '
               'documentation about the window</a>.</p>')
    groups = {}
    for menu, action, keys in rows:
        groups.setdefault(menu, []).append((action, keys))
    for menu, items in groups.items():
        out += ['    <h2 id="%s">%s menu</h2>' % ("menu-" + slugify(menu), esc(menu)),
                '    <table class="keys">',
                '      <caption class="vh">Keyboard shortcuts of the %s menu</caption>' % esc(menu),
                '      <thead><tr><th scope="col">Action</th><th scope="col">Keys</th></tr></thead>',
                '      <tbody>']
        for action, keys in items:
            cell = " or ".join("<kbd>%s</kbd>" % esc(k) for k in keys)
            out.append('      <tr><th scope="row">%s</th><td>%s</td></tr>' % (esc(action), cell))
        out += ['      </tbody>', '    </table>']
    return make_page(
        shell, "shortcuts.html", "Keyboard shortcuts | DX-CAD by Designmatix",
        "Every keyboard shortcut of the DX-CAD window, grouped by menu, as the public "
        "documentation lists them.",
        "\n".join(out), SHORTCUTS_STYLE)


def build_shortcuts(root, shell, date):
    return {"shortcuts.html": (shortcuts_page(root, shell), date)}


# ----------------------------------------------------------------- images ---

IMG_RE = re.compile(r"<img\b[^>]*>")
ATTR_RE = re.compile(r'\s([a-zA-Z-]+)(?:="([^"]*)")?')


def picture_size(data):
    """(width, height) of a PNG, GIF or JPEG, read from its bytes; None if it is
    none of these or is cut short."""
    try:
        if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
            return struct.unpack(">II", data[16:24])
        if data[:6] in (b"GIF87a", b"GIF89a"):
            return struct.unpack("<HH", data[6:10])
        if data[:2] == b"\xff\xd8":
            i = 2
            while i + 9 < len(data):
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                if marker == 0xFF:
                    i += 1
                    continue
                if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                    i += 2
                    continue
                length = struct.unpack(">H", data[i + 2:i + 4])[0]
                if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                    h, w = struct.unpack(">HH", data[i + 5:i + 9])
                    return (w, h)
                i += 2 + length
    except struct.error:
        pass
    return None


def finish_images(text, page, lookup):
    """The page's <img> tags with a width and a height (read from the picture by
    picture_size) and with loading="lazy" on every picture but the first: that one
    is at the top of the page and loads at once.  A picture written into the
    page as data: is part of the page and is left as it is.  lookup(page, src)
    gives a picture's bytes, or None."""
    seen = [0]

    def fix(m):
        tag = m.group(0)
        attrs = dict((k.lower(), v) for k, v in ATTR_RE.findall(tag))
        src = html.unescape(attrs.get("src", ""))
        if not src or src.startswith("data:"):
            return tag
        first = seen[0] == 0
        seen[0] += 1
        if "width" not in attrs or "height" not in attrs:
            data = lookup(page, src)
            size = picture_size(data) if data else None
            if size:
                tag = re.sub(r"\s*/?>$", lambda e: ' width="%d" height="%d"%s' % (
                    size[0], size[1], e.group(0).lstrip()), tag, count=1)
        lazy = attrs.get("loading", "").lower() == "lazy"
        if first and lazy:
            tag = re.sub(r'\s+loading="lazy"', "", tag, count=1, flags=re.I)
        elif not first and not lazy:
            tag = re.sub(r'\s+loading="[^"]*"', "", tag, count=1, flags=re.I)
            tag = re.sub(r"\s*/?>$", lambda e: ' loading="lazy"' + e.group(0).lstrip(),
                         tag, count=1)
        return tag
    return IMG_RE.sub(fix, text)


def picture_lookup(root, made):
    """lookup(page, src) for finish_images: a picture this script makes (in made),
    else the file in the site's folder."""
    def lookup(page, src):
        src = src.split("#")[0].split("?")[0]
        if re.match(r"[a-z][a-z0-9+.-]*:|//", src, re.I):
            return None
        if src.startswith("/"):
            rel = src.lstrip("/")
        else:
            rel = posixpath.normpath(posixpath.join(posixpath.dirname(page), src))
        if rel in made:
            content = made[rel]
            content = content[0] if isinstance(content, tuple) else content
            return content if isinstance(content, bytes) else None
        path = os.path.join(root, *rel.split("/"))
        return read_bytes(path) if os.path.isfile(path) else None
    return lookup


# --------------------------------------------------------- 404, footers ---

NOT_FOUND_STYLE = """
.doc .lead{font-size:19px;max-width:62ch;margin:0 0 24px}
.doc .gone{font-family:var(--cond);font-size:15px;color:var(--ink-2);margin:0 0 8px}
.doc .ways{list-style:none;padding:0;margin:24px 0 0;display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px}
.doc .ways li{margin:0;max-width:none;border:1px solid var(--ink);padding:14px 16px}
.doc .ways a{font-family:var(--cond);font-weight:700;font-size:19px}
.doc .ways span{display:block;font-size:14px;color:var(--ink-2);margin-top:2px}
"""

# (address, name, what it is): the main pages the 404 page sends a visitor to.
MAIN_PAGES = [
    ("/", "Home", "What DX-CAD is, what it costs and how to get it."),
    ("/docs/", "Documentation", "The window, the examples and the known limits."),
    ("/tutorial.html", "Tutorial", "Your first part in ten minutes."),
    ("/gallery.html", "Examples", "Every example part, with its picture and its script."),
    ("/releases.html", "Releases", "What each DX-CAD release brought."),
    ("/faq.html", "Questions", "What DX-CAD does and does not do, in short answers."),
    ("/shortcuts.html", "Shortcuts", "Every keyboard shortcut of the window."),
    ("/search.html", "Search", "Find a word anywhere on the site."),
    ("/fabrication.html", "Fabrication", "The add-on for sheet and plate layout."),
    ("/drafting-pro.html", "Drafting Pro", "The add-on for drawings."),
]


def not_found_page(shell):
    out = [
        '    <p class="gone">Error 404</p>',
        '    <h1>That page is not here</h1>',
        '    <p class="lead">The address may have been typed wrongly, or the page may have moved. '
        'These are the main pages of the site:</p>',
        '    <ul class="ways">',
    ]
    for href, name, what in MAIN_PAGES:
        out.append('      <li><a href="%s">%s</a><span>%s</span></li>' % (href, name, esc(what)))
    out.append('    </ul>')
    return make_page(
        shell, "404.html", "Page not found | DX-CAD by Designmatix",
        "This page does not exist. Start again from the home page, the documentation, "
        "the tutorial or the search page of DX-CAD.",
        "\n".join(out), NOT_FOUND_STYLE, robots="noindex, follow")


def build_footers(root, made, lookup):
    """Every hand-made page with its footer replaced by FOOTER and its theme block
    in place: {path: text}."""
    out = {}
    for rel in page_files(root):
        if rel in made:
            continue
        text = read_text(os.path.join(root, rel))
        if len(FOOTER_RE.findall(text)) == 1:
            text = FOOTER_RE.sub(lambda m: FOOTER, text)
        if rel == "index.html":
            text = index_with_software(text, read_latest(root))
        out[rel] = finish_images(with_theme(text), rel, lookup)
    return out


# ---------------------------------------------------------------- sitemap ---

def page_files(root):
    found = []
    for folder, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS)
        for name in sorted(files):
            if name.endswith(".html"):
                rel = os.path.relpath(os.path.join(folder, name), root)
                found.append(rel.replace(os.sep, "/"))
    return found


def address(rel):
    if rel == "index.html":
        return SITE
    if rel.endswith("/index.html"):
        return SITE + rel[:-len("index.html")]
    return SITE + rel


def build_sitemap(root, made):
    """sitemap.xml: the pages here, each with the date it last changed."""
    old = {}
    order = []
    path = os.path.join(root, "sitemap.xml")
    if os.path.exists(path):
        for loc, mod in re.findall(
                r"<url>\s*<loc>(.*?)</loc>\s*<lastmod>(.*?)</lastmod>\s*</url>",
                read_text(path), re.S):
            old[loc] = mod
            order.append(loc)
    pages = set(page_files(root)) | {rel for rel in made if rel.endswith(".html")}
    pages -= NOT_LISTED
    wanted = {address(rel): rel for rel in pages}
    # A made page is dated by its data, but a page that is already committed
    # exactly as it is made keeps the date it has: only a page that changes
    # (or is new) takes the newest release's date.
    dates = {}
    for rel, (content, d) in made.items():
        if not rel.endswith(".html"):
            continue
        loc = address(rel)
        if loc in old and not differences(root, {rel: content}):
            continue
        dates[loc] = d.isoformat()
    locs = [loc for loc in order if loc in wanted]
    locs += sorted(loc for loc in wanted if loc not in locs)
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc in locs:
        lastmod = dates.get(loc) or old.get(loc) or datetime.date.today().isoformat()
        lines += ['  <url>', '    <loc>%s</loc>' % loc,
                  '    <lastmod>%s</lastmod>' % lastmod, '  </url>']
    lines += ['</urlset>', '']
    return "\n".join(lines)


# ------------------------------------------------------------------- main ---

def build_all(root):
    """Every file this script makes, as {relative path: text or bytes}."""
    shell = read_shell(root)
    made = {}
    made.update(build_releases(root, shell))
    date = made["releases.html"][1]      # the newest release's date
    made.update(build_gallery(root, shell, date))
    made.update(build_addons(root, shell, date))
    made.update(build_tutorial(root, shell, date))
    made.update(build_docs(root, shell, date))
    made.update(build_download(root, shell, date))
    made.update(build_faq(root, shell, date))
    made.update(build_shortcuts(root, shell, date))
    made["search.html"] = (search_page(shell), date)
    made["404.html"] = (not_found_page(shell), date)
    lookup = picture_lookup(root, made)
    for rel, (content, d) in list(made.items()):
        if rel.endswith(".html"):
            made[rel] = (finish_images(content, rel, lookup), d)
    files = {rel: content for rel, (content, _) in made.items()}
    files.update(build_footers(root, made, lookup))
    files.update(search_files(root, made))
    files["sitemap.xml"] = build_sitemap(root, made)
    return files


def differences(root, files):
    """Names of the files whose committed content is not what is made."""
    bad = []
    for rel, content in sorted(files.items()):
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            bad.append(rel)
        elif isinstance(content, bytes):
            if read_bytes(path) != content:
                bad.append(rel)
        elif read_text(path) != content:
            bad.append(rel)
    return bad


def write_files(root, files):
    """Write the files that are not already as made; leave the others alone."""
    for rel in differences(root, files):
        content = files[rel]
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = content if isinstance(content, bytes) else content.encode("utf-8")
        with open(path, "wb") as f:
            f.write(data)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="say whether every page made here is as committed; write nothing")
    ap.add_argument("--all", action="store_true",
                    help="remake every page made from data/, and the sitemap (the default)")
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    help="the site's folder (default: this repository)")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)
    files = build_all(root)
    bad = differences(root, files)
    if args.check:
        if bad:
            print("Not as made from data/: " + ", ".join(bad[:12])
                  + (" and %d more" % (len(bad) - 12) if len(bad) > 12 else ""))
            print("Run: python scripts/build_pages.py --all")
            return 1
        print("All %d made files are as committed." % len(files))
        return 0
    write_files(root, files)
    print("Wrote %d files (%d changed)." % (len(files), len(bad)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
