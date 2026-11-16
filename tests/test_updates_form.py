"""Item 4022: the optional "Email me updates" form beside the download buttons."""
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACTION = "https://licence.designmatix.co.uk/v1/updates/subscribe"


class Forms(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms, self.current, self.labels, self.scripts = [], None, {}, 0
        self.label_for = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "form":
            self.current = {"attrs": a, "inputs": [], "links": [], "label_fors": []}
            self.forms.append(self.current)
        elif self.current is not None and tag == "input":
            self.current["inputs"].append(a)
        elif self.current is not None and tag == "label" and "for" in a:
            self.current["label_fors"].append(a["for"])
        elif self.current is not None and tag == "a":
            self.current["links"].append(a.get("href", ""))
        elif tag == "script" and self.current is not None:
            self.scripts += 1

    def handle_endtag(self, tag):
        if tag == "form":
            self.current = None


def the_form():
    p = Forms()
    p.feed((ROOT / "index.html").read_text(encoding="utf-8"))
    found = [f for f in p.forms if f["attrs"].get("action") == ACTION]
    assert len(found) == 1, "one updates form on the home page"
    return found[0], p


def test_the_form_posts_to_the_service_over_https():
    form, _ = the_form()
    assert form["attrs"].get("method") == "post"
    assert form["attrs"]["action"].startswith("https://")


def test_the_email_field_is_labelled_required_and_named_email():
    form, _ = the_form()
    emails = [i for i in form["inputs"] if i.get("type") == "email"]
    assert len(emails) == 1
    field = emails[0]
    assert field.get("name") == "email" and "required" in field and field.get("maxlength") == "254"
    assert field.get("id") in form["label_fors"]


def test_the_hidden_trap_field_is_there_and_out_of_the_tab_order():
    form, _ = the_form()
    traps = [i for i in form["inputs"] if i.get("name") == "website"]
    assert len(traps) == 1 and traps[0].get("tabindex") == "-1"


def test_no_script_and_the_privacy_notice_is_linked():
    form, parser = the_form()
    assert parser.scripts == 0
    assert any(h.startswith("/privacy.html") for h in form["links"])
    assert 'id="updates"' in (ROOT / "privacy.html").read_text(encoding="utf-8")
