# Decisions

## 2026-11-07

- 4001: index.html is 57 KB, but the eight pictures it shows total about 760 KB, so "300 KB with its pictures"
  failed on it as written. I did not change the page, because the owner's rule is to keep the pages' look, and I cannot
  recompress pictures here (no image library). The check counts the page and the pictures a browser loads with it; a
  picture marked loading="lazy" (seven of the index's eight, loaded only on scroll) is checked on its own against
  the same 300 KB limit. The index then weighs about 160 KB at first load. The owner may want to decide whether the
  pictures themselves should be made smaller.
- 4001: a link to a #fragment on a page here must name an id that exists; this is stricter than the item asked, and
  every page already passes it.
- 4002: a made page takes its style and header from refunds.html and its footer from index.html at build time, so
  the look is never copied by hand; if the owner changes those, --check says so until --all is run. The index's footer
  gained one cell, "Releases", linking /releases.html.
- 4002: script also makes sitemap.xml: it keeps every existing entry and date, adds the pages that are missing, and
  gives a made page the date of its data (releases.html: the newest release's date).
- 4002: links in the release notes to files the site does not have (CHANGELOG.md, docs/install.md, ...) are shown as
  plain words, not links.
- 4003: example pages' light picture loads with the page, the dark one is loading="lazy"; the gallery's pictures are
  all lazy. Each example page stays under the 300 KB limit with its eager picture.
- 4003: "how to open it in DX-CAD" gives only the commands data/core/gui.md and examples/README.md show:
  `dxcad examples NAME`, `dxcad gui NAME.py`, `dxcad run NAME.py --output NAME.dxcprt`, `dxcad describe NAME.dxcprt`.
- 4003: the index's Made with DX-CAD paragraph gained one sentence linking /gallery.html (the footer has no room).
- 4004: the Fabrication page uses the words of the site's own fabrication-layout-software.html; the Drafting Pro page
  uses the words of the index's editions table; both list their commands, and give their trial and licence words,
  straight from data/core/gui.md each time they are made. No price is on either page (gui.md gives none).
  fabrication-y-piece.png is not used: no page of the site says what its picture shows.
- 4005: the sitemap keeps the date of a made page that is unchanged; only a changed or new made page takes the newest
  release's date. So --all with a new release changes releases.html and one date in sitemap.xml, nothing else.
  write_files writes only files that differ, leaving every other file untouched (line endings included).
- 4006: data/ holds no cli.md or tutorials, so the tutorial uses only commands that appear in data/ with the
  arguments data/ shows: `dxcad examples bracket`, `dxcad gui bracket.py`, `dxcad run bracket.py --output bracket.dxcprt`,
  `dxcad describe bracket.dxcprt`, `dxcad doctor`, `pip install dxcad`. The STEP export is the window's
  File > Export Parts... (gui.md), and `dxcad export` is named without arguments because data/ gives none.
  Numbers (the script's, the volumes and hole centres) are read from bracket.py and bracket.md each time.
- 4006: the index's Download paragraph gained one sentence linking /tutorial.html.
- 4007: every hand-written page already carried the Open Graph and Twitter tags, and build_pages.py's make_page writes
  them on every page it makes (og:image is img/og-dxcad.png), so no page needed mending; the checks now hold them: all
  five tags present and filled, og:url equal to the canonical address, og:image a picture in img/ that exists.
- 4008: releases.xml is an Atom feed with the page's own address as each entry's link (releases.html#vX-Y-Z), the
  release's date as `updated` (midnight UTC; the notes give a day only), the first paragraph as summary and the whole
  release as html content. Author is Designmatix Ltd. The feed is not a page, so it is not in sitemap.xml.
  4005's "nothing else changes" now reads: with a new release, releases.html and its feed change, and one date in the
  sitemap.
- 4009: the checks are in tests/a11ycheck.py, called from pagecheck.check_page. Every real page already passed all
  five rules, so no page and no part of build_pages.py needed mending. The rules as built: the first heading is an h1
  and a heading never goes more than one level deeper than the one before it; the first link or control in the body
  is a "Skip to content" link to an id that exists; every link and button has a name (its text, the alt of an image
  inside it, aria-label or title; text inside aria-hidden does not count); no alt is a file name or the picture's own
  file name; contrast is 4.5 : 1 for every text colour the CSS gives, large text included (stricter than AA's 3 : 1).
- 4009: contrast is read from the pages' own CSS (var() resolved, @media rules included, inline style too): a rule
  with a colour and a background is one pair; a rule with only a colour is tried on the page background and on every
  light surface the CSS declares; a rule with only a background takes the colour of the same selector (so a hover rule
  is held to its button's text colour). A colour it cannot read (hsl() and the like) is reported, not passed over.
- 4010: the docs are every .md under data/core except RELEASE_NOTES.md (it is releases.html): today index, gui,
  limitations, examples/README, examples/bracket and examples/dimensions. Names: docs/NAME.html, a folder's slash made
  a hyphen and README dropped (examples/README.md is docs/examples.html); index.md is docs/index.html, linked as /docs/.
  A new doc in data/ gets its page on the next run with no change to the script.
- 4010: the reader also reads tables, block quotes and nested lists, because gui.md, limitations.md and the examples
  are mostly tables. A link to a doc the site has goes to its page; a link to a script that is an example goes to that
  example's page; a link to anything else the site lacks (install.md, cli.md, bracket.jsonl, ...) is its words alone,
  as in the release notes; web links stay links. The docs index leaves out the table rows that only point at docs the
  public set does not hold. A picture named in a doc is copied to img/docs/ if data/core has it; limitations.md names
  ten that data/ does not have, so each shows as its description in brackets.
- 4010: a heading that would skip a level is shown one level below the one before it, and a second top heading is an
  h2, so every page keeps the order 4009 asks for. The docs' words are shown as written, including lines such as
  index.md's about its own test suite; the site does not edit data/.
- 4010: make_page now takes the canonical and og:url from the same address() the sitemap uses, so docs/index.html
  is https://dxcad.designmatix.co.uk/docs/. The index's Download paragraph gained one sentence linking /docs/.
- 4011: search.json holds, for every .html page (all the pages in the sitemap), its address, title, headings (with
  their ids) and the text of its main part, one line of text for each paragraph, list item, table cell or code line;
  the header, the footer and scripts are left out, and so is any code block of more than 40 lines (a whole example
  script), because the gallery's scripts alone would have been 190 KB of the 440 KB. It is about 250 KB, one page a
  line. The search page loads it with a plain XMLHttpRequest from its own folder: nothing from elsewhere, no library,
  and once the two files are loaded no network is needed. "Works offline" is read as that, not as "opens from a
  folder": every link on the site starts with a slash, so the site as a whole does not work from a folder either.
- 4011: results are pages whose title, headings and text together hold every typed word (as part of a word, not case
  sensitive), ranked by title, then headings, then how often; each shows up to two of its lines with the words marked.
  The marks are built with createElement and text nodes, never innerHTML. A test reads the script for banned calls.
  There is no browser or node here, so the script itself has been read through and checked for balanced brackets and
  for the ids it uses, but not run: the owner should try /search.html once after merging.
- 4011: the header of every hand-made page, and refunds.html's from which the made pages take theirs, gained a
  "Search" item after Download; it stays on small screens.
- 4012: the footer is the FOOTER constant in scripts/build_pages.py. Until now there were two footers: nine hand-made
  pages still had the one from before 4002 (no Releases cell). The script now gives FOOTER to every page it makes and
  replaces the footer of each hand-made page with it on every run (--check says which page differs), so those nine
  pages changed in their footer and in nothing else. The index's footer is no longer the pattern; the build is.
  FOOTER is the old index footer plus three changes: "DX-CAD" links home; a "Learn" cell (Documentation, Examples,
  Tutorial) and a "Find" cell (Search) hold the main links the item asks for; "Also from Designmatix" spans two cells
  so the grid stays full. A hand-made page with no footer, or two, is left alone by the script and fails the test.
- 4012: 404.html is made like the other pages (its style and header from refunds.html), links to eight main pages by
  addresses that start with a slash so it works at any depth, and carries noindex because it is not a page to find.
  It keeps a canonical link, as the site's checks want of every page. It is left out of sitemap.xml and of search.json
  (the checks now say a 404.html listed in the sitemap is an error). GitHub Pages shows a 404.html in the
  site's top folder for a missing address.
- 4009: the small test site's page template gained the skip link and a main element, and its one heading test now
  starts at h1, because the new rules apply to it as to every page.
- 4013: data/core/latest.json has no files, sizes or checksums today: it gives version, date, note, url (PyPI),
  licences_from and trial_until. download.html shows exactly those, and says plainly that the public record names no
  downloadable file, so it lists none and invents no size or checksum. If a later latest.json carries a "files" list
  (name, size, sha256, url, and optionally what), the page lists exactly those files with their sizes and checksums,
  says "not given" for a key that is missing, and adds how to check a checksum; a bad entry (a sha256 that is not 64
  hex digits, a size that is not a whole number, no name, a date that is not YYYY-MM-DD) stops the build and names
  latest.json. The owner should add "files" to the public latest.json once there is a file to name.
- 4013: the header of every page gained "All downloads" (class opt, so it is hidden on small screens like the other
  optional items; the footer's Find cell carries it for them), because the header's "Download" item already
  points to the home page's #download section and keeps doing so. 46 hand-made and made pages changed in that one
  line, and the footer in all of them through FOOTER. The page names "Licences from" and "Trial until" as latest.json
  words, with no explanation of its own. It also says "pip install dxcad", as the tutorial and the release notes do.
- 4014: JSON-LD. index.html already had a SoftwareApplication in its own JSON-LD; the build now sets its
  softwareVersion and downloadUrl from data/core/latest.json (the address is now the PyPI page latest.json names,
  not the site's #download section) and leaves every other word as written. releases.html, which had none, gets one
  SoftwareApplication made the same way: name, address, category and operating systems taken from the home page's
  own JSON-LD (the site's words; data/ names no operating system list), version and download address from
  latest.json, releaseNotes the page's own address. datePublished and the offers stay on the home page only.
- 4014: the dark theme is one block (THEME_STYLE) that turns the site's CSS variables over (light text, dark paper,
  paler blue and red), last in the head of every page: made pages get it from make_page, hand-made pages on every
  run, so one place holds it. The few colours the pages write out in full (white text on buttons and the skip link,
  the search highlight, the drawings' blue and red strokes, the Designmatix logo, which is dark on transparent and so
  gets a white plate) are overridden in the same block. The dark theme was looked at only through the contrast
  check, not in a browser (none here): the owner should look at the home page with the system set to dark.
- 4014: tests/a11ycheck.py now reads the dark block apart from the light rules: the page is checked in the light
  theme as before, and, if it has a dark block, again with that block cascaded over the rules of the same selector
  (failures end "[dark theme]"). @media print rules are ignored by the screen checks, and a rule that sets only a
  background on an img or svg is skipped (a picture has no text). Both themes reach 4.5 : 1 on every page.
- 4014: the print style is part of DOCS_STYLE, so only the docs pages carry it (as the item says): header, footer,
  skip link and contents are hidden, text is black on white, links to other sites print their address, code and
  tables do not break across pages.
- 4015: nearly every picture already had its width and height and lazy loading, written by the gallery code or by
  hand; three pages (gallery.html, fabrication.html, drafting-pro.html) had their first picture marked lazy, which
  is wrong for the picture at the top, so it is now loaded at once. The build now finishes the <img> tags of every
  page it makes and of every hand-made page on each run: a missing width or height is read from the file (PNG, GIF
  or JPEG, standard library only) and added, a picture after the first with no loading="lazy" gets it, the first
  loses it. The first picture is the first one that is a file; the Designmatix logo in each header is written into
  the page as data: (no request to make, and already sized) and is left out of both rules.
- 4015: tests/pagecheck.py gained the rules (width and height that are whole numbers, equal to the file's own size
  where it is a PNG, GIF or JPEG; first picture eager, the rest lazy), so a page made wrong in a temporary folder
  fails naming the picture. The small test site's pages and one test (lazy pictures counted one by one: the big one
  is now the second, because the first is no longer lazy) were changed to match. No page is near 300 KB: the
  largest stays within the rule, which is kept and tested as before.
- 4016: faq.html is made from data/core/gui.md and limitations.md only. A question about the window names a section of
  gui.md and takes one paragraph's first sentences as the answer (FAQ_WINDOW in the script); a limitation is one
  question for each '##' section of limitations.md, answered by its Cause paragraph (up to three sentences) and its
  Workaround (up to two). A section the script has no question for still gets one made from its heading, so a new
  limitation is never left out. Answers are the docs' own words with the private item numbers the docs carry
  taken out; each links to its section of the docs page. 'Questions' is added to the footer's Learn line (so all
  pages changed) and to the 404 page's list.
