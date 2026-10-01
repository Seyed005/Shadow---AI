import json
import statistics
import sys
import time
from pathlib import Path

# Add the project root to Python's import path.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT)
    )

from detection.detection_pipeline import run_detection


CORPUS_PATH = Path(
    "benchmark/attack_corpus_v3.json"
)

RESULT_PATH = Path(
    "benchmark/results/v3_unicode_results.json"
)


def load_cases():
    with CORPUS_PATH.open(
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def run_experiment(
    cases,
    canonicalization_enabled
):
    results = []

    total_expected = 0
    total_detected = 0
    latencies = []

    for case in cases:

        start_time = time.perf_counter()

        findings = run_detection(
            case["text"],
            enable_canonicalization=(
                canonicalization_enabled
            )
        )

        elapsed_ms = (
            time.perf_counter()
            - start_time
        ) * 1000

        detected_types = {
            finding["type"]
            for finding in findings
        }

        expected_types = set(
            case["expected_entities"]
        )

        detected_expected = (
            expected_types
            & detected_types
        )

        total_expected += len(
            expected_types
        )

        total_detected += len(
            detected_expected
        )

        latencies.append(
            elapsed_ms
        )

        results.append({
            "id": case["id"],
            "expected_entities": sorted(
                expected_types
            ),
            "detected_entities": sorted(
                detected_expected
            ),
            "all_detected_types": sorted(
                detected_types
            ),
            "detected": (
                expected_types
                <= detected_types
            ),
            "latency_ms": elapsed_ms
        })

    detection_rate = (
        total_detected / total_expected
        if total_expected
        else 0.0
    )

    bypass_rate = (
        1.0 - detection_rate
    )

    average_latency = (
        statistics.mean(latencies)
        if latencies
        else 0.0
    )

    return {
        "total_cases": len(cases),
        "total_expected_entities": (
            total_expected
        ),
        "total_detected_expected_entities": (
            total_detected
        ),
        "detection_rate": detection_rate,
        "bypass_rate": bypass_rate,
        "average_latency_ms": (
            average_latency
        ),
        "results": results
    }


def main():

    cases = load_cases()

    print("=" * 60)
    print("V3 UNICODE RED TEAM BENCHMARK")
    print("=" * 60)

    print(
        f"Corpus cases: {len(cases)}"
    )

    # -------------------------------------------------
    # V2 baseline
    # -------------------------------------------------

    print("\nRunning V2 baseline...")

    v2 = run_experiment(
        cases,
        canonicalization_enabled=False
    )

    # -------------------------------------------------
    # V3 hardened detector
    # -------------------------------------------------

    print("Running V3 hardened detector...")

    v3 = run_experiment(
        cases,
        canonicalization_enabled=True
    )

    # -------------------------------------------------
    # Summary
    # -------------------------------------------------

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    print("\nV2")
    print(
        f"Detection rate: "
        f"{v2['detection_rate']:.4f}"
    )

    print(
        f"Bypass rate: "
        f"{v2['bypass_rate']:.4f}"
    )

    print(
        f"Average latency: "
        f"{v2['average_latency_ms']:.2f} ms"
    )

    print("\nV3")
    print(
        f"Detection rate: "
        f"{v3['detection_rate']:.4f}"
    )

    print(
        f"Bypass rate: "
        f"{v3['bypass_rate']:.4f}"
    )

    print(
        f"Average latency: "
        f"{v3['average_latency_ms']:.2f} ms"
    )

    # -------------------------------------------------
    # Improvement
    # -------------------------------------------------

    detection_improvement = (
        v3["detection_rate"]
        - v2["detection_rate"]
    )

    bypass_reduction = (
        v2["bypass_rate"]
        - v3["bypass_rate"]
    )

    print("\nV3 improvement")

    print(
        f"Detection-rate improvement: "
        f"{detection_improvement:.4f}"
    )

    print(
        f"Bypass-rate reduction: "
        f"{bypass_reduction:.4f}"
    )

    # -------------------------------------------------
    # Save results
    # -------------------------------------------------

    output = {
        "experiment_version": "V3",
        "corpus_version": "V3-UNICODE",
        "v2_baseline": v2,
        "v3_hardened": v3,
        "detection_rate_improvement": (
            detection_improvement
        ),
        "bypass_rate_reduction": (
            bypass_reduction
        )
    }

    RESULT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with RESULT_PATH.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            indent=2
        )

    print(
        f"\nResults saved to: "
        f"{RESULT_PATH}"
    )


if __name__ == "__main__":
    main()