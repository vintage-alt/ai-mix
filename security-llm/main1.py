with open("idor_candidates.py") as f:
    burp_data = f.read()

prompt = system_prompt + """

Analyze these endpoints.
For each:
- Why it might be vulnerable
- What to test next
- Example payloads
""" + burp_data
