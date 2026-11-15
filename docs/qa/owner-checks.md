# The owner's checks for the website

This is for the person who merges and publishes the site. The tests look at the
pages' words and markup. They cannot look at a page in a browser, at a page on
the live address, or at whether a sentence is right. Part 1 is what only a
person can check, riskiest first. Part 2 is what a test already checks, so you
need not.

Where a step says "the site", open the branch's pages from a local server
(`python -m http.server 8000` in the top folder, then http://localhost:8000/)
before you merge, and the live address, https://dxcad.designmatix.co.uk/,
after. Every link on the site starts with a slash, so opening a file straight
from a folder does not work; that is how the site has always been.

## Part 1. What only a person can check

### 1. The search page does what it should (item 4011)

No browser or node was available when it was written; the script was read, not run.

1. Open /search.html.
2. Type `bracket`. Results should appear as you type, each with a page title and
   up to two lines of its words with `bracket` marked.
3. Type `bracket holes`. Fewer or equal results; each shows both words.
4. Type `zzzzqq`. A plain "nothing found" message and no error.
5. Click a result. It opens the right page, at the heading if it shows one.
6. Open the browser's developer tools, Network tab, reload: only your own
   files load (the page, search.json, the style), nothing from another address.
7. Switch the network off and type again: it still searches.

Expected: all of the above. If typing does nothing, the script has failed:
open the Console tab and note the first red line.

### 2. The gallery's filter buttons (item 4018)

The test that runs the script needs node, which was not installed, so it was
skipped (see the audit in REPORT.md).

1. Open /gallery.html. The buttons (All, sketch, sheet metal, ...) should be
   there above the pictures, and every example should show.
2. Click `sheet metal`. Only the examples tagged so stay; a count says how many.
3. Click `All`. Every example is back.
4. Click two tags in turn: each click replaces the last filter.
5. Tab to a button with the keyboard and press Enter: it works and shows which
   button is pressed.
6. In developer tools turn JavaScript off (Settings, Debugger, Disable
   JavaScript) and reload: no buttons, every example shows.

Expected: as written. Compare a card's tags with its script (open its page,
read "Uses: ...") for two or three examples.

### 3. The dark theme (item 4014)

Only checked by computing contrast, never seen.

