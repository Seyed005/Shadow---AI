import json
import math
import sys
import time
from pathlib import Path


# =========================================================
# EXPERIMENT VERSION
# =========================================================

EXPERIMENT_VERSION = (
    sys.argv[1].upper()
    if len(sys.argv) > 1
    else "V1"
)


# =========================================================
# PROJECT PATH
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# =========================================================
# SHADOW AI IMPORTS
# =========================================================

from detection.detection_pipeline import run_detection
from detection.normalizer import normalize_findings

from processing.pdf_processor import extract_pdf_content
from processing.docx_processor import extract_docx_content
from processing.xlsx_processor import extract_xlsx_content
from processing.pptx_processor import extract_pptx_content
from processing.image_processor import extract_image_content


# =========================================================
# PATHS
# =========================================================

CORPUS_PATH = (
    BASE_DIR
    / "benchmark"
    / "attack_corpus.json"
)

RESULTS_DIR = (
    BASE_DIR
    / "benchmark"
    / "results"
)


# =========================================================
# MULTIMODAL PROCESSORS
# =========================================================

PROCESSORS = {
    "PDF": extract_pdf_content,
    "DOCX": extract_docx_content,
    "XLSX": extract_xlsx_content,
    "PPTX": extract_pptx_content,
    "IMAGE": extract_image_content,
}


# =========================================================
# LOAD CORPUS
# =========================================================

def load_corpus():

    with open(
        CORPUS_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# =========================================================
# GET INPUT TEXT
# =========================================================

def get_input_text(case):

    modality = case["modality"]

    # -----------------------------
    # TEXT CASE
    # -----------------------------

    if modality == "TEXT":

        return case["input"]

    # -----------------------------
    # MULTIMODAL CASE
    # -----------------------------

    file_path = BASE_DIR / case["file"]

    if not file_path.exists():

        raise FileNotFoundError(
            f"Benchmark file not found: {file_path}"
        )

    processor = PROCESSORS.get(modality)

    if processor is None:

        raise ValueError(
            f"Unsupported benchmark modality: "
            f"{modality}"
        )

    result = processor(
        str(file_path)
    )

    return result["text"]


# =========================================================
# ENTITY EXTRACTION
# =========================================================

def normalize_entity_types(findings):

    return {
        finding["type"]
        for finding in findings
        if finding.get("type")
    }


# =========================================================
# ENTITY METRICS
# =========================================================

def calculate_entity_metrics(
    expected_entities,
    detected_entities
):

    expected = set(
        expected_entities
    )

    detected = set(
        detected_entities
    )

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

        else 0.0
    )

    recall = (

        true_positive
        / recall_denominator

        if recall_denominator

        else 0.0
    )

    if precision + recall:

        f1 = (
            2
            * precision
            * recall
            / (precision + recall)
        )

    else:

        f1 = 0.0

    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


# =========================================================
# P95 LATENCY
# =========================================================

def percentile_95(values):

    if not values:

        return 0.0

    ordered = sorted(values)

    index = (
        math.ceil(
            0.95
            * len(ordered)
        )
        - 1
    )

    index = max(
        0,
        min(
            index,
            len(ordered) - 1
        )
    )

    return ordered[index]


# =========================================================
# RUN ONE CASE
# =========================================================

