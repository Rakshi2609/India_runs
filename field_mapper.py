import json

with open("data/sample_candidates.json") as f:
    candidates = json.load(f)

def walk(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            walk(v, f"{prefix}.{k}" if prefix else k)

    elif isinstance(obj, list):
        if len(obj) > 0:
            walk(obj[0], prefix)

    else:
        print(prefix, "->", type(obj).__name__)

print("=" * 80)
print("FIELD MAP")
print("=" * 80)

walk(candidates[0])
