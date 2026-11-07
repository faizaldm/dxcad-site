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
    assert "&pound;" not in body and "\u00a3" not in body and "249" not in body


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
                       "search.json", "sitemap.xml"]
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
    assert changed == ["data/core/faq.md", "docs/faq.html", "search.json", "sitemap.xml"]
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


# ----------------------------------------------------------------- search ---

def search_list():
    import json
    return json.loads(read(ROOT / "search.json"))


def url_of(rel):
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[:-len("index.html")]
    return "/" + rel


def test_search_json_lists_every_page_in_the_sitemap_with_title_and_headings():
    entries = search_list()
    by_url = {e["url"]: e for e in entries}
    assert len(by_url) == len(entries)
    locs = pagecheck.sitemap_locs(str(ROOT))
    assert sorted("/" + loc[len("https://dxcad.designmatix.co.uk/"):] for loc in locs) \
        == sorted(by_url)
    for rel in pagecheck.page_files(str(ROOT)):
        if rel in pagecheck.NOT_LISTED:
            assert url_of(rel) not in by_url
            continue
        entry = by_url[url_of(rel)]
        page = pagecheck.parse(str(ROOT), rel)
        assert entry["title"] == " ".join(page.titles[0].split()), rel
        have = [h["t"] for h in entry["headings"]]
        for _, text in page.headings:
            assert text in have, "%s: heading %r is not in search.json" % (rel, text)
        assert entry["text"].strip(), rel


def test_search_json_holds_the_words_of_pages_and_links_headings_by_id():
    by_url = {e["url"]: e for e in search_list()}
    gui = by_url["/docs/gui.html"]
    assert "Opening it" in [h["t"] for h in gui["headings"]]
    assert {"t": "Opening it", "id": "opening-it"} in gui["headings"]
    assert "opens the viewer" in gui["text"]
    assert "Registered office" not in gui["text"]          # the footer is not searched
    assert "createElement" not in by_url["/search.html"]["text"]    # nor is a script
    assert "Skip to content" not in gui["text"]
    # a long example script is left out, its description and its commands are not
    source = read(EXAMPLES / "gearbox.py")
    longest = max(source.split("\n"), key=len).strip()
    assert len(source.split("\n")) > 40 and len(longest) > 30
    gearbox = by_url["/examples/gearbox.html"]
    assert longest not in gearbox["text"] and "How to open it in DX-CAD" in gearbox["text"]
    assert "dxcad examples gearbox" in gearbox["text"]       # a short command block is kept


def test_search_json_is_ascii_one_page_a_line_and_not_huge():
    text = read(ROOT / "search.json")
    text.encode("ascii")
    assert text.startswith("[\n") and text.endswith("]\n")
    assert len(text.split("\n")) == len(search_list()) + 3     # the brackets, and the end
    assert len(text) < 400 * 1024


def test_search_page_is_plain_javascript_from_here_and_nothing_else():
    page = read(ROOT / "search.html")
    page.encode("ascii")
    assert not re.search(r"<script[^>]*\ssrc=", page)               # one inline script only
    assert not re.search(r'(src|srcset|poster|action)="(https?:)?//', page)
    assert '<link rel="stylesheet"' not in page and "@import" not in page
    assert "<iframe" not in page and "<form" not in page
    script = re.search(r"<script>(.*?)</script>", page, re.S).group(1)
    for banned in ("innerHTML", "eval(", "document.write", "import(", "fetch(", "http://",
                   "https://", "localStorage", "navigator.sendBeacon"):
        assert banned not in script, banned
    assert script.count("{") == script.count("}") and script.count("(") == script.count(")")
    assert script.count("[") == script.count("]")
    assert '"search.json"' in script
    for name in re.findall(r'getElementById\("([^"]+)"\)', script):
        assert 'id="%s"' % name in page, name
    assert '<label for="q">' in page and 'id="q" type="search"' in page
    assert "<noscript>" in page and 'aria-live="polite"' in page


def test_search_page_is_in_the_sitemap_and_in_the_search_list():
    assert "https://dxcad.designmatix.co.uk/search.html" in pagecheck.sitemap_locs(str(ROOT))
    assert "/search.html" in {e["url"] for e in search_list()}


def test_every_page_links_to_search_from_its_header():
    for rel in pagecheck.page_files(str(ROOT)):
        text = read(ROOT / rel)
        header = text[text.index('<header class="bar">'):text.index("</header>")]
        assert 'href="/search.html"' in header, rel


