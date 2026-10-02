import json
import sys
import time
from pathlib import Path
from statistics import mean

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from detection.detection_pipeline import run_detection
from backend.risk_engine import calculate_risk
from backend.policy import get_policy_decision


CORPUS_PATH = (
    PROJECT_ROOT
    / "benchmark"
    / "attack_corpus_v6.json"
)

RESULTS_DIR = (
    PROJECT_ROOT
    / "benchmark"
    / "results"
)

RESULTS_PATH = (
    RESULTS_DIR
    / "v6_1_red_team_results.json"
)


def load_corpus():

    with open(
        CORPUS_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def detect_entities(findings):

    return sorted(
        {
            finding.get("type")
            for finding in findings
            if finding.get("type")
        }
    )


def calculate_case_metrics(
    expected_entities,
    detected_entities
):

    expected = set(expected_entities)
    detected = set(detected_entities)

    true_positive = len(
        expected & detected
    )

    false_positive = len(
        detected - expected
    )

    false_negative = len(
        expected - detected
    )

    precision_denominator = (
        true_positive
        + false_positive
    )

    recall_denominator = (
        true_positive
        + false_negative
    )

    precision = (
        true_positive
        / precision_denominator
        if precision_denominator
        else 1.0
    )

    recall = (
        true_positive
        / recall_denominator
        if recall_denominator
        else 1.0
    )

    f1_denominator = (
        precision
        + recall
    )

    f1 = (
        2 * precision * recall
        / f1_denominator
        if f1_denominator
        else 0.0
    )

    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def evaluate_split(results):

    if not results:

        return {
            "cases": 0,
            "detected_cases": 0,
            "bypassed_cases": 0,
            "detection_rate": 0.0,
            "bypass_rate": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
        }

    total_tp = sum(
        item["metrics"]["true_positive"]
        for item in results
    )

    total_fp = sum(
        item["metrics"]["false_positive"]
        for item in results
    )

    total_fn = sum(
        item["metrics"]["false_negative"]
        for item in results
    )

    detected_cases = sum(
        1
        for item in results
        if item["detection_status"]
        == "DETECTED"
    )

    bypassed_cases = sum(
        1
        for item in results
        if item["bypass_status"]
        == "BYPASS"
    )

    cases = len(results)

    precision_denominator = (
        total_tp
        + total_fp
    )

    recall_denominator = (
        total_tp
        + total_fn
    )

    precision = (
        total_tp
        / precision_denominator
        if precision_denominator
        else 1.0
    )

    recall = (
        total_tp
        / recall_denominator
        if recall_denominator
        else 1.0
    )

    f1_denominator = (
        precision
        + recall
    )

    f1 = (
        2 * precision * recall
        / f1_denominator
        if f1_denominator
        else 0.0
    )

    return {
        "cases": cases,
        "detected_cases": detected_cases,
        "bypassed_cases": bypassed_cases,
        "detection_rate": detected_cases / cases,
        "bypass_rate": bypassed_cases / cases,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def percentile(
    values,
    percentile_value
):

    if not values:
        return 0.0

    sorted_values = sorted(values)

    if len(sorted_values) == 1:
        return sorted_values[0]

    position = (
        len(sorted_values) - 1
    ) * percentile_value

    lower = int(position)

    upper = min(
        lower + 1,
        len(sorted_values) - 1
    )

    weight = position - lower

    return (
        sorted_values[lower]
        + weight
        * (
            sorted_values[upper]
            - sorted_values[lower]
        )
    )


def evaluate_case(case):

    case_id = case["id"]
    split = case["split"]
    category = case["category"]
    modality = case.get(
        "modality",
        "TEXT"
    )

    turns = case["turns"]

    expected_entities = case.get(
        "expected_entities",
        []
    )

    history = []

    turn_results = []

    total_start = time.perf_counter()

    for turn_index, text in enumerate(
        turns,
        start=1
    ):

        start_time = time.perf_counter()

        findings = run_detection(
            text,
            enable_canonicalization=True,
            enable_confusables=True,
        )

        current_entities = detect_entities(
            findings
        )

        risk_result = calculate_risk(
            findings,
            history
        )

        policy_result = get_policy_decision(
            risk_result
        )

        latency_ms = (
            time.perf_counter()
            - start_time
        ) * 1000

        turn_results.append(
            {
                "turn": turn_index,
                "text": text,
                "detected_entities": (
                    current_entities
                ),
                "findings": findings,
                "risk": risk_result,
                "policy": policy_result,
                "latency_ms": round(
                    latency_ms,
                    4
                ),
            }
        )

        history.append(
            {
                "findings": findings,
                "isolated_risk": (
                    risk_result[
                        "isolated_risk"
                    ]
                ),
            }
        )

    total_latency_ms = (
        time.perf_counter()
        - total_start
    ) * 1000

    final_turn = turn_results[-1]

    detected_entities = sorted(
        {
            entity
            for turn in turn_results
            for entity in turn[
                "detected_entities"
            ]
        }
    )

    metrics = calculate_case_metrics(
        expected_entities,
        detected_entities
    )

    required_detected = set(
        expected_entities
    )

    actual_detected = set(
        detected_entities
    )

    if required_detected.issubset(
        actual_detected
    ):

        detection_status = "DETECTED"
        bypass_status = "NO_BYPASS"

    else:

        detection_status = "MISSED"
        bypass_status = "BYPASS"

    return {
        "id": case_id,
        "split": split,
        "category": category,
        "modality": modality,
        "turns": turns,
        "expected_entities": (
            expected_entities
        ),
        "detected_entities": (
            detected_entities
        ),
        "detection_status": (
            detection_status
        ),
        "bypass_status": bypass_status,
        "metrics": metrics,
        "final_risk": (
            final_turn["risk"]
        ),
        "final_policy": (
            final_turn["policy"]
        ),
        "total_latency_ms": round(
            total_latency_ms,
            4
        ),
        "turn_results": turn_results,
    }


def main():

    corpus = load_corpus()

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    development_results = []
    held_out_results = []

    for case in corpus:

        result = evaluate_case(case)

        if case["split"] == "development":

            development_results.append(
                result
            )

        elif case["split"] == "held_out":

            held_out_results.append(
                result
            )

        else:

            raise ValueError(
                f"Unknown split "
                f"'{case['split']}' "
                f"for case {case['id']}"
            )

    all_results = (
        development_results
        + held_out_results
    )

    development_summary = (
        evaluate_split(
            development_results
        )
    )

    held_out_summary = (
        evaluate_split(
            held_out_results
        )
    )

    overall_summary = evaluate_split(
        all_results
    )

    latencies = [
        result["total_latency_ms"]
        for result in all_results
    ]

    summary = {

        "benchmark_version": "V6.1",

        "baseline_version": "V6.0",

        "corpus": (
            "attack_corpus_v6.json"
        ),

        "methodology": {

            "purpose": (
                "Measure the V6.1 Purple "
                "Team hardened gateway "
                "against the same controlled "
                "V6 Red Team corpus."
            ),

            "development_cases": (
                len(development_results)
            ),

            "held_out_cases": (
                len(held_out_results)
            ),

            "held_out_cases_used_for_fixes": (
                False
            ),

            "policy_authority": (
                "backend.policy."
                "get_policy_decision"
            ),

            "detection_pipeline": (
                "run_detection with "
                "canonicalization and "
                "confusable normalization "
                "enabled"
            ),

            "baseline_result_file": (
                "v6_red_team_results.json"
            ),
        },

        "development": (
            development_summary
        ),

        "held_out": (
            held_out_summary
        ),

        "overall": {

            **overall_summary,

            "average_latency_ms": (
                mean(latencies)
                if latencies
                else 0.0
            ),

            "p95_latency_ms": percentile(
                latencies,
                0.95
            ),
        },
    }

    output = {

        "summary": summary,

        "cases": all_results,
    }

    with open(
        RESULTS_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("=" * 60)
    print("V6.1 PURPLE TEAM BENCHMARK")
    print("=" * 60)

    print(
        f"Total cases: "
        f"{len(all_results)}"
    )

    print()
    print("DEVELOPMENT")
    print("-" * 60)

    print(
        f"Cases: "
        f"{development_summary['cases']}"
    )

    print(
        f"Detection rate: "
        f"{development_summary['detection_rate']:.4f}"
    )

    print(
        f"Bypass rate: "
        f"{development_summary['bypass_rate']:.4f}"
    )

    print(
        f"Precision: "
        f"{development_summary['precision']:.4f}"
    )

    print(
        f"Recall: "
        f"{development_summary['recall']:.4f}"
    )

    print(
        f"F1: "
        f"{development_summary['f1']:.4f}"
    )

    print()
    print("HELD-OUT")
    print("-" * 60)

    print(
        f"Cases: "
        f"{held_out_summary['cases']}"
    )

    print(
        f"Detection rate: "
        f"{held_out_summary['detection_rate']:.4f}"
    )

    print(
        f"Bypass rate: "
        f"{held_out_summary['bypass_rate']:.4f}"
    )

    print(
        f"Precision: "
        f"{held_out_summary['precision']:.4f}"
    )

    print(
        f"Recall: "
        f"{held_out_summary['recall']:.4f}"
    )

    print(
        f"F1: "
        f"{held_out_summary['f1']:.4f}"
    )

    print()
    print("OVERALL")
    print("-" * 60)

    print(
        f"Average latency: "
        f"{summary['overall']['average_latency_ms']:.4f} ms"
    )

    print(
        f"P95 latency: "
        f"{summary['overall']['p95_latency_ms']:.4f} ms"
    )

    print()
    print("CASE RESULTS")
    print("-" * 60)

    for result in all_results:

        print(
            f"{result['id']} | "
            f"{result['split']} | "
            f"{result['category']} | "
            f"{result['detection_status']} | "
            f"{result['bypass_status']} | "
            f"risk={result['final_risk']['total_risk']}"
        )

    print()
    print(
        "Results saved to: "
        f"{RESULTS_PATH}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()