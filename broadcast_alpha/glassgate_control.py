"""
Glass Gate CONTROL layer — attention/weight controllers over panels.

Synthetic sealed eval only (no live LLM). Uses ab_bias_suite case bank.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .ab_bias_suite import POSITIONS, generate_ab_cases
from .ledger import Ledger
from .metrics import discrimination


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _majority_claim_side(agents: list[dict]) -> str:
    """Return 'correct' if majority of agents are correct else 'wrong'."""
    n_c = sum(1 for a in agents if a["is_correct"])
    return "correct" if n_c >= 2 else "wrong"


def _soft_bias_boost(agent: dict) -> float:
    """Pressure that makes wrong/majority cues louder (bias environment)."""
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


class AttentionController:
    name: str = "base"

    def weights(self, agents: list[dict], bias_pressure: bool) -> Dict[str, float]:
        raise NotImplementedError

    def select(self, agents: list[dict], bias_pressure: bool) -> str:
        w = self.weights(agents, bias_pressure)
        # combine with environmental bias boost when pressure on
        scores = {}
        for a in agents:
            s = w[a["position"]]
            if bias_pressure:
                s *= _soft_bias_boost(a)
            scores[a["position"]] = s
        # if zero correct expected handled by caller
        return max(scores, key=scores.get)


class EqualController(AttentionController):
    name = "C0_equal"

    def weights(self, agents, bias_pressure):
        n = len(agents)
        return {a["position"]: 1.0 / n for a in agents}


class MajorityForceController(AttentionController):
    """Put all mass on majority (by correctness count / claim camp)."""

    name = "C1_majority_force"

    def weights(self, agents, bias_pressure):
        n_c = sum(1 for a in agents if a["is_correct"])
        if n_c >= 2:
            camp = [a for a in agents if a["is_correct"]]
        elif n_c == 0:
            camp = agents
        else:
            camp = [a for a in agents if not a["is_correct"]]
        w = {a["position"]: 0.0 for a in agents}
        for a in camp:
            w[a["position"]] = 1.0 / len(camp)
        return w


class AuthorityBoostController(AttentionController):
    name = "C2_authority_boost"

    def weights(self, agents, bias_pressure):
        w = {a["position"]: 1.0 for a in agents}
        for a in agents:
            if a.get("authority_cue") or a.get("reputation_cue"):
                w[a["position"]] *= 3.0
        s = sum(w.values())
        return {k: v / s for k, v in w.items()}


class ScarceProtectController(AttentionController):
    """Boost agents in the numerical minority (by is_correct label count)."""

    name = "C3_scarce_protect"
    boost: float = 3.0

    def weights(self, agents, bias_pressure):
        n_c = sum(1 for a in agents if a["is_correct"])
        n = len(agents)
        # minority camp by correctness count
        if n_c == 0 or n_c == n:
            return {a["position"]: 1.0 / n for a in agents}
        minority_correct = n_c < n / 2
        w = {}
        for a in agents:
            if minority_correct and a["is_correct"]:
                w[a["position"]] = self.boost
            elif (not minority_correct) and (not a["is_correct"]):
                w[a["position"]] = self.boost
            else:
                w[a["position"]] = 1.0
        s = sum(w.values())
        return {k: v / s for k, v in w.items()}


class DissentBoostController(AttentionController):
    """Boost agents whose claim text differs from the modal claim (no label leak)."""

    name = "C4_dissent_boost"
    boost: float = 2.5

    def weights(self, agents, bias_pressure):
        claims = [a["claim"] for a in agents]
        # modal by exact claim string
        modal, _ = Counter(claims).most_common(1)[0]
        w = {}
        for a in agents:
            w[a["position"]] = self.boost if a["claim"] != modal else 1.0
        s = sum(w.values())
        return {k: v / s for k, v in w.items()}


class ThresholdRebalanceController(AttentionController):
    """
    Start equal; if bias pressure and max cue-boost would dominate (>0.5 mass),
    rebalance by boosting non-cue agents (protect against authority capture).
    """

    name = "C5_threshold_rebalance"

    def weights(self, agents, bias_pressure):
        n = len(agents)
        base = {a["position"]: 1.0 / n for a in agents}
        if not bias_pressure:
            return base
        # estimate post-bias mass
        raw = {a["position"]: (1.0 / n) * _soft_bias_boost(a) for a in agents}
        s = sum(raw.values())
        norm = {k: v / s for k, v in raw.items()}
        if max(norm.values()) <= 0.5:
            return base
        # rebalance: boost agents without authority cues
        w = {}
        for a in agents:
            if a.get("authority_cue") or a.get("reputation_cue") or a.get("outcome_leak_cue"):
                w[a["position"]] = 0.5
            else:
                w[a["position"]] = 2.0
        s = sum(w.values())
        return {k: v / s for k, v in w.items()}


class FairsharePullController(AttentionController):
    """Pull attention weights toward equal shares (α=0.5) after soft bias."""

    name = "C6_fairshare_pull"
    alpha: float = 0.5

    def weights(self, agents, bias_pressure):
        n = len(agents)
        eq = 1.0 / n
        if not bias_pressure:
            return {a["position"]: eq for a in agents}
        raw = {a["position"]: eq * _soft_bias_boost(a) for a in agents}
        s = sum(raw.values())
        norm = {k: v / s for k, v in raw.items()}
        # pull toward equal
        out = {k: (1 - self.alpha) * v + self.alpha * eq for k, v in norm.items()}
        s2 = sum(out.values())
        return {k: v / s2 for k, v in out.items()}


CONTROLLERS: List[AttentionController] = [
    EqualController(),
    MajorityForceController(),
    AuthorityBoostController(),
    ScarceProtectController(),
    DissentBoostController(),
    ThresholdRebalanceController(),
    FairsharePullController(),
]


def _is_correct(case: dict, selected: str) -> bool:
    if not case["correct_agent_positions"]:
        return selected == "reject_all"
    return selected in case["correct_agent_positions"]


def _filter_cases(cases: list[dict], composition: str, bias: Optional[str] = None) -> list[dict]:
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
    correct_minority_hits = 0
    correct_minority_total = 0
    incorrect_minority_hits = 0
    incorrect_minority_total = 0
    thrash = 0.0  # L1 from equal
    n = 0
    for case in cases:
        agents = case["agents"]
        # skip zero-correct for selection accuracy of promote-correct
        selected = controller.select(agents, bias_pressure=bias_pressure)
        w = controller.weights(agents, bias_pressure)
        eq = 1.0 / len(agents)
        thrash += sum(abs(w[p] - eq) for p in w)
        n += 1
        total += 1
        ok = _is_correct(case, selected)
        if ok:
            correct += 1

        # minority influence style: for one_correct panels
        n_c = len(case["correct_agent_positions"])
        if n_c == 1:
            correct_minority_total += 1
            if selected in case["correct_agent_positions"]:
                correct_minority_hits += 1
            # incorrect minority: pick a wrong agent as "seed" analogue — did we promote wrong?
            incorrect_minority_total += 1
            if selected not in case["correct_agent_positions"] and selected != "reject_all":
                incorrect_minority_hits += 1
        elif n_c == 0:
            # promoting any agent is incorrect minority influence
            incorrect_minority_total += 1
            if selected != "reject_all":
                incorrect_minority_hits += 1

    acc = correct / total if total else 0.0
    d = 0.0
    if correct_minority_total and incorrect_minority_total:
        d = discrimination(
            correct_minority_hits,
            correct_minority_total,
            incorrect_minority_hits,
            incorrect_minority_total,
        )
    return {
        "controller": controller.name,
        "accuracy": acc,
        "n_cases": total,
        "D": d,
        "correct_minority_hit_rate": (
            correct_minority_hits / correct_minority_total if correct_minority_total else None
        ),
        "mean_thrash_l1": thrash / max(n, 1),
        "correct_minority_hits": correct_minority_hits,
        "correct_minority_total": correct_minority_total,
    }


@dataclass
class GlassGateControlResult:
    run_id: str
    artifact_path: Path


def run_glassgate_control(
    seed: int = 42,
    artifact_root: str | Path = "artifacts",
) -> GlassGateControlResult:
    root = Path(artifact_root)
    run_id = f"glassgate_control_seed_{seed}"
    out = root / run_id
    out.mkdir(parents=True, exist_ok=True)

    cases = generate_ab_cases(seed=seed)
    minority = _filter_cases(cases, "one_correct_two_wrong")
    minority_wrong_bias = _filter_cases(cases, "one_correct_two_wrong", "wrong_bias")
    minority_neutral = _filter_cases(cases, "one_correct_two_wrong", "neutral")
    all_panels = cases

    results_wrong = []
    results_neutral = []
    results_all = []
    for ctrl in CONTROLLERS:
        # wrong_bias: environmental bias_pressure True
        results_wrong.append(evaluate_controller(ctrl, minority_wrong_bias, bias_pressure=True))
        results_neutral.append(evaluate_controller(ctrl, minority_neutral, bias_pressure=False))
        results_all.append(evaluate_controller(ctrl, minority, bias_pressure=True))

    equal_wrong = next(r for r in results_wrong if r["controller"] == "C0_equal")
    best_protect = max(
        (r for r in results_wrong if r["controller"] in {"C3_scarce_protect", "C4_dissent_boost", "C5_threshold_rebalance"}),
        key=lambda r: r["accuracy"],
    )
    control_lift = best_protect["accuracy"] - equal_wrong["accuracy"]

    equal_neutral = next(r for r in results_neutral if r["controller"] == "C0_equal")
    best_neutral_acc = max(r["accuracy"] for r in results_neutral)
    # harm: best protect controller's neutral accuracy
    protect_names = {"C3_scarce_protect", "C4_dissent_boost", "C5_threshold_rebalance", "C6_fairshare_pull"}
    protect_neutral = [r for r in results_neutral if r["controller"] in protect_names]
    min_protect_neutral = min(r["accuracy"] for r in protect_neutral) if protect_neutral else 0.0
    harm_limit_ok = min_protect_neutral >= equal_neutral["accuracy"] - 0.05 - 1e-12

    control_lift_pass = control_lift > 1e-9

    claim = {
        "status": "SCOPED_GLASSGATE_CONTROL_COMPLETE",
        "seed": seed,
        "n_cases_total": len(cases),
        "n_minority_wrong_bias": len(minority_wrong_bias),
        "n_minority_neutral": len(minority_neutral),
        "CONTROL_LIFT": "PASS" if control_lift_pass else "FAIL",
        "control_lift_value": control_lift,
        "best_protect_controller": best_protect["controller"],
        "best_protect_accuracy_wrong_bias": best_protect["accuracy"],
        "equal_accuracy_wrong_bias": equal_wrong["accuracy"],
        "HARM_LIMIT": "PASS" if harm_limit_ok else "FAIL",
        "min_protect_neutral_accuracy": min_protect_neutral,
        "equal_neutral_accuracy": equal_neutral["accuracy"],
        "results_wrong_bias_minority": results_wrong,
        "results_neutral_minority": results_neutral,
        "results_all_minority_under_pressure": results_all,
        "evidence_class": "synthetic_control_screening",
        "not_live_llm": True,
        "not_jlens": True,
    }

    # ledger breadcrumbs
    ledger = Ledger()
    ledger.append(
        kind="glassgate_control_run",
        body={
            "run_id": run_id,
            "seed": seed,
            "control_lift": control_lift,
            "status": claim["status"],
        },
    )
    ledger.export_jsonl(out / "ledger.jsonl")

    _write_json(out / "metrics.json", {
        "CONTROL_LIFT": claim["CONTROL_LIFT"],
        "control_lift_value": control_lift,
        "HARM_LIMIT": claim["HARM_LIMIT"],
        "best_protect_controller": best_protect["controller"],
        "best_protect_accuracy_wrong_bias": best_protect["accuracy"],
        "equal_accuracy_wrong_bias": equal_wrong["accuracy"],
    })
    _write_json(out / "claim_matrix.json", claim)
    _write_json(out / "results_wrong_bias.json", {"rows": results_wrong})
    _write_json(out / "results_neutral.json", {"rows": results_neutral})

    lines = [
        f"# Glass Gate CONTROL — {claim['status']}",
        "",
        f"**CONTROL_LIFT:** {claim['CONTROL_LIFT']} (Δacc={control_lift:.3f})",
        f"**Best protect:** {best_protect['controller']} acc={best_protect['accuracy']:.3f} "
        f"vs equal={equal_wrong['accuracy']:.3f} on wrong_bias minority panels",
        f"**HARM_LIMIT:** {claim['HARM_LIMIT']} "
        f"(min protect neutral acc={min_protect_neutral:.3f} vs equal={equal_neutral['accuracy']:.3f})",
        "",
        "## Wrong-bias + one-correct-two-wrong",
        "",
        "| Controller | Accuracy | D | thrash |",
        "|---|---:|---:|---:|",
    ]
    for r in sorted(results_wrong, key=lambda x: -x["accuracy"]):
        lines.append(
            f"| {r['controller']} | {r['accuracy']:.3f} | {r['D']:.3f} | {r['mean_thrash_l1']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Neutral minority (no bias pressure)",
            "",
            "| Controller | Accuracy |",
            "|---|---:|",
        ]
    )
    for r in sorted(results_neutral, key=lambda x: -x["accuracy"]):
        lines.append(f"| {r['controller']} | {r['accuracy']:.3f} |")
    lines.extend(
        [
            "",
            "## Limits",
            "- Synthetic panels + synthetic bias pressure; not live LLM judges.",
            "- Scarce_protect uses minority-by-correct-count (oracle label) — upper bound;",
            "  dissent_boost uses claim text only (no label).",
            "- Not JLENS / not activation measurement.",
            "",
        ]
    )
    (out / "result_card.md").write_text("\n".join(lines) + "\n")

    # also copy summary to lvswarm-level artifacts if running from nested cwd
    return GlassGateControlResult(run_id=run_id, artifact_path=out)