def test_search_json_is_made_by_the_script(tmp_path):
    root = copy_site(tmp_path / "site")
    assert run_script(root, "--check").returncode == 0
    Path(root, "search.json").write_bytes(b"[]\n")
    result = run_script(root, "--check")
    assert result.returncode == 1 and "search.json" in result.stdout
    assert run_script(root).returncode == 0
    assert read(Path(root, "search.json")) == read(ROOT / "search.json")


def test_a_changed_word_in_a_doc_is_found_in_the_search_list(tmp_path):
    import json
    root = copy_site(tmp_path / "site")
    gui = Path(root, "data", "core", "gui.md")
    gui.write_bytes(read(gui).replace("opens the viewer", "opens the zebrafish viewer", 1).encode())
    assert run_script(root).returncode == 0
    by_url = {e["url"]: e for e in json.loads(read(Path(root, "search.json")))}
    assert "zebrafish" in by_url["/docs/gui.html"]["text"]
    assert pagecheck.check_site(root) == []


def test_a_new_doc_is_in_the_search_list_with_its_headings(tmp_path):
    import json
    root = copy_site(tmp_path / "site")
    Path(root, "data", "core", "faq.md").write_bytes(b"# Questions\n\nWords.\n\n## One thing\n\nMore.\n")
    assert run_script(root).returncode == 0
    by_url = {e["url"]: e for e in json.loads(read(Path(root, "search.json")))}
    entry = by_url["/docs/faq.html"]
    assert [h["t"] for h in entry["headings"]] == ["Questions", "One thing"]
    assert entry["headings"][1]["id"] == "one-thing"


def test_page_text_reader_skips_footer_script_and_whole_scripts():
    code = "\n".join("line %d" % i for i in range(50))
    page = ('<html><head><title>  A  title </title></head><body><header><a href="/">Home</a></header>'
            '<main><h1 id="top">Top <code>x</code></h1><p>One   sentence <b>here</b>.</p>'
            '<table><tr><td>Cell a</td><td>Cell b</td></tr></table>'
            '<pre>short one\nshort two</pre><pre>%s</pre><script>var secret = 1;</script>'
            '<footer><p>Company words</p></footer></main></body></html>' % code)
    entry = bp.search_entry("sub/page.html", page)
    assert entry["url"] == "/sub/page.html" and entry["title"] == "A title"
    assert entry["headings"] == [{"t": "Top x", "id": "top"}]
    lines = entry["text"].split("\n")
    assert lines == ["Top x", "One sentence here .".replace(" .", "."), "Cell a", "Cell b",
                     "short one", "short two"]
    assert bp.search_entry("index.html", page)["url"] == "/"
    assert bp.search_entry("docs/index.html", page)["url"] == "/docs/"


# ------------------------------------------------------- 404 and the footer ---

MAIN_LINKS = ["/", "/docs/", "/gallery.html", "/tutorial.html", "/releases.html",
              "/search.html", "/eula.html", "/refunds.html", "/privacy.html"]


def footer_of(text):
    found = re.findall(r'<footer class="tb".*?</footer>', text.replace("\r\n", "\n"), re.S)
    assert len(found) == 1
    return found[0]


def test_every_pages_footer_is_the_same_and_has_the_main_links():
    pages = pagecheck.page_files(str(ROOT))
    assert len(pages) > 40
    for rel in pages:
        footer = footer_of(read(ROOT / rel))
        assert footer == bp.FOOTER, "%s: its footer is not the one in the build script" % rel
        hrefs = re.findall(r'href="([^"]*)"', footer)
        for link in MAIN_LINKS:
            assert link in hrefs, "%s: its footer lacks %s" % (rel, link)


def test_the_footer_has_one_place_and_keeps_the_companys_words():
    assert bp.FOOTER.startswith('<footer class="tb"') and bp.FOOTER.endswith("</footer>")
    for words in ("Designmatix Ltd", "12697280", "England and Wales", "Paddle.com",
                  "support@designmatix.co.uk"):
        assert words in bp.FOOTER
    shell = bp.read_shell(str(ROOT))
    assert shell["footer"] == bp.FOOTER


