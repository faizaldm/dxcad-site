"""Makes the site's pages that are made from data/, and sitemap.xml.

Standard library only.  Run from anywhere:

    python scripts/build_pages.py            write every page it makes
    python scripts/build_pages.py --all      the same, named in full
    python scripts/build_pages.py --check    say whether each page is as committed

Pages made here:

    releases.html     from data/core/RELEASE_NOTES.md

The look of a made page is the look of the pages that are written by hand: its
style and its header are those of refunds.html, its footer is the index's.
Nothing in data/ is ever written to.
"""

import argparse
import datetime
import html
import os
import re
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


def make_page(shell, path, title, description, body, head_extra=""):
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
    if head_extra:
        head.append(head_extra)
    head.append(shell["style"])
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
    pages = set(page_files(root)) | set(made)
    wanted = {address(rel): rel for rel in pages}
    dates = {address(rel): d.isoformat() for rel, (_, d) in made.items()}
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
    """Every file this script makes, as {relative path: text}."""
    shell = read_shell(root)
    made = {}
    made.update(build_releases(root, shell))
    files = {rel: text for rel, (text, _) in made.items()}
    files["sitemap.xml"] = build_sitemap(root, made)
    return files


def differences(root, files):
    """Names of the files whose committed text is not what is made."""
    bad = []
    for rel, text in sorted(files.items()):
        path = os.path.join(root, rel)
        if not os.path.exists(path) or read_text(path) != text:
            bad.append(rel)
    return bad


def write_files(root, files):
    for rel, text in sorted(files.items()):
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(text.encode("utf-8"))


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
            print("Not as made from data/: " + ", ".join(bad))
            print("Run: python scripts/build_pages.py --all")
            return 1
        print("All %d made files are as committed." % len(files))
        return 0
    write_files(root, files)
    print("Wrote %s." % (", ".join(bad) if bad else "nothing new (all were as committed)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
