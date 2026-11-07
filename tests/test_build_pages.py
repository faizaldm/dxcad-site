"""scripts/build_pages.py: the pages made from data/ are what the script makes."""

import datetime
import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import pagecheck

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "build_pages.py"

spec = importlib.util.spec_from_file_location("build_pages", SCRIPT)
bp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bp)


def read(path):
    return Path(path).read_bytes().decode("utf-8").replace("\r\n", "\n")


def copy_site(dest):
    """A working copy of the site."""
    ignore = shutil.ignore_patterns(".git", ".venv", "logs", "__pycache__", ".pytest_cache")
    shutil.copytree(ROOT, dest, ignore=ignore)
    return str(dest)


def run_script(root, *args):
    return subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), *args],
                          capture_output=True, text=True)


def notes_releases():
    """(version, date) of every release, read from the notes by a plain scan."""
    text = read(ROOT / "data" / "core" / "RELEASE_NOTES.md")
    found = []
    for block in re.split(r"(?m)^## ", text)[1:]:
        version = block.split("\n", 1)[0].strip()
        m = re.search(r"(\d{1,2}) (%s) (\d{4})" % "|".join(bp.MONTHS), block)
        found.append((version, "%s %s %s" % (m.group(1), m.group(2), m.group(3))))
    return found


# ------------------------------------------------------------ the pages ---

