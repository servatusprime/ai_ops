param(
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

if (Get-Command pre-commit -ErrorAction SilentlyContinue) {
  Push-Location $repoRoot
  $preCommitOutput = & pre-commit run markdownlint --files $Paths 2>&1
  Pop-Location
  $preCommitExit = $LASTEXITCODE

  if ($preCommitExit -eq 0) {
    exit 0
  }

  $preCommitText = ($preCommitOutput | Out-String)
  $isEnvFailure = $preCommitText -match "OperationalError" `
    -or $preCommitText -match "readonly database" `
    -or $preCommitText -match "Permission denied"

  if (-not $isEnvFailure) {
    $preCommitOutput | ForEach-Object { Write-Output $_ }
    exit $preCommitExit
  }

  Write-Warning "pre-commit markdownlint failed due environment permissions; falling back to markdownlint CLI."
}

if (-not (Test-Path $config)) {
  Write-Host "Missing .markdownlint.json at repo root: $repoRoot"
  exit 1
}

Push-Location $repoRoot

# In full-repo mode, linting "." is more reliable than passing hundreds of path args.
# This avoids markdownlint CLI usage fallthrough when argument expansion is ambiguous.
if ($FullRepoLint) {
  if (Test-Path $ignore) {
    & markdownlint -c $config --ignore-path $ignore "."
  } else {
    & markdownlint -c $config "."
  }
} else {
  if (Test-Path $ignore) {
    & markdownlint -c $config --ignore-path $ignore $Paths
  } else {
    & markdownlint -c $config $Paths
  }
}
Pop-Location

exit $LASTEXITCODE
