[CmdletBinding(SupportsShouldProcess = $true)]
param()

$ErrorActionPreference = 'Stop'

function Get-RepoRoot {
  return (Resolve-Path (Join-Path $PSScriptRoot '..\..'))
}

$RepoRoot = (Get-RepoRoot).Path

# SEC-AIOPS-012: cleanup safety is embedded and cannot be replaced by an
# environment-selected dot-sourced file. Reject the legacy override explicitly
# so a caller cannot believe its guard implementation was honored.
if ($env:RE_GUARDS_PATH) {
  throw "RE_GUARDS_PATH is unsupported; cleanup uses embedded fixed guards"
}

function Test-EmbeddedInRoot {
  param([string]$Path, [string]$Root = $RepoRoot)
  $lexicalPath = [IO.Path]::GetFullPath($Path)
  $lexicalRoot = [IO.Path]::GetFullPath($Root)
  $sep = [IO.Path]::DirectorySeparatorChar
  if ($lexicalPath -ne $lexicalRoot -and
      -not $lexicalPath.StartsWith($lexicalRoot + $sep, [System.StringComparison]::OrdinalIgnoreCase)) {
    return $false
  }
  $relative = if ($lexicalPath -eq $lexicalRoot) { @() } else {
    $lexicalPath.Substring($lexicalRoot.Length).TrimStart('\', '/') -split '[\\/]'
  }
  $current = $lexicalRoot
  foreach ($part in $relative) {
    if ([string]::IsNullOrWhiteSpace($part)) { continue }
    $current = Join-Path $current $part
    if (Test-Path -LiteralPath $current) {
      $item = Get-Item -LiteralPath $current -Force -ErrorAction Stop
      if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { return $false }
    }
  }
  try {
    $resolvedPath = (Resolve-Path -LiteralPath $lexicalPath -ErrorAction Stop).Path
    $resolvedRoot = (Resolve-Path -LiteralPath $lexicalRoot -ErrorAction Stop).Path
    return ($resolvedPath -eq $resolvedRoot) -or
      $resolvedPath.StartsWith($resolvedRoot + $sep, [System.StringComparison]::OrdinalIgnoreCase)
  }
  catch { return $false }
}

function Remove-EmbeddedSafe {
  param([string]$Path, [switch]$Permanent, [switch]$WhatIf)
  if (-not (Test-EmbeddedInRoot -Path $Path)) { throw "Path outside embedded repo guard: $Path" }
  $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
  if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
    throw "Refusing to remove a symlink/reparse point: $Path"
  }
  Remove-Item -LiteralPath $Path -Recurse -Force -WhatIf:$WhatIf
}

$cutoff = (Get-Date).AddDays(-14)
$sandbox = Join-Path $RepoRoot '90_Sandbox'
if (-not (Test-EmbeddedInRoot $sandbox)) { throw "Sandbox path outside repo root" }
Get-ChildItem -LiteralPath $sandbox -Force -ErrorAction SilentlyContinue | ForEach-Object {
  if ($_.LastWriteTime -lt $cutoff) {
    Remove-EmbeddedSafe -Path $_.FullName -WhatIf:$WhatIfPreference
  }
}