def test_check_passes_on_the_committed_pages():
    result = subprocess.run([sys.executable, str(SCRIPT), "--check"],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_releases_page_is_what_the_script_makes():
    files = bp.build_all(str(ROOT))
    assert read(ROOT / "releases.html") == files["releases.html"]
    assert read(ROOT / "sitemap.xml") == files["sitemap.xml"]


def test_releases_page_has_a_section_and_date_for_every_release():
    page = read(ROOT / "releases.html")
    releases = notes_releases()
    assert len(releases) >= 6
    positions = []
    for version, date in releases:
        sid = "v" + version.replace(".", "-")
        m = re.search(r'<div class="release" id="%s">(.*?)</div>\n' % sid, page, re.S)
        assert m, "no section for release " + version
        assert "DX-CAD %s</h2>" % version in m.group(1)
        assert date in m.group(1), "release %s lacks its date %s" % (version, date)
        positions.append(page.index('id="%s"' % sid))
    assert positions == sorted(positions), "releases are not newest first"


def test_every_line_of_the_notes_is_on_the_page():
    """Each list item's first words, in the notes, appear on the page."""
    page = re.sub(r"<[^>]+>", "", read(ROOT / "releases.html"))
    page = page.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    notes = read(ROOT / "data" / "core" / "RELEASE_NOTES.md")
    items = re.findall(r"(?m)^- (.*)$", notes)
    assert len(items) > 40
    for item in items:
        words = re.sub(r"[`]", "", re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", item))
        assert words[:40] in page, "missing from releases.html: " + item


def test_releases_page_is_linked_and_in_the_sitemap():
    index = read(ROOT / "index.html")
    footer = index[index.index('<footer class="tb"'):]
    assert 'href="/releases.html"' in footer
    assert "https://dxcad.designmatix.co.uk/releases.html" in pagecheck.sitemap_locs(str(ROOT))
    assert "releases.html" in pagecheck.page_files(str(ROOT))


def test_made_page_is_plain_ascii_and_links_only_to_the_site():
    raw = (ROOT / "releases.html").read_bytes()
    raw.decode("ascii")
    page = raw.decode("ascii")
    assert not re.search(r'href="[^"]*\.md"', page), "a link to a file the site lacks"


def test_made_page_has_the_looks_of_the_others():
    page = read(ROOT / "releases.html")
    refunds = read(ROOT / "refunds.html")
    index = read(ROOT / "index.html")
    style = refunds[refunds.index("<style>"):refunds.index("</style>")]
    assert style in page
    header = refunds[refunds.index('<header class="bar">'):refunds.index("</header>")]
    assert header in page
    footer = index[index.index('<footer class="tb"'):index.index("</footer>")]
    assert footer in page


# --------------------------------------------- changing the data changes it ---

def test_changing_a_line_of_the_data_changes_the_page(tmp_path):
    root = copy_site(tmp_path / "site")
    assert run_script(root, "--check").returncode == 0
    notes = Path(root, "data", "core", "RELEASE_NOTES.md")
    text = read(notes)
    changed = text.replace("Find bar (Ctrl+F, F3,", "Find bar (Ctrl+F, F4,")
    assert changed != text
    notes.write_bytes(changed.encode("utf-8"))
    before = read(Path(root, "releases.html"))
    check = run_script(root, "--check")
    assert check.returncode == 1 and "releases.html" in check.stdout
    assert run_script(root).returncode == 0
    after = read(Path(root, "releases.html"))
    assert after != before
    assert "F4," in after and "F4," not in before
    assert run_script(root, "--check").returncode == 0


def test_changing_a_release_date_changes_page_and_sitemap(tmp_path):
    root = copy_site(tmp_path / "site")
    notes = Path(root, "data", "core", "RELEASE_NOTES.md")
    notes.write_bytes(read(notes).replace("3 November 2026", "4 November 2026").encode())
    assert run_script(root).returncode == 0
    page = read(Path(root, "releases.html"))
    assert "4 November 2026" in page and 'datetime="2026-11-04"' in page
    sitemap = read(Path(root, "sitemap.xml"))
    assert re.search(r"releases\.html</loc>\s*<lastmod>2026-11-04<", sitemap)


def test_a_new_release_adds_its_section(tmp_path):
    root = copy_site(tmp_path / "site")
    notes = Path(root, "data", "core", "RELEASE_NOTES.md")
    text = read(notes)
    new = ("## 0.1.6\n\nAn update to 0.1.5, 9 November 2026. A test release.\n\n"
           "### Install\n\n- A new line for the test.\n\n")
    notes.write_bytes(text.replace("## 0.1.5\n", new + "## 0.1.5\n", 1).encode())
    assert run_script(root).returncode == 0
    page = read(Path(root, "releases.html"))
    assert page.index('id="v0-1-6"') < page.index('id="v0-1-5"')
    assert "9 November 2026" in page and "A new line for the test." in page
    assert pagecheck.check_site(root) == []


def test_the_script_does_not_touch_data(tmp_path):
    root = copy_site(tmp_path / "site")

    def digest():
        h = hashlib.sha256()
        for folder, dirs, files in os.walk(os.path.join(root, "data")):
            dirs.sort()
            for name in sorted(files):
                h.update(name.encode())
                h.update(Path(folder, name).read_bytes())
        return h.hexdigest()

    before = digest()
    assert run_script(root, "--all").returncode == 0
    assert digest() == before


def test_a_made_page_that_is_edited_fails_check(tmp_path):
    root = copy_site(tmp_path / "site")
    page = Path(root, "releases.html")
    page.write_bytes(read(page).replace("What is new in each release",
                                        "What is new", 1).encode())
    assert run_script(root, "--check").returncode == 1


# --------------------------------------------------------------- the parts ---

NOTES = """# Release notes

Lead words.

## 0.2.0

An update to 0.1.9, 2 December 2026. It has `code` and [a link](FILE.md) & <b>.
A second line of the same paragraph.

### Modelling

- First item that goes on
  to a second line.
- Second item.

### Known limitations

- None.

## 0.1.9

The first public release, 16 October 2026.
"""


def test_parse_release_notes():
    releases = bp.parse_release_notes(NOTES)
    assert [r["version"] for r in releases] == ["0.2.0", "0.1.9"]
    assert releases[0]["date"] == datetime.date(2026, 12, 2)
    assert releases[1]["date"] == datetime.date(2026, 10, 16)
    kinds = [k for k, _ in releases[0]["blocks"]]
    assert kinds == ["p", "h3", "ul", "h3", "ul"]
    assert releases[0]["blocks"][2][1] == ["First item that goes on to a second line.",
                                           "Second item."]


def test_inline_escapes_and_drops_dead_links():
    out = bp.inline("It has `code` and [a link](FILE.md) & <b>.")
    assert out == "It has <code>code</code> and a link &amp; &lt;b&gt;."


def test_a_release_without_a_date_is_an_error():
    with pytest.raises(ValueError):
        bp.parse_release_notes("## 0.3.0\n\nNo date here.\n")


def test_pages_made_here_pass_the_site_checks(tmp_path):
    root = copy_site(tmp_path / "site")
    assert run_script(root).returncode == 0
    assert pagecheck.check_site(root) == []


# ---------------------------------------------------------------- gallery ---

EXAMPLES = ROOT / "data" / "core" / "examples"
GALLERY = ROOT / "data" / "core" / "gallery"
NAMES = sorted(p.stem for p in EXAMPLES.glob("*.py"))


def unescape(text):
    import html
    return html.unescape(text)


def test_there_are_examples():
    assert len(NAMES) >= 20


@pytest.mark.parametrize("name", NAMES)
def test_example_page_has_picture_text_and_whole_script(name):
    page = read(ROOT / "examples" / (name + ".html"))
    script = read(EXAMPLES / (name + ".py"))
    # the picture: copied byte for byte, and shown with alt text
    assert (ROOT / "img" / "gallery" / (name + ".png")).read_bytes() == \
        (GALLERY / (name + ".png")).read_bytes()
    assert 'src="/img/gallery/%s.png"' % name in page
    assert re.search(r'<img src="/img/gallery/%s\.png" alt="[^"]+"' % name, page)
    # the dark picture, where there is one
    dark = GALLERY / "dark" / (name + ".png")
    if dark.exists():
        assert (ROOT / "img" / "gallery" / "dark" / (name + ".png")).read_bytes() == \
            dark.read_bytes()
        assert 'src="/img/gallery/dark/%s.png"' % name in page
    else:
        assert "/img/gallery/dark/" not in page
    # the whole script, as text, escaped
    blocks = re.findall(r'<pre class="script"><code>(.*?)</code></pre>', page, re.S)
    assert unescape(blocks[-1]) == script.rstrip("\n")
    assert "<script" not in page.replace("<script type=\"application/ld+json\"", "")
    # how to open it in DX-CAD
    assert "dxcad examples %s" % name in page and "dxcad gui %s.py" % name in page


@pytest.mark.parametrize("name", NAMES)
def test_example_description_is_the_scripts_first_docstring_line(name):
    import ast
    doc = ast.get_docstring(ast.parse(read(EXAMPLES / (name + ".py"))))
    first = doc.strip().split("\n")[0].strip()
    assert first
    page = read(ROOT / "examples" / (name + ".html"))
    assert unescape(re.search(r'<p class="lead">(.*?)</p>', page).group(1)) == first
    gallery = read(ROOT / "gallery.html")
    assert "<span>%s</span>" % bp.esc(first) in gallery


def test_gallery_lists_every_example_with_its_picture():
    page = read(ROOT / "gallery.html")
    for name in NAMES:
        assert 'href="/examples/%s.html"' % name in page
        assert 'src="/img/gallery/%s.png"' % name in page
    assert len(re.findall(r'<li><a href="/examples/', page)) == len(NAMES)


def test_gallery_is_linked_from_the_index_and_in_the_sitemap():
    assert 'href="/gallery.html"' in read(ROOT / "index.html")
    locs = pagecheck.sitemap_locs(str(ROOT))
    assert "https://dxcad.designmatix.co.uk/gallery.html" in locs
    for name in NAMES:
        assert "https://dxcad.designmatix.co.uk/examples/%s.html" % name in locs


def test_a_new_example_gets_a_page_and_a_picture(tmp_path):
    root = copy_site(tmp_path / "site")
    base = Path(root, "data", "core")
    (base / "examples" / "zed.py").write_bytes(
        b'"""A zed shape, for the test.\n\nMore words.\n"""\nLENGTH = 5 < 6\n')
    shutil.copyfile(base / "gallery" / "tray.png", base / "gallery" / "zed.png")
    assert run_script(root).returncode == 0
    page = read(Path(root, "examples", "zed.html"))
    assert "A zed shape, for the test." in page and "LENGTH = 5 &lt; 6" in page
    assert Path(root, "img", "gallery", "zed.png").exists()
    assert "examples/zed.html" in read(Path(root, "gallery.html"))
    assert pagecheck.check_site(root) == []


def test_an_example_without_a_picture_is_an_error(tmp_path):
    root = copy_site(tmp_path / "site")
    Path(root, "data", "core", "examples", "zed.py").write_bytes(b'"""A zed."""\n')
    result = run_script(root)
    assert result.returncode != 0 and "zed" in result.stderr


def test_a_changed_picture_changes_the_copy(tmp_path):
    root = copy_site(tmp_path / "site")
    shutil.copyfile(Path(root, "data", "core", "gallery", "bracket.png"),
                    Path(root, "data", "core", "gallery", "tray.png"))
    check = run_script(root, "--check")
    assert check.returncode == 1 and "img/gallery/tray.png" in check.stdout


# ---------------------------------------------------------------- add-ons ---

GUI = read(ROOT / "data" / "core" / "gui.md")
ADDONS = [("fabrication.html", "Fabrication"), ("drafting-pro.html", "Drafting Pro")]


def gui_commands(name):
    """Every command gui.md names for an add-on, by a plain scan of its table rows."""
    return re.findall(r"(?m)^\| `([^`]+ - %s)` \|" % re.escape(name), GUI)


def page_text(page):
    return unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page)))


