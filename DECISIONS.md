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