def test_a_footer_changed_by_hand_fails_check_and_all_puts_it_back(tmp_path):
    root = copy_site(tmp_path / "site")
    page = Path(root, "privacy.html")
    text = read(page)
    page.write_bytes(text.replace("Refund policy", "Refunds, our policy", 1).encode())
    result = run_script(root, "--check")
    assert result.returncode == 1 and "privacy.html" in result.stdout
    assert run_script(root, "--all").returncode == 0
    assert read(page) == text
    assert run_script(root, "--check").returncode == 0


def test_all_changes_only_the_footer_of_a_hand_made_page(tmp_path):
    root = copy_site(tmp_path / "site")
    before = snapshot(root)
    page = Path(root, "python-cad.html")
    old = footer_of(read(page))
    page.write_bytes(read(page).replace(old, old.replace("<span>Licence</span>",
                                                       "<span>Our licence</span>")).encode())
    assert run_script(root, "--all").returncode == 0
    after = snapshot(root)
    def norm(data):
        return data.replace(b"\r\n", b"\n")
    assert sorted(k for k in after if norm(before.get(k, b"")) != norm(after[k])) == []


def test_changing_the_footer_in_the_script_changes_every_page(tmp_path):
    root = copy_site(tmp_path / "site")
    script = Path(root, "scripts", "build_pages.py")
    text = read(script)
    assert "<span>Find</span>" in text
    script.write_bytes(text.replace("<span>Find</span>", "<span>Look</span>", 1).encode())
    run = subprocess.run([sys.executable, str(script), "--root", root, "--all"],
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    for rel in pagecheck.page_files(root):
        assert "<span>Look</span>" in read(Path(root, rel)), rel
        assert "<span>Find</span>" not in read(Path(root, rel)), rel


def test_404_page_exists_is_not_in_the_sitemap_or_the_search_list_and_is_not_indexed():
    page = read(ROOT / "404.html")
    page.encode("ascii")
    assert "404.html" in pagecheck.page_files(str(ROOT))
    assert "https://dxcad.designmatix.co.uk/404.html" not in pagecheck.sitemap_locs(str(ROOT))
    assert "/404.html" not in {e["url"] for e in search_list()}
    assert '<meta name="robots" content="noindex, follow">' in page
    assert "<h1>That page is not here</h1>" in page
    assert "<title>Page not found | DX-CAD by Designmatix</title>" in page
    assert 'link rel="canonical" href="https://dxcad.designmatix.co.uk/404.html"' in page


def test_404_page_links_to_the_main_pages_from_the_root_so_it_works_at_any_depth():
    page = read(ROOT / "404.html")
    body = page[page.index('<article class="doc">'):page.index("<footer")]
    hrefs = re.findall(r'href="([^"]*)"', body)
    for link in ("/", "/docs/", "/tutorial.html", "/gallery.html", "/releases.html",
                 "/search.html", "/fabrication.html", "/drafting-pro.html"):
        assert link in hrefs
    assert all(h.startswith("/") for h in hrefs)
    assert not re.search(r'(src|href)="(?!/|#|https?:|mailto:|tel:|data:)', page)


def test_404_page_looks_like_the_others_and_is_sound(tmp_path):
    page = read(ROOT / "404.html")
    refunds = read(ROOT / "refunds.html")
    assert refunds[refunds.index("<style>"):refunds.index("</style>")] in page
    assert refunds[refunds.index('<header class="bar">'):refunds.index("</header>")] in page
    assert pagecheck.check_page(str(ROOT), "404.html") == []


def test_a_missing_404_page_is_made_again(tmp_path):
    root = copy_site(tmp_path / "site")
    Path(root, "404.html").unlink()
    result = run_script(root, "--check")
    assert result.returncode == 1 and "404.html" in result.stdout
    assert run_script(root).returncode == 0
    assert read(Path(root, "404.html")) == read(ROOT / "404.html")
    assert "404.html" not in read(Path(root, "sitemap.xml"))


# --------------------------------------------------------------- download ---

import json as _json
from html.parser import HTMLParser as _HTMLParser

SHA_A = "a" * 63 + "1"
SHA_B = hashlib.sha256(b"dxcad").hexdigest()


class _Rows(_HTMLParser):
    """The rows of the page's files table: [[cell text, ...], ...]."""

    def __init__(self):
        super().__init__()
        self.rows, self._row, self._cell = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            self._row.append("".join(self._cell).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None


def files_rows(page):
    """The body rows of the files table (its header row is dropped)."""
    if 'class="files"' not in page:
        return []
    table = page[page.index('class="files"'):page.index("</table>")]
    p = _Rows()
    p.feed(table)
    return [r for r in p.rows if r and r[0] != "File"]


def latest_data(root=ROOT):
    return _json.loads(read(Path(root) / "data" / "core" / "latest.json"))


def put_latest(root, **changes):
    path = Path(root) / "data" / "core" / "latest.json"
    data = _json.loads(read(path))
    data.update(changes)
    path.write_bytes((_json.dumps(data, indent=2) + "\n").encode())


def test_download_page_is_what_the_script_makes():
    assert read(ROOT / "download.html") == bp.build_all(str(ROOT))["download.html"]


def test_download_page_gives_latest_jsons_version_date_and_address():
    latest = latest_data()
    page = read(ROOT / "download.html")
    y, m, d = (int(x) for x in latest["date"].split("-"))
    assert "<strong>%s</strong>" % latest["version"] in page
    assert "%d %s %d" % (d, bp.MONTHS[m - 1], y) in page
    assert 'datetime="%s"' % latest["date"] in page
    assert 'href="%s"' % latest["url"] in page
    assert latest["version"] in re.search(r"<title>(.*?)</title>", page).group(1)
    assert latest["version"] == notes_releases()[0][0]       # the notes and latest.json agree


def test_download_page_lists_exactly_latest_jsons_files():
    latest = latest_data()
    listed = [f.get("name") or f.get("file") or f.get("filename")
              or f.get("url", "").rsplit("/", 1)[-1] for f in latest.get("files") or []]
    page = read(ROOT / "download.html")
    assert [r[0] for r in files_rows(page)] == listed
    if not listed:      # latest.json names no file: the page says so, in place of a table
        assert "names no downloadable file" in page


def test_download_page_lists_files_with_their_sizes_and_checksums(tmp_path):
    root = copy_site(tmp_path / "site")
    put_latest(root, files=[
        dict(name="dxcad-0.1.5-setup.exe", size=123456789, sha256=SHA_A,
             url="https://example.org/dxcad-0.1.5-setup.exe"),
        dict(name="dxcad-0.1.5-portable.zip", size=2048, sha256=SHA_B.upper()),
        dict(name="dxcad-0.1.5.tar.gz"),
    ])
    assert run_script(root).returncode == 0
    page = read(Path(root, "download.html"))
    rows = files_rows(page)
    assert [r[0] for r in rows] == ["dxcad-0.1.5-setup.exe", "dxcad-0.1.5-portable.zip",
                                    "dxcad-0.1.5.tar.gz"]
    assert rows[0][1] == "123,456,789 bytes (117.7 MB)" and rows[0][2] == SHA_A
    assert rows[1][1] == "2,048 bytes (2.0 KB)" and rows[1][2] == SHA_B     # lower case
    assert rows[2][1] == "not given" and rows[2][2] == "not given"          # nothing invented
    assert 'href="https://example.org/dxcad-0.1.5-setup.exe"' in page
    assert "Check a download" in page and "shasum -a 256" in page
    assert "names no downloadable file" not in page
    assert pagecheck.check_page(root, "download.html") == []


def test_a_changed_latest_json_changes_the_page(tmp_path):
    root = copy_site(tmp_path / "site")
    before = read(Path(root, "download.html"))
    put_latest(root, version="0.1.6", date="2026-11-09")
    result = run_script(root, "--check")
    assert result.returncode == 1 and "download.html" in result.stdout
    assert run_script(root, "--all").returncode == 0
    after = read(Path(root, "download.html"))
    assert after != before
    assert "<strong>0.1.6</strong>" in after and "9 November 2026" in after
    assert "<strong>0.1.5</strong>" not in after
    assert run_script(root, "--check").returncode == 0


@pytest.mark.parametrize("changes, words", [
    (dict(files=[dict(name="a.zip", sha256="abc")]), "sha256"),
    (dict(files=[dict(name="a.zip", size="big")]), "size"),
    (dict(files=[dict(size=1)]), "no name"),
    (dict(date="3 November"), "date"),
])
def test_a_bad_latest_json_stops_the_build_and_says_why(tmp_path, changes, words):
    root = copy_site(tmp_path / "site")
    put_latest(root, **changes)
    result = run_script(root)
    assert result.returncode != 0
    assert "latest.json" in result.stderr and words in result.stderr


def test_download_page_is_in_the_sitemap_the_search_list_and_every_header_and_footer():
    assert "https://dxcad.designmatix.co.uk/download.html" in pagecheck.sitemap_locs(str(ROOT))
    assert "/download.html" in {e["url"] for e in search_list()}
    for rel in pagecheck.page_files(str(ROOT)):
        text = read(ROOT / rel)
        header = text[text.index('<header class="bar">'):text.index("</header>")]
        footer = text[text.index('<footer class="tb"'):text.index("</footer>")]
        assert 'href="/download.html"' in header, rel
        assert 'href="/download.html"' in footer, rel


def test_download_page_is_sound_and_loads_nothing_from_elsewhere():
    assert pagecheck.check_page(str(ROOT), "download.html") == []
    assert "<script" not in read(ROOT / "download.html")


# ------------------------------------------------- structured data, theme ---

def test_a_changed_latest_json_changes_the_json_ld_of_the_home_and_release_pages(tmp_path):
    root = copy_site(tmp_path / "site")
    put_latest(root, version="0.1.6", date="2026-11-09", url="https://pypi.org/project/dxcad/0.1.6/")
    assert run_script(root).returncode == 0
    import json
    for rel in ("index.html", "releases.html"):
        text = read(Path(root, rel))
        blocks = re.findall(r'<script type="application/ld\+json">\n(.*?)\n</script>', text, re.S)
        nodes = []
        for b in blocks:
            data = json.loads(b)
            nodes += [n for n in data.get("@graph", [data]) if n.get("@type") == "SoftwareApplication"]
        assert [n["softwareVersion"] for n in nodes] == ["0.1.6"], rel
        assert [n["downloadUrl"] for n in nodes] == ["https://pypi.org/project/dxcad/0.1.6/"], rel
    assert run_script(root, "--check").returncode == 0


def test_the_home_page_keeps_every_other_word_of_its_json_ld_when_the_version_changes(tmp_path):
    import json
    root = copy_site(tmp_path / "site")
    put_latest(root, version="0.1.6", date="2026-11-09")
    run_script(root)

    def ld(path):
        return json.loads(re.search(r'<script type="application/ld\+json">\n(.*?)\n</script>',
                                    read(path), re.S).group(1))
    old, new = ld(ROOT / "index.html"), ld(Path(root, "index.html"))
    for data in (old, new):
        for node in data["@graph"]:
            if node["@type"] == "SoftwareApplication":
                node.pop("softwareVersion")
                node.pop("downloadUrl")
    assert old == new


def test_the_theme_block_is_put_back_once_on_a_hand_made_page(tmp_path):
    root = copy_site(tmp_path / "site")
    page = Path(root, "privacy.html")
    text = read(page)
    page.write_bytes(re.sub(r'<style id="theme">.*?</style>\n', "", text, flags=re.S).encode())
    result = run_script(root, "--check")
    assert result.returncode == 1 and "privacy.html" in result.stdout
    assert run_script(root).returncode == 0
    assert read(page) == text and text.count('<style id="theme">') == 1
    page.write_bytes(text.replace("</head>", bp.THEME_STYLE + "\n</head>", 1).encode())    # a second copy
    assert run_script(root).returncode == 0 and read(page) == text


def test_the_theme_block_and_the_print_style_are_ascii_and_fit_the_size_limit():
    bp.THEME_STYLE.encode("ascii")
    assert len(bp.THEME_STYLE) < 1500
    assert "@media print" in bp.DOCS_STYLE and "@media print" not in bp.THEME_STYLE


# ----------------------------------------------------------------- images ---

def png_of(w, h):
    import struct as st
    import zlib as zl

    def chunk(kind, data):
        body = kind + data
        return st.pack(">I", len(data)) + body + st.pack(">I", zl.crc32(body))
    raw = b"".join(b"\x00" + b"\xff\xff\xff" * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", st.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zl.compress(raw)) + chunk(b"IEND", b""))


def test_a_bare_picture_in_a_hand_made_page_is_given_its_size_and_lazy_loading(tmp_path):
    root = copy_site(tmp_path / "site")
    Path(root, "img", "wide.png").write_bytes(png_of(64, 48))
    Path(root, "img", "tall.png").write_bytes(png_of(48, 64))
    page = Path(root, "privacy.html")
    text = read(page)
    bare = ('<p><img src="/img/wide.png" alt="Wide" loading="lazy">'
            '<img src="/img/tall.png" alt="Tall"></p>\n')
    anchor = '<main class="wrap" id="main">\n'
    assert anchor in text
    page.write_bytes(text.replace(anchor, anchor + bare, 1).encode())
    assert run_script(root, "--check").returncode == 1
    assert run_script(root).returncode == 0
    made = read(page)
    assert ('<img src="/img/wide.png" alt="Wide" width="64" height="48">') in made    # the first: not lazy
    assert ('<img src="/img/tall.png" alt="Tall" width="48" height="64" loading="lazy">') in made
    assert run_script(root, "--check").returncode == 0
    before = made
    assert run_script(root).returncode == 0 and read(page) == before                  # nothing more to do
    assert pagecheck.check_page(root, "privacy.html") == []


def test_pictures_written_into_the_page_and_outside_the_site_are_left_alone():
    def nothing(page, src):
        raise AssertionError("looked up " + src)
    tag = '<img src="data:image/png;base64,AAAA" alt="x" width="1" height="1">'
    assert bp.finish_images(tag, "a.html", nothing) == tag
    out = bp.finish_images('<img src="https://example.org/a.png" alt="x">', "a.html",
                           lambda page, src: None)
    assert out == '<img src="https://example.org/a.png" alt="x">'    # first picture: no size to read, no lazy


def test_the_script_reads_the_size_of_a_gif_and_a_jpeg_too():
    import struct as st
    gif = b"GIF89a" + st.pack("<HH", 11, 9) + b"\x00" * 10
    jpg = (b"\xff\xd8\xff\xe0" + st.pack(">H", 6) + b"JFIF"
           + b"\xff\xc0" + st.pack(">H", 11) + b"\x08" + st.pack(">HH", 17, 13) + b"\x01\x01\x11\x00")
    assert bp.picture_size(gif) == (11, 9) and bp.picture_size(jpg) == (13, 17)
    assert bp.picture_size(png_of(7, 5)) == (7, 5)
    assert bp.picture_size(b"nothing") is None and bp.picture_size(jpg[:12]) is None


def test_the_gallery_the_add_on_pages_and_the_home_page_have_sized_pictures():
    for rel in ("gallery.html", "fabrication.html", "drafting-pro.html", "index.html",
                "examples/bracket.html"):
        text = read(ROOT / rel)
        imgs = [t for t in re.findall(r"<img\b[^>]*>", text) if 'src="data:' not in t]
        assert imgs, rel
        assert all(" width=" in t and " height=" in t for t in imgs), rel
        assert 'loading="lazy"' not in imgs[0] and all('loading="lazy"' in t for t in imgs[1:]), rel


# -------------------------------------------------------------------- faq ---

import html as _html


def _plain_words(text):
    """Text with its markup, marks, entities and case taken off, as one line."""
    text = re.sub(r"<[^>]+>", "", text)
    text = _html.unescape(text)
    text = re.sub(r"\(items? [\d, and]+\)", "", text)
    text = re.sub(r"[`*]|\]\([^)]*\)|\[", "", text)
    return re.sub(r"\s+([.,;:])", lambda m: m.group(1), " ".join(text.lower().split()))


def faq_entries_of(page):
    """[(question, [answer paragraph text], more href)] read from the page by a plain scan."""
    found = []
    for block in re.findall(r'<div class="qa" id="[^"]+">\n(.*?)\n    </div>', page, re.S):
        question = re.search(r"<h3>(.*?)</h3>", block, re.S).group(1)
        href = re.search(r'<p class="more">More: <a href="([^"]+)"', block).group(1)
        paras = re.findall(r'<p>(.*?)</p>', block, re.S)
        found.append((_html.unescape(question), paras, href))
    return found


def limitation_headings(root=ROOT):
    text = read(Path(root) / "data" / "core" / "limitations.md")
    return re.findall(r"(?m)^## (.+?)\s*$", text)


def heading_id(heading):
    return re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")


def ids_of(path):
    return set(re.findall(r'\sid="([^"]+)"', read(path)))


def test_faq_page_is_what_the_script_makes():
    assert read(ROOT / "faq.html") == bp.build_all(str(ROOT))["faq.html"]


def test_every_answers_link_goes_to_a_page_here_and_to_a_heading_on_it():
    entries = faq_entries_of(read(ROOT / "faq.html"))
    assert len(entries) >= 15
    for question, paras, href in entries:
        assert href.startswith("/docs/"), (question, href)
        path, _, frag = href.partition("#")
        rel = "docs/index.html" if path == "/docs/" else path.lstrip("/")
        assert (ROOT / rel).is_file(), "%s: %s is not a page here" % (question, href)
        if frag:
            assert frag in ids_of(ROOT / rel), "%s: %s has no #%s" % (question, rel, frag)


def test_every_limitation_in_limitations_md_has_its_question_linked_to_its_section():
    headings = limitation_headings()
    assert len(headings) >= 10
    entries = faq_entries_of(read(ROOT / "faq.html"))
    linked = [href for _, _, href in entries]
    for heading in headings:
        href = "/docs/limitations.html#" + heading_id(heading)
        assert linked.count(href) == 1, "limitations.md: '%s' has no question" % heading
        question = next(q for q, _, h in entries if h == href)
        assert question.endswith("?")


def test_every_answer_is_the_docs_own_words():
    page = read(ROOT / "faq.html")
    docs = _plain_words(read(ROOT / "data" / "core" / "gui.md")
                        + " " + read(ROOT / "data" / "core" / "limitations.md"))
    for question, paras, _ in faq_entries_of(page):
        assert paras, question
        for para in paras:
            words = _plain_words(para)
            words = words[len("workaround: "):] if words.startswith("workaround: ") else words
            for sentence in re.split(r"(?<=[.!?]) ", words):
                assert sentence in docs, "%s: not in the docs: %r" % (question, sentence)


def test_faq_page_carries_no_private_item_numbers_and_no_labels_of_the_source():
    page = read(ROOT / "faq.html")
    body = page[page.index('<article class="doc">'):page.index("</article>")]
    assert not re.search(r"\bitems? \d+", body)
    assert "Cause:" not in body
    assert "<script" not in page


def test_faq_page_is_sound_in_the_sitemap_the_search_list_the_footer_and_the_404_page():
    assert pagecheck.check_page(str(ROOT), "faq.html") == []
    assert "https://dxcad.designmatix.co.uk/faq.html" in pagecheck.sitemap_locs(str(ROOT))
    assert "/faq.html" in {e["url"] for e in search_list()}
    assert 'href="/faq.html"' in bp.FOOTER
    for rel in pagecheck.page_files(str(ROOT)):
        assert 'href="/faq.html"' in footer_of(read(ROOT / rel)), rel
    assert 'href="/faq.html"' in read(ROOT / "404.html")


def test_a_new_limitation_in_a_copy_of_the_data_gets_a_question_and_changes_the_page(tmp_path):
    root = copy_site(tmp_path / "site")
    path = Path(root, "data", "core", "limitations.md")
    text = read(path)
    new = ("## Text on a curved face\n\nCause: lettering is flat. It cannot bend.\n\n"
           "Workaround: cut the text from a flat plate first.\n\n")
    text = text.replace("## The robustness suite", new + "## The robustness suite", 1)
    path.write_bytes(text.encode())
    result = run_script(root, "--check")
    assert result.returncode == 1 and "faq.html" in result.stdout
    assert run_script(root, "--all").returncode == 0
    entries = faq_entries_of(read(Path(root, "faq.html")))
    hrefs = [h for _, _, h in entries]
    assert "/docs/limitations.html#text-on-a-curved-face" in hrefs
    q, paras, _ = next(e for e in entries if e[2].endswith("#text-on-a-curved-face"))
    assert q == "What should I know about: text on a curved face?"
    assert paras == ["Lettering is flat. It cannot bend.",
                     "Workaround: Cut the text from a flat plate first."]
    assert run_script(root, "--check").returncode == 0
    assert pagecheck.check_page(root, "faq.html") == []


def test_a_changed_word_in_the_docs_changes_the_answer(tmp_path):
    root = copy_site(tmp_path / "site")
    path = Path(root, "data", "core", "limitations.md")
    path.write_bytes(read(path).replace("one radius per call", "two radii per call", 1).encode())
    assert run_script(root, "--all").returncode == 0
    assert "two radii per call" in read(Path(root, "faq.html"))


def test_the_build_stops_and_says_why_when_a_section_the_questions_need_is_gone(tmp_path):
    root = copy_site(tmp_path / "site")
    path = Path(root, "data", "core", "gui.md")
    path.write_bytes(read(path).replace("## Tabs", "## Pages", 1).encode())
    result = run_script(root, "--check")
    assert result.returncode != 0 and "Tabs" in result.stderr
