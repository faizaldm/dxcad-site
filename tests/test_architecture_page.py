"""The Architecture add-on's page (item 4025): coming soon, and saying only what the
site's own pages already say of it (CLAUDE.md: nothing about the paid add-ons beyond
what data/ and the site's pages say)."""

import importlib.util
import re
from pathlib import Path

import pagecheck

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "build_pages.py"
spec = importlib.util.spec_from_file_location("build_pages", SCRIPT)
bp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bp)


def read(name):
    return (ROOT / name).read_bytes().decode("utf-8").replace("\r\n", "\n")


def article(page):
    return page[page.index("<article"):page.index("</article>")]


def test_the_page_says_coming_soon_and_offers_dx_cad_pro():
    body = article(read("architecture.html"))
    assert "<h1>The Architecture add-on</h1>" in body
    assert "Coming soon." in body
    assert 'href="/#pricing"' in body and 'href="/#download"' in body


def test_every_feature_it_names_is_on_the_home_page_already():
    home = " ".join(read("index.html").split())
    spec = bp.ARCHITECTURE_SOON
    assert bp.esc(spec["lead"]) in home
    for _title, items in spec["sections"]:
        for item in items:
            assert bp.esc(item) in home, item
    assert ("Levels, grids, element types and hosted elements in a model" in home
            and "read-only schedules saved as CSV" in home)


def test_the_page_names_no_price_and_needs_no_javascript():
    page = read("architecture.html")
    page.encode("ascii")
    body = article(page)
    assert "&pound;" not in body and "GBP" not in body and "<script" not in body


def test_the_home_page_card_links_to_it_and_it_is_in_the_sitemap():
    assert re.search(r'id="architecture">.*?href="/architecture\.html"', read("index.html"), re.S)
    assert "https://dxcad.designmatix.co.uk/architecture.html" in pagecheck.sitemap_locs(str(ROOT))
    assert 'href="/architecture.html"' in read("404.html")
