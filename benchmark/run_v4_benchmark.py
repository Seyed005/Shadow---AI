import json
import statistics
import sys
import time
from pathlib import Path


# Allow direct execution:
# python benchmark/run_v4_benchmark.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from detection.detection_pipeline import run_detection


CORPUS_PATH = PROJECT_ROOT / "benchmark" / "attack_corpus_v4.json"
RESULTS_DIR = PROJECT_ROOT / "benchmark" / "results"
RESULTS_PATH = RESULTS_DIR / "v4_unicode_results.json"


def evaluate_case(case, enable_confusables):
    start = time.perf_counter()

    findings = run_detection(
        case["text"],
        enable_canonicalization=True,
        enable_confusables=enable_confusables,
    )

    latency_ms = (time.perf_counter() - start) * 1000

    detected_entities = {
        finding["type"]
        for finding in findings
    }

    expected_entities = set(
        case["expected_entities"]
    )

    detected = bool(
        expected_entities.intersection(
            detected_entities
        )
    )

    return {
        "id": case["id"],
        "category": case["category"],
        "expected_entities": sorted(
            expected_entities
        ),
        "detected_entities": sorted(
            detected_entities
        ),
        "detected": detected,
        "bypass": not detected,
        "latency_ms": latency_ms,
        "findings": findings,
    }


def run_version(corpus, enable_confusables):

    results = [
        evaluate_case(
            case,
            enable_confusables
        )
        for case in corpus
    ]

    detection_rate = (
        sum(
            result["detected"]
            for result in results
        )
        / len(results)
    )

    bypass_rate = (
        sum(
            result["bypass"]
            for result in results
        )
        / len(results)
    )

    latencies = [
        result["latency_ms"]
        for result in results
    ]

    return {
        "detection_rate": detection_rate,
        "bypass_rate": bypass_rate,
        "average_latency_ms": statistics.mean(
            latencies
        ),
        "results": results,
    }


def main():

    with open(
        CORPUS_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        corpus = json.load(file)

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print()
    print("========================================")
    print("V4 UNICODE HOMOGLYPH BENCHMARK")
    print("========================================")

    print(
        f"Corpus cases: {len(corpus)}"
    )

    print()
    print("Running V3 baseline...")

    v3 = run_version(
        corpus,
        enable_confusables=False
    )

    print("Running V4 hardened...")

    v4 = run_version(
        corpus,
        enable_confusables=True
    )

    detection_improvement = (
        v4["detection_rate"]
        - v3["detection_rate"]
    )

    bypass_reduction = (
        v3["bypass_rate"]
        - v4["bypass_rate"]
    )

    latency_change = (
        v4["average_latency_ms"]
        - v3["average_latency_ms"]
    )

    output = {

        "experiment":
            "V3_vs_V4_unicode_homoglyph_hardening",

        "corpus":
            str(
                CORPUS_PATH.relative_to(
                    PROJECT_ROOT
                )
            ),

        "cases":
            len(corpus),

        "v3_baseline":
            v3,

        "v4_hardened":
            v4,

        "comparison": {

            "detection_rate_improvement":
                detection_improvement,

            "bypass_rate_reduction":
                bypass_reduction,

            "average_latency_change_ms":
                latency_change
        }
    }

    with open(
        RESULTS_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            indent=4,
            ensure_ascii=False
        )

    print()
    print("========================================")
    print("RESULTS")
    print("========================================")

    print(
        f"V3 detection rate: "
        f"{v3['detection_rate']:.4f}"
    )

    print(
        f"V4 detection rate: "
        f"{v4['detection_rate']:.4f}"
    )

    print(
        f"V3 bypass rate: "
        f"{v3['bypass_rate']:.4f}"
    )

    print(
        f"V4 bypass rate: "
        f"{v4['bypass_rate']:.4f}"
    )

    print(
        f"Detection improvement: "
        f"{detection_improvement:+.4f}"
    )

    print(
        f"Bypass reduction: "
        f"{bypass_reduction:+.4f}"
    )

    print(
        f"V3 average latency: "
        f"{v3['average_latency_ms']:.4f} ms"
    )

    print(
        f"V4 average latency: "
        f"{v4['average_latency_ms']:.4f} ms"
    )

    print()
    print(
        f"Saved results to: "
        f"{RESULTS_PATH}"
    )


if __name__ == "__main__":
    main()