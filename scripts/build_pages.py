"""Makes the site's pages that are made from data/, and sitemap.xml.

Standard library only.  Run from anywhere:

    python scripts/build_pages.py            write every page it makes
    python scripts/build_pages.py --all      the same, named in full
    python scripts/build_pages.py --check    say whether each page is as committed

Pages made here:

    releases.html     from data/core/RELEASE_NOTES.md
    gallery.html, examples/NAME.html, img/gallery/...
                      from data/core/examples and data/core/gallery

The look of a made page is the look of the pages that are written by hand: its
style and its header are those of refunds.html, its footer is the index's.
Nothing in data/ is ever written to.
"""

import argparse
import ast
import datetime
import html
import os
import re
import struct
import sys

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


def read_shell(root):
    """The style, header and footer a made page takes from the hand-made ones."""
    refunds = read_text(os.path.join(root, "refunds.html"))
    index = read_text(os.path.join(root, "index.html"))
    icons = [ln for ln in refunds.split("\n")
             if ln.startswith(('<link rel="icon"', '<link rel="apple-touch-icon"'))]
    return {
        "icons": icons,
        "style": between(refunds, "<style>", "</style>", "style", "refunds.html"),
        "header": between(refunds, '<header class="bar">', "</header>", "header",
                          "refunds.html"),
        "footer": between(index, '<footer class="tb"', "</footer>", "footer",
                          "index.html"),
    }


def make_page(shell, path, title, description, body, extra_style=""):
    """A whole page, as text.  path is the page's file name, e.g. releases.html."""
    url = SITE + path
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
        '<meta name="robots" content="index, follow">',
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
    head.append(shell["style"])
    if extra_style:
        head.append("<style>\n%s\n</style>" % extra_style.strip("\n"))
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
        releases_body(releases))
    return {"releases.html": (page, latest["date"])}


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
    """sitemap.xml: the pages here; each made page's date is its data's date."""
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
    wanted = {address(rel): rel for rel in pages}
    dates = {address(rel): d.isoformat() for rel, (_, d) in made.items()
             if rel.endswith(".html")}
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
    files = {rel: content for rel, (content, _) in made.items()}
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
    for rel, content in sorted(files.items()):
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
