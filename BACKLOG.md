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
- [ ] 4003. A gallery: every example of DX-CAD with its picture and its script (M)
  The examples (data/core/examples, with their pictures in data/core/gallery) show what a model.py is: a page each
  sells the "model as a script" idea better than a paragraph.
  - gallery.html: every example's picture with its one-line description (the script's first docstring line); a page
    each, examples/NAME.html: the picture (light, and the dark one where there is one), the description, the whole
    script shown as text (escaped), and how to open it in DX-CAD. Pictures copied into img/gallery/ by the script.
  - Made by scripts/build_pages.py; in the sitemap; linked from the index.
  Accept: tests/test_build_pages.py: one page per example in data/core/examples, each with its picture, its text and
  its whole script; --check passes; tests/test_pages.py passes.
- [ ] 4004. A page for each add-on, Fabrication and Drafting Pro, from what is public already (S)
  - fabrication.html and drafting-pro.html: what each does in plain words, its commands and its trial and licence
    words, taken only from what the site's own pages and data/core/gui.md already say (nothing from the add-ons'
    private repositories); pictures already in img/ where they fit; linked from the index and from each other; in
    the sitemap. Made by scripts/build_pages.py.
  Accept: tests/test_build_pages.py: each page's trial and licence words are the ones in data/core/gui.md; every
  command named on a page is named in data/core/gui.md; --check passes; tests/test_pages.py passes.
- [ ] 4005. A release refresh in one command, and how to publish, for the owner (S)
  - scripts/build_pages.py --all remakes every page made from data/ and the sitemap; README.md says, in plain words,
    how the owner refreshes data/ (DX-CAD's release notes and the public SDK's docs) after a release, runs the script and the tests,
    and publishes (merge into main; GitHub Pages serves main).
  Accept: tests/test_build_pages.py: --all on a copy with a new release added to data/ adds its section to
  releases.html and nothing else changes; README.md names the three steps.

- [ ] 4006. "Your first part in ten minutes": a tutorial page from the public SDK docs (S)
  - tutorial.html: from installing DX-CAD to a bracket with four holes exported as STEP, every command and number as
    data/ (the release notes and the public SDK docs) gives them; nothing from a private repository. Made by
    scripts/build_pages.py, in the sitemap, linked from the index.
  Accept: tests/test_build_pages.py: every command on the page appears in data/; --check passes; tests/test_pages.py
  passes.

- [ ] 4007. Every page carries Open Graph and Twitter card tags, and the checks hold them (S)
  - og:title, og:description, og:url (its canonical address), og:image (a picture already in img/) and twitter:card on
    every page, made by scripts/build_pages.py where it makes the page.
  Accept: tests/test_pages.py fails on a page without them (made in a temporary folder) and passes on every page.

- [ ] 4008. An Atom feed of the release pages (S)
  - releases.xml: one entry per release from data/core/RELEASE_NOTES.md, newest first, linked from releases.html's
    head; made by scripts/build_pages.py (standard library only).
  Accept: tests/test_build_pages.py: the feed parses as Atom with its required elements, one entry per release with
  its date; --check passes; tests/test_pages.py passes.