def run_case(case):

    start_time = (
        time.perf_counter()
    )

    input_text = get_input_text(
        case
    )

    raw_findings = run_detection(
        input_text
    )

    findings = normalize_findings(
        raw_findings
    )

    detected_entities = (
        normalize_entity_types(
            findings
        )
    )

    expected_entities = set(
        case.get(
            "expected_entities",
            []
        )
    )

    metrics = calculate_entity_metrics(
        expected_entities,
        detected_entities
    )

    expected_detection = case.get(
        "expected_detection",
        False
    )

    # ---------------------------------------------
    # Attack-level detection result
    # ---------------------------------------------

    if expected_detection:

        detection_success = (
            len(detected_entities) > 0
        )

    else:

        detection_success = (
            len(detected_entities) == 0
        )

    latency_ms = (
        time.perf_counter()
        - start_time
    ) * 1000

    return {

        "attack_id":
            case["attack_id"],

        "category":
            case["category"],

        "modality":
            case["modality"],

        "expected_entities":
            sorted(expected_entities),

        "detected_entities":
            sorted(detected_entities),

        "findings":
            findings,

        "expected_detection":
            expected_detection,

        "detection_success":
            detection_success,

        "true_positive":
            metrics[
                "true_positive"
            ],

        "false_positive":
            metrics[
                "false_positive"
            ],

        "false_negative":
            metrics[
                "false_negative"
            ],

        "precision":
            metrics[
                "precision"
            ],

        "recall":
            metrics[
                "recall"
            ],

        "f1":
            metrics[
                "f1"
            ],

        "latency_ms":
            latency_ms,
    }


# =========================================================
# AGGREGATE RESULTS
# =========================================================

def aggregate_results(results):

    total_tp = sum(
        result["true_positive"]
        for result in results
    )

    total_fp = sum(
        result["false_positive"]
        for result in results
    )

    total_fn = sum(
        result["false_negative"]
        for result in results
    )

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

        else 0.0
    )

    recall = (

        total_tp
        / recall_denominator

        if recall_denominator

        else 0.0
    )

    if precision + recall:

        f1 = (
            2
            * precision
            * recall
            / (precision + recall)
        )

    else:

        f1 = 0.0

    total_cases = len(
        results
    )

    successful_cases = sum(

        1

        for result in results

        if result[
            "detection_success"
        ]
    )

    detection_rate = (

        successful_cases
        / total_cases

        if total_cases

        else 0.0
    )

    bypass_rate = (
        1 - detection_rate
    )

    latencies = [

        result["latency_ms"]

        for result in results
    ]

    average_latency = (

        sum(latencies)
        / len(latencies)

        if latencies

        else 0.0
    )

    benign_results = [

        result

        for result in results

        if result["category"]
        == "BENIGN"
    ]

    benign_count = len(
        benign_results
    )

    benign_false_positives = sum(

        1

        for result
        in benign_results

        if result[
            "detected_entities"
        ]
    )

    false_positive_rate = (

        benign_false_positives
        / benign_count

        if benign_count

        else 0.0
    )

    attack_results = [

        result

        for result in results

        if result["category"]
        != "BENIGN"
    ]

    attack_count = len(
        attack_results
    )

    attack_bypasses = sum(

        1

        for result
        in attack_results

        if not result[
            "detection_success"
        ]
    )

    attack_bypass_rate = (

        attack_bypasses
        / attack_count

        if attack_count

        else 0.0
    )

    return {

        "total_cases":
            total_cases,

        "successful_cases":
            successful_cases,

        "total_true_positive":
            total_tp,

        "total_false_positive":
            total_fp,

        "total_false_negative":
            total_fn,

        "precision":
            precision,

        "recall":
            recall,

        "f1":
            f1,

        "attack_detection_rate":
            detection_rate,

        "bypass_rate":
            bypass_rate,

        "average_latency_ms":
            average_latency,

        "p95_latency_ms":
            percentile_95(
                latencies
            ),

        "benign_cases":
            benign_count,

        "benign_false_positives":
            benign_false_positives,

        "false_positive_rate":
            false_positive_rate,

        "attack_cases":
            attack_count,

        "attack_bypasses":
            attack_bypasses,

        "attack_bypass_rate":
            attack_bypass_rate,
    }


# =========================================================
# PRINT SUMMARY
# =========================================================

