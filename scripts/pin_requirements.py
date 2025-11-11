"""
Script: pin_requirements.py

Run this script using the project's virtualenv Python to generate a pinned
`requirements.txt` from the active environment. It uses the same interpreter
that runs the script (so activate the venv before running), and writes
`requirements.txt` in the project root.

Usage (Linux/macOS):
    source venv/bin/activate
    python scripts/pin_requirements.py

Usage (Windows PowerShell):
    .\.venv\Scripts\Activate.ps1
    python .\scripts\pin_requirements.py

The script will:
 - call `pip freeze` with the current interpreter
 - write the output to `requirements.txt` (backups existing file to requirements.txt.bak)
 - print a short summary

Note: Review the generated `requirements.txt` for any environment-specific
or editable entries you don't want to commit (for example, local paths).
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQ_FILE = os.path.join(ROOT, 'requirements.txt')
BACKUP = REQ_FILE + '.bak'

def main():
    print('Using Python:', sys.executable)
    # run pip freeze via current interpreter to ensure correct env
    try:
        reqs = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True)
    except subprocess.CalledProcessError as e:
        print('ERROR: pip freeze failed:', e)
        sys.exit(1)

    # backup existing requirements.txt
    if os.path.exists(REQ_FILE):
        shutil.copy2(REQ_FILE, BACKUP)
        print(f'Backed up existing requirements.txt to {os.path.basename(BACKUP)}')

    # write new requirements.txt
    with open(REQ_FILE, 'w', encoding='utf-8') as f:
        f.write(reqs)

    lines = [l for l in reqs.splitlines() if l.strip()]
    print(f'Wrote {len(lines)} packages to requirements.txt')
    print('Tip: review the file, remove any local/editable entries, then commit:')
    print('  git add requirements.txt && git commit -m "chore: pin requirements"')

if __name__ == '__main__':
    main()
