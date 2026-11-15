"""Item 4021: the daily download counts from GitHub's running totals."""
import datetime
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import download_stats as ds  # noqa: E402

D1, D2, D3 = datetime.date(2026, 11, 15), datetime.date(2026, 11, 16), datetime.date(2026, 11, 17)


def release(tag, **counts):
    return {"tag_name": tag, "draft": False,
            "assets": [{"name": n, "download_count": c} for n, c in counts.items()]}


def files(setup=0, macos=0, fab=0):
    return {"DX-CAD-0.1.6-windows-x64-setup.exe": setup, "DX-CAD-0.1.6-macos.dmg": macos,
            "dxcad_fabrication-0.1.2-cp312-cp312-win_amd64.whl": fab}


def test_kinds_of_the_site_files():
    assert ds.kind_of("DX-CAD-0.1.6-windows-x64-setup.exe") == "Windows installer"
    assert ds.kind_of("DX-CAD-0.1.6-windows-x64.zip") == "Windows zip"
    assert ds.kind_of("DX-CAD-0.1.6-macos.dmg") == "macOS"
    assert ds.kind_of("DX-CAD-x86_64.AppImage") == "Linux"
    assert ds.kind_of("dxcad_fabrication-0.1.2-cp312-cp312-win_amd64.whl") == "Fabrication"
    assert ds.kind_of("dxcad_drafting_pro-0.1.2-cp312-cp312-win_amd64.whl") == "Drafting Pro"
    assert ds.kind_of("dxcad_architecture-0.1.0-cp312-cp312-win_amd64.whl") == "Architecture"
    assert ds.kind_of("notes.txt") == "Other"


def test_a_day_is_the_total_less_the_day_before():
    rows = ds.rows_from_releases([release("v0.1.6", **files(10, 4, 1))], D1)
    rows = ds.add_snapshot(rows, ds.rows_from_releases([release("v0.1.6", **files(17, 4, 3))], D2))
    rows = ds.add_snapshot(rows, ds.rows_from_releases([release("v0.1.6", **files(20, 6, 3))], D3))
    daily = ds.daily_by_kind(rows)
    assert daily == {"2026-11-16": {"Windows installer": 7, "macOS": 0, "Fabrication": 2},
                     "2026-11-17": {"Windows installer": 3, "macOS": 2, "Fabrication": 0}}


def test_a_new_release_counts_its_whole_total_on_its_first_day():
    rows = ds.rows_from_releases([release("v0.1.6", **files(10))], D1)
    rows = ds.add_snapshot(rows, ds.rows_from_releases(
        [release("v0.1.6", **files(12)), release("v0.1.7", **{"DX-CAD-0.1.7-macos.dmg": 5})], D2))
    assert ds.daily_by_kind(rows)["2026-11-16"]["Windows installer"] == 2
    assert ds.daily_by_kind(rows)["2026-11-16"]["macOS"] == 5


def test_a_lower_total_counts_as_none_and_a_second_run_replaces_its_day():
    rows = ds.rows_from_releases([release("v0.1.6", **files(10))], D1)
    rows = ds.add_snapshot(rows, ds.rows_from_releases([release("v0.1.6", **files(8))], D2))
    assert ds.daily_by_kind(rows)["2026-11-16"]["Windows installer"] == 0
    again = ds.add_snapshot(rows, ds.rows_from_releases([release("v0.1.6", **files(15))], D2))
    assert len(again) == len(rows)
    assert ds.daily_by_kind(again)["2026-11-16"]["Windows installer"] == 5


def test_drafts_are_left_out_and_pages_are_followed():
    pages = [[release("v%d" % i, **files(1)) for i in range(100)],
             [release("v100", **files(1)), dict(release("draft", **files(9)), draft=True)]]
    calls = []

    def opener(req):
        calls.append(req.full_url)
        return io.BytesIO(json.dumps(pages[len(calls) - 1]).encode())

    found = ds.fetch_releases(token="t", opener=opener)
    assert len(found) == 101 and all(r["tag_name"] != "draft" for r in found)
    assert [u.rsplit("=", 1)[1] for u in calls] == ["1", "2"]


def test_totals_file_and_report_round_trip(tmp_path):
    rows = ds.rows_from_releases([release("v0.1.6", **files(10, 4, 1))], D1)
    rows = ds.add_snapshot(rows, ds.rows_from_releases([release("v0.1.6", **files(17, 4, 3))], D2))
    path = tmp_path / "totals.csv"
    ds.write_totals(str(path), rows)
    assert ds.read_totals(str(path)) == rows
    text = ds.report(rows)
    text.encode("ascii")
    assert "## Total so far (2026-11-16)" in text and "| All | 24 |" in text
    assert "| 2026-11-16 | 7 | 0 | 2 | 9 |" in text


def test_report_before_a_second_snapshot_says_so():
    rows = ds.rows_from_releases([release("v0.1.6", **files(10))], D1)
    assert "after the second snapshot" in ds.report(rows)


def test_the_workflow_runs_daily_and_writes_only_the_stats_branch():
    wf = (ROOT / ".github" / "workflows" / "download-stats.yml").read_text(encoding="ascii")
    assert 'cron: "17 5 * * *"' in wf and "workflow_dispatch" in wf
    assert "git push --quiet origin stats" in wf and "origin main" not in wf
    assert "contents: write" in wf
