"""The site's checks: pages parse, links and pictures resolve, the sitemap matches."""

import os
import shutil
from pathlib import Path

import pytest

import pagecheck

ROOT = Path(__file__).resolve().parent.parent
PAGES = pagecheck.page_files(str(ROOT))


def test_pages_are_found():
    assert "index.html" in PAGES
    assert "sdk/index.html" in PAGES
    assert not any(p.startswith(("data/", ".venv/", "tests/")) for p in PAGES)


@pytest.mark.parametrize("rel", PAGES)
def test_page_is_sound(rel):
    problems = pagecheck.check_page(str(ROOT), rel)
    assert not problems, "%s: %s" % (rel, "; ".join(problems))


def test_sitemap_and_robots():
    problems = pagecheck.check_site(str(ROOT))
    assert not problems, "; ".join("%s %s" % p for p in problems)


# Checks that must fail: each works on a small site made in a temporary folder.

PAGE = """<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<title>{title}</title>
<meta name="description" content="A page.">
<link rel="canonical" href="https://dxcad.designmatix.co.uk/{path}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="A page.">
<meta property="og:url" content="https://dxcad.designmatix.co.uk/{path}">
<meta property="og:image" content="https://dxcad.designmatix.co.uk/img/og.png">
<meta name="twitter:card" content="summary_large_image">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<main id="main">
{body}
</main>
</body>
</html>
"""

SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
"""


def make_site(tmp_path, pages=None, sitemap=("", "about.html"), robots=True):
    """A site of two pages; pages maps a path to its body (or a whole page)."""
    pages = pages or {}
    bodies = {"index.html": '<a href="about.html">About</a>',
              "about.html": '<a href="/">Home</a><img src="pic.png" alt="A picture" width="10" height="10">'}
    bodies.update(pages)
    (tmp_path / "pic.png").write_bytes(b"x" * 100)
    (tmp_path / "img").mkdir(exist_ok=True)
    (tmp_path / "img" / "og.png").write_bytes(b"x" * 100)
    for rel, body in bodies.items():
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if body.lstrip().startswith("<!doctype"):
            target.write_text(body, encoding="utf-8")
        else:
            canon = "" if rel == "index.html" else rel
            target.write_text(PAGE.format(title="T", path=canon, body=body),
                              encoding="utf-8")
    urls = "\n".join("<url><loc>https://dxcad.designmatix.co.uk/%s</loc></url>" % p
                     for p in sitemap)
    (tmp_path / "sitemap.xml").write_text(SITEMAP.format(urls=urls), encoding="utf-8")
    if robots:
        (tmp_path / "robots.txt").write_text(
            "User-agent: *\nAllow: /\n\nSitemap: https://dxcad.designmatix.co.uk/sitemap.xml\n")
    return str(tmp_path)


def reasons(root):
    return ["%s %s" % pr for pr in pagecheck.check_site(root)]


def test_a_good_small_site_passes(tmp_path):
    assert pagecheck.check_site(make_site(tmp_path)) == []


def test_broken_link_fails_naming_page_and_link(tmp_path):
    root = make_site(tmp_path, {"about.html": '<a href="gone.html">Gone</a>'})
    found = reasons(root)
    assert any(r.startswith("about.html ") and "gone.html" in r for r in found), found


def test_broken_picture_fails(tmp_path):
    root = make_site(tmp_path, {"index.html": '<img src="img/none.png" alt="x">'})
    found = reasons(root)
    assert any(r.startswith("index.html ") and "img/none.png" in r for r in found), found


def test_missing_alt_fails(tmp_path):
    root = make_site(tmp_path, {"about.html": '<img src="pic.png">'})
    found = reasons(root)
    assert any(r.startswith("about.html ") and "alt text" in r for r in found), found


def test_empty_alt_fails(tmp_path):
    root = make_site(tmp_path, {"about.html": '<img src="pic.png" alt="">'})
    assert any("alt text" in r for r in reasons(root))


def test_page_left_out_of_sitemap_fails(tmp_path):
    root = make_site(tmp_path, sitemap=("",))
    found = reasons(root)
    assert any(r.startswith("about.html ") and "missing from sitemap.xml" in r
               for r in found), found


def test_sitemap_entry_without_page_fails(tmp_path):
    root = make_site(tmp_path, sitemap=("", "about.html", "ghost.html"))
    assert any("ghost.html" in r and r.startswith("sitemap.xml") for r in reasons(root))


def test_robots_must_name_sitemap(tmp_path):
    root = make_site(tmp_path)
    (tmp_path / "robots.txt").write_text("User-agent: *\nAllow: /\n")
    assert any(r.startswith("robots.txt ") for r in reasons(root))


@pytest.mark.parametrize("old,new,words", [
    ("<title>T</title>", "", "<title>"),
    ("<title>T</title>", "<title>A</title><title>B</title>", "<title>"),
    ('<meta name="description" content="A page.">', "", "meta description"),
    ('<link rel="canonical" href="https://dxcad.designmatix.co.uk/about.html">', "",
     "canonical"),
    ('<link rel="canonical" href="https://dxcad.designmatix.co.uk/about.html">',
     '<link rel="canonical" href="https://dxcad.designmatix.co.uk/other.html">',
     "canonical link is"),
    ('lang="en-GB"', 'lang="en"', "lang"),
    ('<a href="/">Home</a>', '<div><a href="/">Home</a>', "not closed"),
])
def test_head_faults_fail(tmp_path, old, new, words):
    root = make_site(tmp_path)
    page = tmp_path / "about.html"
    text = page.read_text(encoding="utf-8")
    assert old in text
    page.write_text(text.replace(old, new), encoding="utf-8")
    found = [r for r in reasons(root) if r.startswith("about.html ")]
    assert any(words in r for r in found), found


def test_missing_anchor_fails(tmp_path):
    root = make_site(tmp_path, {"index.html": '<a href="about.html#nowhere">x</a>'})
    assert any("missing anchor" in r for r in reasons(root))


def test_anchor_that_exists_passes(tmp_path):
    root = make_site(tmp_path, {"index.html": '<h1 id="here">h</h1><a href="#here">x</a>'})
    assert pagecheck.check_site(root) == []


def test_links_out_of_the_site_are_left_alone(tmp_path):
    body = '<a href="https://example.org/x">x</a><a href="mailto:a@b.c">m</a>'
    assert pagecheck.check_site(make_site(tmp_path, {"index.html": body})) == []


def test_page_over_300_kb_with_its_pictures_fails(tmp_path):
    root = make_site(tmp_path)
    (tmp_path / "pic.png").write_bytes(b"x" * (301 * 1024))
    found = reasons(root)
    assert any(r.startswith("about.html ") and "KB with its pictures" in r
               for r in found), found


def test_lazy_pictures_count_one_by_one(tmp_path):
    body = "".join('<img src="p%d.png" alt="p" width="10" height="10"%s>' % (i, ' loading="lazy"' if i else "")
                   for i in range(3))
    for i in range(3):
        (tmp_path / ("p%d.png" % i)).write_bytes(b"x" * (200 * 1024))
    root = make_site(tmp_path, {"index.html": body})
    assert pagecheck.check_site(root) == []
    (tmp_path / "p1.png").write_bytes(b"x" * (301 * 1024))
    assert any("p1.png" in r for r in reasons(root))


def test_pages_in_folders_use_folder_canonicals(tmp_path):
    root = make_site(tmp_path, {"sdk/index.html": "<p>sdk</p>"},
                     sitemap=("", "about.html"))
    found = reasons(root)
    assert any(r.startswith("sdk/index.html ") and "canonical link is" in r
               for r in found), found


def test_copy_of_real_site_with_a_link_broken_fails(tmp_path):
    """The real pages, copied: renaming one picture breaks the pages that use it."""
    for item in ROOT.iterdir():
        if item.is_file():
            shutil.copyfile(item, tmp_path / item.name)
    for name in PAGES:
        dest = tmp_path / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, dest)
    shutil.copytree(ROOT / "img", tmp_path / "img")
    if (ROOT / "flat-patterns").is_dir():
        shutil.copytree(ROOT / "flat-patterns", tmp_path / "flat-patterns", dirs_exist_ok=True)
    assert pagecheck.check_site(str(tmp_path)) == []
    os.rename(tmp_path / "img" / "channel.png", tmp_path / "img" / "channel-old.png")
    found = reasons(str(tmp_path))
    assert any(r.startswith("index.html ") and "img/channel.png" in r for r in found)


# Open Graph and Twitter card tags.

OG_TAGS = {
    "og:title": '<meta property="og:title" content="T">',
    "og:description": '<meta property="og:description" content="A page.">',
    "og:url": '<meta property="og:url" content="https://dxcad.designmatix.co.uk/about.html">',
    "og:image": '<meta property="og:image" content="https://dxcad.designmatix.co.uk/img/og.png">',
    "twitter:card": '<meta name="twitter:card" content="summary_large_image">',
}


@pytest.mark.parametrize("tag", sorted(OG_TAGS))
def test_page_without_a_social_tag_fails(tmp_path, tag):
    root = make_site(tmp_path)
    page = tmp_path / "about.html"
    text = page.read_text(encoding="utf-8")
    assert OG_TAGS[tag] in text
    page.write_text(text.replace(OG_TAGS[tag], ""), encoding="utf-8")
    found = [r for r in reasons(root) if r.startswith("about.html ")]
    assert any("no %s tag" % tag in r for r in found), found


def test_og_url_must_be_the_canonical_address(tmp_path):
    root = make_site(tmp_path)
    page = tmp_path / "about.html"
    text = page.read_text(encoding="utf-8")
    page.write_text(text.replace(OG_TAGS["og:url"],
                    '<meta property="og:url" content="https://dxcad.designmatix.co.uk/x.html">'),
                    encoding="utf-8")
    assert any("og:url" in r and r.startswith("about.html ") for r in reasons(root))


def test_og_image_must_be_a_picture_in_img(tmp_path):
    root = make_site(tmp_path)
    page = tmp_path / "about.html"
    text = page.read_text(encoding="utf-8")
    good = OG_TAGS["og:image"]
    page.write_text(text.replace(good, good.replace("img/og.png", "img/gone.png")),
                    encoding="utf-8")
    assert any("og:image" in r and "does not resolve" in r for r in reasons(root))
    page.write_text(text.replace(good, good.replace("img/og.png", "pic.png")),
                    encoding="utf-8")
    assert any("og:image" in r and "img/" in r for r in reasons(root))


def test_empty_social_tag_fails(tmp_path):
    root = make_site(tmp_path)
    page = tmp_path / "about.html"
    text = page.read_text(encoding="utf-8")
    page.write_text(text.replace(OG_TAGS["og:title"], '<meta property="og:title" content="">'),
                    encoding="utf-8")
    assert any("og:title tag is empty" in r for r in reasons(root))


def test_every_real_page_has_the_social_tags():
    for rel in PAGES:
        p = pagecheck.parse(str(ROOT), rel)
        keys = {m.get("property") or m.get("name") for m in p.metas}
        for key in OG_TAGS:
            assert key in keys, "%s lacks %s" % (rel, key)


# Accessibility: headings in order, contrast, a skip link, named links and buttons.

def edit_about(tmp_path, old, new):
    """Make the small site, then change about.html: old text becomes new."""
    root = make_site(tmp_path)
    page = tmp_path / "about.html"
    text = page.read_text(encoding="utf-8")
    assert old in text
    page.write_text(text.replace(old, new), encoding="utf-8")
    return root


def about_reasons(root):
    return [r for r in reasons(root) if r.startswith("about.html ")]


def test_headings_in_order_pass(tmp_path):
    body = "<h1>A</h1><h2>B</h2><h3>C</h3><h2>D</h2><h4>E</h4>"
    root = make_site(tmp_path, {"about.html": body})
    found = about_reasons(root)
    assert len(found) == 1 and "<h4>" in found[0] and "skipping a level" in found[0], found
    body = "<h1>A</h1><h2>B</h2><h3>C</h3><h2>D</h2><h3>E</h3>"
    assert pagecheck.check_site(make_site(tmp_path, {"about.html": body})) == []


def test_skipped_heading_level_fails_naming_page_and_rule(tmp_path):
    root = make_site(tmp_path, {"about.html": "<h1>One</h1><h3>Three</h3>"})
    found = about_reasons(root)
    assert any("heading <h3>" in r and "follows <h1>" in r for r in found), found


def test_first_heading_must_be_h1(tmp_path):
    root = make_site(tmp_path, {"about.html": "<h2>Two</h2>"})
    assert any("first heading is <h2>" in r for r in about_reasons(root))


def test_page_without_a_skip_link_fails(tmp_path):
    root = edit_about(tmp_path, '<a class="skip" href="#main">Skip to content</a>', "")
    assert any('"Skip to content"' in r for r in about_reasons(root)), about_reasons(root)


def test_skip_link_must_not_come_after_other_links(tmp_path):
    root = edit_about(tmp_path, '<a class="skip" href="#main">Skip to content</a>',
                      '<a href="/">Home</a><a class="skip" href="#main">Skip to content</a>')
    assert any('"Skip to content"' in r for r in about_reasons(root))


def test_skip_link_must_say_so(tmp_path):
    root = edit_about(tmp_path, ">Skip to content<", ">Go<")
    assert any('does not say "Skip to content"' in r for r in about_reasons(root))


def test_skip_link_must_point_at_an_id(tmp_path):
    root = edit_about(tmp_path, 'href="#main"', 'href="#nowhere"')
    assert any("missing id" in r for r in about_reasons(root))


@pytest.mark.parametrize("body", [
    '<a href="about.html"></a>',
    '<a href="about.html"><img src="pic.png" alt=""></a>',
    '<a href="about.html"><span aria-hidden="true">Go</span></a>',
    "<button></button>",
    '<button><img src="pic.png" alt=""></button>',
])
def test_link_or_button_without_a_name_fails(tmp_path, body):
    root = make_site(tmp_path, {"about.html": body})
    assert any("no name a screen reader can say" in r for r in about_reasons(root)),         about_reasons(root)


@pytest.mark.parametrize("body", [
    '<a href="about.html">About</a>',
    '<a href="about.html" aria-label="About us"></a>',
    '<a href="about.html"><img src="pic.png" alt="About" width="10" height="10"></a>',
    '<a href="about.html"><span class="vh">About</span></a>',
    "<button>Go</button>",
    '<button aria-label="Close"></button>',
])
def test_named_link_or_button_passes(tmp_path, body):
    root = make_site(tmp_path, {"about.html": body})
    assert about_reasons(root) == []


@pytest.mark.parametrize("alt", ["pic.png", "IMG_0042.JPG", "photo-1.webp", "diagram.svg"])
def test_file_name_as_alt_fails(tmp_path, alt):
    root = make_site(tmp_path, {"about.html": '<img src="pic.png" alt="%s">' % alt})
    assert any("file name for alt text" in r for r in about_reasons(root)), about_reasons(root)


def test_alt_that_is_a_sentence_passes(tmp_path):
    body = '<img src="pic.png" alt="A bracket with four holes, in a CAD window" width="10" height="10">'
    assert about_reasons(make_site(tmp_path, {"about.html": body})) == []


STYLE = "<style>:root{--a:#14213D;--b:#FFFFFF;--c:#9AA3B5}%s</style>"


def styled(rules):
    return STYLE % rules + "<p>Words</p>"


def test_low_contrast_text_fails_naming_the_rule(tmp_path):
    root = make_site(tmp_path, {"about.html": styled("body{color:var(--a);background:var(--b)}"
                                                     ".note{color:var(--c)}")})
    found = about_reasons(root)
    assert any("contrast" in r and ".note" in r and "#9AA3B5" in r for r in found), found


def test_low_contrast_pair_in_one_rule_fails(tmp_path):
    root = make_site(tmp_path, {"about.html": styled(".btn{color:#fff;background:#7a8cff}")})
    assert any("contrast" in r and ".btn" in r for r in about_reasons(root))


def test_low_contrast_inline_style_fails(tmp_path):
    root = make_site(tmp_path, {"about.html": '<p style="color:#bbb;background:#fff">x</p>'})
    assert any("contrast" in r for r in about_reasons(root))


def test_hover_background_is_held_to_the_rule_colour(tmp_path):
    rules = ".btn{color:#fff;background:#1624B8}.btn:hover{background:#9AA3B5}"
    root = make_site(tmp_path, {"about.html": styled(rules)})
    assert any("contrast" in r and ".btn:hover" in r for r in about_reasons(root))


def test_good_contrast_passes_and_media_rules_are_read(tmp_path):
    rules = ("body{color:var(--a);background:var(--b)}.btn{color:#fff;background:#1E2FE0}"
             "@media (max-width:700px){.note{color:var(--c)}}")
    root = make_site(tmp_path, {"about.html": styled(rules)})
    assert any("contrast" in r and ".note" in r for r in about_reasons(root))
    good = rules.replace("--c)}", "--a)}")
    assert about_reasons(make_site(tmp_path, {"about.html": styled(good)})) == []


def test_colour_it_cannot_read_is_reported(tmp_path):
    root = make_site(tmp_path, {"about.html": styled(".x{color:hsl(10,20%,30%)}")})
    assert any("cannot read the colour" in r for r in about_reasons(root))


def test_contrast_arithmetic():
    import a11ycheck
    assert round(a11ycheck.contrast((0, 0, 0), (255, 255, 255)), 2) == 21.0
    assert round(a11ycheck.contrast((119, 119, 119), (255, 255, 255)), 2) == 4.48
    assert a11ycheck.contrast((255, 255, 255), (255, 255, 255)) == 1.0


def test_every_real_page_has_a_skip_link_and_one_h1():
    for rel in PAGES:
        p = pagecheck.parse(str(ROOT), rel)
        assert p.first_focusable["href"].startswith("#"), rel
        assert [h for h, _ in p.headings].count(1) == 1, rel


# 404.html is reachable but is not listed in the sitemap.

def test_a_404_page_may_be_left_out_of_the_sitemap(tmp_path):
    root = make_site(tmp_path, {"404.html": "<h1>Gone</h1>"})
    assert pagecheck.check_site(root) == []


def test_a_404_page_listed_in_the_sitemap_fails_naming_it(tmp_path):
    root = make_site(tmp_path, {"404.html": "<h1>Gone</h1>"},
                     sitemap=("", "about.html", "404.html"))
    found = reasons(root)
    assert any(r.startswith("sitemap.xml ") and "404.html" in r and "stay out" in r
               for r in found), found


def test_other_pages_must_still_be_in_the_sitemap_beside_a_404_page(tmp_path):
    root = make_site(tmp_path, {"404.html": "<h1>Gone</h1>", "extra.html": "<h1>E</h1>"})
    found = reasons(root)
    assert any(r.startswith("extra.html ") and "missing from sitemap.xml" in r for r in found)
    assert not any(r.startswith("404.html ") for r in found)


# ---------------------------------------------------------------------------
# Structured data, and the dark theme.

import json
import re

DARK_PAGE = ("body{color:var(--a);background:var(--b)}"
             "@media (prefers-color-scheme:dark){:root{--a:#E6EAF2;--b:#0E1526;--c:#AEB8CC}%s}")


def read_page(rel):
    return (ROOT / rel).read_bytes().decode("utf-8").replace("\r\n", "\n")


def json_ld(rel):
    """The parsed JSON-LD blocks of a page."""
    blocks = re.findall(r'<script type="application/ld\+json">\n(.*?)\n</script>', read_page(rel), re.S)
    return [json.loads(b) for b in blocks]


def software_nodes(rel):
    out = []
    for data in json_ld(rel):
        out += [n for n in data.get("@graph", [data]) if n.get("@type") == "SoftwareApplication"]
    return out


LATEST = json.loads(read_page("data/core/latest.json"))


@pytest.mark.parametrize("rel", ["index.html", "releases.html"])
def test_software_json_ld_parses_and_names_the_version_in_data(rel):
    nodes = software_nodes(rel)
    assert len(nodes) == 1, rel
    node = nodes[0]
    assert node["name"] == "DX-CAD"
    assert node["softwareVersion"] == LATEST["version"]
    assert node["downloadUrl"] == LATEST["url"]
    assert node["operatingSystem"].count("Windows") >= 1 and "macOS" in node["operatingSystem"]
    assert node["url"] == "https://dxcad.designmatix.co.uk/"
    assert node["applicationCategory"]


def test_the_release_notes_and_the_json_ld_name_the_same_version():
    notes = read_page("data/core/RELEASE_NOTES.md")
    first = re.search(r"(?m)^## (\S+)", notes).group(1)
    assert software_nodes("releases.html")[0]["softwareVersion"] == first


def test_the_home_pages_own_json_ld_is_otherwise_kept():
    graph = json_ld("index.html")[0]["@graph"]
    assert [n["@type"] for n in graph] == ["Organization", "WebSite", "SoftwareApplication"]
    app = graph[2]
    assert app["offers"] and app["publisher"] == {"@id": "https://dxcad.designmatix.co.uk/#org"}


@pytest.mark.parametrize("rel", PAGES)
def test_every_page_has_the_dark_theme_block_last_in_its_head(rel):
    text = read_page(rel)
    head = text[:text.index("</head>")]
    assert head.count('<style id="theme">') == 1, rel
    assert head.rindex("<style") == head.index('<style id="theme">'), rel
    assert "prefers-color-scheme:dark" in head[head.index('<style id="theme">'):]


@pytest.mark.parametrize("rel", PAGES)
def test_both_themes_reach_aa_contrast_on_every_page(rel):
    import a11ycheck
    p = pagecheck.Page()
    p.feed(read_page(rel))
    p.close()
    assert a11ycheck.has_dark_theme(p), rel
    assert a11ycheck._contrast_problems(p, False) == [], rel
    assert a11ycheck._contrast_problems(p, True) == [], rel


def test_the_dark_theme_is_held_to_contrast_naming_the_theme(tmp_path):
    bad = DARK_PAGE % ".note{color:var(--c)}:root{--c:#3B4766}"
    root = make_site(tmp_path, {"about.html": STYLE % bad + "<p>Words</p>"})
    found = about_reasons(root)
    assert any("contrast" in r and ".note" in r and "[dark theme]" in r for r in found), found


def test_a_good_dark_theme_passes_and_the_light_theme_is_not_read_as_dark(tmp_path):
    good = DARK_PAGE % ".note{color:var(--c)}"
    root = make_site(tmp_path, {"about.html": STYLE % ("body{color:var(--a);background:var(--b)}"
                                                         + good.split("}", 1)[1]) + "<p>Words</p>"})
    assert about_reasons(root) == []


def test_a_dark_rule_that_fails_in_light_does_not_fail_the_light_theme(tmp_path):
    # --c is #9AA3B5 in the light theme (poor on white) but the .note rule is dark-only
    bad_light = "body{color:var(--a);background:var(--b)}"
    dark = "@media (prefers-color-scheme:dark){:root{--a:#E6EAF2;--b:#0E1526;--c:#AEB8CC}.note{color:var(--c)}}"
    root = make_site(tmp_path, {"about.html": STYLE % (bad_light + dark) + "<p>Words</p>"})
    assert about_reasons(root) == []


def test_a_dark_rule_overrides_the_light_rule_of_the_same_selector(tmp_path):
    # in light the button is white on blue; in dark its colour and background are turned over
    css = (".btn{color:#fff;background:#1E2FE0}"
           "@media (prefers-color-scheme:dark){.btn{color:#0E1526;background:#9DAAFF}}")
    root = make_site(tmp_path, {"about.html": STYLE % css + "<p>Words</p>"})
    assert about_reasons(root) == []
    worse = css.replace("color:#0E1526", "color:#FFFFFF")
    (tmp_path / "w").mkdir()
    found = about_reasons(make_site(tmp_path / "w", {"about.html": STYLE % worse + "<p>Words</p>"}))
    assert any(".btn" in r and "[dark theme]" in r for r in found), found


def test_print_rules_are_not_read_as_screen_rules(tmp_path):
    css = "body{color:#14213D;background:#fff}@media print{.x{color:#ccc}}"
    root = make_site(tmp_path, {"about.html": STYLE % css + "<p>Words</p>"})
    assert about_reasons(root) == []


DOC_PAGES = [p for p in PAGES if p.startswith("docs/")]


def test_there_are_docs_pages():
    assert "docs/index.html" in DOC_PAGES and len(DOC_PAGES) >= 3


@pytest.mark.parametrize("rel", DOC_PAGES)
def test_a_docs_page_has_a_print_style_that_hides_the_chrome_and_shows_addresses(rel):
    text = read_page(rel)
    m = re.search(r"@media print\{(.*?)\n\}\n", text, re.S)
    assert m, rel
    css = m.group(1)
    assert ".bar" in css and ".tb" in css and ".skip" in css          # header, footer, skip link gone
    assert "attr(href)" in css                                        # links say where they go
    assert "#000" in css and "background:#fff" in css                 # black on white
    assert "break-inside:avoid" in css


# ---------------------------------------------------------------------------
# Pictures sized for the web: width and height on each, lazy below the top.

import struct
import zlib


def png_bytes(w, h):
    """A real, tiny PNG of the size given (every pixel white)."""
    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))
    raw = b"".join(b"\x00" + b"\xff\xff\xff" * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def sized_site(tmp_path, body, w=40, h=30):
    root = make_site(tmp_path, {"about.html": body})
    (tmp_path / "pic.png").write_bytes(png_bytes(w, h))      # after make_site, which writes its own
    return root


def test_img_without_width_and_height_fails_naming_the_page_and_picture(tmp_path):
    root = sized_site(tmp_path, '<img src="pic.png" alt="A picture">')
    found = about_reasons(root)
    assert any("pic.png" in r and "no width and height" in r for r in found), found


@pytest.mark.parametrize("tag", ['<img src="pic.png" alt="A" width="40">',
                                 '<img src="pic.png" alt="A" height="30">',
                                 '<img src="pic.png" alt="A" width="" height="30">',
                                 '<img src="pic.png" alt="A" width="40px" height="30">',
                                 '<img src="pic.png" alt="A" width="0" height="0">'])
def test_img_with_half_a_size_fails(tmp_path, tag):
    found = about_reasons(sized_site(tmp_path, tag))
    assert any("no width and height" in r for r in found), found


def test_img_that_gives_the_wrong_size_fails_saying_both(tmp_path):
    root = sized_site(tmp_path, '<img src="pic.png" alt="A" width="400" height="300">')
    found = about_reasons(root)
    assert any("400x300" in r and "40x30" in r for r in found), found


def test_img_with_the_files_size_passes(tmp_path):
    root = sized_site(tmp_path, '<img src="pic.png" alt="A" width="40" height="30">')
    assert about_reasons(root) == []


def test_the_second_picture_must_be_lazy_and_the_first_must_not(tmp_path):
    one = '<img src="pic.png" alt="A" width="40" height="30"%s>'
    two = '<img src="two.png" alt="B" width="40" height="30"%s>'
    (tmp_path / "two.png").write_bytes(png_bytes(40, 30))
    root = sized_site(tmp_path, one % "" + two % "")
    assert any("two.png" in r and 'not loading="lazy"' in r for r in about_reasons(root))
    root = sized_site(tmp_path, one % ' loading="lazy"' + two % ' loading="lazy"')
    assert any("first picture" in r and "pic.png" in r for r in about_reasons(root))
    root = sized_site(tmp_path, one % "" + two % ' loading="lazy"')
    assert about_reasons(root) == []


def test_a_picture_written_into_the_page_is_left_out_of_both_rules(tmp_path):
    logo = '<img src="data:image/png;base64,AAAA" alt="Logo">'
    root = sized_site(tmp_path, logo + '<img src="pic.png" alt="A" width="40" height="30">')
    assert about_reasons(root) == []


def test_picture_dimensions_reads_png_gif_and_jpeg(tmp_path):
    (tmp_path / "a.png").write_bytes(png_bytes(7, 5))
    (tmp_path / "a.gif").write_bytes(b"GIF89a" + struct.pack("<HH", 11, 9) + b"\x00" * 10)
    # a JPEG: SOI, an APP0 segment, then a baseline frame header 13 x 17
    jpg = (b"\xff\xd8" + b"\xff\xe0" + struct.pack(">H", 6) + b"JFIF"
           + b"\xff\xc0" + struct.pack(">H", 11) + b"\x08" + struct.pack(">HH", 17, 13) + b"\x01\x01\x11\x00")
    (tmp_path / "a.jpg").write_bytes(jpg)
    (tmp_path / "a.txt").write_bytes(b"not a picture")
    assert pagecheck.picture_dimensions(str(tmp_path / "a.png")) == (7, 5)
    assert pagecheck.picture_dimensions(str(tmp_path / "a.gif")) == (11, 9)
    assert pagecheck.picture_dimensions(str(tmp_path / "a.jpg")) == (13, 17)
    assert pagecheck.picture_dimensions(str(tmp_path / "a.txt")) is None


def real_images(rel):
    text = read_page(rel)
    return [dict(re.findall(r'(\w[\w-]*)="([^"]*)"', tag)) for tag in re.findall(r"<img\b[^>]*>", text)
            if 'src="data:' not in tag]


@pytest.mark.parametrize("rel", PAGES)
def test_every_picture_on_every_page_has_the_size_of_its_file_and_lazy_after_the_first(rel):
    imgs = real_images(rel)
    for i, img in enumerate(imgs):
        w, h = pagecheck.picture_dimensions(str(ROOT / img["src"].lstrip("/")))
        assert (img.get("width"), img.get("height")) == (str(w), str(h)), (rel, img["src"])
        assert (img.get("loading") == "lazy") == (i > 0), (rel, img["src"])


def test_the_site_has_pictures_for_these_rules_to_check():
    assert sum(len(real_images(rel)) for rel in PAGES) > 60