def print_summary(summary):

    print()
    print("=" * 60)
    print(
        f"SHADOW AI "
        f"{EXPERIMENT_VERSION} "
        f"BENCHMARK"
    )
    print("=" * 60)

    print(
        f"Total cases:          "
        f"{summary['total_cases']}"
    )

    print(
        f"Successful cases:     "
        f"{summary['successful_cases']}"
    )

    print(
        f"True positives:       "
        f"{summary['total_true_positive']}"
    )

    print(
        f"False positives:      "
        f"{summary['total_false_positive']}"
    )

    print(
        f"False negatives:      "
        f"{summary['total_false_negative']}"
    )

    print(
        f"Precision:            "
        f"{summary['precision']:.4f}"
    )

    print(
        f"Recall:               "
        f"{summary['recall']:.4f}"
    )

    print(
        f"F1:                   "
        f"{summary['f1']:.4f}"
    )

    print(
        f"Detection rate:       "
        f"{summary['attack_detection_rate']:.4f}"
    )

    print(
        f"Bypass rate:          "
        f"{summary['bypass_rate']:.4f}"
    )

    print(
        f"Average latency:      "
        f"{summary['average_latency_ms']:.2f} ms"
    )

    print(
        f"P95 latency:          "
        f"{summary['p95_latency_ms']:.2f} ms"
    )

    print(
        f"Benign-case FPR:      "
        f"{summary['false_positive_rate']:.4f}"
    )

    print(
        f"Attack bypass rate:   "
        f"{summary['attack_bypass_rate']:.4f}"
    )

    print("=" * 60)


# =========================================================
# MAIN BENCHMARK
# =========================================================

def main():

    print()
    print(
        f"Loading Shadow AI "
        f"{EXPERIMENT_VERSION} benchmark..."
    )

    print(
        f"Corpus: {CORPUS_PATH}"
    )

    corpus = load_corpus()

    cases = corpus["cases"]

    print(
        f"Cases loaded: {len(cases)}"
    )

    results = []

    for case in cases:

        print()
        print(
            f"Running "
            f"{case['attack_id']}..."
        )

        try:

            result = run_case(
                case
            )

            results.append(
                result
            )

            print(
                f"  Expected: "
                f"{result['expected_entities']}"
            )

            print(
                f"  Detected: "
                f"{result['detected_entities']}"
            )

            print(
                f"  Latency: "
                f"{result['latency_ms']:.2f} ms"
            )

        except Exception as error:

            print(
                f"  ERROR: {error}"
            )

            results.append({

                "attack_id":
                    case["attack_id"],

                "category":
                    case["category"],

                "modality":
                    case["modality"],

                "error":
                    str(error),
            })

    valid_results = [

        result

        for result in results

        if "error" not in result
    ]

    summary = aggregate_results(
        valid_results
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output = {

        "experiment_version":
            EXPERIMENT_VERSION,

        "corpus_version":
            corpus[
                "benchmark_version"
            ],

        "summary":
            summary,

        "results":
            results,
    }

    # ---------------------------------------------
    # Experiment-specific output filename
    # ---------------------------------------------

    if EXPERIMENT_VERSION == "V1":

        output_filename = (
            "v1_baseline_results.json"
        )

    elif EXPERIMENT_VERSION == "V2":

        output_filename = (
            "v2_results.json"
        )

    elif EXPERIMENT_VERSION == "V3":

        output_filename = (
            "v3_results.json"
        )

    else:

        output_filename = (
            f"{EXPERIMENT_VERSION.lower()}"
            f"_results.json"
        )

    output_path = (
        RESULTS_DIR
        / output_filename
    )

    # ---------------------------------------------
    # Safety: never overwrite an existing experiment
    # ---------------------------------------------

    if output_path.exists():

        raise FileExistsError(
            "\nExperiment result already exists:\n"
            f"{output_path}\n\n"
            "The benchmark was NOT overwritten.\n"
            "Choose a new experiment version."
        )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            indent=2
        )

    print_summary(
        summary
    )

    print()
    print(
        "Results saved to:"
    )

    print(
        output_path
    )


# =========================================================
# SCRIPT ENTRY POINT
# =========================================================

if __name__ == "__main__":

    main()