"""Daily download counts of the site's GitHub releases (item 4021).

GitHub keeps one running total per release file (download_count). Once a day the workflow
.github/workflows/download-stats.yml runs this script on the "stats" branch:

    python scripts/download_stats.py snapshot stats/       # appends today's totals
    python scripts/download_stats.py report stats/         # remakes stats/README.md

stats/totals.csv holds one row per file per day: date (UTC), release tag, file name, the
kind of file, and GitHub's running total. A day's downloads of a file are its total that day
less its total on the day before; stats/README.md shows them by kind for the last 60 days,
newest first, and each kind's total so far.

Standard library only. The token comes from GITHUB_TOKEN (the workflow's own); the counts are
public, so the script also works without one, within GitHub's limit for unsigned requests.
"""
import csv
import datetime
import json
import os
import sys
import urllib.request

REPO = "faizaldm/dxcad-site"
API = "https://api.github.com/repos/%s/releases?per_page=100&page=%d"
FIELDS = ["date", "tag", "file", "kind", "total"]
DAYS = 60

# The kind of a file, from its name: the first rule that matches wins.
KINDS = [
    ("Windows installer", lambda n: n.endswith("-setup.exe")),
    ("Windows zip", lambda n: n.endswith(".zip")),
    ("macOS", lambda n: n.endswith(".dmg")),
    ("Linux", lambda n: n.endswith(".AppImage")),
    ("Fabrication", lambda n: n.startswith("dxcad_fabrication-")),
    ("Drafting Pro", lambda n: n.startswith("dxcad_drafting_pro-")),
    ("Architecture", lambda n: n.startswith("dxcad_architecture-")),
]
OTHER = "Other"


def kind_of(name):
    for kind, test in KINDS:
        if test(name):
            return kind
    return OTHER


def fetch_releases(token=None, opener=urllib.request.urlopen):
    """Every published release of the site, as GitHub's API gives it (drafts left out)."""
    found, page = [], 1
    while True:
        req = urllib.request.Request(API % (REPO, page), headers={
            "Accept": "application/vnd.github+json", "User-Agent": "dxcad-site-download-stats"})
        if token:
            req.add_header("Authorization", "Bearer " + token)
        with opener(req) as resp:
            batch = json.load(resp)
        found += [r for r in batch if not r.get("draft")]
        if len(batch) < 100:
            return found
        page += 1


def rows_from_releases(releases, day):
    """One row per release file: its running total on `day` (a date)."""
    rows = []
    for rel in releases:
        for asset in rel.get("assets", []):
            rows.append({"date": day.isoformat(), "tag": rel["tag_name"], "file": asset["name"],
                         "kind": kind_of(asset["name"]), "total": int(asset["download_count"])})
    return sorted(rows, key=lambda r: (r["tag"], r["file"]))


def read_totals(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="ascii") as f:
        return [dict(r, total=int(r["total"])) for r in csv.DictReader(f)]


def write_totals(path, rows):
    with open(path, "w", newline="", encoding="ascii") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def add_snapshot(old, new):
    """The old rows with the new day's rows in place of any rows of the same day (a second run
    on one day replaces that day's counts rather than counting them twice)."""
    days = {r["date"] for r in new}
    kept = [r for r in old if r["date"] not in days]
    return sorted(kept + new, key=lambda r: (r["date"], r["tag"], r["file"]))


def daily_by_kind(rows):
    """{date: {kind: downloads that day}} for every day after the first with a snapshot.
    A file first seen on a day counts its whole total that day (it was published since the
    day before). A total that went down (GitHub recounted) counts as 0, never below."""
    by_day = {}
    for r in rows:
        by_day.setdefault(r["date"], {})[(r["tag"], r["file"])] = (r["kind"], r["total"])
    days = sorted(by_day)
    out = {}
    for before, day in zip(days, days[1:]):
        counts = {}
        for key, (kind, total) in by_day[day].items():
            prev = by_day[before].get(key, (kind, 0))[1]
            counts[kind] = counts.get(kind, 0) + max(0, total - prev)
        out[day] = counts
    return out


def report(rows, days=DAYS):
    kinds = [k for k, _ in KINDS] + [OTHER]
    daily = daily_by_kind(rows)
    seen = [k for k in kinds if any(k in c for c in daily.values()) or
            any(r["kind"] == k for r in rows)]
    lines = ["# Downloads of DX-CAD from this site's GitHub releases", "",
             "Made each day by scripts/download_stats.py from GitHub's running totals "
             "(stats/totals.csv). A day is a UTC day; its downloads are each file's total "
             "that day less its total the day before. pip installs from PyPI are not counted here.",
             ""]
    if rows:
        last = max(r["date"] for r in rows)
        totals = {}
        for r in rows:
            if r["date"] == last:
                totals[r["kind"]] = totals.get(r["kind"], 0) + r["total"]
        lines += ["## Total so far (%s)" % last, "", "| Kind | Downloads |", "|---|---:|"]
        lines += ["| %s | %d |" % (k, totals.get(k, 0)) for k in seen]
        lines += ["| All | %d |" % sum(totals.values()), ""]
    lines += ["## By day, newest first (last %d days)" % days, ""]
    if not daily:
        lines += ["The first day's counts come after the second snapshot.", ""]
        return "\n".join(lines)
    lines += ["| Day | " + " | ".join(seen) + " | All |",
              "|---|" + "---:|" * (len(seen) + 1)]
    for day in sorted(daily, reverse=True)[:days]:
        c = daily[day]
        lines.append("| %s | %s | %d |" % (day, " | ".join(str(c.get(k, 0)) for k in seen),
                                           sum(c.values())))
    return "\n".join(lines) + "\n"


def main(argv):
    if len(argv) != 3 or argv[1] not in ("snapshot", "report"):
        print("usage: download_stats.py snapshot|report FOLDER")
        return 2
    folder = argv[2]
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "totals.csv")
    rows = read_totals(path)
    if argv[1] == "snapshot":
        today = datetime.datetime.now(datetime.timezone.utc).date()
        new = rows_from_releases(fetch_releases(os.environ.get("GITHUB_TOKEN")), today)
        rows = add_snapshot(rows, new)
        write_totals(path, rows)
        print("%s: %d files, %d downloads in all" % (today, len(new), sum(r["total"] for r in new)))
    with open(os.path.join(folder, "README.md"), "w", newline="", encoding="ascii") as f:
        f.write(report(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
