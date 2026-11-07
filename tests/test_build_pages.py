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
    """A working copy of the site (not the data's pictures, which the tests do not need)."""
    ignore = shutil.ignore_patterns(".git", ".venv", "logs", "__pycache__",
                                    ".pytest_cache", "gallery", "examples")
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
