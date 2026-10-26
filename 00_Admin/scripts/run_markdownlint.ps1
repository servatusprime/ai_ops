param(
  [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
  [string[]]$Paths
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$callerRoot = (Resolve-Path ".").Path
$config = Join-Path $repoRoot ".markdownlint.json"
$ignore = Join-Path $repoRoot ".markdownlintignore"

function Normalize-MarkdownPaths {
  param(
    [string[]]$InputPaths,
    [string]$RepoRoot,
    [string]$CallerRoot
  )

  $normalized = @()
  foreach ($path in $InputPaths) {
    if ([string]::IsNullOrWhiteSpace($path)) {
      continue
    }

    $candidatePaths = @()
    if ([System.IO.Path]::IsPathRooted($path)) {
      $candidatePaths += $path
    } else {
      $candidatePaths += (Join-Path $CallerRoot $path)
      $candidatePaths += (Join-Path $RepoRoot $path)
      if ($path -like "ai_ops/*") {
        $candidatePaths += (Join-Path $CallerRoot ($path -replace "^ai_ops/", ""))
      }
    }

    $resolved = $null
    foreach ($candidate in $candidatePaths) {
      if (Test-Path $candidate) {
        $resolved = (Resolve-Path -LiteralPath $candidate).Path
        break
      }
    }

    if ($null -eq $resolved) {
      $normalized += $path
      continue
    }

    $baseUri = New-Object System.Uri((Join-Path $RepoRoot ""))
    $targetUri = New-Object System.Uri($resolved)
    $relative = [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($targetUri).ToString()).Replace("/", "\")
    if ($relative -like "..*") {
      $normalized += $resolved
    } else {
      $normalized += $relative
    }
  }

  return $normalized
}

if (-not $Paths -or $Paths.Count -eq 0) {
  $FullRepoLint = $true
  $Paths = & git -C $repoRoot ls-files "*.md"
} else {
  $FullRepoLint = $false
}

if (-not $Paths -or $Paths.Count -eq 0) {
  Write-Host "No markdown files found to lint."
  exit 0
}

$Paths = Normalize-MarkdownPaths -InputPaths $Paths -RepoRoot $repoRoot -CallerRoot $callerRoot

if (-not (Test-Path $config)) {
  Write-Host "Missing .markdownlint.json at repo root: $repoRoot"
  exit 1
}

# Delegate to the canonical trusted tool resolver. Repo-local explicit paths
# are batched into one trusted invocation; external scopes retain isolation.
$lintScript = Join-Path $repoRoot "00_Admin/scripts/lint.ps1"
$scopes = if ($FullRepoLint) { @(".") } else { $Paths }
$batchable = $scopes.Count -gt 1
foreach ($scope in $scopes) {
  if ($scope -like "..*" -or [System.IO.Path]::IsPathRooted($scope)) {
    $batchable = $false
    break
  }
}
if ($batchable) {
  & $lintScript -NoFix -MarkdownOnly -MarkdownPaths $scopes
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
} else {
  foreach ($scope in $scopes) {
    & $lintScript -NoFix -MarkdownOnly -Scope $scope
    if ($LASTEXITCODE -ne 0) {
      exit $LASTEXITCODE
    }
  }
}

exit 0
