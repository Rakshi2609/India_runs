import json

status = {
    "Schema Discovery": "✅ 100%",
    "JD Analysis": "✅ 100%",
    "Signal Analysis": "✅ 100%",
    "Feature Engineering": "✅ 100%",
    "Semantic Matching": "✅ 100%",
    "Scoring Engine": "✅ 100%", 
    "Submission Generation": "✅ 100%"
}

print("=" * 80)
print("CURRENT PROGRESS")
print("=" * 80)
for task, state in status.items():
    print(f"{task:<25} {state}")

  