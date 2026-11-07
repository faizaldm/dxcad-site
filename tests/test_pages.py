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
</head>
<body>
{body}
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
              "about.html": '<a href="/">Home</a><img src="pic.png" alt="A picture">'}
    bodies.update(pages)
    (tmp_path / "pic.png").write_bytes(b"x" * 100)
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
    root = make_site(tmp_path, {"index.html": '<h2 id="here">h</h2><a href="#here">x</a>'})
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
    body = "".join('<img src="p%d.png" alt="p" loading="lazy">' % i for i in range(3))
    for i in range(3):
        (tmp_path / ("p%d.png" % i)).write_bytes(b"x" * (200 * 1024))
    root = make_site(tmp_path, {"index.html": body})
    assert pagecheck.check_site(root) == []
    (tmp_path / "p0.png").write_bytes(b"x" * (301 * 1024))
    assert any("p0.png" in r for r in reasons(root))


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
    assert pagecheck.check_site(str(tmp_path)) == []
    os.rename(tmp_path / "img" / "channel.png", tmp_path / "img" / "channel-old.png")
    found = reasons(str(tmp_path))
    assert any(r.startswith("index.html ") and "img/channel.png" in r for r in found)
