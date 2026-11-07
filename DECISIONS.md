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
