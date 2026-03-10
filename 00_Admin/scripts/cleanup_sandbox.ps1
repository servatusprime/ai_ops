$ErrorActionPreference = 'Stop'

function Get-RepoRoot {
  return (Resolve-Path (Join-Path $PSScriptRoot '..\..'))
}

$RepoRoot = (Get-RepoRoot).Path

if ($env:RE_GUARDS_PATH -and (Test-Path $env:RE_GUARDS_PATH)) {
  . $env:RE_GUARDS_PATH
}

if (-not (Get-Command Test-InRoot -ErrorAction SilentlyContinue)) {
  function Test-InRoot {
    param([string]$Path, [string]$Root = $RepoRoot)
    return (Resolve-Path $Path).Path.StartsWith((Resolve-Path $Root).Path)
  }
}

if (-not (Get-Command Remove-Safe -ErrorAction SilentlyContinue)) {
  function Remove-Safe {
    param([string]$Path, [switch]$Permanent, [switch]$WhatIf)
    Remove-Item -LiteralPath $Path -Recurse -Force -WhatIf:$WhatIf
  }
}

$cutoff = (Get-Date).AddDays(-14)
$sandbox = Join-Path $RepoRoot '90_Sandbox'
if (-not (Test-InRoot $sandbox)) { throw "Sandbox path outside repo root" }
Get-ChildItem -LiteralPath $sandbox -Force -ErrorAction SilentlyContinue | ForEach-Object {
  if ($_.LastWriteTime -lt $cutoff) {
    Remove-Safe -Path $_.FullName -WhatIf:\False
  }
}
