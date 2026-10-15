import re

INPUT = "data/burp/filtered.txt"
OUTPUT = "data/burp/idor_candidates.txt"

idors = []

with open(INPUT, "r") as f:
    for line in f:
        if re.search(r"(id=|user|account|order)", line.lower()):
            idors.append(line.strip())

with open(OUTPUT, "w") as f:
    f.write("\n".join(idors))

print(f"[+] Found {len(idors)} IDOR candidates")
