import re

INPUT = "summary.txt"
OUTPUT = "filtered.txt"

patterns = [
    r"id=",
    r"user",
    r"account",
    r"order",
    r"api",
    r"admin"
]

filtered = []

with open(INPUT, "r", encoding="utf-8") as f:
    for line in f:
        if any(re.search(p, line.lower()) for p in patterns):
            filtered.append(line.strip())

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(filtered))

print(f"[+] Filtered {len(filtered)} high-risk endpoints")
