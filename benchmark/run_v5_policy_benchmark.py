import sys
from pathlib import Path

# Make the Shadow AI project root importable when this
# file is executed directly from the benchmark directory.
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


CORPUS_PATH = (
    PROJECT_ROOT
    / "benchmark"
    / "attack_corpus_v5_policy.json"
)

RESULTS_PATH = (
    PROJECT_ROOT
    / "benchmark"
    / "results"
    / "v5_policy_results.json"
)


def detect_and_normalize(text: str):
    findings = run_detection(
        text,
        enable_canonicalization=True,
        enable_confusables=True
    )

    return normalize_findings(findings)


def get_entity_types(findings):
    return sorted(
        {
            finding.get("type")
            for finding in findings
            if finding.get("type")
        }
    )


def evaluate_case(case):
    turns = case["turns"]

    stateless_turns = []
    stateful_turns = []

    stateful_history = []

    for turn_index, text in enumerate(turns, start=1):

        # =================================================
        # STATELESS
        # =================================================

        start = time.perf_counter()

        stateless_findings = detect_and_normalize(text)

        stateless_risk = calculate_risk(
            stateless_findings,
            []
        )

        stateless_policy = get_policy_decision(
            stateless_risk
        )

        stateless_latency = (
            time.perf_counter() - start
        ) * 1000

        stateless_turns.append({
            "turn": turn_index,
            "text": text,
            "entities": get_entity_types(
                stateless_findings
            ),
            "findings": stateless_findings,
            "risk": stateless_risk,
            "policy": stateless_policy,
            "latency_ms": round(
                stateless_latency,
                4
            )
        })

        # =================================================
        # STATEFUL
        # =================================================

        start = time.perf_counter()

        stateful_findings = detect_and_normalize(text)

        stateful_risk = calculate_risk(
            stateful_findings,
            stateful_history
        )

        stateful_policy = get_policy_decision(
            stateful_risk
        )

        stateful_latency = (
            time.perf_counter() - start
        ) * 1000

        stateful_turns.append({
            "turn": turn_index,
            "text": text,
            "entities": get_entity_types(
                stateful_findings
            ),
            "findings": stateful_findings,
            "risk": stateful_risk,
            "policy": stateful_policy,
            "latency_ms": round(
                stateful_latency,
                4
            )
        })

        # Store only the information required by
        # the existing risk engine for the next turn.
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

    # -----------------------------------------------------
    # Final-turn comparison
    # -----------------------------------------------------

    stateless_final = stateless_turns[-1]
    stateful_final = stateful_turns[-1]

    stateless_decision = stateless_final[
        "policy"
    ]["decision"]

    stateful_decision = stateful_final[
        "policy"
    ]["decision"]

    policy_changed = (
        stateless_decision
        != stateful_decision
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
            "final_total_risk": stateless_final[
                "risk"
            ]["total_risk"],
            "final_policy": stateless_decision
        },
        "stateful": {
            "turns": stateful_turns,
            "final_total_risk": stateful_final[
                "risk"
            ]["total_risk"],
            "final_policy": stateful_decision
        },
        "comparison": {
            "final_risk_difference": round(
                stateful_final["risk"]["total_risk"]
                - stateless_final["risk"]["total_risk"],
                2
            ),
            "policy_changed": policy_changed,
            "policy_transition": (
                f"{stateless_decision} -> "
                f"{stateful_decision}"
                if policy_changed
                else stateless_decision
            )
        }
    }


def main():

    with CORPUS_PATH.open(
        "r",
        encoding="utf-8"
    ) as file:
        corpus = json.load(file)

    results = [
        evaluate_case(case)
        for case in corpus
    ]

    policy_changed_cases = [
        result
        for result in results
        if result["comparison"]["policy_changed"]
    ]

    synergy_cases = []

    historical_contributions = []

    for result in results:

        for turn in result["stateful"]["turns"]:

            historical = turn["risk"][
                "historical_risk"
            ]

            synergy = turn["risk"][
                "synergy_risk"
            ]

            if historical > 0:
                historical_contributions.append(
                    historical
                )

            if synergy > 0:
                synergy_cases.append(
                    result["id"]
                )

    unique_synergy_cases = sorted(
        set(synergy_cases)
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

    risk_differences = [
        result["comparison"][
            "final_risk_difference"
        ]
        for result in results
    ]

    summary = {
        "corpus_cases": len(results),

        "policy_changed_cases": len(
            policy_changed_cases
        ),

        "policy_change_rate": round(
            len(policy_changed_cases)
            / len(results),
            4
        ) if results else 0,

        "average_final_risk_difference": round(
            statistics.mean(risk_differences),
            4
        ) if risk_differences else 0,

        "average_historical_risk_contribution": round(
            statistics.mean(
                historical_contributions
            ),
            4
        ) if historical_contributions else 0,

        "stateful_synergy_case_count": len(
            unique_synergy_cases
        ),

        "stateless_average_latency_ms": round(
            statistics.mean(
                stateless_latencies
            ),
            4
        ) if stateless_latencies else 0,

        "stateful_average_latency_ms": round(
            statistics.mean(
                stateful_latencies
            ),
            4
        ) if stateful_latencies else 0
    }

    output = {
        "experiment": (
            "V5.1 Stateful Policy Transition Evaluation"
        ),
        "method": {
            "stateless": (
                "Each turn evaluated with empty history."
            ),
            "stateful": (
                "Previous turns retained as risk history."
            ),
            "policy_authority": (
                "backend.policy.get_policy_decision"
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

    print("=" * 60)
    print("V5.1 STATEFUL POLICY TRANSITION BENCHMARK")
    print("=" * 60)
    print(f"Corpus cases: {len(results)}")
    print()

    print(
        "Policy changed cases:",
        summary["policy_changed_cases"]
    )

    print(
        "Policy change rate:",
        summary["policy_change_rate"]
    )

    print(
        "Average final risk difference:",
        summary["average_final_risk_difference"]
    )

    print(
        "Average historical risk contribution:",
        summary["average_historical_risk_contribution"]
    )

    print(
        "Cases with synergy activation:",
        summary["stateful_synergy_case_count"]
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
