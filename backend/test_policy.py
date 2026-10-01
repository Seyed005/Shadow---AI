from backend.policy import get_policy_decision


test_cases = [
    {
        "total_risk": 5
    },
    {
        "total_risk": 20
    },
    {
        "total_risk": 50
    },
    {
        "total_risk": 107.5
    }
]


for test_case in test_cases:

    result = get_policy_decision(
        test_case
    )

    print(
        f"Risk: {test_case['total_risk']} "
        f"→ {result}"
    )