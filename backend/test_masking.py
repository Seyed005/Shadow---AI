from backend.masking import mask_sensitive_data


text = "Password: DemoPass123"


findings = [
    {
        "type": "PASSWORD",
        "start": 10,
        "end": 21
    }
]


result = mask_sensitive_data(
    text,
    findings
)


print("Original:")
print(text)

print("Sanitized:")
print(result)