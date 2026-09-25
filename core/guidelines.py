"""The guideline library: guidelines.json plus kb.json, one section per flow
and one per subflow, each with a stable id.

Section ids are `<flow>` and `<flow>/<subflow>`, built from the ontology ids,
so they cannot drift from the enums. guidelines.json names flows and
subflows in display text ("Product Defect", "Initiate Refund"); the mapping
to ontology ids is derived, not typed:
- a flow's display name, lowercased with spaces and hyphens as underscores,
  is its ontology id ("Single-Item Query" -> single_item_query);
- within a flow, guidelines.json lists subflows in the ontology's order, and
  the pairing is accepted only if every pair shares a name token
  ("Initiate Refund" / refund_initiate share "refund"). A pair that does not
  raises, so a reordered file cannot silently misfile a section.

A subflow section *lists* an action when kb.json names it for that subflow
(the dataset's required action sequence) or when one of the section's
buttons resolves to it. Buttons resolve by name-token overlap against the
action enum ("Membership Privileges" -> membership, "Log Out/In" ->
log-out-in); buttons with no overlap ("N/A", "End Conversation") are
communication steps with no action.
"""

import json
import re
from functools import lru_cache
from pathlib import Path

from core.enums import ACTIONS, FLOWS, SUBFLOW_FLOW

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "abcd"


