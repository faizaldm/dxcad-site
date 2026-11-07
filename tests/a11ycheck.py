"""Accessibility checks for one parsed page (see pagecheck.Page).

Headings in order, a working skip link, a name for every link and button, no
file names for alt text, and WCAG AA contrast for the colours the page's CSS
gives its text.  Standard library only.
"""

import re

# WCAG AA asks 4.5 : 1 for text (3 : 1 for large text); the site holds all of
# its text to the stricter figure.
MIN_CONTRAST = 4.5
NAMED_COLOURS = {"white": (255, 255, 255), "black": (0, 0, 0)}
FILE_NAME = re.compile(r"^[^\s/\\]+\.(png|jpe?g|gif|svg|webp|avif|ico|bmp|tiff?)$", re.I)
KEEPING = ("transparent", "inherit", "initial", "unset", "currentcolor", "revert")


def heading_problems(p):
    """Headings start at h1 and never skip a level going down."""
    out = []
    prev = 0
    for level, text in p.headings:
        if level - prev > 1:
            if prev == 0:
                out.append("its first heading is <h%d> %r, not <h1>" % (level, text[:40]))
            else:
                out.append("heading <h%d> %r follows <h%d>, skipping a level"
                           % (level, text[:40], prev))
        prev = level
    return out


def skip_link_problems(p):
    """The first thing a keyboard reaches is a "Skip to content" link that works."""
    first = p.first_focusable
    if first is None or first.get("_tag") != "a":
        return ['does not start with a "Skip to content" link']
    href = first.get("href", "")
    if not href.startswith("#") or len(href) < 2:
        return ['its first link is %r, not a "Skip to content" link to an id on the page'
                % href[:40]]
    out = []
    names = [n for n in p.named if n["attrs"] is first]
    if not names or not re.fullmatch(r"skip to (main )?content", names[0]["name"].lower()):
        out.append('its first link does not say "Skip to content"')
    if href[1:] not in p.ids:
        out.append('its "Skip to content" link points to a missing id %r' % href[1:])
    return out


def name_problems(p):
    """Every link and button has a name a screen reader can say."""
    out = []
    for n in p.named:
        a = n["attrs"]
        name = (a.get("aria-label") or n["name"] or a.get("title")
                or a.get("aria-labelledby") or "").strip()
        if not name:
            what = a.get("href") or a.get("id") or ""
            out.append("<%s %s> has no name a screen reader can say" % (n["tag"], what[:60]))
    return out


def alt_problems(p):
    """An alt that is a file name tells nobody what the picture shows."""
    out = []
    for img in p.imgs:
        alt = img.get("alt", "").strip()
        src = img.get("src", "")
        base = src.split("?")[0].rsplit("/", 1)[-1]
        if alt and (FILE_NAME.match(alt) or (base and alt.lower() == base.lower())):
            out.append("image %r has a file name for alt text: %r" % (src[:60], alt))
    return out


# ---------------------------------------------------------------- contrast ---

def parse_colour(value):
    """(r, g, b) of a solid colour written as hex, rgb() or white/black, else None."""
    value = value.strip().lower().replace("!important", "").strip()
    if value in NAMED_COLOURS:
        return NAMED_COLOURS[value]
    m = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", value)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = re.fullmatch(r"rgb\(\s*(\d+)[\s,]+(\d+)[\s,]+(\d+)\s*\)", value)
    if m:
        return tuple(min(255, int(g)) for g in m.groups())
    return None


def luminance(rgb):
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg, bg):
    hi, lo = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def split_top(text, sep):
    """Split on sep outside brackets and quotes (a url(data:...;base64) has ';')."""
    parts, depth, quote, cur = [], 0, "", []
    for ch in text:
        if quote:
            if ch == quote:
                quote = ""
        elif ch in ('"', "'"):
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
            continue
        cur.append(ch)
    parts.append("".join(cur))
    return parts


