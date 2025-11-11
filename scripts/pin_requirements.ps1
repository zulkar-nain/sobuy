# PowerShell helper to pin requirements.txt using the current Python interpreter
# Usage (PowerShell):
#   .\.venv\Scripts\Activate.ps1
#   .\scripts\pin_requirements.ps1

$python = $env:PYTHON_EXE
if (-not $python) { $python = 'python' }
$root = Join-Path $PSScriptRoot '..'
$req = Join-Path $root 'requirements.txt'

Write-Output "Using interpreter: $(& $python -c 'import sys; print(sys.executable)')"
& $python -m pip freeze > $req
Write-Output "Pinned requirements written to $req"
Write-Output "Review the file, then commit: git add requirements.txt; git commit -m 'chore: pin requirements'"
