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
    assert changed == ["data/core/RELEASE_NOTES.md", "releases.html", "sitemap.xml"]
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
