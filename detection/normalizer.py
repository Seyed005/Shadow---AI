def canonical_type(entity_type):
    """
    Convert detector-specific entity names
    into one common Shadow AI entity name.
    """

    mapping = {
        "EMAIL_ADDRESS": "EMAIL",
        "PHONE_NUMBER": "PHONE",
        "IP_ADDRESS": "IP_ADDRESS",
        "PERSON": "PERSON",
        "PASSWORD": "PASSWORD",
        "EMPLOYEE_ID": "EMPLOYEE_ID",
        "API_KEY_LIKE": "API_KEY_LIKE",
    }

    return mapping.get(entity_type, entity_type)


def normalize_findings(findings):
    """
    Normalize detector outputs and remove duplicate findings.
    """

    merged = []

    for finding in findings:

        entity_type = canonical_type(
            finding.get("type")
        )

        start = finding.get("start")
        end = finding.get("end")

        confidence = finding.get(
            "confidence",
            finding.get("score", 1.0)
        )

        source = finding.get(
            "source",
            "UNKNOWN"
        )

        new_finding = {
            "type": entity_type,
            "source": source,
            "confidence": confidence,
            "start": start,
            "end": end
        }

        duplicate = False

        for existing in merged:

            # Different entity types cannot be duplicates.
            if existing["type"] != entity_type:
                continue

            # ------------------------------------------------
            # Case 1: Both findings have valid positions
            # ------------------------------------------------
            if (
                start is not None
                and end is not None
                and existing["start"] is not None
                and existing["end"] is not None
            ):

                overlaps = (
                    start < existing["end"]
                    and end > existing["start"]
                )

                if overlaps:
                    duplicate = True

            # ------------------------------------------------
            # Case 2: Both findings have NO positions
            # ------------------------------------------------
            elif (
                start is None
                and end is None
                and existing["start"] is None
                and existing["end"] is None
            ):

                # We cannot prove these are duplicates.
                # Keep both findings.
                duplicate = False

            # ------------------------------------------------
            # Case 3: Only one finding has positions
            # ------------------------------------------------
            else:

                # We cannot safely determine duplication.
                duplicate = False

            if duplicate:

                existing["source"] = (
                    existing["source"]
                    + "+"
                    + source
                )

                existing["confidence"] = max(
                    existing["confidence"],
                    confidence
                )

                break

        if not duplicate:
            merged.append(new_finding)

    return merged


if __name__ == "__main__":

    test_findings = [

        {
            "type": "EMAIL",
            "source": "BASIC",
            "confidence": 1.0,
            "start": 12,
            "end": 28
        },

        {
            "type": "EMAIL_ADDRESS",
            "source": "PRESIDIO",
            "confidence": 1.0,
            "start": 12,
            "end": 28
        },

        {
            "type": "EMPLOYEE_ID",
            "source": "CUSTOM",
            "confidence": 0.95,
            "start": 40,
            "end": 51
        }
    ]

    result = normalize_findings(test_findings)

    print("Deduplicated Findings:")

    for finding in result:
        print(finding)