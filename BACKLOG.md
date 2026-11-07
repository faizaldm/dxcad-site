# Backlog: DX-CAD's website

Written by the owner. Each item: what to build, then the Accept line its tests check.

- [x] 4001. The site's checks: every page parses, every link and picture resolves, the sitemap matches the pages (S)
  The site has no tests. A link or a picture renamed in one page breaks quietly.
  - tests/test_pages.py: every .html page parses (html.parser), has one title, a meta description, a canonical link
    to its own address on https://dxcad.designmatix.co.uk/, lang="en-GB"; every internal href and src resolves to a
    file here; every img has alt text; sitemap.xml lists exactly the pages a visitor can reach (and robots.txt names
    it); no page is over 300 KB with its pictures.
  - Whatever fails on the pages as they are is mended in the pages, each mend named in REPORT.md.
  Accept: tests/test_pages.py passes on every page; a page with a broken link, a missing alt or a page left out of
  the sitemap (made in a temporary folder) fails it, naming the page and the reason.
- [x] 4002. Release pages: what each DX-CAD release brought, in plain words, made from the release notes (S)
  - scripts/build_pages.py (standard library only) makes releases.html from data/core/RELEASE_NOTES.md: one section
    per release, newest first, its date and its lines in plain words, linked from the index's footer and in the
    sitemap. --check answers whether every page it makes is as committed.
  Accept: tests/test_build_pages.py: releases.html is what the script makes from data/ (--check passes); it has a
  section for every release in data/core/RELEASE_NOTES.md with its date; changing a line of a copy of the data in a
  temporary folder changes the page. tests/test_pages.py passes.
- [x] 4003. A gallery: every example of DX-CAD with its picture and its script (M)
  The examples (data/core/examples, with their pictures in data/core/gallery) show what a model.py is: a page each
  sells the "model as a script" idea better than a paragraph.
  - gallery.html: every example's picture with its one-line description (the script's first docstring line); a page
    each, examples/NAME.html: the picture (light, and the dark one where there is one), the description, the whole
    script shown as text (escaped), and how to open it in DX-CAD. Pictures copied into img/gallery/ by the script.
  - Made by scripts/build_pages.py; in the sitemap; linked from the index.
  Accept: tests/test_build_pages.py: one page per example in data/core/examples, each with its picture, its text and
  its whole script; --check passes; tests/test_pages.py passes.
- [x] 4004. A page for each add-on, Fabrication and Drafting Pro, from what is public already (S)
  - fabrication.html and drafting-pro.html: what each does in plain words, its commands and its trial and licence
    words, taken only from what the site's own pages and data/core/gui.md already say (nothing from the add-ons'
    private repositories); pictures already in img/ where they fit; linked from the index and from each other; in
    the sitemap. Made by scripts/build_pages.py.
  Accept: tests/test_build_pages.py: each page's trial and licence words are the ones in data/core/gui.md; every
  command named on a page is named in data/core/gui.md; --check passes; tests/test_pages.py passes.
- [x] 4005. A release refresh in one command, and how to publish, for the owner (S)
  - scripts/build_pages.py --all remakes every page made from data/ and the sitemap; README.md says, in plain words,
    how the owner refreshes data/ (DX-CAD's release notes and the public SDK's docs) after a release, runs the script and the tests,
    and publishes (merge into main; GitHub Pages serves main).
  Accept: tests/test_build_pages.py: --all on a copy with a new release added to data/ adds its section to
  releases.html and nothing else changes; README.md names the three steps.

- [x] 4006. "Your first part in ten minutes": a tutorial page from the public SDK docs (S)
  - tutorial.html: from installing DX-CAD to a bracket with four holes exported as STEP, every command and number as
    data/ (the release notes and the public SDK docs) gives them; nothing from a private repository. Made by
    scripts/build_pages.py, in the sitemap, linked from the index.
  Accept: tests/test_build_pages.py: every command on the page appears in data/; --check passes; tests/test_pages.py
  passes.

