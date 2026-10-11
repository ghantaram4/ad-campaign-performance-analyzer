"""Report potential secrets by location and rule, never by value."""
import json
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[1]
files = subprocess.check_output(['rg', '--files', '--hidden', '--no-ignore', '-g', '!.git/**', '-g', '!.venv/**', '-g', '!.browser-tools/**', '-g', '!__pycache__/**', '-g', '!**/__pycache__/**', '-g', '!.pytest_cache/**'], cwd=root, text=True).splitlines()
rules = {
    'private-key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    'aws-access-key': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'github-token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{50,})\b'),
    'openai-token': re.compile(r'\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}\b'),
    'google-api-key': re.compile(r'\bAIza[A-Za-z0-9_-]{35}\b'),
    'credential-assignment': re.compile(r'''(?i)(?:api[_-]?key|secret[_-]?key|password|access[_-]?token)\s*[:=]\s*["'][^"'\r\n]{8,}["']'''),
}
findings = []
scanned = 0
sensitive_paths = []
for name in files:
    path = root / name
    if path.name == '.env' or path.name.startswith('.env.') or path.name == 'secrets.toml' or path.suffix in {'.pem', '.key', '.p12'}:
        sensitive_paths.append(name)
    if path.stat().st_size > 2 * 1024 * 1024:
        continue
    try:
        content = path.read_text(encoding='utf-8')
    except (UnicodeError, OSError):
        continue
    scanned += 1
    for number, line in enumerate(content.splitlines(), 1):
        for rule, pattern in rules.items():
            if pattern.search(line):
                findings.append({'file': name, 'line': number, 'rule': rule})
report = {'scanned_text_files': scanned, 'findings': findings, 'sensitive_paths': sensitive_paths,
          'scope': 'Current workspace, including ignored files and logs; excludes dependencies, binary/large files and git history. Heuristic scan, not proof of absence.'}
(root / 'validation/secret-scan.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report))
