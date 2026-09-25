import copy

import pytest

from core import samples
from core.data import load_sample_file
from core.metrics import cohen_kappa, confused_pairs, macro_f1, percentile
from core.perturb import perturb
from core.points import (action_points, compliant, guideline_next, no_action_candidates, no_action_points, norm_value,
                         points_for, value_recall, values_match)
from core.qa import qa_rules, required_steps


def synthetic(subflow="refund_initiate"):
    """A compliant refund conversation built from the sample file's shape."""
    req = required_steps(subflow)
    turns = [{"speaker": "agent", "text": "Hi, how can I help?"},
             {"speaker": "customer", "text": "I want a refund. I'm Rodriguez Domingo, order 3764775976, it was $84."}]
    vals = {"pull-up-account": ["rodriguez domingo"], "validate-purchase": ["rd542657", "rd542657@email.com", "3764775976"],
            "record-reason": ["credit card"], "enter-details": ["3764775976"], "offer-refund": ["84"]}
    for a in req:
        turns.append({"speaker": "agent", "text": f"Let me do {a}."})
        turns.append({"speaker": "action", "text": f"{a} done", "action": a, "values": vals.get(a, [])})
    turns.append({"speaker": "customer", "text": "Credit card please, rd542657@email.com, username rd542657."})
    turns.append({"speaker": "agent", "text": "Anything else?"})
    for n, t in enumerate(turns):
        t["i"] = n
        t.setdefault("action", None)
        t.setdefault("values", None)
    return {"id": "900001", "subflow": subflow, "flow": "product_defect", "turns": turns, "scenario": {}, "scenario_subflow": subflow}


def test_points_split_action_and_no_action_turns():
    c = synthetic()
    assert action_points(c) == [t["i"] for t in c["turns"] if t["speaker"] == "action"]
    for i in no_action_candidates(c):
        assert c["turns"][i]["speaker"] == "agent"
        assert i + 1 == len(c["turns"]) or c["turns"][i + 1]["speaker"] != "action"
    assert no_action_points(c, 1) == no_action_points(c, 1)
    pts = points_for(c, 1)
    assert [p["i"] for p in pts] == sorted(p["i"] for p in pts)


def test_guideline_next_walks_the_required_order():
    c = synthetic()
    req = required_steps("refund_initiate")
    assert guideline_next(c, 0) == req[0]
    last_action = action_points(c)[-1]
    assert guideline_next(c, last_action) == req[-1]
    assert guideline_next(c, last_action + 1) is None
    assert compliant(c)


def test_value_normalisation():
    assert norm_value(" $84 ") == "84" and norm_value("84.00") == "84"
    assert values_match(["Rodriguez  Domingo"], ["rodriguez domingo"])
    assert not values_match(["a"], ["a", "b"])
    assert value_recall(["a"], ["a", "b"]) == 0.5 and value_recall([], []) is None


def test_every_perturbation_keeps_its_twin_and_one_defect():
    c = synthetic()
    for kind, expected in (("remove", "missed"), ("swap", "out_of_order"), ("value", "wrong_value")):
        p = perturb(c, kind, 7)
        assert p is not None, kind
        assert p["twin"] == c["id"] and p["id"] == f"{c['id']}~{kind}"
        assert p["perturbation"]["expected"] == expected
        assert [t["i"] for t in p["turns"]] == list(range(len(p["turns"])))
        assert perturb(c, kind, 7) == p  # seeded
    assert c == synthetic()  # the twin is untouched


def test_remove_drops_the_step_and_its_announcing_line():
    c = synthetic()
    p = perturb(c, "remove", 7)
    a = p["perturbation"]["actions"][0]
    assert not any(t["action"] == a for t in p["turns"])
    assert len(p["turns"]) == len(c["turns"]) - 2
    assert not any(t["text"] == f"Let me do {a}." for t in p["turns"])


def test_the_rule_qa_catches_removed_and_swapped_steps():
    c = synthetic()
    assert all(s["status"] == "followed" for s in qa_rules(c).values())
    for kind in ("remove", "swap"):
        p = perturb(c, kind, 7)
        st = qa_rules(p)
        assert any(st[a]["status"] == p["perturbation"]["expected"] for a in p["perturbation"]["actions"]), kind


def test_value_perturbation_changes_a_value_the_customer_typed():
    c = synthetic()
    p = perturb(c, "value", 7)
    a = p["perturbation"]["actions"][0]
    before = next(t for t in c["turns"] if t["action"] == a)["values"]
    after = next(t for t in p["turns"] if t["action"] == a)["values"]
    assert before != after


def test_metrics():
    assert percentile([1, 2, 3, 4, 100], 50) == 3 and percentile([1, 2, 3, 4, 100], 95) == 100
    assert macro_f1(["a", "a", "b"], ["a", "a", "b"]) == 1.0
    assert macro_f1(["a", "b"], ["b", "a"]) == 0.0
    assert confused_pairs(["a", "b", "a"], ["b", "a", "a"]) == [(("a", "b"), 2)]
    assert cohen_kappa(["x", "y"], ["x", "y"]) == 1.0


def test_samples_are_frozen_and_hash_checked(tmp_path, monkeypatch):
    monkeypatch.setattr(samples, "SAMPLES", tmp_path)
    rec = samples.draw("t", [str(i) for i in range(50)], n=5, seed=3, split="test")
    assert samples.load("t")["ids"] == rec["ids"]
    with pytest.raises(FileExistsError):
        samples.draw("t", [str(i) for i in range(50)], n=5, seed=4, split="test")
    import json
    p = tmp_path / "t.json"
    d = json.loads(p.read_text())
    d["ids"][0] = "999"
    p.write_text(json.dumps(d))
    with pytest.raises(ValueError):
        samples.load("t")


def test_the_real_sample_conversations_score_without_error():
    for c in load_sample_file():
        c = copy.deepcopy(c)
        points_for(c, 1)
        qa_rules(c)


def test_typed_qa_statuses_are_normalised():
    from qa_agreement import norm_status
    assert norm_status(" Out-of-order ") == "out_of_order"
    assert norm_status("out of order") == "out_of_order"
    assert norm_status("wrong_value") == "wrong_value"
