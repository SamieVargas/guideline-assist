import json

from stubs import FakeClient, assist_out, reply

from core.assist import assist
from core.contracts import QA_STATUSES, assist_schema
from core.data import load_sample_file
from core.llm import call
from core.qa import qa_model, required_steps
from core.validate import citation_valid, validate_assist, validate_qa, validate_intent

HAIKU = "claude-haiku-4-5-20251001"
SONNET = "claude-sonnet-5"


# --- the validator ---------------------------------------------------------

def test_a_well_formed_assist_output_passes():
    assert validate_assist(assist_out("refund_initiate", "pull-up-account", ["rodriguez domingo"])) == []
    assert validate_assist(assist_out("unclear", "none_yet")) == []
    assert validate_assist(assist_out("refund_initiate", "none_yet")) == []


def test_ids_outside_the_enums_are_rejected():
    v = validate_assist(assist_out("refund_initiate", "pull-up-account", section="product_defect/refund_initiate") | {"intent": "refund_all"})
    assert any("not a subflow id" in x for x in v)
    v = validate_assist(assist_out("refund_initiate", "issue-refund"))
    assert any("not an action name" in x for x in v)


def test_a_section_that_does_not_exist_or_does_not_match_the_intent_is_rejected():
    v = validate_assist(assist_out("refund_initiate", "pull-up-account", section="product_defect/refund_everything"))
    assert any("does not exist" in x for x in v)
    v = validate_assist(assist_out("refund_initiate", "pull-up-account", section="order_issue/manage_cancel"))
    assert any("is not the section for intent" in x for x in v)
    assert not citation_valid(assist_out("refund_initiate", "pull-up-account", section="order_issue/manage_cancel"))


def test_a_next_action_the_section_does_not_list_is_rejected():
    v = validate_assist(assist_out("boots", "offer-refund"))
    assert any("is not listed in section single_item_query/boots" in x for x in v)


def test_unclear_intent_allows_no_section_and_no_action():
    v = validate_assist(assist_out("unclear", "pull-up-account", section="none"))
    assert any("must be 'none_yet'" in x for x in v)
    v = validate_assist(assist_out("unclear", "none_yet", section="account_access/recover_username"))
    assert any("section_id must be 'none'" in x for x in v)


def test_suggestion_is_one_line_and_values_are_empty_on_none_yet():
    v = validate_assist(assist_out("boots", "none_yet", ["x"]))
    assert any("slot_values must be empty" in x for x in v)
    v = validate_assist(assist_out("boots", "search-faq", suggestion="line one\nline two"))
    assert any("one line" in x for x in v)


def test_arm_b_rejects_a_section_it_was_not_shown():
    out = assist_out("refund_initiate", "pull-up-account")
    assert validate_assist(out, allowed_sections={"product_defect/refund_update"}) != []


def test_intent_validator():
    assert validate_intent({"intent": "boots"}) == []
    assert validate_intent({"intent": "unclear"}, allow_unclear=False) != []


def test_qa_validator_needs_every_step_once_pointing_at_real_action_turns():
    conv = load_sample_file()[0]
    req = required_steps(conv["subflow"])
    first = {}
    for t in conv["turns"]:
        if t["speaker"] == "action":
            first.setdefault(t["action"], t["i"])
    good = {"steps": [{"action": a, "status": "followed" if a in first else "missed", "turn": first.get(a), "note": ""} for a in req]}
    assert validate_qa(good, turns=conv["turns"], required_actions=req) == []
    bad = {"steps": good["steps"][:-1] + [{**good["steps"][-1], "status": "followed", "turn": 0}]}
    assert any("is not an ACTION" in x or "must point at a turn" in x for x in validate_qa(bad, turns=conv["turns"], required_actions=req))
    assert any("appears 0 times" in x for x in validate_qa({"steps": good["steps"][1:]}, turns=conv["turns"], required_actions=req))


# --- the call wrapper --------------------------------------------------------