1. Set the computer to dark mode (or in developer tools, Rendering, "Emulate
   prefers-color-scheme: dark").
2. Look at the home page top to bottom, then /gallery.html, /docs/gui.html,
   /download.html, /faq.html and /search.html.
3. Look for: text you cannot read, a white box where there should be dark, a
   logo that disappears, pictures with a dark background on a dark page,
   buttons with unreadable words, the search highlight, the hand-drawn
   pictures' lines.
4. Switch back to light mode and check the home page looks as it did before.

Expected: readable everywhere; the light page unchanged.

### 4. The home page, before it is published (items 4002 to 4015)

Several items changed the hand-made pages' header, footer and picture tags, and
the home page's structured data. Compare with the live site side by side.

1. Open the live home page and the branch's, at a normal width and then narrow
   (about 400 pixels wide).
2. The look should be the same: the same colours, spacing and pictures. The
   header gains "Search" and "All downloads" (the second hides on a narrow
   screen); the footer gains "Learn" and "Find" cells.
3. Scroll the branch's page: pictures should load as you go and keep their
   place (the page must not jump as they appear).
4. In the page's source (View source), find `"@type": "SoftwareApplication"`.
   `softwareVersion` should be the version in the release notes' newest
   section and `downloadUrl` the address in data/core/latest.json (now the
   PyPI page, where before it was the site's #download section). Decide
   whether that is the address you want there.

### 5. The footer and header on small screens (items 4011, 4012, 4013)

1. At about 400 pixels wide, open /, /releases.html, /docs/gui.html and /404.html.
2. The header should fit without a sideways scroll, with the logo, Search and
   the other items you expect.
3. The footer should show every cell with no gap or overlap ("Also from
   Designmatix" spans two cells so the grid is full).

### 6. The 404 page on the live address (item 4012)

Only possible after publishing.

1. Open https://dxcad.designmatix.co.uk/no-such-page and then
   https://dxcad.designmatix.co.uk/docs/no-such-page.
2. Both should show the site's own 404 page, in the site's style, with its
   links working from either depth.

### 7. The download page says what you mean (item 4013)

data/core/latest.json names no downloadable file today, so the page lists none
and says so; it invents no size or checksum.

1. Read /download.html. Is the sentence about files right for what you want
   visitors to see?
2. When you have a file to offer, add `files` to the public latest.json (name,
   size, sha256, url), copy it into data/, run `python scripts/build_pages.py
   --all`, and read the page again.

Expected: today, the version, the date, the PyPI address and the plain
sentence that no file is named; later, each file with its size and checksum,
and how to check one.

### 8. The tutorial works on a clean machine (item 4006)

Its commands are checked against the docs, not run.

1. On a machine without DX-CAD, follow /tutorial.html word for word, every
   command and click.
2. Expected: you end with a bracket with four holes and a STEP file, and each
   number the page gives (volumes, hole centres) matches what you see.

### 9. The pages read right (items 4004, 4006, 4010, 4016, 4017)

The tests hold these to the public docs' words; only you can say whether the
words, taken alone, are what you want said in public.

1. /fabrication.html and /drafting-pro.html: no price, no promise you do not
   keep, the trial and licence words as in the window's help.
2. /faq.html: read every question and answer. Each answer should be a fair
   short answer, and each link should open the docs page at the right section.
3. /docs/limitations.html: ten pictures it names are not on the site, so each
   shows as its description in brackets. Decide whether you want them copied
   into data/ from the public SDK.
4. /shortcuts.html: try five shortcuts in the app, one from each menu, and the
   Mac key note.

### 10. The Atom feed (item 4008)

1. Open /releases.xml in a feed reader, or paste its address into an Atom
   validator.
2. Expected: one entry per release, newest first, each with its date, and the
   link opens the release on /releases.html.

### 11. The link preview (item 4007)

1. Paste the home page's live address into a chat or a post box that shows
   link previews.
2. Expected: the title, the description and the DX-CAD picture. Repeat with
   one made page, such as /gallery.html.

### 12. Printing a docs page (item 4014)

1. Open /docs/gui.html, then Print, Preview.
2. Expected: no header, footer or skip link; black text on white; a link to
   another site followed by its address; a table does not break across pages.

### 13. The picture weight (item 4001)

The home page's eight pictures total about 760 KB; seven load only as you
scroll, so the first load is about 160 KB.

1. Open the home page with developer tools' Network tab, with the cache off.
2. Expected: about 160 KB at first load; more as you scroll.
3. Decide whether to make the pictures themselves smaller (no image tool was
   available to do it).

### 14. Names the owner's rule forbids that were already on the site (audit, item 4019)

The rule is that no other CAD product, person or email address is named in the
repository. Three things predate this run and could not be changed without
editing the pages "as they are" or the read-only data/:

1. The home page's "Works beside ..." row and two later lines name another CAD
   product and its maker, as a trademark notice. Decide whether to keep them.
2. Every footer (and the home page's structured data) carries the company's
   support address. It was in the footer before the run; the build now writes
   the footer from one place, so to change it, change `FOOTER` in the script.
3. data/core/gui.md names a third-party software package (the one the 3D kernel
   comes from) in its About window row; it is shown as written on
   /docs/gui.html and in the search list.

Open each place named, and decide; none is a fault of the tests.

### 15. The owner's own steps (item 4005)

1. Follow README.md's three steps once with a copy of the data (add a fake
   release to the end of a copy of data/core/RELEASE_NOTES.md in a temporary
   folder and run the script with `--root`).
2. Expected: the new release's section, its feed entry and one sitemap date
   change, and nothing else.

## Part 2. What a test already checks

Run all of it with `python -m pytest -n 4 -q` (about 45 seconds) and
`python scripts/build_pages.py --check`. Each line names a test in
tests/test_pages.py (P) or tests/test_build_pages.py (B).

| What | Test |
|---|---|
| Every page parses, has one title, a description, a canonical link to its own address, lang en-GB | P `test_page_is_sound` |
| Every internal link, fragment and picture resolves | P `test_page_is_sound`, `test_missing_anchor_fails`, `test_copy_of_real_site_with_a_link_broken_fails` |
| Every picture has alt text, and it is not a file name | P `test_missing_alt_fails`, `test_file_name_as_alt_fails` |
| The sitemap lists exactly the pages (404 page left out), robots.txt names it | P `test_sitemap_and_robots`, `test_page_left_out_of_sitemap_fails`, `test_a_404_page_listed_in_the_sitemap_fails_naming_it` |
| No page is over 300 KB with its pictures | P `test_page_over_300_kb_with_its_pictures_fails`, `test_lazy_pictures_count_one_by_one` |
| Open Graph and Twitter tags on every page | P `test_every_real_page_has_the_social_tags`, `test_page_without_a_social_tag_fails` |
| Headings in order, one h1 | P `test_skipped_heading_level_fails_naming_page_and_rule`, `test_every_real_page_has_a_skip_link_and_one_h1` |
| A "Skip to content" link first on every page | P `test_page_without_a_skip_link_fails`, `test_skip_link_must_not_come_after_other_links` |
| Every link and button has a name | P `test_link_or_button_without_a_name_fails` |
| Text contrast 4.5 : 1 in the light and the dark theme | P `test_both_themes_reach_aa_contrast_on_every_page`, `test_low_contrast_text_fails_naming_the_rule` |
| Dark theme block on every page; print style on the docs pages | P `test_every_page_has_the_dark_theme_block_last_in_its_head`, `test_a_docs_page_has_a_print_style_that_hides_the_chrome_and_shows_addresses` |
| JSON-LD parses and names the version in data/ | P `test_software_json_ld_parses_and_names_the_version_in_data`, `test_the_release_notes_and_the_json_ld_name_the_same_version` |
| Every picture has its file's width and height; lazy after the first | P `test_every_picture_on_every_page_has_the_size_of_its_file_and_lazy_after_the_first`, `test_img_without_width_and_height_fails_naming_the_page_and_picture` |
| Made pages are as the script makes them | B `test_check_passes_on_the_committed_pages`, `test_a_made_page_that_is_edited_fails_check` |
| A release has its section, date and lines on the releases page | B `test_releases_page_has_a_section_and_date_for_every_release`, `test_every_line_of_the_notes_is_on_the_page` |
| The Atom feed: required elements, one entry per release, dated | B `test_feed_is_atom_with_its_required_elements`, `test_feed_has_one_entry_per_release_newest_first_with_its_date` |
| One page per example with picture and whole script; tags match the script's calls | B `test_example_page_has_picture_text_and_whole_script`, `test_each_examples_tags_match_the_calls_in_its_script` |
| Add-on pages: commands, trial and licence words are gui.md's; no price | B `test_addon_page_names_only_commands_that_gui_md_names`, `test_addon_page_trial_and_licence_words_are_guis`, `test_addon_page_has_no_price` |
| The tutorial's commands and numbers are the data's | B `test_tutorial_commands_all_appear_in_data`, `test_tutorial_numbers_are_the_data_s` |
| A page for each public doc with its headings, code blocks and table rows | B `test_each_doc_has_a_page_with_every_heading_and_code_block`, `test_every_table_row_of_the_docs_is_on_the_pages`, `test_docs_links_between_pages_work` |
| Search list covers every page with title and headings; the search page loads nothing from elsewhere | B `test_search_json_lists_every_page_in_the_sitemap_with_title_and_headings`, `test_search_page_is_plain_javascript_from_here_and_nothing_else` |
| The footer is the same on every page, and has the main links | B `test_every_pages_footer_is_the_same_and_has_the_main_links`, `test_a_footer_changed_by_hand_fails_check_and_all_puts_it_back` |
| The 404 page exists, is not in the sitemap, links from the root | B `test_404_page_exists_is_not_in_the_sitemap_or_the_search_list_and_is_not_indexed`, `test_404_page_links_to_the_main_pages_from_the_root_so_it_works_at_any_depth` |
| The download page lists exactly latest.json's files, sizes and checksums | B `test_download_page_lists_exactly_latest_jsons_files`, `test_download_page_lists_files_with_their_sizes_and_checksums`, `test_a_changed_latest_json_changes_the_page` |
| Every question has a link that goes to a page here; every limitation has its question | B `test_every_answers_link_goes_to_a_page_here_and_to_a_heading_on_it`, `test_every_limitation_in_limitations_md_has_its_question_linked_to_its_section` |
| The shortcuts page lists exactly gui.md's shortcuts, grouped as gui.md groups them | B `test_shortcuts_page_lists_exactly_the_shortcuts_in_gui_md`, `test_shortcuts_are_grouped_by_menu_in_the_order_gui_md_has_them` |
| The gallery's filter script reads the names the page writes; every example shows without JavaScript | B `test_the_filter_script_reads_the_tags_the_page_writes_and_sets_what_the_page_styles`, `test_with_no_javascript_every_example_shows_and_the_buttons_stay_hidden` |
| Made pages are ASCII, load nothing from elsewhere | B `test_made_page_is_plain_ascii_and_links_only_to_the_site`, `test_docs_pages_are_ascii_and_load_nothing_from_elsewhere` |
| `--all` with a new release changes only the release page, its feed and one sitemap date | B `test_all_with_a_new_release_adds_its_section_and_changes_nothing_else` |
| The script never changes data/ | B `test_the_script_does_not_touch_data` |
| README.md names the three steps and every file the script makes | B `test_readme_names_the_three_steps`, `test_readme_names_every_file_the_script_makes` |
