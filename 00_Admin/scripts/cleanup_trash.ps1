$ErrorActionPreference = 'Stop'

function Get-RepoRoot {
  return (Resolve-Path (Join-Path $PSScriptRoot '..\..'))
}

$RepoRoot = (Get-RepoRoot).Path

# SEC-AIOPS-012: only dot-source a guards file that resolves inside the repo
# root -- an unconditional dot-source of an env-var-controlled path is a code-
# execution gadget if RE_GUARDS_PATH is ever attacker-influenced (compromised
# CI runner config, shared shell profile).
if ($env:RE_GUARDS_PATH -and (Test-Path $env:RE_GUARDS_PATH)) {
  $ResolvedGuardsPath = (Resolve-Path $env:RE_GUARDS_PATH).Path
  $ResolvedRepoRootForGuards = (Resolve-Path $RepoRoot).Path
  if ($ResolvedGuardsPath -eq $ResolvedRepoRootForGuards -or
      $ResolvedGuardsPath.StartsWith($ResolvedRepoRootForGuards + [System.IO.Path]::DirectorySeparatorChar)) {
    . $ResolvedGuardsPath
  } else {
    throw "RE_GUARDS_PATH resolves outside repo root, refusing to dot-source: $ResolvedGuardsPath"
  }
}

if (-not (Get-Command Test-InRoot -ErrorAction SilentlyContinue)) {
  function Test-InRoot {
    # SEC-AIOPS-018: append a trailing separator (or require exact equality)
    # before the prefix comparison, so a sibling directory that merely shares
    # a name prefix (e.g. "ai_ops" vs "ai_ops_evil") cannot pass.
    param([string]$Path, [string]$Root = $RepoRoot)
    $resolvedPath = (Resolve-Path $Path).Path
    $resolvedRoot = (Resolve-Path $Root).Path
    $sep = [System.IO.Path]::DirectorySeparatorChar
    return ($resolvedPath -eq $resolvedRoot) -or $resolvedPath.StartsWith($resolvedRoot + $sep)
  }
}

if (-not (Get-Command Remove-Safe -ErrorAction SilentlyContinue)) {
  function Remove-Safe {
    param([string]$Path, [switch]$Permanent, [switch]$WhatIf)
    Remove-Item -LiteralPath $Path -Recurse -Force -WhatIf:$WhatIf
  }
}

$cutoff = (Get-Date).AddDays(-30)
$trash = Join-Path $RepoRoot '99_Trash'
if (-not (Test-InRoot $trash)) { throw "Trash path outside repo root" }
Get-ChildItem -LiteralPath $trash -Force -ErrorAction SilentlyContinue | ForEach-Object {
  if ($_.LastWriteTime -lt $cutoff) {
    # PERMANENT delete ONLY inside Trash
    Remove-Safe -Path $_.FullName -Permanent -WhatIf:\False
  }
}
