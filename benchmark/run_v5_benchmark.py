import sys
from pathlib import Path

# Add the Shadow AI project root to Python's import path.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import json
import statistics
import time

from detection.detection_pipeline import run_detection
from detection.normalizer import normalize_findings
from backend.risk_engine import calculate_risk
from backend.policy import get_policy_decision


CORPUS_PATH = PROJECT_ROOT / "benchmark" / "attack_corpus_v5.json"
RESULTS_PATH = (
    PROJECT_ROOT
    / "benchmark"
    / "results"
    / "v5_stateful_results.json"
)


def detect_and_normalize(text: str):
    findings = run_detection(
        text,
        enable_canonicalization=True,
        enable_confusables=True
    )

    return normalize_findings(findings)


def entity_types(findings):
    return sorted(
        set(
            finding.get("type")
            for finding in findings
            if finding.get("type")
        )
    )


def evaluate_case(case):
    turns = case["turns"]

    stateless_turns = []
    stateful_turns = []

    stateful_history = []

    for turn_index, text in enumerate(turns, start=1):

        # -------------------------------------------------
        # STATELESS
        # -------------------------------------------------

        start = time.perf_counter()

        findings = detect_and_normalize(text)

        stateless_risk = calculate_risk(
            findings,
            []
        )

        stateless_policy = get_policy_decision(
            stateless_risk
        )

        stateless_latency_ms = (
            time.perf_counter() - start
        ) * 1000

        stateless_turns.append({
            "turn": turn_index,
            "text": text,
            "entities": entity_types(findings),
            "findings": findings,
            "risk": stateless_risk,
            "policy": stateless_policy,
            "latency_ms": round(
                stateless_latency_ms,
                4
            )
        })

        # -------------------------------------------------
        # STATEFUL
        # -------------------------------------------------

        start = time.perf_counter()

        stateful_findings = detect_and_normalize(text)

        stateful_risk = calculate_risk(
            stateful_findings,
            stateful_history
        )

        stateful_policy = get_policy_decision(
            stateful_risk
        )

        stateful_latency_ms = (
            time.perf_counter() - start
        ) * 1000

        stateful_turns.append({
            "turn": turn_index,
            "text": text,
            "entities": entity_types(
                stateful_findings
            ),
            "findings": stateful_findings,
            "risk": stateful_risk,
            "policy": stateful_policy,
            "latency_ms": round(
                stateful_latency_ms,
                4
            )
        })

        # -------------------------------------------------
        # SAVE CURRENT TURN INTO STATE
        # -------------------------------------------------

        stateful_history.append({
            "isolated_risk": stateful_risk[
                "isolated_risk"
            ],
            "findings": [
                {
                    "type": finding.get("type"),
                    "confidence": finding.get(
                        "confidence",
                        1.0
                    )
                }
                for finding in stateful_findings
            ]
        })

    final_stateless = (
        stateless_turns[-1]
        if stateless_turns
        else {}
    )

    final_stateful = (
        stateful_turns[-1]
        if stateful_turns
        else {}
    )

    return {
        "id": case["id"],
        "category": case["category"],
        "description": case.get(
            "description",
            ""
        ),
        "expected_entities": case.get(
            "expected_entities",
            []
        ),
        "turn_count": len(turns),
        "stateless": {
            "turns": stateless_turns,
            "final_total_risk": final_stateless.get(
                "risk",
                {}
            ).get("total_risk", 0),
            "final_policy": final_stateless.get(
                "policy",
                {}
            ).get("decision")
        },
        "stateful": {
            "turns": stateful_turns,
            "final_total_risk": final_stateful.get(
                "risk",
                {}
            ).get("total_risk", 0),
            "final_policy": final_stateful.get(
                "policy",
                {}
            ).get("decision")
        }
    }


def main():

    with CORPUS_PATH.open(
        "r",
        encoding="utf-8"
    ) as file:
        corpus = json.load(file)

    results = []

    for case in corpus:
        results.append(
            evaluate_case(case)
        )

    stateless_latencies = [
        turn["latency_ms"]
        for result in results
        for turn in result["stateless"]["turns"]
    ]

    stateful_latencies = [
        turn["latency_ms"]
        for result in results
        for turn in result["stateful"]["turns"]
    ]

    stateless_final_risks = [
        result["stateless"]["final_total_risk"]
        for result in results
    ]

    stateful_final_risks = [
        result["stateful"]["final_total_risk"]
        for result in results
    ]

    stateful_increases = [
        stateful - stateless
        for stateful, stateless
        in zip(
            stateful_final_risks,
            stateless_final_risks
        )
    ]

    summary = {
        "corpus_cases": len(results),
        "stateless_average_final_risk": round(
            statistics.mean(stateless_final_risks),
            4
        ),
        "stateful_average_final_risk": round(
            statistics.mean(stateful_final_risks),
            4
        ),
        "average_final_risk_increase": round(
            statistics.mean(stateful_increases),
            4
        ),
        "stateless_average_latency_ms": round(
            statistics.mean(stateless_latencies),
            4
        ) if stateless_latencies else 0,
        "stateful_average_latency_ms": round(
            statistics.mean(stateful_latencies),
            4
        ) if stateful_latencies else 0
    }

    output = {
        "experiment": (
            "V5 Stateful vs Stateless Risk Evaluation"
        ),
        "method": {
            "stateless": (
                "Each turn evaluated with empty history."
            ),
            "stateful": (
                "Previous turns retained as risk history."
            ),
            "canonicalization": True,
            "confusable_hardening": True
        },
        "summary": summary,
        "cases": results
    }

    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with RESULTS_PATH.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            output,
            file,
            indent=4
        )

    print("=" * 50)
    print("V5 STATEFUL VS STATELESS BENCHMARK")
    print("=" * 50)
    print(f"Corpus cases: {len(results)}")
    print()

    print(
        "Stateless average final risk:",
        summary["stateless_average_final_risk"]
    )

    print(
        "Stateful average final risk:",
        summary["stateful_average_final_risk"]
    )

    print(
        "Average final risk increase:",
        summary["average_final_risk_increase"]
    )

    print(
        "Stateless average latency:",
        summary["stateless_average_latency_ms"],
        "ms"
    )

    print(
        "Stateful average latency:",
        summary["stateful_average_latency_ms"],
        "ms"
    )

    print()
    print(
        f"Saved results to: {RESULTS_PATH}"
    )


if __name__ == "__main__":
    main()