def parse_declarations(text):
    out = {}
    for part in split_top(text, ";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out


def parse_css(text):
    """[(selector, {property: value})], with @media and @supports flattened."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    rules = []
    i, n = 0, len(text)
    while i < n:
        j = text.find("{", i)
        if j < 0:
            break
        prelude = text[i:j].strip()
        depth, k, quote = 1, j + 1, ""
        while k < n and depth:
            ch = text[k]
            if quote:
                if ch == quote:
                    quote = ""
            elif ch in ('"', "'"):
                quote = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            k += 1
        inner = text[j + 1:k - 1]
        if prelude.startswith("@"):
            if prelude.lower().startswith(("@media", "@supports")):
                rules.extend(parse_css(inner))
        else:
            for sel in prelude.split(","):
                rules.append((" ".join(sel.split()), parse_declarations(inner)))
        i = k
    return rules


def resolve_vars(value, variables, depth=0):
    def sub(m):
        name, fallback = m.group(1), m.group(2)
        if name in variables and depth < 10:
            return resolve_vars(variables[name], variables, depth + 1)
        return fallback if fallback is not None else m.group(0)
    return re.sub(r"var\(\s*(--[\w-]+)\s*(?:,\s*([^)]*))?\)", sub, value)


def colour_of(prop, value):
    """("ok", rgb), ("none", None) when no solid colour is set, or ("bad", text)."""
    value = value.strip()
    low = value.lower()
    if prop != "color":   # background and background-color
        if "gradient" in low or "url(" in low:
            return ("none", None)
        tokens = split_top(value, " ")
        found = [parse_colour(t) for t in tokens if parse_colour(t)]
        if found:
            return ("ok", found[0])
        if low in KEEPING or low == "none" or any(t.lower() in KEEPING for t in tokens):
            return ("none", None)
        return ("bad", value)
    if low in KEEPING:
        return ("none", None)
    rgb = parse_colour(value)
    return ("ok", rgb) if rgb else ("bad", value)


def show(rgb):
    return "#%02X%02X%02X" % rgb


def contrast_problems(p):
    """Each text colour the page's CSS sets, on the background it sits on.

    A rule that sets a colour and a background is checked as a pair.  A rule
    that sets only a colour is checked on the page background and on every
    other light surface the CSS declares.  A rule that sets only a background
    is checked with the colour the same selector has (without :hover or
    :focus), or the page's text colour.
    """
    rules = []
    for css in p.styles:
        rules.extend(parse_css(css))
    for inline in p.inline_styles:
        rules.append(("style=" + inline[:30], parse_declarations(inline)))
    variables = {}
    for sel, decls in rules:
        if sel in (":root", "html"):
            for k, v in decls.items():
                if k.startswith("--"):
                    variables[k] = v
    out = []
    entries = []
    for sel, decls in rules:
        entry = {}
        for prop in ("color", "background", "background-color"):
            if prop not in decls:
                continue
            kind, val = colour_of(prop, resolve_vars(decls[prop], variables))
            if kind == "bad":
                out.append("rule %r: cannot read the colour in %s: %s" % (sel[:50], prop, val[:40]))
            elif kind == "ok":
                entry["fg" if prop == "color" else "bg"] = val
        entries.append((sel, entry))
    body = next((e for s, e in entries if s == "body"), {})
    page_bg = body.get("bg", (255, 255, 255))
    page_fg = body.get("fg", (0, 0, 0))
    surfaces = [page_bg]
    for _, e in entries:
        if "bg" in e and luminance(e["bg"]) > 0.5 and e["bg"] not in surfaces:
            surfaces.append(e["bg"])
    base = {s: e["fg"] for s, e in entries if "fg" in e}
    for sel, e in entries:
        fg, bg = e.get("fg"), e.get("bg")
        if fg and bg:
            pairs = [(fg, bg)]
        elif fg:
            pairs = [(fg, s) for s in surfaces]
        elif bg:
            stem = re.sub(r":(hover|focus|focus-visible|active)\b", "", sel)
            pairs = [(base.get(stem, page_fg), bg)]
        else:
            continue
        for f, b in pairs:
            ratio = contrast(f, b)
            if ratio < MIN_CONTRAST:
                out.append("text %s on %s (rule %r) has contrast %.2f : 1, under %.1f : 1"
                           % (show(f), show(b), sel[:50], ratio, MIN_CONTRAST))
    return out


def a11y_problems(p):
    out = []
    out.extend(heading_problems(p))
    out.extend(skip_link_problems(p))
    out.extend(name_problems(p))
    out.extend(alt_problems(p))
    out.extend(contrast_problems(p))
    return out
