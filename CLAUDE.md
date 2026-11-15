# Rules for this repository (owner rules, 6 November 2026)

This is DX-CAD's website, https://dxcad.designmatix.co.uk/, served by GitHub Pages from main. It is built by an
autonomous loop from BACKLOG.md items on auto/* branches; the owner merges and publishes. Python 3.12 in .venv, with
pytest, is for its tests and its page script only.

- The site stays plain static HTML and CSS, as it is: no framework, no build step beyond scripts/build_pages.py
  (Python's standard library only), no JavaScript a page needs to be read, no tracking, no third-party script, font
  or embed. Keep the pages' look: their own CSS, the header and the footer as they are.
- This repository is PUBLIC. Nothing from DX-CAD's private repositories goes into it except what the owner copies
  into data/, which is only what is public already or written for users: data/core holds DX-CAD's release notes
  (written for users) and, from the public DX-CAD-SDK repository, its examples, their pictures, gui.md, index.md,
  limitations.md and latest.json. Read them; never edit them. Never write anything about the paid add-ons beyond what
  these and the site's own pages already say. Pages made from data/ are made by scripts/build_pages.py, and the tests
  hold the committed pages to what it makes.
- Prices, trial terms, licence words, versions and dates come from data/ or from the pages as they are; never from
  memory and never invented.
- Every page keeps a title, a meta description, a canonical link and its place in sitemap.xml; every internal link
  and image resolves; every image has alt text. Never edit CNAME.

## Working rules

- Build items in BACKLOG.md order, one at a time; tick an item only when its Accept lines are met. If an item is too
  large, split it: leave it open, write the parts below it with the next free numbers in this repository's range
  (4001 and up), and say so in the report. Numbers in this repository never reuse another DX-CAD repository's.
- You cannot install packages, download files or reach the network. If something needs a package or a document that
  is missing, write it in BLOCKED.md with the exact name and move on.
- Tests: while building, `python -m pytest -n 4 <files>`; before each commit, `python -m pytest -n 4 -q`. Every item
  adds tests.
- Commits are signed off (-s), the subject ending with the item number in brackets, e.g. "feat: ... (4001)".
- Never push, never force-push, rebase, amend or reset --hard; never commit to main. Never run rm -rf.
- Text files are ASCII. Plain English in docs, pages and messages. Never name another CAD product, a person or an
  email address anywhere in this repository (the owner's rule for every DX-CAD repository).
- Never edit .claude/ or scripts/night.ps1.
- At the end of a session, write REPORT.md: items done, anything blocked, decisions taken (also in DECISIONS.md), and
  the test time.
