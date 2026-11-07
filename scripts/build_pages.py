"""Makes the site's pages that are made from data/, and sitemap.xml.

Standard library only.  Run from anywhere:

    python scripts/build_pages.py            write every page it makes
    python scripts/build_pages.py --all      the same, named in full
    python scripts/build_pages.py --check    say whether each page is as committed

Pages made here:

    releases.html     from data/core/RELEASE_NOTES.md
    gallery.html, examples/NAME.html, img/gallery/...
                      from data/core/examples and data/core/gallery
    fabrication.html, drafting-pro.html
                      from data/core/gui.md and the site's own words

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
