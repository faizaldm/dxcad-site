# Report

## Run audit, 7 November 2026 (item 4019)

Range audited: every commit after 1ff1333 (the owner's data/ commit, 09:44), 2e2aa18 to 2a8228d: the 18 items 4001 to
4018 and the four queue commits. Checked by reading each commit's diff and by searching the tree.

| Commit | Finding | What was done |
|---|---|---|
| d3c344c (4018) | One `pytest.skip`: the test that runs the gallery's filter script skips where node is not installed (not installed here). It carries its reason in the test. | Kept, explained. The script is also held by a test that reads it (`test_the_filter_script_reads_the_tags_the_page_writes_and_sets_what_the_page_styles`). Owner check 2 in docs/qa/owner-checks.md covers the behaviour. |
| d3c344c (4018) | One assertion changed: the count of gallery links now matches the new `<li data-tags=...>` markup. | Same strength; nothing loosened. |
| 7d7aa5e (4015) | Test changed: the big picture in the size-limit test is now the second picture (the first is now eager, not lazy). | Same rule, same limit (300 KB); nothing loosened. |
| 0940f1e (4011) | Two expected file lists gained `search.json`; one pound sign written as an escape. | The new generated file is expected; the escape keeps the test file ASCII; nothing loosened. |
| eaf3d08 (4008) | Expected file list gained `releases.xml`. | As above. |
| all | Assertions removed, tolerances changed, tests left out by a marker or name, other skips or xfails: none. The 300 KB and 4.5 : 1 limits were set once (4001, 4009) and never changed. | none needed |
| all | Debug prints, TODO, FIXME: none (the script's only prints are its `--check` and `--all` messages). | none needed |
| all | Files over 1 MB: none in the repository. | none needed |
| all | Text that is not ASCII in any file this run added or changed (pictures excepted): none. | none needed |
| all | A person's name: none in this run's files. The owner's own pages (home, SDK pages, product pages) carry the owner's GitHub account name in links to the SDK docs; they are not from this run. The git sign-off lines carry the owner's name and address, as the owner's `-s` rule makes them; the 18 `Co-Authored-By: Claude` trailers are the harness's attribution. | Explained; history not touched. |
| all | Another CAD product's name: the home page's "Works beside ..." row and two later lines name one, with a trademark notice (owner's own text, before this run; copied into search.json); data/core/gui.md names a third-party software package in its About window row (read-only; shown on docs/gui.html and in search.json). | Not mended: the rules keep the pages "as they are" and forbid editing data/. Owner decision, in docs/qa/owner-checks.md section 14. |
| all | An email address: the company support address is in the footer of every page and the home page's structured data. It was in the owner's footer before this run; FOOTER in the build script copies it. | Not mended, same reason; owner decision, section 14. |
| README.md | Stale: did not name tutorial.html, releases.xml, download.html, faq.html or shortcuts.html, and said the footer comes from index.html. | Mended; `test_readme_names_every_file_the_script_makes` fails if a file the script makes is not named. |
| 4001 to 4018 | CHANGELOG line: this repository has no CHANGELOG; no item has a help text beyond its page. | Not started (see DECISIONS.md, 4019): each item has its entry in DECISIONS.md and its commit subject. |

Each ticked item has a test that fails without its change. Done by making the change undone in a temporary copy of the
site (the page deleted, a link broken, a tag removed, a width removed, a README step renamed and so on) and running
the suite; all 18 failed, naming a test:

| Item | Change undone in the copy | First failing test |
|---|---|---|
| 4001 | a link to a file that is not there | test_check_passes_on_the_committed_pages |
| 4002 | a change in releases.html | test_check_passes_on_the_committed_pages |
| 4003 | examples/bracket.html deleted | test_example_description_is_the_scripts_first_docstring_line[bracket] |
| 4004 | fabrication.html deleted | test_check_passes_on_the_committed_pages |
| 4005 | README's "Publish" step renamed | test_readme_names_the_three_steps |
| 4006 | tutorial.html deleted | test_check_passes_on_the_committed_pages |
| 4007 | og:title removed from index.html | test_a_new_example_gets_a_page_and_a_picture |
| 4008 | releases.xml deleted | test_check_passes_on_the_committed_pages |
| 4009 | the skip link's words changed | test_a_new_example_gets_a_page_and_a_picture |
| 4010 | docs/gui.html deleted | test_check_passes_on_the_committed_pages |
| 4011 | search.json deleted | test_search_json_lists_every_page_in_the_sitemap_with_title_and_headings |
| 4012 | 404.html deleted | test_check_passes_on_the_committed_pages |
| 4013 | download.html deleted | test_check_passes_on_the_committed_pages |
| 4014 | the JSON-LD type changed | test_check_passes_on_the_committed_pages |
| 4015 | every width removed from gallery.html | test_check_passes_on_the_committed_pages |
| 4016 | faq.html deleted | test_check_passes_on_the_committed_pages |
| 4017 | shortcuts.html deleted | test_check_passes_on_the_committed_pages |
| 4018 | a gallery tag changed | test_check_passes_on_the_committed_pages |

Full passes: the whole suite has no slow marker, so "slow" is the whole of it. Before the audit's own edits, two
parallel passes (`-n 4`, 47 s and 44 s) and two serial passes (129 s and 125 s) each gave 479 passed, 1 skipped.
No test passed once and failed once, so no flaky test was found. After the audit's edits: 484 passed, 1 skipped
(`-n 4`, 35 s). A final pair of passes is recorded in the night run entry below.
