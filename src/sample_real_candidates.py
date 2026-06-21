import json

count = 0

with open("data/candidates.jsonl") as f:
    for line in f:
        c = json.loads(line)

        title = c["profile"]["current_title"]

        if "recommendation" in title.lower():
            print(json.dumps(c, indent=2))
            break
