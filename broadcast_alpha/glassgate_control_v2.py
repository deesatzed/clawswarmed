"""
Glass Gate CONTROL v2 — label-free primary claim; oracle ceiling separate.

Synthetic sealed only. No live LLM.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import statistics

from .ab_bias_suite import POSITIONS, generate_ab_cases, _family_payload, _correct_positions, _build_agents, _bias_type, TASK_FAMILIES, PANEL_COMPOSITIONS, BIAS_CONDITIONS
from .ledger import Ledger
from .metrics import discrimination


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def _soft_bias_boost(agent: dict) -> float:
    b = 1.0
    if agent.get("authority_cue"):
        b *= 1.8
    if agent.get("reputation_cue"):
        b *= 1.6
    if agent.get("outcome_leak_cue"):
        b *= 1.7
    if agent.get("confidence_cue") == "high_confidence_verbose":
        b *= 1.4
        b *= 1.0 + min(0.3, agent.get("claim_length", 0) / 500.0)
    return b


def sanitize_agents(agents: list[dict]) -> list[dict]:
    """Strip labels so deployable controllers cannot read is_correct."""
    out = []
    for a in agents:
        b = dict(a)
        b.pop("is_correct", None)
        out.append(b)
    return out


def expand_ab_cases(seed: int = 42, repeats: int = 5) -> list[dict]:
    """Larger bank: base generator × seed offsets + extra template indices."""
    cases = []
    for r in range(repeats):
        batch = generate_ab_cases(seed=seed + r * 17)
        for c in batch:
            c = dict(c)
            c["case_id"] = f"{c['case_id']}-r{r}"
            c["expand_repeat"] = r
            cases.append(c)
    # extra synthetic variants with shifted templates
    index = 10_000
    for r in range(repeats):
        for task_family in TASK_FAMILIES:
            for panel_composition in ("one_correct_two_wrong", "two_correct_one_wrong"):
                for bias_condition in ("neutral", "wrong_bias", "correct_bias"):
                    payload = _family_payload(task_family, index + r)
                    # light paraphrase of evidence
                    payload = dict(payload)
                    payload["evidence"] = payload["evidence"] + f" Context tag {seed}-{r}-{index}."
                    correct_positions = _correct_positions(seed + index + r, panel_composition)
                    bias_type = _bias_type(seed + index + r, bias_condition, panel_composition)
                    agents = _build_agents(payload, correct_positions, bias_condition, bias_type)
                    expected = "reject_all" if not correct_positions else correct_positions[0]
                    cases.append(
                        {
                            "case_id": f"AB2-{task_family}-{panel_composition}-{bias_condition}-{index}",
                            "seed": seed + r,
                            "task_family": task_family,
                            "panel_composition": panel_composition,
                            "bias_condition": bias_condition,
                            "bias_type": bias_type,
                            "evidence": payload["evidence"],
                            "question": payload["question"],
                            "agents": agents,
                            "correct_agent_positions": correct_positions,
                            "expected_choice": expected,
                            "expand_repeat": r,
                        }
                    )
                    index += 1
    return cases


class AttentionController:
    name: str = "base"
    kind: str = "deployable"  # or oracle

    def weights(self, agents: list[dict], evidence: str, bias_pressure: bool) -> Dict[str, float]:
        raise NotImplementedError

    def select(self, agents: list[dict], evidence: str, bias_pressure: bool) -> str:
        w = self.weights(agents, evidence, bias_pressure)
        scores = {}
        for a in agents:
            s = w[a["position"]]
            if bias_pressure:
                s *= _soft_bias_boost(a)
            scores[a["position"]] = s
        return max(scores, key=scores.get)


class EqualController(AttentionController):
    name = "deployable_equal"
    kind = "deployable"

    def weights(self, agents, evidence, bias_pressure):
        n = len(agents)
        return {a["position"]: 1.0 / n for a in agents}


class MajorityForceController(AttentionController):
    """Uses claim-text majority camp only (no labels)."""

    name = "deployable_majority_claim"
    kind = "deployable"

    def weights(self, agents, evidence, bias_pressure):
        claims = [a["claim"] for a in agents]
        modal, _ = Counter(claims).most_common(1)[0]
        camp = [a for a in agents if a["claim"] == modal]
        w = {a["position"]: 0.0 for a in agents}
        for a in camp:
            w[a["position"]] = 1.0 / len(camp)
        return w


class AuthorityBoostController(AttentionController):
    name = "deployable_authority_boost"
    kind = "deployable"

    def weights(self, agents, evidence, bias_pressure):
        w = {a["position"]: 1.0 for a in agents}
        for a in agents:
            if a.get("authority_cue") or a.get("reputation_cue"):
                w[a["position"]] *= 3.0
        s = sum(w.values()) or 1.0
        return {k: v / s for k, v in w.items()}


class DissentBoostController(AttentionController):
    name = "deployable_dissent_boost"
    kind = "deployable"
    boost = 2.5

    def weights(self, agents, evidence, bias_pressure):
        claims = [a["claim"] for a in agents]
        modal, _ = Counter(claims).most_common(1)[0]
        w = {a["position"]: (self.boost if a["claim"] != modal else 1.0) for a in agents}
        s = sum(w.values())
        return {k: v / s for k, v in w.items()}


class EvidenceOverlapController(AttentionController):
    """Weight by Jaccard overlap of claim tokens with evidence (label-free)."""

    name = "deployable_evidence_overlap"
    kind = "deployable"

    def weights(self, agents, evidence, bias_pressure):
        ev = _tokenize(evidence)
        raw = {}
        for a in agents:
            j = _jaccard(_tokenize(a["claim"]), ev)
            # under bias pressure, penalize length/confidence theater
            pen = 1.0
            if bias_pressure:
                if a.get("confidence_cue") == "high_confidence_verbose":
                    pen *= 0.7
                pen *= 1.0 / (1.0 + max(0, a.get("claim_length", 0) - 120) / 200.0)
            raw[a["position"]] = max(j, 0.05) * pen
        s = sum(raw.values()) or 1.0
        return {k: v / s for k, v in raw.items()}


class EvidencePlusDissentController(AttentionController):
    """Combine evidence overlap with dissent-from-modal-claim."""

    name = "deployable_evidence_dissent"
    kind = "deployable"

    def weights(self, agents, evidence, bias_pressure):
        ev = _tokenize(evidence)
        claims = [a["claim"] for a in agents]
        modal, _ = Counter(claims).most_common(1)[0]
        raw = {}
        for a in agents:
            j = _jaccard(_tokenize(a["claim"]), ev)
            dissent = 2.0 if a["claim"] != modal else 1.0
            pen = 1.0
            if bias_pressure and a.get("authority_cue"):
                pen *= 0.85  # slight anti-authority under known wrong_bias training — actually no training; mild
            raw[a["position"]] = max(0.05, j) * dissent * pen
        s = sum(raw.values()) or 1.0
        return {k: v / s for k, v in raw.items()}


class AntiCueController(AttentionController):
    """Downweight authority/reputation/outcome cues; upweight short evidence-aligned claims."""

    name = "deployable_anti_cue"
    kind = "deployable"

    def weights(self, agents, evidence, bias_pressure):
        ev = _tokenize(evidence)
        raw = {}
        for a in agents:
            j = max(0.05, _jaccard(_tokenize(a["claim"]), ev))
            cue_pen = 1.0
            if a.get("authority_cue"):
                cue_pen *= 0.4
            if a.get("reputation_cue"):
                cue_pen *= 0.5
            if a.get("outcome_leak_cue"):
                cue_pen *= 0.35
            if a.get("confidence_cue") == "high_confidence_verbose":
                cue_pen *= 0.6
            raw[a["position"]] = j * cue_pen
        s = sum(raw.values()) or 1.0
        return {k: v / s for k, v in raw.items()}


class OracleScarceProtectController(AttentionController):
    """CEILING ONLY — uses is_correct labels."""

    name = "oracle_scarce_protect"
    kind = "oracle"
    boost = 3.0

    def weights(self, agents, evidence, bias_pressure):
        # agents here must still have is_correct
        n_c = sum(1 for a in agents if a.get("is_correct"))
        n = len(agents)
        if n_c == 0 or n_c == n:
            return {a["position"]: 1.0 / n for a in agents}
        minority_correct = n_c < n / 2
        w = {}
        for a in agents:
            if minority_correct and a.get("is_correct"):
                w[a["position"]] = self.boost
            elif (not minority_correct) and (not a.get("is_correct")):
                w[a["position"]] = self.boost
            else:
                w[a["position"]] = 1.0
        s = sum(w.values())
        return {k: v / s for k, v in w.items()}


DEPLOYABLE = [
    EqualController(),
    MajorityForceController(),
    AuthorityBoostController(),
    DissentBoostController(),
    EvidenceOverlapController(),
    EvidencePlusDissentController(),
    AntiCueController(),
]
ORACLE = [OracleScarceProtectController()]


def _is_correct(case: dict, selected: str) -> bool:
    if not case["correct_agent_positions"]:
        return selected == "reject_all"
    return selected in case["correct_agent_positions"]


def _filter(cases: list[dict], composition: str, bias: Optional[str] = None) -> list[dict]:
    out = []
    for c in cases:
        if c["panel_composition"] != composition:
            continue
        if bias is not None and c["bias_condition"] != bias:
            continue
        out.append(c)
    return out


def evaluate_controller(
    controller: AttentionController,
    cases: list[dict],
    bias_pressure: bool,
) -> dict:
    correct = 0
    total = 0
    cm_h = cm_t = im_h = im_t = 0
    thrash = 0.0
    for case in cases:
        agents_full = case["agents"]
        if controller.kind == "oracle":
            agents = agents_full
        else:
            agents = sanitize_agents(agents_full)
            # safety: ensure no is_correct
            assert all("is_correct" not in a for a in agents)

        selected = controller.select(agents, case["evidence"], bias_pressure)
        w = controller.weights(agents, case["evidence"], bias_pressure)
        eq = 1.0 / len(agents)
        thrash += sum(abs(w[p] - eq) for p in w)
        total += 1
        if _is_correct(case, selected):
            correct += 1

        n_c = len(case["correct_agent_positions"])
        if n_c == 1:
            cm_t += 1
            if selected in case["correct_agent_positions"]:
                cm_h += 1
            im_t += 1
            if selected not in case["correct_agent_positions"] and selected != "reject_all":
                im_h += 1

    acc = correct / total if total else 0.0
    d = 0.0
    if cm_t and im_t:
        d = discrimination(cm_h, cm_t, im_h, im_t)
    return {
        "controller": controller.name,
        "kind": controller.kind,
        "accuracy": acc,
        "n_cases": total,
        "D": d,
        "correct_minority_hit_rate": (cm_h / cm_t) if cm_t else None,
        "mean_thrash_l1": thrash / max(total, 1),
    }


def _mean_std(xs: List[float]) -> dict:
    if not xs:
        return {"mean": 0.0, "std": 0.0, "ci90_low": 0.0, "ci90_high": 0.0}
    m = statistics.mean(xs)
    sd = statistics.pstdev(xs) if len(xs) > 1 else 0.0
    # approx normal CI for display; also percentile
    xs_s = sorted(xs)
    lo = xs_s[max(0, int(0.05 * (len(xs_s) - 1)))]
    hi = xs_s[min(len(xs_s) - 1, int(0.95 * (len(xs_s) - 1)))]
    return {"mean": m, "std": sd, "ci90_low": lo, "ci90_high": hi}


@dataclass
class GlassGateControlV2Result:
    run_id: str
    artifact_path: Path


def run_glassgate_control_v2(
    seed: int = 42,
    n_seeds: int = 20,
    artifact_root: str | Path = "artifacts",
    expand_repeats: int = 5,
) -> GlassGateControlV2Result:
    root = Path(artifact_root)
    run_id = f"glassgate_control_v2_seed_{seed}"
    out = root / run_id
    out.mkdir(parents=True, exist_ok=True)

    # multi-seed over expanded banks
    deployable_names = [c.name for c in DEPLOYABLE]
    per_seed = []
    acc_wrong = {n: [] for n in deployable_names}
    acc_neutral = {n: [] for n in deployable_names}
    oracle_wrong = []

    for s in range(seed, seed + n_seeds):
        cases = expand_ab_cases(seed=s, repeats=expand_repeats)
        wrong = _filter(cases, "one_correct_two_wrong", "wrong_bias")
        neutral = _filter(cases, "one_correct_two_wrong", "neutral")
        seed_row = {"seed": s, "n_wrong": len(wrong), "n_neutral": len(neutral), "deployable": {}, "oracle": {}}
        for ctrl in DEPLOYABLE:
            rw = evaluate_controller(ctrl, wrong, bias_pressure=True)
            rn = evaluate_controller(ctrl, neutral, bias_pressure=False)
            acc_wrong[ctrl.name].append(rw["accuracy"])
            acc_neutral[ctrl.name].append(rn["accuracy"])
            seed_row["deployable"][ctrl.name] = {"wrong": rw, "neutral": rn}
        for ctrl in ORACLE:
            # oracle needs full agents with labels — evaluate on full agent dicts
            rw = evaluate_controller(ctrl, wrong, bias_pressure=True)
            oracle_wrong.append(rw["accuracy"])
            seed_row["oracle"][ctrl.name] = rw
        per_seed.append(seed_row)

    # aggregate
    equal = "deployable_equal"
    summary_wrong = {n: _mean_std(acc_wrong[n]) for n in deployable_names}
    summary_neutral = {n: _mean_std(acc_neutral[n]) for n in deployable_names}
    oracle_summary = _mean_std(oracle_wrong)

    # best deployable by mean wrong_bias acc excluding pure baselines? include all deployable
    best_dep = max(deployable_names, key=lambda n: summary_wrong[n]["mean"])
    # exclude equal and majority and authority as "best protect" candidates for lift
    protect_candidates = [
        n
        for n in deployable_names
        if n
        not in {
            "deployable_equal",
            "deployable_majority_claim",
            "deployable_authority_boost",
        }
    ]
    best_protect = max(protect_candidates, key=lambda n: summary_wrong[n]["mean"])

    lift = summary_wrong[best_protect]["mean"] - summary_wrong[equal]["mean"]
    # multi-seed robust: frac seeds where best_protect > equal
    wins = 0
    for row in per_seed:
        bp = row["deployable"][best_protect]["wrong"]["accuracy"]
        eq = row["deployable"][equal]["wrong"]["accuracy"]
        if bp > eq + 1e-12:
            wins += 1
    frac_win = wins / max(n_seeds, 1)

    harm_ok = True
    for n in protect_candidates:
        if summary_neutral[n]["mean"] < summary_neutral[equal]["mean"] - 0.05 - 1e-12:
            harm_ok = False

    deployable_lift_pass = lift >= 0.10 - 1e-12
    multi_seed_robust = frac_win >= 0.75 - 1e-12

    claim = {
        "status": "SCOPED_GLASSGATE_CONTROL_V2_COMPLETE",
        "seed_base": seed,
        "n_seeds": n_seeds,
        "expand_repeats": expand_repeats,
        "DEPLOYABLE_LIFT": "PASS" if deployable_lift_pass else "FAIL",
        "deployable_lift_value": lift,
        "best_deployable_protect": best_protect,
        "best_deployable_wrong_acc_mean": summary_wrong[best_protect]["mean"],
        "equal_wrong_acc_mean": summary_wrong[equal]["mean"],
        "MULTI_SEED_ROBUST": "PASS" if multi_seed_robust else "FAIL",
        "frac_seeds_protect_beats_equal": frac_win,
        "HARM_LIMIT": "PASS" if harm_ok else "FAIL",
        "ORACLE_CEILING": {
            "controller": "oracle_scarce_protect",
            "wrong_acc_mean": oracle_summary["mean"],
            "wrong_acc_ci90": [oracle_summary["ci90_low"], oracle_summary["ci90_high"]],
            "note": "Uses is_correct labels — not a deployable claim",
        },
        "summary_wrong_bias": summary_wrong,
        "summary_neutral": summary_neutral,
        "not_live_llm": True,
        "not_jlens": True,
        "primary_claim": "deployable_only",
    }

    ledger = Ledger()
    ledger.append(
        kind="glassgate_control_v2_run",
        body={
            "run_id": run_id,
            "DEPLOYABLE_LIFT": claim["DEPLOYABLE_LIFT"],
            "lift": lift,
            "best_protect": best_protect,
        },
    )
    ledger.export_jsonl(out / "ledger.jsonl")

    _write_json(out / "claim_matrix.json", claim)
    _write_json(out / "metrics.json", {
        "DEPLOYABLE_LIFT": claim["DEPLOYABLE_LIFT"],
        "deployable_lift_value": lift,
        "MULTI_SEED_ROBUST": claim["MULTI_SEED_ROBUST"],
        "HARM_LIMIT": claim["HARM_LIMIT"],
        "best_deployable_protect": best_protect,
        "oracle_ceiling_mean": oracle_summary["mean"],
    })
    _write_json(out / "per_seed.json", {"rows": per_seed})  # may be large
    # smaller summary without full per-case
    _write_json(
        out / "summary_tables.json",
        {
            "wrong_bias": summary_wrong,
            "neutral": summary_neutral,
            "oracle": oracle_summary,
        },
    )

    lines = [
        f"# Glass Gate CONTROL V2 — {claim['status']}",
        "",
        f"**Primary claim (deployable):** DEPLOYABLE_LIFT={claim['DEPLOYABLE_LIFT']} "
        f"(Δ={lift:.3f}, best={best_protect})",
        f"**MULTI_SEED_ROBUST:** {claim['MULTI_SEED_ROBUST']} (frac={frac_win:.2f})",
        f"**HARM_LIMIT:** {claim['HARM_LIMIT']}",
        f"**ORACLE_CEILING (not deployable):** mean acc={oracle_summary['mean']:.3f}",
        "",
        "## Deployable mean accuracy — wrong_bias minority (n_seeds={})".format(n_seeds),
        "",
        "| Controller | mean acc | CI90 |",
        "|---|---:|---:|",
    ]
    for n, s in sorted(summary_wrong.items(), key=lambda kv: -kv[1]["mean"]):
        lines.append(f"| {n} | {s['mean']:.3f} | [{s['ci90_low']:.3f}, {s['ci90_high']:.3f}] |")
    lines.extend(
        [
            "",
            "## Limits",
            "- Synthetic panels + synthetic bias; not live LLM judges.",
            "- Oracle ceiling uses labels; primary flags ignore it.",
            "- Anti-cue uses visible cue flags (behavioral), not correctness labels.",
            "",
        ]
    )
    (out / "result_card.md").write_text("\n".join(lines) + "\n")

    return GlassGateControlV2Result(run_id=run_id, artifact_path=out)
