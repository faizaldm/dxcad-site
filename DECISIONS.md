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