@pytest.mark.parametrize("file,name", ADDONS)
def test_addon_page_names_only_commands_that_gui_md_names(file, name):
    page = read(ROOT / file)
    named = [unescape(c) for c in re.findall(r"<code>([^<]*)</code>", page)]
    assert named, "the page names no command"
    known = gui_commands(name)
    assert len(known) >= 9
    for cmd in named:
        assert cmd in known, "%s names %r, which gui.md does not" % (file, cmd)
        assert "`%s`" % cmd in GUI
    # and it names every one of them
    assert sorted(named) == sorted(known)


@pytest.mark.parametrize("file,name", ADDONS)
def test_addon_page_trial_and_licence_words_are_guis(file, name):
    text = page_text(read(ROOT / file))
    section = GUI[GUI.index("### %s\n" % name):]
    m = re.search(r"What a listed command's panel says depends on .*?Buy link\.", section, re.S)
    assert m and ("download %s and install" % name) in m.group(0)
    sentences = (m.group(0),
                 re.search(r"The paid add-ons, Fabrication and Drafting Pro, [^.]*\.",
                           GUI).group(0))
    for sentence in sentences:
        assert re.sub(r"\s+", " ", sentence) in text
    assert "%s is a paid add-on." % name in text
    assert "Free during your trial" in text and "Install from File" in text


@pytest.mark.parametrize("file,name", ADDONS)
def test_addon_page_has_no_price(file, name):
    page = read(ROOT / file)
    body = page[page.index("<article"):page.index("</article>")]
    assert "&pound;" not in body and "£" not in body and "249" not in body