def test_native_contract_sends_the_schema_and_a_cached_library_prefix():
    client = FakeClient([assist_out("unclear", "none_yet")])
    out, meta = assist(client, [], arm="A", model=HAIKU)
    req = client.requests[0]
    assert req["output_config"]["format"]["type"] == "json_schema"
    assert req["output_config"]["format"]["schema"] == assist_schema()
    assert req["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert "SECTION product_defect/refund_initiate" in req["system"][0]["text"]
    assert meta["valid"] and meta["calls"] == 1 and out["intent"] == "unclear"


def test_sonnet_requests_turn_thinking_off():
    client = FakeClient([assist_out("unclear", "none_yet")])
    assist(client, [], arm="A", model=SONNET)
    assert client.requests[0]["thinking"] == {"type": "disabled"}


def test_prompt_contract_has_no_schema_and_recovers_fenced_json():
    fenced = "```json\n" + json.dumps(assist_out("unclear", "none_yet")) + "\n```"
    client = FakeClient([fenced])
    out, meta = assist(client, [], arm="A", model=HAIKU, contract="prompt")
    assert "output_config" not in client.requests[0]
    assert "Respond ONLY with one JSON object" in json.dumps(client.requests[0]["system"])
    assert meta["parse_paths"] == ["recovered"] and meta["valid"]


def test_one_reject_and_retry_names_the_violation():
    bad = assist_out("boots", "offer-refund")
    good = assist_out("boots", "search-faq")
    client = FakeClient([bad, good])
    out, meta = assist(client, [], arm="A", model=HAIKU)
    assert meta["retries"] == 1 and meta["valid"] and out["next_action"] == "search-faq"
    retry_msg = client.requests[1]["messages"][-1]["content"]
    assert "offer-refund" in retry_msg and "not listed" in retry_msg
    assert meta["first_violations"]


def test_after_the_one_retry_the_last_output_stands_flagged():
    bad = assist_out("boots", "offer-refund")
    client = FakeClient([bad, bad])
    out, meta = assist(client, [], arm="A", model=HAIKU)
    assert not meta["valid"] and meta["retries"] == 1 and out["next_action"] == "offer-refund"
    assert len(client.requests) == 2


def test_usage_and_cost_include_cache_reads():
    client = FakeClient([reply(assist_out("unclear", "none_yet"), cache_read=25000)])
    _, meta = assist(client, [], arm="A", model=HAIKU)
    assert meta["usage"]["cache_read_input_tokens"] == 25000
    # 120 in at $1 + 25,000 cache reads at $0.10 + 60 out at $5, per million
    assert abs(meta["cost_usd"] - (120 * 1 + 25000 * 0.1 + 60 * 5) / 1e6) < 1e-9


def test_arm_b_stops_after_the_intent_call_when_unclear():
    client = FakeClient([{"intent": "unclear"}])
    out, meta = assist(client, [], arm="B", model=HAIKU)
    assert meta["calls"] == 1 and out["next_action"] == "none_yet"


def test_arm_b_puts_only_the_one_section_in_context():
    client = FakeClient([{"intent": "refund_initiate"}, assist_out("refund_initiate", "pull-up-account", ["a b"])])
    out, meta = assist(client, [], arm="B", model=HAIKU)
    sys2 = json.dumps(client.requests[1]["system"])
    assert "SECTION product_defect/refund_initiate" in sys2 and "SECTION product_defect/refund_update" not in sys2
    assert "cache_control" not in sys2
    assert client.requests[1]["output_config"]["format"]["schema"]["properties"]["section_id"]["enum"] == ["product_defect/refund_initiate", "none"]
    assert meta["calls"] == 2 and out["next_action"] == "pull-up-account"


def test_disk_cache_serves_a_repeat_and_marks_it(tmp_path):
    client = FakeClient([assist_out("unclear", "none_yet")])
    _, m1 = assist(client, [], arm="A", model=HAIKU)
    _, m2 = assist(client, [], arm="A", model=HAIKU)
    assert len(client.requests) == 1 and not m1["from_cache"] and m2["from_cache"]
    client2 = FakeClient([assist_out("unclear", "none_yet")])
    assist(client2, [], arm="A", model=HAIKU, tag="run1")
    assert len(client2.requests) == 1  # a different tag is a different call


def test_qa_model_returns_one_status_per_required_step():
    conv = load_sample_file()[0]
    req = required_steps(conv["subflow"])
    first = {}
    for t in conv["turns"]:
        if t["speaker"] == "action":
            first.setdefault(t["action"], t["i"])
    payload = {"steps": [{"action": a, "status": "followed" if a in first else "missed", "turn": first.get(a), "note": ""} for a in req]}
    st, meta = qa_model(FakeClient([payload]), conv, model=SONNET)
    assert meta["valid"] and set(st) == set(req) and all(s["status"] in QA_STATUSES for s in st.values())


def test_call_rejects_an_unknown_contract():
    import pytest
    with pytest.raises(ValueError):
        call(FakeClient([]), model=HAIKU, system="x", user="y", schema={}, validator=lambda o: [], contract="xml")
