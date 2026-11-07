"""Checks for the site's pages, written so they can be run on any folder.

The tests run them on this repository and, to show that they fail when they
should, on copies made in a temporary folder.  Standard library only.
"""

import os
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

import a11ycheck

SITE = "https://dxcad.designmatix.co.uk/"
MAX_PAGE_BYTES = 300 * 1024

# Pages that are reachable (GitHub Pages serves 404.html for a missing address)
# but are not listed in sitemap.xml.
NOT_LISTED = {"404.html"}

# Folders that hold the repository's own files, not pages a visitor reaches.
SKIP_DIRS = {"data", "logs", "prompts", "scripts", "tests", "node_modules", "__pycache__"}

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}
# Tags whose end tag HTML lets a page leave out.
OPTIONAL_END = {"p", "li", "dt", "dd", "tr", "td", "th", "thead", "tbody",
                "tfoot", "option", "optgroup", "colgroup", "caption", "html",
                "head", "body"}
EXTERNAL = ("http:", "https:", "mailto:", "tel:", "data:", "javascript:", "//")


def page_files(root):
    """Every .html file a visitor can reach, as paths relative to root with '/'."""
    found = []
    for folder, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs
                         if not d.startswith(".") and d not in SKIP_DIRS)
        for name in sorted(files):
            if name.endswith(".html"):
                rel = os.path.relpath(os.path.join(folder, name), root)
                found.append(rel.replace(os.sep, "/"))
    return found


def canonical_for(rel):
    """The address a page must give as its canonical link."""
    if rel == "index.html":
        return SITE
    if rel.endswith("/index.html"):
        return SITE + rel[: -len("index.html")]
    return SITE + rel


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.titles = []
        self.metas = []          # attribute dicts of <meta>
        self.links = []          # attribute dicts of <link>
        self.refs = []           # (tag, attribute, value)
        self.imgs = []           # attribute dicts of <img>
        self.ids = set()
        self.html_lang = None
        self.errors = []
        self.headings = []       # (level, text)
        self.named = []          # {"tag", "attrs", "name"} for each link and button
        self.styles = []         # text of each <style>
        self.inline_styles = []  # style="..." attribute values
        self.first_focusable = None   # attributes of the first link or control in <body>
        self._stack = []
        self._frames = []        # open elements whose text is gathered
        self._in_title = False
        self._in_style = False
        self._in_body = False

    def handle_starttag(self, tag, attrs):
        a = {k: (v if v is not None else "") for k, v in attrs}
        if tag == "html":
            self.html_lang = a.get("lang")
        if tag == "title":
            self._in_title = True
            self.titles.append("")
        if tag == "style":
            self._in_style = True
            self.styles.append("")
        if tag == "body":
            self._in_body = True
        if a.get("style"):
            self.inline_styles.append(a["style"])
        self._note_structure(tag, a)
        if tag == "meta":
            self.metas.append(a)
        if tag == "link":
            self.links.append(a)
        if tag == "img":
            self.imgs.append(a)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a" and a.get("name"):
            self.ids.add(a["name"])
        for key in ("href", "src", "poster"):
            if key in a:
                self.refs.append((tag, key, a[key]))
        if "srcset" in a:
            for part in a["srcset"].split(","):
                bits = part.split()
                if bits:
                    self.refs.append((tag, "srcset", bits[0]))
        if tag not in VOID:
            self._stack.append(tag)

    def _note_structure(self, tag, a):
        """Headings, names of links and controls, the first thing to tab to."""
        focusable = ((tag == "a" and "href" in a) or tag in ("button", "select", "textarea")
                     or (tag == "input" and a.get("type", "").lower() != "hidden"))
        if self._in_body and focusable and self.first_focusable is None:
            a["_tag"] = tag
            self.first_focusable = a
        hidden = a.get("aria-hidden", "").lower() == "true"
        if tag in VOID:
            if tag == "img" and self._frames:
                for frame in self._frames:
                    if frame["kind"] == "name":
                        frame["text"].append(" " + a.get("alt", "") + " ")
            if tag == "input" and a.get("type", "").lower() in ("submit", "button", "reset", "image"):
                name = a.get("value") or a.get("alt") or ""
                self.named.append({"tag": "input", "attrs": a, "name": name.strip()})
            return
        if re.fullmatch(r"h[1-6]", tag):
            self._frames.append({"tag": tag, "kind": "heading", "text": [], "attrs": a})
        elif (tag == "a" and "href" in a) or tag == "button" or a.get("role") == "button":
            self._frames.append({"tag": tag, "kind": "name", "text": [], "attrs": a})
        elif hidden:
            self._frames.append({"tag": tag, "kind": "hidden", "text": [], "attrs": a})

    def _close_frame(self, tag):
        for i in range(len(self._frames) - 1, -1, -1):
            if self._frames[i]["tag"] == tag:
                frame = self._frames[i]
                del self._frames[i:]
                text = " ".join("".join(frame["text"]).split())
                if frame["kind"] == "heading":
                    self.headings.append((int(tag[1]), text))
                elif frame["kind"] == "name":
                    self.named.append({"tag": tag, "attrs": frame["attrs"], "name": text})
                return

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and self._stack and self._stack[-1] == tag:
            self._stack.pop()

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "style":
            self._in_style = False
        if tag not in VOID:
            self._close_frame(tag)
        if tag in VOID:
            return
        if tag in self._stack:
            while self._stack:
                top = self._stack.pop()
                if top == tag:
                    break
                if top not in OPTIONAL_END:
                    self.errors.append("<%s> is not closed before </%s>" % (top, tag))
        else:
            self.errors.append("</%s> closes nothing" % tag)

    def handle_data(self, data):
        if self._in_title:
            self.titles[-1] += data
        if self._in_style:
            self.styles[-1] += data
        if self._frames and not any(f["kind"] == "hidden" for f in self._frames):
            for frame in self._frames:
                frame["text"].append(data)

    def close(self):
        super().close()
        for top in self._stack:
            if top not in OPTIONAL_END:
                self.errors.append("<%s> is never closed" % top)