def test_addon_pages_use_pictures_already_in_img_with_alt_text():
    for file, _ in ADDONS:
        page = read(ROOT / file)
        imgs = re.findall(r'<img src="(/img/[^"]+)" alt="([^"]+)"', page)
        assert imgs
        for src, alt in imgs:
            assert (ROOT / src.lstrip("/")).is_file()
            assert "Fabrication" in alt or "Drafting Pro" in alt


def test_addon_pages_are_linked_from_the_index_and_each_other_and_in_the_sitemap():
    index = read(ROOT / "index.html")
    locs = pagecheck.sitemap_locs(str(ROOT))
    for file, _ in ADDONS:
        assert 'href="/%s"' % file in index
        assert "https://dxcad.designmatix.co.uk/" + file in locs
    assert 'href="/drafting-pro.html"' in read(ROOT / "fabrication.html")
    assert 'href="/fabrication.html"' in read(ROOT / "drafting-pro.html")


def test_changing_a_command_in_gui_md_changes_the_page(tmp_path):
    root = copy_site(tmp_path / "site")
    gui = Path(root, "data", "core", "gui.md")
    text = read(gui)
    changed = text.replace("Place dimensions on a drawing's views by picking edges and points.",
                           "Place dimensions on a drawing's views, new words.")
    assert changed != text
    gui.write_bytes(changed.encode())
    assert run_script(root, "--check").returncode == 1
    assert run_script(root).returncode == 0
    assert "new words" in read(Path(root, "drafting-pro.html"))
    assert pagecheck.check_site(root) == []


def test_missing_addon_section_in_gui_md_is_an_error(tmp_path):
    root = copy_site(tmp_path / "site")
    gui = Path(root, "data", "core", "gui.md")
    gui.write_bytes(read(gui).replace("### Fabrication\n", "### Fabricating\n").encode())
    result = run_script(root)
    assert result.returncode != 0 and "Fabrication" in result.stderr


# --------------------------------------------------------------- tutorial ---

def all_data_text():
    """Every text file in data/, as one string."""
    parts = []
    for folder, dirs, files in os.walk(ROOT / "data"):
        for name in sorted(files):
            if name.endswith((".md", ".py", ".json", ".jsonl", ".txt")):
                parts.append(read(Path(folder, name)))
    return "\n".join(parts)


DATA = all_data_text()


def commands_on(page):
    """Every shell command on a page: lines of the code blocks, and inline code."""
    found = []
    for block in re.findall(r'<pre class="script"><code>(.*?)</code></pre>', page, re.S):
        found += [ln.strip() for ln in unescape(block).split("\n") if ln.strip()]
    for inline_code in re.findall(r"<code>([^<\n]*)</code>", page):
        found.append(unescape(inline_code))
    return [c for c in found if c.startswith(("dxcad ", "pip ", "python "))]


def test_tutorial_commands_all_appear_in_data():
    page = read(ROOT / "tutorial.html")
    commands = commands_on(page)
    assert len(commands) >= 6
    for cmd in commands:
        assert cmd in DATA, "tutorial.html gives %r, which data/ does not" % cmd
    for needed in ("pip install dxcad", "dxcad examples bracket", "dxcad gui bracket.py",
                   "dxcad run bracket.py --output bracket.dxcprt",
                   "dxcad describe bracket.dxcprt", "dxcad doctor", "dxcad export"):
        assert needed in commands


def test_tutorial_numbers_are_the_data_s():
    page = read(ROOT / "tutorial.html")
    text = unescape(re.sub(r"<[^>]+>", "", page))
    script = read(EXAMPLES / "bracket.py")
    for line in re.findall(r"(?m)^[A-Z_]+ = [\d.]+$", script):
        assert line in text, line
    story = re.sub(r"\s+", " ", read(EXAMPLES / "bracket.md"))
    for number in ("33128.761", "41528.761", "10, 30, 50 and 70",
                   "10, 36.667, 63.333 and 90", "80 x 30 x 46", "100 x 30 x 46"):
        assert number in story and number in text
    assert "F5" in text and "Export Parts..." in text and "STEP" in text
    for item in ("Windows: an installer, or a portable zip that needs no Python; "
                 "both carry dxcad.exe, the command line.",
                 "macOS (Apple silicon) and Linux (x64) builds."):
        assert item in text
        assert item in re.sub(r"\s+", " ", DATA.replace("`", ""))


def test_tutorial_is_linked_and_in_the_sitemap():
    assert 'href="/tutorial.html"' in read(ROOT / "index.html")
    assert "https://dxcad.designmatix.co.uk/tutorial.html" in pagecheck.sitemap_locs(str(ROOT))


def test_changing_a_number_in_the_bracket_changes_the_tutorial(tmp_path):
    root = copy_site(tmp_path / "site")
    py = Path(root, "data", "core", "examples", "bracket.py")
    py.write_bytes(read(py).replace("HOLE_DIAMETER = 5.0", "HOLE_DIAMETER = 6.0").encode())
    assert run_script(root, "--check").returncode == 1
    assert run_script(root).returncode == 0
    assert "HOLE_DIAMETER = 6.0" in read(Path(root, "tutorial.html"))
    assert pagecheck.check_site(root) == []


