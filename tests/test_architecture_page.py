"""The Architecture add-on's page (items 4025 and 4027): made from data/architecture/,
the add-on's own product text and command list copied with the owner's approval on
25 November 2026, for its launch; without that folder, the coming-soon page made from
the home page's words."""

import importlib.util
import re
import shutil
from pathlib import Path

import pagecheck

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "build_pages.py"
spec = importlib.util.spec_from_file_location("build_pages", SCRIPT)
bp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bp)
DATA = ROOT / "data" / "architecture"


def read(name):
    return (ROOT / name).read_bytes().decode("utf-8").replace("\r\n", "\n")


def article(page):
    return page[page.index("<article"):page.index("</article>")]


def test_the_page_has_every_section_of_the_add_ons_own_text():
    body = article(read("architecture.html"))
    lead, sections = bp.arch_sections((DATA / "website.md").read_text(encoding="ascii"))
    assert bp.esc(lead) in body
    for head, text in sections:
        assert bp.esc(text) in body, head
    assert "Coming soon" not in body


def test_the_page_lists_every_command_and_starter():
    body = article(read("architecture.html"))
    commands = (DATA / "commands.md").read_text(encoding="ascii")
    for name, _what in re.findall(r"(?m)^- ([^:]+): (.+)$", commands.split("## Starters")[0]):
        assert "<strong>%s</strong>" % bp.esc(name) in body
    for name, _what in re.findall(r"(?m)^- examples/([^:]+): (.+)$", commands.split("## Starters")[1]):
        for one in name.replace("examples/", "").split(" and "):
            assert "<code>%s</code>" % bp.esc(one.strip()) in body


def test_the_price_is_the_one_the_release_notes_give_and_nothing_needs_javascript():
    page = read("architecture.html")
    page.encode("ascii")
    assert "GBP 169" in (ROOT / "data" / "core" / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    body = article(page)
    assert "GBP 169" in body and "<script" not in body
    assert 'href="/#download"' in body


def test_the_home_page_no_longer_says_coming_soon_and_links_to_it():
    home = read("index.html")
    assert "coming soon" not in home.lower()
    assert re.search(r'id="architecture">.*?href="/architecture\.html"', home, re.S)
    assert "https://dxcad.designmatix.co.uk/architecture.html" in pagecheck.sitemap_locs(str(ROOT))


def test_without_the_data_the_page_is_the_coming_soon_one(tmp_path):
    ignore = shutil.ignore_patterns(".git", ".venv", "logs", "__pycache__", ".pytest_cache", "architecture")
    root = tmp_path / "site"
    shutil.copytree(ROOT, root, ignore=ignore)
    files = bp.build_all(str(root))
    assert "Coming soon." in files["architecture.html"]


def test_the_owners_linkedin_posts_are_plain_links_with_no_embed():
    arch, ai = read("architecture.html"), read("ai-cad-software.html")
    assert 'href="https://lnkd.in/p/epYJexVZ"' in arch
    for post in ("epYJexVZ", "edcrid7u", "eQbnks_7"):
        assert 'href="https://lnkd.in/p/%s"' % post in ai
    for page in (arch, ai):
        assert "linkedin.com/embed" not in page and "<iframe" not in page


def test_the_launch_renders_are_shown_with_alt_text_and_their_sizes():
    body = article(read("architecture.html"))
    for pic, alt in bp.ARCH_PICTURES:
        data = (ROOT / "img" / pic).read_bytes()
        w, h = bp.picture_size(data)
        assert '<img src="/img/%s" alt="%s" width="%d" height="%d"' % (pic, bp.esc(alt), w, h) in body
        assert len(data) < 200 * 1024


def test_the_buy_buttons_are_the_owners_stripe_links():
    arch, home = read("architecture.html"), read("index.html")
    assert 'href="https://buy.stripe.com/fZu7sKbek6Oq9uS3iycV206"' in arch
    assert 'href="https://buy.stripe.com/dRm9AS3LS1u636ucT8cV205"' in arch
    assert 'href="https://buy.stripe.com/fZu7sKbek6Oq9uS3iycV206">Buy DX-CAD+Architecture' in home
