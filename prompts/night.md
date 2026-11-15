Read CLAUDE.md, BACKLOG.md, BLOCKED.md and the last entry in REPORT.md (if
they exist). This is the DX-CAD website repository, not DX-CAD.

Run `git branch --no-merged main --list 'auto/*'`. If it lists a branch,
check out the newest one and continue on it. Otherwise get today's date
with `date +%F` and create branch auto/<that date> from main.

If BACKLOG.md has no unchecked items when you start: do not draft any
items. The owner writes this repository's backlog. Append a dated entry to
REPORT.md saying the backlog is empty, commit it as 'chore: night run
report', end your final message with the word FINISHED and stop.

Work BACKLOG.md top to bottom following the rules in CLAUDE.md. For each
item: implement, add tests, run Test and Smoke as defined below, commit,
mark the item [x]. If an item is too large, split it as CLAUDE.md says.
- Test: `python -m pytest -n 4 -q` (while working, the files you changed).
- Run every command with the Bash tool. The venv is already active, so run
  Python as plain `python`.
- Smoke: the tests pass and `python scripts/build_pages.py --check` (once 4002 is done)

Do not ask me anything. Do not wait for input. If a choice is ambiguous,
decide per CLAUDE.md and log it in DECISIONS.md.

Stop when any of these is true:
- BACKLOG.md has no unchecked items
- you have completed 12 items this run
- 3 consecutive items ended up in BLOCKED.md

Then run Test and Smoke one final time and append a dated entry to
REPORT.md with these headings:
DONE (item, commit hash, one line each)
DECISIONS (copied from DECISIONS.md for this run)
BLOCKED (item, one-line cause, what the owner must do)
TESTS (pass/fail counts, time of the full run, smoke result)
REVIEW (anything you are unsure about)

Commit REPORT.md, BACKLOG.md, DECISIONS.md and BLOCKED.md as
'chore: night run report'. End your final message with the word FINISHED.