def test_changing_the_bracket_story_changes_the_tutorial(tmp_path):
    root = copy_site(tmp_path / "site")
    md = Path(root, "data", "core", "examples", "bracket.md")
    md.write_bytes(read(md).replace("33128.761", "33128.762").encode())
    assert run_script(root).returncode == 0
    assert "33128.762" in read(Path(root, "tutorial.html"))


def test_the_tutorial_is_an_error_if_its_data_goes_missing(tmp_path):
    root = copy_site(tmp_path / "site")
    md = Path(root, "data", "core", "examples", "bracket.md")
    md.write_bytes(read(md).replace("The answer is the bracket again", "Nothing").encode())
    result = run_script(root)
    assert result.returncode != 0 and "first volume" in result.stderr


# ------------------------------------------------------------------- feed ---

ATOM = "{http://www.w3.org/2005/Atom}"
MONTH_NUMBER = {m: i + 1 for i, m in enumerate(bp.MONTHS)}


def parse_feed(path):
    import xml.etree.ElementTree as ET
    return ET.parse(path).getroot()


def test_feed_is_atom_with_its_required_elements():
    feed = parse_feed(ROOT / "releases.xml")
    assert feed.tag == ATOM + "feed"
    for tag in ("id", "title", "updated"):
        assert feed.find(ATOM + tag) is not None and feed.find(ATOM + tag).text.strip()
    assert feed.find(ATOM + "author/" + ATOM + "name").text.strip()
    rels = {l.get("rel"): l.get("href") for l in feed.findall(ATOM + "link")}
    assert rels["self"] == "https://dxcad.designmatix.co.uk/releases.xml"
    assert rels["alternate"] == "https://dxcad.designmatix.co.uk/releases.html"
    for entry in feed.findall(ATOM + "entry"):
        for tag in ("id", "title", "updated"):
            assert entry.find(ATOM + tag).text.strip(), tag
        assert entry.find(ATOM + "link").get("href").startswith(
            "https://dxcad.designmatix.co.uk/releases.html#v")
        assert entry.find(ATOM + "summary").text.strip()
        assert entry.find(ATOM + "content").get("type") == "html"
    ids = [e.find(ATOM + "id").text for e in feed.findall(ATOM + "entry")]
    assert len(ids) == len(set(ids))


def test_feed_has_one_entry_per_release_newest_first_with_its_date():
    feed = parse_feed(ROOT / "releases.xml")
    entries = feed.findall(ATOM + "entry")
    releases = notes_releases()
    assert [e.find(ATOM + "title").text for e in entries] == \
        ["DX-CAD " + v for v, _ in releases]
    for entry, (version, date) in zip(entries, releases):
        day, month, year = date.split()
        want = "%04d-%02d-%02dT00:00:00Z" % (int(year), MONTH_NUMBER[month], int(day))
        assert entry.find(ATOM + "updated").text == want
        assert entry.find(ATOM + "id").text.endswith("#v" + version.replace(".", "-"))
    updated = [e.find(ATOM + "updated").text for e in entries]
    assert updated == sorted(updated, reverse=True)
    assert feed.find(ATOM + "updated").text == updated[0]


def test_feed_content_holds_the_release_lines():
    import html
    feed = parse_feed(ROOT / "releases.xml")
    first = feed.findall(ATOM + "entry")[0]
    content = html.unescape(first.find(ATOM + "content").text)
    assert "<li>" in content and "<h3>Modelling</h3>" in content
    assert "Go to Line (Ctrl+G)" in content


def test_releases_page_head_links_to_the_feed():
    page = read(ROOT / "releases.html")
    head = page[:page.index("</head>")]
    assert re.search(r'<link rel="alternate" type="application/atom\+xml"[^>]*href="/releases\.xml"',
                     head)
    assert (ROOT / "releases.xml").is_file()


def test_feed_is_ascii_and_made_by_the_script():
    raw = (ROOT / "releases.xml").read_bytes()
    raw.decode("ascii")
    assert read(ROOT / "releases.xml") == bp.build_all(str(ROOT))["releases.xml"]


def test_a_new_release_is_a_new_entry_at_the_top_of_the_feed(tmp_path):
    root = copy_site(tmp_path / "site")
    notes = Path(root, "data", "core", "RELEASE_NOTES.md")
    new = ("## 0.1.6\n\nAn update to 0.1.5, 9 November 2026. It has <angle> & `code`.\n\n"
           "### Install\n\n- A line for 0.1.6.\n\n")
    notes.write_bytes(read(notes).replace("## 0.1.5\n", new + "## 0.1.5\n", 1).encode())
    assert run_script(root, "--check").returncode == 1
    assert run_script(root).returncode == 0
    feed = parse_feed(Path(root, "releases.xml"))
    entries = feed.findall(ATOM + "entry")
    assert len(entries) == len(notes_releases()) + 1
    assert entries[0].find(ATOM + "title").text == "DX-CAD 0.1.6"
    assert entries[0].find(ATOM + "updated").text == "2026-11-09T00:00:00Z"
    assert "<angle> & code" in entries[0].find(ATOM + "summary").text
    assert feed.find(ATOM + "updated").text == "2026-11-09T00:00:00Z"
    assert run_script(root, "--check").returncode == 0
    assert pagecheck.check_site(root) == []