def parse(root, rel):
    p = Page()
    with open(os.path.join(root, rel), encoding="utf-8") as f:
        p.feed(f.read())
    p.close()
    return p


def resolve(root, rel, ref):
    """Path of the file a link points to, or None if it leaves the site."""
    ref = ref.strip()
    if not ref or ref.lower().startswith(EXTERNAL):
        return None
    parts = urlsplit(ref)
    path = unquote(parts.path)
    if not path:
        return rel   # a '#fragment' or '?query' on this very page
    if path.startswith("/"):
        target = os.path.join(root, path.lstrip("/"))
    else:
        target = os.path.join(root, os.path.dirname(rel), path)
    target = os.path.normpath(target)
    if os.path.isdir(target):
        target = os.path.join(target, "index.html")
    return os.path.relpath(target, root).replace(os.sep, "/")


def size_problems(root, rel, p=None):
    """The page plus the pictures a browser loads with it must fit the limit.

    A picture marked loading="lazy" is fetched only when the visitor scrolls to
    it, so it is not part of the page's first load; each one must still fit the
    limit on its own.
    """
    p = p or parse(root, rel)
    total = os.path.getsize(os.path.join(root, rel))
    out = []
    seen = set()
    for img in p.imgs:
        target = resolve(root, rel, img.get("src", ""))
        if not target or target in seen or not os.path.isfile(os.path.join(root, target)):
            continue
        seen.add(target)
        size = os.path.getsize(os.path.join(root, target))
        if img.get("loading", "").lower() == "lazy":
            if size > MAX_PAGE_BYTES:
                out.append("picture %s is %d KB, over the %d KB limit"
                           % (target, size // 1024, MAX_PAGE_BYTES // 1024))
        else:
            total += size
    if total > MAX_PAGE_BYTES:
        out.append("is %d KB with its pictures, over the %d KB limit"
                   % (total // 1024, MAX_PAGE_BYTES // 1024))
    return out


def social_problems(root, rel, p, canon):
    """Open Graph and Twitter card tags: present, filled, and true to the page."""
    out = []
    tags = {}
    for m in p.metas:
        key = m.get("property") or m.get("name") or ""
        if key.startswith(("og:", "twitter:")):
            tags.setdefault(key, []).append(m.get("content", ""))
    for key in ("og:title", "og:description", "og:url", "og:image", "twitter:card"):
        values = tags.get(key, [])
        if not values:
            out.append("has no %s tag" % key)
        elif len(values) > 1:
            out.append("has %s more than once" % key)
        elif not values[0].strip():
            out.append("its %s tag is empty" % key)
    url = tags.get("og:url", [""])[0]
    if url and url != canonical_for(rel):
        out.append("og:url is %r, should be its canonical address %r"
                   % (url, canonical_for(rel)))
    image = tags.get("og:image", [""])[0]
    if image:
        if not image.startswith(SITE + "img/"):
            out.append("og:image %r is not a picture in img/ on this site" % image)
        elif not os.path.isfile(os.path.join(root, image[len(SITE):])):
            out.append("og:image %r does not resolve to a file" % image)
    if tags.get("twitter:card", [""])[0] not in ("", "summary", "summary_large_image"):
        out.append("twitter:card is %r" % tags["twitter:card"][0])
    return out


def check_page(root, rel):
    """Problems with one page, as a list of plain sentences."""
    out = []
    p = parse(root, rel)
    for e in p.errors:
        out.append("does not parse cleanly: " + e)
    if p.html_lang != "en-GB":
        out.append('<html> has lang=%r, not "en-GB"' % p.html_lang)
    if len(p.titles) != 1:
        out.append("has %d <title> elements, not one" % len(p.titles))
    elif not p.titles[0].strip():
        out.append("its <title> is empty")
    descs = [m for m in p.metas if m.get("name", "").lower() == "description"]
    if len(descs) != 1 or not descs[0].get("content", "").strip():
        out.append("has no single, filled meta description")
    canon = [l for l in p.links if l.get("rel", "").lower() == "canonical"]
    if len(canon) != 1:
        out.append("has %d canonical links, not one" % len(canon))
    elif canon[0].get("href") != canonical_for(rel):
        out.append("canonical link is %r, should be %r"
                   % (canon[0].get("href"), canonical_for(rel)))
    out.extend(social_problems(root, rel, p, canon))
    out.extend(a11ycheck.a11y_problems(p))
    for img in p.imgs:
        if not img.get("alt", "").strip():
            out.append("image %r has no alt text" % (img.get("src", "")[:60],))
    for tag, attr, value in p.refs:
        target = resolve(root, rel, value)
        if target is None:
            continue
        if not os.path.isfile(os.path.join(root, target)):
            out.append("<%s %s=%r> does not resolve to a file" % (tag, attr, value[:80]))
            continue
        frag = urlsplit(value).fragment
        if frag and target.endswith(".html") and attr == "href":
            ids = p.ids if target == rel else parse(root, target).ids
            if unquote(frag) not in ids:
                out.append("link %r points to a missing anchor" % (value[:80],))
    out.extend(size_problems(root, rel, p))
    return out


def sitemap_locs(root):
    tree = ET.parse(os.path.join(root, "sitemap.xml"))
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [e.text.strip() for e in tree.getroot().findall("s:url/s:loc", ns)]


def check_site(root):
    """Problems for the whole folder, as (page, reason) pairs."""
    problems = []
    pages = page_files(root)
    for rel in pages:
        for reason in check_page(root, rel):
            problems.append((rel, reason))
    try:
        locs = sitemap_locs(root)
    except (OSError, ET.ParseError) as err:
        problems.append(("sitemap.xml", "cannot be read: %s" % err))
        locs = None
    if locs is not None:
        wanted = {canonical_for(rel): rel for rel in pages if rel not in NOT_LISTED}
        for dup in sorted({l for l in locs if locs.count(l) > 1}):
            problems.append(("sitemap.xml", "lists %s more than once" % dup))
        for addr, rel in sorted(wanted.items()):
            if addr not in locs:
                problems.append((rel, "is missing from sitemap.xml"))
        hidden = {canonical_for(rel) for rel in pages if rel in NOT_LISTED}
        for loc in locs:
            if loc in hidden:
                problems.append(("sitemap.xml", "lists %s, which must stay out of it" % loc))
            elif loc not in wanted:
                problems.append(("sitemap.xml", "lists %s, which is no page here" % loc))
    try:
        with open(os.path.join(root, "robots.txt"), encoding="utf-8") as f:
            robots = f.read()
        pattern = r"(?im)^sitemap:\s*" + re.escape(SITE + "sitemap.xml") + r"\s*$"
        if not re.search(pattern, robots):
            problems.append(("robots.txt", "does not name " + SITE + "sitemap.xml"))
    except OSError:
        problems.append(("robots.txt", "is missing"))
    return problems
