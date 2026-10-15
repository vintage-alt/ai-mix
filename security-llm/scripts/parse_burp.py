from lxml import etree

INPUT = "history.json"
OUTPUT = "summary.txt"

interesting = []

print("[*] Parsing Burp XML (recovery mode)...")

parser = etree.XMLParser(
    recover=True,      # 🔥 key fix
    huge_tree=True     # allow very large files
)

tree = etree.parse(INPUT, parser)
root = tree.getroot()

for item in root.findall("item"):
    method = item.findtext("method", default="")
    url = item.findtext("url", default="")
    status = item.findtext("status", default="")
    length = item.findtext("responseLength", default="")

    if url:
        interesting.append(
            f"{method} {url} → {status} (len={length})"
        )

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(interesting))

print(f"[+] Extracted {len(interesting)} endpoints")
print(f"[+] Output written to {OUTPUT}")