# ------------------------------------------------------------------- --all ---

def snapshot(root):
    """Every file under root (except data/, which the script never writes), by content."""
    found = {}
    for folder, dirs, files in os.walk(root):
        for name in files:
            path = Path(folder, name)
            found[path.relative_to(root).as_posix()] = path.read_bytes()
    return found


def test_all_with_a_new_release_adds_its_section_and_changes_nothing_else(tmp_path):
    root = copy_site(tmp_path / "site")
    before = snapshot(root)
    notes = Path(root, "data", "core", "RELEASE_NOTES.md")
    new = ("## 0.1.6\n\nAn update to 0.1.5, 9 November 2026. It mends one thing.\n\n"
           "### Install\n\n- A line that is new in 0.1.6.\n\n")
    notes.write_bytes(read(notes).replace("## 0.1.5\n", new + "## 0.1.5\n", 1).encode())
    assert run_script(root, "--all").returncode == 0
    after = snapshot(root)
    changed = sorted(k for k in after if before.get(k) != after[k])
    # the release notes (the test's own edit), the page, its Atom feed (4008), the sitemap
    assert changed == ["data/core/RELEASE_NOTES.md", "releases.html", "releases.xml",
                       "sitemap.xml"]
    assert set(after) == set(before)
    page = after["releases.html"].decode()
    assert 'id="v0-1-6"' in page and "A line that is new in 0.1.6." in page
    assert page.index('id="v0-1-6"') < page.index('id="v0-1-5"')
    # the sitemap changed in one date only: releases.html's
    old_lines = before["sitemap.xml"].decode().replace("\r\n", "\n").split("\n")
    new_lines = after["sitemap.xml"].decode().split("\n")
    diff = [(a, b) for a, b in zip(old_lines, new_lines) if a != b]
    assert len(old_lines) == len(new_lines)
    assert diff == [("    <lastmod>2026-11-03</lastmod>", "    <lastmod>2026-11-09</lastmod>")]
    # and a second run has nothing more to do
    assert run_script(root, "--check").returncode == 0


def test_all_is_the_same_as_no_flag(tmp_path):
    a = copy_site(tmp_path / "a")
    b = copy_site(tmp_path / "b")
    for root in (a, b):
        notes = Path(root, "data", "core", "RELEASE_NOTES.md")
        notes.write_bytes(read(notes).replace("3 November 2026", "5 November 2026").encode())
    assert run_script(a, "--all").returncode == 0
    assert run_script(b).returncode == 0
    assert snapshot(a) == snapshot(b)


def test_readme_names_the_three_steps():
    text = read(ROOT / "README.md")
    text.encode("ascii")
    assert "Refresh `data/`" in text
    assert "python scripts/build_pages.py --all" in text
    assert "python -m pytest" in text
    assert "merge" in text.lower() and "`main`" in text
    assert re.search(r"(?m)^1\. \*\*Refresh", text)
    assert re.search(r"(?m)^2\. \*\*Make the pages and run the tests", text)
    assert re.search(r"(?m)^3\. \*\*Publish", text)
    for name in ("RELEASE_NOTES.md", "gui.md", "latest.json", "limitations.md"):
        assert name in text


# ------------------------------------------------------------------- docs ---

CORE = ROOT / "data" / "core"
DOC_SOURCES = sorted(p.relative_to(CORE).as_posix() for p in CORE.rglob("*.md")
                     if p.name != "RELEASE_NOTES.md")


def doc_page_path(src):
    """docs/NAME.html for a source, written out here, not taken from the script."""
    stem = src[:-3]
    if stem.endswith("/README"):
        stem = stem[:-7]
    return "docs/%s.html" % stem.replace("/", "-")


def source_headings_and_code(text):
    """(heading texts, code block texts) of a markdown source, by a plain scan."""
    import html as htmllib
    headings, blocks, cur = [], [], None
    for line in text.replace("\r\n", "\n").split("\n"):
        if line.startswith("```"):
            if cur is None:
                cur = []
            else:
                blocks.append("\n".join(cur))
                cur = None
        elif cur is not None:
            cur.append(line)
        else:
            m = re.match(r"^#{1,6}\s+(.*?)\s*$", line)
            if m:
                headings.append(" ".join(htmllib.unescape(m.group(1).replace("`", "")).split()))
    return headings, blocks


def page_headings_and_code(page):
    import html as htmllib
    p = pagecheck.Page()
    p.feed(page)
    p.close()
    code = [htmllib.unescape(c) for c in re.findall(r"<pre[^>]*><code>(.*?)</code></pre>",
                                                   page, re.S)]
    return [t for _, t in p.headings], code


