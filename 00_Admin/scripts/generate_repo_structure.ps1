$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $PSCommandPath
$pyScript = Join-Path $scriptDir "generate_repo_structure.py"

if (-not (Test-Path $pyScript -PathType Leaf)) {
    throw "Missing script: $pyScript"
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "python not found in PATH; required for repo structure generation."
}

& python $pyScript
if ($LASTEXITCODE -ne 0) {
    throw "generate_repo_structure.py failed with exit code $LASTEXITCODE"
}
