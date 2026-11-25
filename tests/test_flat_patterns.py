"""The flat-pattern pages (owner, 24 November 2026): one per shape family, made
by scripts/build_pages.py from data/fabrication/, the public pack copied from
DX-CAD Fabrication's docs/site-pack."""

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import pagecheck

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "build_pages.py"
DATA = ROOT / "data" / "fabrication"
FLATS = ROOT / "flat-patterns"
SITE = "https://dxcad.designmatix.co.uk/"

spec = importlib.util.spec_from_file_location("build_pages", SCRIPT)
bp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bp)

PACK = json.loads((DATA / "pack.json").read_text(encoding="ascii"))
ENTRIES = PACK["entries"]


def slug(entry):
    return entry["sizes"][0]["web_page"].split("/")[0]


def read(path):
    return Path(path).read_bytes().decode("utf-8").replace("\r\n", "\n")


def article(page):
    return page[page.index("<article"):page.index("</article>")]


def run_script(root, *args):
    return subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), *args],
                          capture_output=True, text=True)


def test_the_pack_has_every_family_with_two_sizes():
    assert len(ENTRIES) >= 25
    for e in ENTRIES:
        assert len(e["sizes"]) == 2, e["name"]


@pytest.mark.parametrize("entry", ENTRIES, ids=slug)
def test_each_family_has_a_page_with_its_name_description_and_sizes(entry):
    page = read(FLATS / ("%s.html" % slug(entry)))
    body = article(page)
    assert "<h1>%s flat pattern</h1>" % bp.esc(entry["name"]) in body
    assert bp.esc(entry["description"]) in body
    for s in entry["sizes"]:
        assert bp.esc(s["label"]) in body
        for i in s["inputs"]:
            assert bp.esc(i["label"]) in body


@pytest.mark.parametrize("entry", ENTRIES, ids=slug)
def test_each_piece_is_shown_and_offered_as_the_pack_s_own_files(entry):
    page = read(FLATS / ("%s.html" % slug(entry)))
    for s in entry["sizes"]:
        for pc in s["pieces"]:
            for key in ("svg", "dxf", "dxf_r12"):
                assert 'href="/flat-patterns/%s"' % pc[key] in page, pc[key]
                assert (FLATS / pc[key]).read_bytes() == (DATA / pc[key]).read_bytes()
            assert '<img src="/flat-patterns/%s"' % pc["svg"] in page
            assert bp.mm_in(pc["flat_width_mm"], pc["flat_width_in"]) in page
            for a in pc["arcs"]:
                assert bp.mm_in(a["radius_mm"], a["radius_in"]) in page


@pytest.mark.parametrize("entry", ENTRIES, ids=slug)
def test_each_page_is_readable_without_javascript_and_has_no_price(entry):
    page = read(FLATS / ("%s.html" % slug(entry)))
    page.encode("ascii")
    assert "<script" not in page
    body = article(page)
    assert "&pound;" not in body and "£" not in body and "$" not in body
    assert "price" not in body.lower()
    assert 'href="/#download"' in body


def test_the_index_lists_every_family_and_is_linked_from_fabrication():
    index = read(FLATS / "index.html")
    for e in ENTRIES:
        assert 'href="/flat-patterns/%s.html"' % slug(e) in index
    assert 'href="/flat-patterns/"' in read(ROOT / "fabrication.html")


def test_family_pages_and_index_are_in_the_sitemap_and_search():
    locs = pagecheck.sitemap_locs(str(ROOT))
    search = json.loads(read(ROOT / "search.json"))
    urls = {e["url"] for e in search}
    assert SITE + "flat-patterns/" in locs and "/flat-patterns/" in urls
    for e in ENTRIES:
        assert SITE + "flat-patterns/%s.html" % slug(e) in locs
        assert "/flat-patterns/%s.html" % slug(e) in urls


@pytest.mark.parametrize("entry", ENTRIES, ids=slug)
def test_each_3d_view_is_the_pack_s_with_noindex_and_a_canonical_to_its_family(entry):
    for s in entry["sizes"]:
        rel = "flat-patterns/" + s["web_page"]
        assert pagecheck.check_view(str(ROOT), rel) == []
        text = read(ROOT / rel)
        assert '<link rel="canonical" href="%sflat-patterns/%s.html">' % (SITE, slug(entry)) in text
        # Apart from its head, the view is DX-CAD's file as the pack holds it.
        original = read(DATA / s["web_page"])
        assert text.split("</head>", 1)[1] == original.split("</head>", 1)[1]


def test_3d_views_stay_out_of_the_sitemap_the_search_and_the_pages():
    views = pagecheck.view_files(str(ROOT))
    assert len(views) == sum(len(e["sizes"]) for e in ENTRIES)
    locs = set(pagecheck.sitemap_locs(str(ROOT)))
    urls = {e["url"] for e in json.loads(read(ROOT / "search.json"))}
    pages = set(pagecheck.page_files(str(ROOT)))
    for rel in views:
        assert SITE + rel not in locs and "/" + rel not in urls and rel not in pages


def test_a_view_without_noindex_fails_its_check(tmp_path):
    rel = "flat-patterns/" + ENTRIES[0]["sizes"][0]["web_page"]
    (tmp_path / "flat-patterns" / slug(ENTRIES[0])).mkdir(parents=True)
    shutil.copyfile(ROOT / "flat-patterns" / ("%s.html" % slug(ENTRIES[0])),
                    tmp_path / "flat-patterns" / ("%s.html" % slug(ENTRIES[0])))
    text = read(ROOT / rel).replace('content="noindex, follow"', 'content="index, follow"')
    (tmp_path / rel).write_text(text, encoding="ascii")
    assert any("noindex" in p for p in pagecheck.check_view(str(tmp_path), rel))


def test_svg_sizes_are_the_same_in_the_script_and_the_check():
    for e in ENTRIES:
        for s in e["sizes"]:
            for pc in s["pieces"]:
                data = (DATA / pc["svg"]).read_bytes()
                assert bp.svg_box(data) == pagecheck.picture_dimensions(str(DATA / pc["svg"]))


def test_changing_a_description_in_the_pack_changes_its_page(tmp_path):
    ignore = shutil.ignore_patterns(".git", ".venv", "logs", "__pycache__", ".pytest_cache")
    root = tmp_path / "site"
    shutil.copytree(ROOT, root, ignore=ignore)
    assert run_script(root, "--check").returncode == 0
    path = root / "data" / "fabrication" / "pack.json"
    pack = json.loads(path.read_text(encoding="ascii"))
    pack["entries"][0]["description"] = "A plain test description of a shell."
    path.write_text(json.dumps(pack, indent=1), encoding="ascii")
    check = run_script(root, "--check")
    assert check.returncode == 1 and "flat-patterns/%s.html" % slug(ENTRIES[0]) in check.stdout
    assert run_script(root).returncode == 0
    assert "A plain test description of a shell." in read(
        root / "flat-patterns" / ("%s.html" % slug(ENTRIES[0])))


def test_without_the_pack_no_flat_pattern_pages_are_made(tmp_path):
    ignore = shutil.ignore_patterns(".git", ".venv", "logs", "__pycache__", ".pytest_cache",
                                    "fabrication", "flat-patterns")
    root = tmp_path / "site"
    shutil.copytree(ROOT, root, ignore=ignore)
    files = bp.build_all(str(root))
    assert not any(k.startswith("flat-patterns/") for k in files)
    assert not re.search(r'href="/flat-patterns/', files["fabrication.html"])