def test_there_are_public_docs():
    assert {"index.md", "gui.md", "limitations.md"} <= set(DOC_SOURCES)
    assert "RELEASE_NOTES.md" not in DOC_SOURCES


@pytest.mark.parametrize("src", DOC_SOURCES)
def test_each_doc_has_a_page_with_every_heading_and_code_block(src):
    page = read(ROOT / doc_page_path(src))
    want_headings, want_code = source_headings_and_code(read(CORE / src))
    got_headings, got_code = page_headings_and_code(page)
    assert want_headings
    for h in want_headings:
        assert h in got_headings, "%s: heading %r is not on the page" % (src, h)
    for block in want_code:
        assert block.rstrip("\n") in got_code, "%s: a code block is missing: %.60r" % (src, block)
    assert len(got_headings) == len(want_headings)
    assert len(got_code) == len(want_code)


@pytest.mark.parametrize("src", DOC_SOURCES)
def test_each_doc_page_has_one_h1_and_headings_in_order(src):
    p = pagecheck.parse(str(ROOT), doc_page_path(src))
    levels = [lv for lv, _ in p.headings]
    assert levels[0] == 1 and levels.count(1) == 1
    assert all(b - a <= 1 for a, b in zip(levels, levels[1:]))


def test_every_table_row_of_the_docs_is_on_the_pages():
    """The tables of gui.md, limitations.md and the examples keep every row."""
    for src in ("gui.md", "limitations.md", "examples/README.md", "examples/dimensions.md"):
        rows = [l for l in read(CORE / src).split("\n") if l.startswith("|")]
        rows = [r for r in rows if not re.match(r"^\|[\s:|-]+\|$", r)]
        page = read(ROOT / doc_page_path(src))
        assert page.count("<tr>") == len(rows), src


def test_docs_index_is_linked_from_the_main_page_and_lists_the_pages():
    assert doc_page_path("index.md") == "docs/index.html"
    assert 'href="/docs/"' in read(ROOT / "index.html")
    page = read(ROOT / "docs" / "index.html")
    for name in ("gui.html", "limitations.html", "examples.html", "examples-bracket.html"):
        assert 'href="/docs/%s"' % name in page
    locs = pagecheck.sitemap_locs(str(ROOT))
    assert "https://dxcad.designmatix.co.uk/docs/" in locs
    for src in DOC_SOURCES:
        rel = doc_page_path(src).replace("docs/index.html", "docs/")
        assert "https://dxcad.designmatix.co.uk/" + rel in locs


def test_docs_links_between_pages_work():
    page = read(ROOT / "docs" / "gui.html")
    assert 'href="#the-flange-dialog"' in page and 'id="the-flange-dialog"' in page
    bracket = read(ROOT / "docs" / "examples-bracket.html")
    assert 'href="/examples/bracket.html"' in bracket     # bracket.py is the example's page
    assert not [h for h in re.findall(r'href="([^"]*)"', bracket) if "agents" in h]
    readme = read(ROOT / "docs" / "examples.html")
    assert 'href="/docs/examples-bracket.html"' in readme
    assert 'href="/docs/examples-dimensions.html"' in readme


def test_docs_pages_are_ascii_and_load_nothing_from_elsewhere():
    for src in DOC_SOURCES:
        page = read(ROOT / doc_page_path(src))
        page.encode("ascii")
        assert "<script src" not in page and "<iframe" not in page
        assert not re.search(r'(src|srcset)="https?://', page)


def test_docs_pages_are_made_by_the_script_and_check_passes():
    assert run_script(ROOT, "--check").returncode == 0


def test_changing_a_heading_and_a_code_block_of_a_doc_changes_its_page(tmp_path):
    root = copy_site(tmp_path / "site")
    gui = Path(root, "data", "core", "gui.md")
    text = read(gui)
    assert "## Opening it\n" in text and "dxcad gui bracket.py\n```" in text
    gui.write_bytes(text.replace("## Opening it\n", "## Starting it\n", 1)
                    .replace("dxcad gui bracket.py\n```", "dxcad gui plate.py\n```", 1).encode())
    assert run_script(root, "--check").returncode == 1
    assert run_script(root).returncode == 0
    page = read(Path(root, "docs", "gui.html"))
    assert 'id="starting-it"' in page and "Opening it" not in page
    assert "dxcad gui plate.py" in page
    assert pagecheck.check_site(root) == []


def test_a_new_doc_gets_a_page_and_nothing_else_changes_but_the_sitemap(tmp_path):
    root = copy_site(tmp_path / "site")
    before = snapshot(root)
    Path(root, "data", "core", "faq.md").write_bytes(
        b"# Questions\n\nFirst, see [the menus](gui.md#the-menus).\n\n## One\n\n```\ndxcad doctor\n```\n")
    assert run_script(root, "--all").returncode == 0
    after = snapshot(root)
    changed = sorted(k for k in after if before.get(k) != after[k])
    assert changed == ["data/core/faq.md", "docs/faq.html", "sitemap.xml"]
    page = after["docs/faq.html"].decode()
    assert 'href="/docs/gui.html#the-menus"' in page and "dxcad doctor" in page
    assert pagecheck.check_site(root) == []