def _tokens(s: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", s.lower()) if t}


def _flow_id(display: str) -> str:
    return re.sub(r"[\s\-]+", "_", display.strip().lower())


def section_id(subflow: str) -> str:
    return f"{SUBFLOW_FLOW[subflow]}/{subflow}"


def resolve_button(button: str, prefer=()) -> str | None:
    """The action a guideline button names, or None. Candidates in `prefer`
    (the subflow's kb actions) win ties on overlap, so "Membership" in the
    membership FAQ section resolves to search-membership, not membership."""
    bt = _tokens(button)
    if not bt or bt <= {"n", "a"}:
        return None
    best, best_key = None, (0, 0, 0.0)
    for a in ACTIONS:
        at = _tokens(a)
        overlap = len(bt & at)
        if not overlap:
            continue
        key = (overlap, 1 if a in prefer else 0, overlap / len(bt | at))
        if key > best_key:
            best, best_key = a, key
    return best


@lru_cache(maxsize=1)
def library(data_dir: str = str(DATA)) -> dict:
    d = Path(data_dir)
    guidelines = json.loads((d / "guidelines.json").read_text(encoding="utf-8"))
    kb = json.loads((d / "kb.json").read_text(encoding="utf-8"))
    by_flow = {}
    for sub, flow in SUBFLOW_FLOW.items():
        by_flow.setdefault(flow, []).append(sub)
    sections = {}
    for display_flow, body in guidelines.items():
        flow = _flow_id(display_flow)
        if flow not in FLOWS:
            raise ValueError(f"guidelines.json flow {display_flow!r} does not map to an ontology flow")
        subs = list(body["subflows"].items())
        if len(subs) != len(by_flow[flow]):
            raise ValueError(f"{flow}: guidelines.json has {len(subs)} subflows, the ontology {len(by_flow[flow])}")
        sections[flow] = {"id": flow, "kind": "flow", "flow": flow, "title": display_flow,
                          "description": body.get("description", ""), "children": []}
        for (display_sub, sub_body), sub in zip(subs, by_flow[flow]):
            if not (_tokens(display_sub) & _tokens(sub)):
                raise ValueError(f"{flow}: guideline subflow {display_sub!r} shares no name token with ontology {sub!r}")
            required = list(kb[sub])
            steps = []
            for a in sub_body["actions"]:
                steps.append({"button": a.get("button", ""), "type": a.get("type", ""),
                              "action": resolve_button(a.get("button", ""), prefer=required),
                              "text": a.get("text", ""), "subtext": list(a.get("subtext") or [])})
            listed = list(dict.fromkeys(required + [s["action"] for s in steps if s["action"]]))
            sid = section_id(sub)
            sections[sid] = {"id": sid, "kind": "subflow", "flow": flow, "subflow": sub, "title": f"{display_flow} / {display_sub}",
                             "instructions": list(sub_body.get("instructions") or []), "steps": steps,
                             "required_actions": required, "listed_actions": listed}
            sections[flow]["children"].append(sid)
    missing = [s for s in SUBFLOW_FLOW if section_id(s) not in sections]
    if missing:
        raise ValueError(f"subflows with no guideline section: {missing}")
    return sections


def subflow_sections() -> dict:
    return {k: v for k, v in library().items() if v["kind"] == "subflow"}




def section_ids() -> tuple:
    return tuple(subflow_sections())


# How much of each section the rendered library carries, from the original
# rendering down. Every style keeps the section header (which the assist
# cites as section_id), the required action sequence and every listed
# action, so the validator's allowed set is visible in all of them; what
# goes, in order, is repetition, the UI click-through detail under each
# step, the step text, and the free-text instructions.
#   full     the original rendering, byte-identical to the Parts 3-4 runs
#   dedupe   drops the flow description repeated under every subflow (the
#            flow header above the subflows carries it once), lists only the
#            actions beyond the required sequence, and shortens step labels
#   nosub    dedupe without the sub-bullets under each step
#   outline  dedupe without the steps: header, sequence, instructions
#   bare     outline without the instructions
LIBRARY_STYLES = ("full", "dedupe", "nosub", "outline", "bare")


def _render_compact(s: dict, style: str) -> str:
    lines = [f"### SECTION {s['id']} :: {s['title']}",
             "Required action sequence: " + " -> ".join(s["required_actions"])]
    extra = [a for a in s["listed_actions"] if a not in s["required_actions"]]
    if extra:
        lines.append("Also listed: " + ", ".join(extra))
    if style != "bare":
        lines += [f"- {ins}" for ins in s["instructions"]]
    if style in ("dedupe", "nosub"):
        for n, st in enumerate(s["steps"], 1):
            lines.append(f"{n}. {st['action'] or 'talk to the customer'}: {st['text']}")
            if style == "dedupe":
                lines += [f"   * {x}" for x in st["subtext"]]
    return "\n".join(lines)


def render_section(sid: str, style: str = "full") -> str:
    if style not in LIBRARY_STYLES:
        raise ValueError(f"style must be one of {LIBRARY_STYLES}")
    s = library()[sid]
    if s["kind"] == "flow":
        return f"## {s['id']} :: {s['title']}\n{s['description']}"
    if style != "full":
        return _render_compact(s, style)
    flow = library()[s["flow"]]
    lines = [f"### SECTION {s['id']} :: {s['title']}",
             f"Flow: {flow['title']} ({flow['description']})",
             "Required action sequence: " + " -> ".join(s["required_actions"]),
             "Actions this section lists: " + ", ".join(s["listed_actions"])]
    for ins in s["instructions"]:
        lines.append(f"- {ins}")
    for n, st in enumerate(s["steps"], 1):
        tag = st["action"] or "no action (talk to the customer)"
        lines.append(f"Step {n} [{st['button']} -> {tag}]: {st['text']}")
        lines += [f"    * {x}" for x in st["subtext"]]
    return "\n".join(lines)


def render_library(style: str = "full") -> str:
    """The whole library as one text block, flow by flow, deterministic, so
    it can sit in a cached system prefix byte-identical across calls."""
    out = []
    for sid, s in library().items():
        if s["kind"] == "flow":
            out.append(render_section(sid, style))
            out += [render_section(c, style) for c in s["children"]]
    return "\n\n".join(out)


def subflow_menu() -> str:
    """One line per subflow for the intent call in arm B: the id and the
    section title, nothing of the procedure."""
    return "\n".join(f"- {s['subflow']}: {s['title']}" for s in subflow_sections().values())
