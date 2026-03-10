<#
Usage:
  # From repo root (PowerShell 7+ recommended: pwsh)
  pwsh ./00_Admin/scripts/validate_ide_extensions.ps1
  # Auto-install any missing:
  pwsh ./00_Admin/scripts/validate_ide_extensions.ps1 -InstallMissing
#>

param([switch]$InstallMissing)

$ErrorActionPreference = 'Stop'

function Read-Recommendations {
  $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
  $workspaceRoot = Split-Path -Parent $repoRoot
  $candidatePaths = @(
    (Join-Path $workspaceRoot '.vscode\extensions.json'),
    (Join-Path $repoRoot '.vscode\extensions.json')
  )
  $extFile = $candidatePaths | Where-Object { Test-Path $_ } | Select-Object -First 1
  if (-not $extFile) {
    throw "Not found: expected extensions.json at one of: $($candidatePaths -join ', ')"
  }
  # extensions.json is JSONC: allow // and /* */ comments, and trailing commas
  $raw = Get-Content $extFile -Raw
  # Strip block comments
  $san = [System.Text.RegularExpressions.Regex]::Replace($raw, '/\*.*?\*/', '', 'Singleline')
  # Strip line comments
  $san = [System.Text.RegularExpressions.Regex]::Replace($san, '(?m)^\s*//.*$', '')
  # Remove trailing commas before ] or }
  $san = [System.Text.RegularExpressions.Regex]::Replace($san, ',\s*([\]\}])', '$1')
  try {
    ($san | ConvertFrom-Json).recommendations | Sort-Object -Unique
  } catch {
    throw "Failed to parse $extFile after stripping comments/trailing commas."
  }
}

Write-Host "=== IDE Extensions Audit ===" -ForegroundColor Cyan
$recs = Read-Recommendations
if (-not (Get-Command code -ErrorAction SilentlyContinue)) {
  throw "VS Code CLI 'code' not found in PATH. Install VS Code CLI and retry."
}
$installed = code --list-extensions | Sort-Object -Unique

$missing = @($recs | Where-Object { $_ -notin $installed })
$extra   = @($installed | Where-Object { $_ -notin $recs })

Write-Host "`nRecommendations: $($recs.Count)  |  Installed: $($installed.Count)" -ForegroundColor Gray

if ($missing.Count) {
  Write-Host "`nMissing ($($missing.Count)):" -ForegroundColor Yellow
  $missing | ForEach-Object { Write-Host "  - $_" }
} else {
  Write-Host "`nMissing: 0 ✅" -ForegroundColor Green
}

if ($extra.Count) {
  Write-Host "`nExtra/Untracked ($($extra.Count)):" -ForegroundColor DarkYellow
  $extra | ForEach-Object { Write-Host "  - $_" }
  Write-Host "Note: Extra/Untracked extensions are informational and allowed." -ForegroundColor DarkGray
} else {
  Write-Host "`nExtra/Untracked: 0 ✅" -ForegroundColor Green
}

if ($InstallMissing -and $missing.Count) {
  Write-Host "`nInstalling missing extensions..." -ForegroundColor Cyan
  foreach ($id in $missing) {
    Write-Host "  - $id"
    code --install-extension $id | Out-Host
  }
  Write-Host "`nRe-run the audit to confirm. ✅"
} elseif ($missing.Count) {
  $installCmd = 'code --install-extension ' + ($missing -join ' ')
  Write-Host "`nCopy/paste to install missing:" -ForegroundColor Cyan
  Write-Host "  $installCmd"
}

Write-Host ""
