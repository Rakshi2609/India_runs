import json

status = {
    "Schema Discovery": "✅ 100%",
    "JD Analysis": "✅ 100%",
    "Signal Analysis": "✅ 100%",
    "Feature Engineering": "❌ 0%",
    "Semantic Matching": "❌ 0%",
    "Scoring Engine": "❌ 0%",
    "Submission Generation": "❌ 0%"
}

print("=" * 80)
print("CURRENT PROGRESS")
print("=" * 80)
for task, state in status.items():
    print(f"{task:<25} {state}")
