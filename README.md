# DX-CAD's website

This is the source of https://dxcad.designmatix.co.uk/. It is plain HTML and
CSS, served by GitHub Pages from the main branch. There is no framework, no
build step you must run to read a page, no tracking and no script from anyone
else.

Some pages are written by hand: the home page, the product pages, the
licence, refund and privacy pages, and the SDK pages. The others are made by
`scripts/build_pages.py` from the files in `data/`, and must not be edited by
hand (the next run would write over the edit):

- `releases.html` and `releases.xml`, the release page and its Atom feed, from
  DX-CAD's release notes
- `gallery.html`, `examples/NAME.html` and the pictures in `img/gallery/`,
  from the examples and their pictures; the buttons that filter the gallery
  read each example's tags from its script
- `fabrication.html` and `drafting-pro.html`, from the window's help
  (`gui.md`) and the site's own words
- `tutorial.html`, the first-part tutorial, from the public docs
- `docs/NAME.html`, one page for each public SDK doc in `data/core/` (`index.md`
  is `docs/index.html`), and the pictures a doc names that are in `data/core/`
- `download.html`, from `latest.json`
- `faq.html`, the questions page, from `limitations.md` and `gui.md`
- `shortcuts.html`, the keyboard shortcuts, from the table in `gui.md`
- `search.html` and `search.json`, the search page and the list of every page,
  its headings and its words that the page reads
- `404.html`, the page GitHub Pages shows for an address that is not here (it is
  left out of the sitemap and the search)
- `sitemap.xml`, which lists every page

The footer of every page is written once, in `scripts/build_pages.py` (`FOOTER`).
The script gives it to the pages it makes and, on every run, puts it in place of
the footer of the hand-made pages, so change the footer there and nowhere else.
The script also finishes every picture tag (its width and height, and lazy
loading below the first picture), adds the dark theme to every page, and sets
the version and download address in the home page's structured data from
`latest.json`.

## After a DX-CAD release: three steps

1. **Refresh `data/`.** Copy in DX-CAD's release notes (`data/core/RELEASE_NOTES.md`,
   written for users) and, from the public DX-CAD-SDK repository, its examples,
   their pictures, `gui.md`, `index.md`, `limitations.md` and `latest.json`
   (all under `data/core/`). Copy them as they are. Nothing else from any
   private repository goes into this one.

2. **Make the pages and run the tests.** From the top folder:

   ```
   python scripts/build_pages.py --all
   python -m pytest -n 4 -q
   ```

   `--all` remakes every page made from `data/`, and the sitemap. A page that
   did not change keeps its date in the sitemap. To ask only whether the
   pages are as they should be, without writing anything, run
   `python scripts/build_pages.py --check`. The tests check every page: its
   title, description and canonical link, that every link and picture
   resolves, that every picture has alt text, and that the sitemap lists
   exactly the pages there are.

3. **Publish.** Review the change, commit it on a branch, and merge the
   branch into `main`. GitHub Pages serves `main`, so the merge is the
   publishing; the site changes a minute or two later.

## Notes

- The script uses only Python's standard library. Python 3.12 and pytest are
  for the script and its tests only.
- If the script stops with a message, it names the file in `data/` that it
  could not use, for example an example with no picture, or a release with no
  date in its first paragraph. Mend that file's source, copy it in again and
  rerun.
- The made pages take their style and header from `refunds.html` and their
  footer from `FOOTER` in the script. If you change either, run `--all` so the
  made pages follow.
- The tests also read the pages' words and markup, so a hand-made page that
  loses its title, its canonical link, its skip link or a picture's alt text
  fails them; `docs/qa/owner-checks.md` lists what only a person in a browser
  can check.
- Never edit `CNAME`: it holds the site's address.
