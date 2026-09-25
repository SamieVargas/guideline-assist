import json

from core import enums
from core.data import load_sample_file, render_turn
from core.enums import ACTIONS, SUBFLOWS
from core.guidelines import (ROOT, library, render_library, render_section, resolve_button, section_id,
                             subflow_sections)


def test_committed_enums_match_the_ontology():
    from gen_enums import render
    assert (ROOT / "core" / "enums.py").read_text(encoding="utf-8") == render()


def test_enums_are_the_ontology_sizes():
    assert len(SUBFLOWS) == 55 and len(set(SUBFLOWS)) == 55
    assert len(ACTIONS) == 30
    o = json.loads((ROOT / "data" / "abcd" / "ontology.json").read_text(encoding="utf-8"))
    assert set(SUBFLOWS) == {s for v in o["intents"]["subflows"].values() for s in v}
    assert len(enums.FLOWS) == 10


def test_one_section_per_subflow_with_stable_ids():
    secs = subflow_sections()
    assert len(secs) == 55
    assert set(secs) == {section_id(s) for s in SUBFLOWS}
    assert section_id("refund_initiate") == "product_defect/refund_initiate"
    assert library()["product_defect/refund_initiate"]["title"] == "Product Defect / Initiate Refund"
    assert library()["account_access/reset_2fa"]["title"].endswith("Reset Two-Factor Auth")


def test_every_required_action_is_listed_and_known():
    for s in subflow_sections().values():
        assert s["required_actions"], s["id"]
        assert set(s["required_actions"]) <= set(s["listed_actions"]) <= set(ACTIONS)


def test_buttons_resolve_by_name_tokens():
    assert resolve_button("Pull up Account") == "pull-up-account"
    assert resolve_button("Log Out/In") == "log-out-in"
    assert resolve_button("Notify Internal Team") == "notify-team"
    assert resolve_button("Membership Privileges") == "membership"
    assert resolve_button("Membership", prefer=["search-faq", "search-membership", "select-faq"]) == "search-membership"
    assert resolve_button("Search FAQ", prefer=["search-faq", "search-boots"]) == "search-faq"
    assert resolve_button("N/A") is None
    assert resolve_button("End Conversation") is None


def test_library_render_is_deterministic_and_contains_every_section():
    a, b = render_library(), render_library()
    assert a == b
    for sid in subflow_sections():
        assert f"SECTION {sid} ::" in a
    assert "Required action sequence: pull-up-account -> validate-purchase" in render_section("product_defect/refund_initiate")


def test_sample_file_parses_and_actions_show_their_values():
    convs = load_sample_file()
    assert len(convs) == 3
    for c in convs:
        assert c["subflow"] in SUBFLOWS
        acts = [t for t in c["turns"] if t["speaker"] == "action"]
        assert acts and all(t["action"] in ACTIONS for t in acts)
    t = next(t for t in convs[0]["turns"] if t["speaker"] == "action" and t["values"])
    assert t["values"][0] in render_turn(t)


def test_full_library_style_is_byte_identical_to_the_parts_3_4_prompt():
    import hashlib
    assert hashlib.sha256(render_library().encode("utf-8")).hexdigest() == \
        "011fbe9af04070530026ac9b7a55fff1405b6be5d46542817e3e9a944e098384"
    assert render_library("full") == render_library()


def test_every_library_style_keeps_headers_sequences_and_listed_actions():
    from core.guidelines import LIBRARY_STYLES
    sizes = [len(render_library(s)) for s in LIBRARY_STYLES]
    assert sizes == sorted(sizes, reverse=True) and len(set(sizes)) == len(sizes)
    for style in LIBRARY_STYLES:
        text = render_library(style)
        for sid, s in subflow_sections().items():
            sec = render_section(sid, style)
            assert f"SECTION {sid} ::" in sec and sec in text
            assert "Required action sequence: " + " -> ".join(s["required_actions"]) in sec
            for a in s["listed_actions"]:
                assert a in sec, (style, sid, a)