def test_a_doc_picture_in_data_is_copied_and_one_that_is_not_becomes_its_words(tmp_path):
    root = copy_site(tmp_path / "site")
    base = Path(root, "data", "core")
    (base / "pics").mkdir()
    shutil.copyfile(base / "gallery" / "tray.png", base / "pics" / "tray.png")
    (base / "pics.md").write_bytes(
        b"# Pictures\n\n![A tray, flat.](pics/tray.png)\n\n![Not here at all.](pics/none.svg)\n")
    assert run_script(root).returncode == 0
    page = read(Path(root, "docs", "pics.html"))
    assert 'src="/img/docs/pics/tray.png" alt="A tray, flat."' in page
    assert Path(root, "img", "docs", "pics", "tray.png").exists()
    assert "(Picture: Not here at all.)" in page and "none.svg" not in page
    assert pagecheck.check_site(root) == []


# The reader on its own.

def md(text, src="a.md", slugs=None, assets=None, examples=()):
    ctx = {"src": src, "slugs": slugs or {src: {"here"}, "b.md": {"there"}},
           "examples": set(examples), "assets": assets or {}, "used": set()}
    out = []
    state = {"last": 0, "ids": {}, "toc": [], "heading": "", "marks": []}
    bp.doc_blocks_html(bp.md_blocks(text.split("\n")), ctx, out, state)
    return "\n".join(out)


def test_reader_headings_paragraphs_emphasis_and_code():
    out = md("# Title\n\nSome *slanted* and **bold** words, `a < b`, and snake_case_name.\nTwo lines.")
    assert '<h1 id="title">Title</h1>' in out
    assert "<em>slanted</em>" in out and "<strong>bold</strong>" in out
    assert "<code>a &lt; b</code>" in out
    assert "snake_case_name" in out and "<em>case" not in out
    assert "Two lines." in out


def test_reader_heading_levels_never_skip_and_ids_are_github_style():
    out = md("# One\n\n### Deep\n\n## What's New?\n\n## What's New?\n\n# Another top")
    assert '<h2 id="deep">' in out
    assert 'id="whats-new"' in out and 'id="whats-new-1"' in out
    assert out.count("<h1 ") == 1


def test_reader_lists_nest_by_indent_and_keep_their_kind():
    out = md("- one\n- two\n  - inner a\n  - inner b\n- three\n\n1. first\n2. second")
    assert out.index("<ul>") < out.index("inner a") < out.index("three")
    assert out.count("<ul>") == 2 and out.count("</ul>") == 2
    assert "<ol>" in out and "<li>second</li>" in out


def test_reader_list_item_continues_on_the_next_line():
    assert "<li>the first goes on here</li>" in md("- the first\n  goes on here\n- second")


def test_reader_tables_have_header_cells_and_escaped_pipes():
    out = md("| A | B |\n| --- | --- |\n| `x` | a \\| b |\n| 1 | 2 |")
    assert out.count("<tr>") == 3 and '<th scope="col">A</th>' in out
    assert "<td>a | b</td>" in out


def test_reader_quote_and_fence_keep_their_text_and_escape_it():
    out = md('> Make a thing\n> with holes.\n\n```json\n{"a": "<b>"}\n```')
    assert "<blockquote>" in out and "Make a thing with holes." in out.replace("\n", " ")
    assert '<pre class="script"><code>{"a": "&lt;b&gt;"}</code></pre>' in out


def test_reader_html_comments_are_dropped_and_other_html_is_text():
    out = md("<!-- generated -->\n\nA <b>word</b> & more.")
    assert "generated" not in out and "&lt;b&gt;word&lt;/b&gt; &amp; more." in out


def test_reader_links_go_where_the_site_has_a_page_and_nowhere_else():
    slugs = {"a.md": {"here"}, "b.md": {"there"}}
    out = md("[in](#here) [gone](#nope) [other](b.md#there) [far](c.md) "
             "[out](https://example.org/x?a=1&b=2)", slugs=slugs)
    hrefs = re.findall(r'href="([^"]*)"', out)
    assert hrefs == ["#here", "/docs/b.html#there", "https://example.org/x?a=1&amp;b=2"]
    assert "gone" in out and "far" in out
    out = md("[s](bolt.py) [t](missing.py)", src="examples/README.md",
             slugs={"examples/README.md": set()}, examples=("bolt",))
    assert re.findall(r'href="([^"]*)"', out) == ["/examples/bolt.html"]


def test_doc_names():
    assert bp.doc_name("index.md") == "index" and bp.doc_href("index.md") == "/docs/"
    assert bp.doc_name("examples/README.md") == "examples"
    assert bp.doc_name("examples/bracket.md") == "examples-bracket"
    assert bp.doc_path("tutorials/first-part.md") == "docs/tutorials-first-part.html"


def test_doc_description_is_whole_sentences_and_short():
    text = "A first sentence of the page. A second one that is long " + "and long " * 30 + "end."
    d = bp.doc_description(bp.md_blocks([text]), "T")
    assert d == "A first sentence of the page." and len(d) <= 160
