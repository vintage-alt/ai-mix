import subprocess
from pathlib import Path
import re
from lxml import etree
from urllib.parse import urlparse, parse_qs
from collections import defaultdict
import sys

sys.stdout.reconfigure(encoding="utf-8")

print("[SCRIPT STARTED]", flush=True)

# ---------------- CONFIG ----------------
BURP_DIR = Path("data/burp")
SYSTEM_PROMPT_FILE = "prompts/system.txt"
MODEL = "llama3.1:8b"
MAX_ENDPOINTS = 15
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)
# --------------------------------------


def load_system_prompt():
    print("[*] Loading system prompt...")
    return Path(SYSTEM_PROMPT_FILE).read_text(encoding="utf-8")


def parse_burp_xml():
    print("[*] Parsing Burp XML files...")
    endpoints = []

    parser = etree.XMLParser(
        recover=True,
        huge_tree=True,
        no_network=True
    )

    xml_files = list(BURP_DIR.glob("*.xml"))
    print(f"[+] Found {len(xml_files)} XML file(s)")

    for xml in xml_files:
        print(f"[+] Parsing {xml.name} (this may take time)...")
        tree = etree.parse(str(xml), parser)
        items = tree.xpath("//item")
        print(f"[+] Found {len(items)} items")

        for i, item in enumerate(items, 1):
            if i % 5000 == 0:
                print(f"    Processed {i} items")

            url = item.findtext("url") or ""
            method = item.findtext("method") or ""
            request = item.findtext("request") or ""

            auth = bool(re.search(r"authorization:|cookie:", request, re.I))

            if url and method:
                endpoints.append({
                    "url": url,
                    "method": method,
                    "auth": auth
                })

    print(f"[+] Total raw endpoints collected: {len(endpoints)}")
    return endpoints


def summarize_endpoints(endpoints):
    print("[*] Summarizing endpoints...")
    grouped = defaultdict(lambda: {
        "count": 0,
        "methods": set(),
        "params": set(),
        "auth_related": False
    })

    for e in endpoints:
        parsed = urlparse(e["url"])
        path = parsed.path
        params = parse_qs(parsed.query)

        g = grouped[path]
        g["count"] += 1
        g["methods"].add(e["method"])
        g["params"].update(params.keys())

        if e["auth"] or any(k in path.lower() for k in ["auth", "login", "saml", "oauth", "redirect", "token"]):
            g["auth_related"] = True

    summaries = []
    for path, data in grouped.items():
        summaries.append({
            "endpoint": path,
            "methods": list(data["methods"]),
            "parameters": list(data["params"]),
            "count": data["count"],
            "auth_related": data["auth_related"]
        })

    print(f"[+] Summarized into {len(summaries)} unique endpoints")
    return summaries


def select_interesting_endpoints(summaries):
    print("[*] Selecting high-risk endpoints...")

    def score(e):
        s = 0
        if e["auth_related"]:
            s += 5
        if any(p.lower() in ["id", "token", "user", "query"] for p in e["parameters"]):
            s += 3
        s += min(e["count"] // 50, 5)
        return s

    summaries.sort(key=score, reverse=True)
    selected = summaries[:MAX_ENDPOINTS]

    print(f"[+] Selected {len(selected)} endpoints for LLM analysis")
    return selected


def build_prompt(system_prompt, endpoints):
    print("[*] Building LLM prompt...")
    lines = [system_prompt, "\nAnalyze the following endpoints:\n"]

    for e in endpoints:
        lines.append(
            f"""
Endpoint: {e['endpoint']}
Methods: {', '.join(e['methods'])}
Parameters: {', '.join(e['parameters']) or 'None'}
Auth related: {e['auth_related']}
Seen requests: {e['count']}
"""
        )

    prompt = "\n".join(lines)
    print(f"[+] Prompt size ~ {len(prompt) // 1024} KB")
    return prompt


def run_llm(prompt):
    print("[*] Running Ollama (this WILL take time)...")

    proc = subprocess.run(
        ["ollama", "run", MODEL],
        input=prompt.encode("utf-8"),
        capture_output=True
    )

    output = proc.stdout.decode("utf-8", errors="ignore")
    print("[+] Ollama finished")
    return output


def main():
    system_prompt = load_system_prompt()
    raw = parse_burp_xml()
    summaries = summarize_endpoints(raw)
    interesting = select_interesting_endpoints(summaries)

    if not interesting:
        print("[!] No interesting endpoints found")
        return

    prompt = build_prompt(system_prompt, interesting)
    result = run_llm(prompt)

    out_file = OUTPUT_DIR / "analysis.txt"
    out_file.write_text(result, encoding="utf-8")

    print("\n========== AI BUG ANALYSIS ==========\n")
    print(result)
    print("\n===================================")
    print(f"[+] Saved to {out_file}")


if __name__ == "__main__":
    main()