- [x] 4007. Every page carries Open Graph and Twitter card tags, and the checks hold them (S)
  - og:title, og:description, og:url (its canonical address), og:image (a picture already in img/) and twitter:card on
    every page, made by scripts/build_pages.py where it makes the page.
  Accept: tests/test_pages.py fails on a page without them (made in a temporary folder) and passes on every page.

- [x] 4008. An Atom feed of the release pages (S)
  - releases.xml: one entry per release from data/core/RELEASE_NOTES.md, newest first, linked from releases.html's
    head; made by scripts/build_pages.py (standard library only).
  Accept: tests/test_build_pages.py: the feed parses as Atom with its required elements, one entry per release with
  its date; --check passes; tests/test_pages.py passes.

- [x] 4009. Accessibility checks on every page: headings in order, contrast, a skip link, named links and buttons (S)
  - tests/test_pages.py also checks: headings never skip a level; the text and background colours the site's CSS gives
    each kind of text reach WCAG AA contrast (computed in the test); every page starts with a "Skip to content" link;
    every link and button has a name a screen reader can say; no img alt is a file name. Whatever fails is mended in
    the pages or in scripts/build_pages.py, each mend named in REPORT.md.
  Accept: tests/test_pages.py passes on every page and fails, naming the page and the rule, on a page made wrong in a
  temporary folder for each rule.

- [x] 4010. The public SDK's docs as pages of the site, made from data/ (M)
  - docs/NAME.html for each public SDK doc in data/ (its index, gui, limitations and the rest copied there), made by
    scripts/build_pages.py with a small Markdown reader of its own (standard library only: headings, paragraphs,
    lists, code blocks, links, emphasis), in the site's style, links between them made to work, a docs index linked
    from the main page, all in the sitemap. Public material only.
  Accept: tests/test_build_pages.py: a page for each doc in data/, each heading and code block of the source there;
  --check passes; tests/test_pages.py passes.

- [x] 4011. A search page that works with no server and no library (M)
  - search.json made by scripts/build_pages.py (each page's title, address, headings and words), and search.html with
    plain JavaScript: results as you type, the matching words shown in their sentence; it works offline from the files
    alone. Linked from every page's header.
  Accept: tests/test_build_pages.py: search.json lists every page in the sitemap with its title and headings; the page
  loads no script from elsewhere; --check passes; tests/test_pages.py passes.

- [x] 4012. A 404 page and one footer on every page, made by the build (S)
  - 404.html in the site's style with links to the main pages (GitHub Pages serves it for a missing address); every
    page's footer the same, from one place in scripts/build_pages.py.
  Accept: tests/test_build_pages.py: every page's footer is the same and has the main links; 404.html exists and is
  left out of the sitemap; --check passes; tests/test_pages.py passes.

- [x] 4013. A download page from the public latest.json: version, files, sizes and checksums (S)
  - download.html made by scripts/build_pages.py from data/'s latest.json: the current version and date, each file
    with its size and its SHA-256 where latest.json gives one, and what to do with each; linked from every header; in
    the sitemap.
  Accept: tests/test_build_pages.py: the page lists exactly latest.json's files with their sizes and checksums; a
  changed latest.json in a temporary folder changes the page; --check passes; tests/test_pages.py passes.

- [ ] 4014. Structured data on the main and release pages, and a dark theme that follows the system (S)
  - JSON-LD (schema.org SoftwareApplication) on index.html and releases.html with the name, the operating systems, the
    version and the download address from data/; a prefers-color-scheme: dark style that keeps 4009's contrast; a
    print style for the docs pages.
  Accept: tests/test_pages.py: the JSON-LD parses and names the version in data/; both themes reach AA contrast by
  4009's check; --check passes.

- [ ] 4015. Pictures sized for the web: each img with its width and height, lazy loading below the fold (S)
  - Every img gets width and height (read from the file by the standard library), loading="lazy" except the first
    picture of a page, and no page over 300 KB with its pictures (4001's rule) kept.
  Accept: tests/test_pages.py fails on an img without width and height and passes on every page; --check passes.
