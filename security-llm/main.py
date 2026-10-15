import subprocess

with open("prompts/system.txt", "r") as f:
    system_prompt = f.read()

with open("summary.txt", "r") as f:
    burp_data = f.read()

prompt = system_prompt + "\n\nAnalyze these endpoints:\n" + burp_data

result = subprocess.run(
    ["ollama", "run", "llama3.1:8b"],
    input=prompt,
    text=True,
    capture_output=True
)

print(result.stdout)
