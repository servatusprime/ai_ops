# Lint helper for a repo workspace (PowerShell 5+/7+)
# Runs Ruff, markdownlint, and yamllint. Use -Fix to auto-fix where supported.
param(
    [switch] $NoFix,
    [switch] $DryRun,
    [string] $Scope = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$repoName = Split-Path -Leaf $repoRoot
$missing = @()
$trustedNodeSha256 = "f13ac3ca23248dc389507e8fe38c34489ab7edb3e6d6700eb6da6a0b7e128eaf"
$trustedMarkdownlintSha256 = "644e27c3425f651751382d6963b3b6ca6a2395764c2f64efe7e03fc71e604e12"
$trustedMarkdownlintPackageSha256 = "21280478d4322f01e1e59b802a663b2d0c2a5d6ef26c76a6ce3e3c025d4703ec"
$trustedMarkdownlintVersion = "0.47.0"

function Test-WritableDirectory {
    param(
        [string] $Path
    )

    try {
        if (-not (Test-Path $Path)) {
            New-Item -ItemType Directory -Path $Path -Force | Out-Null
        }
        $probeFile = Join-Path $Path ".lint_write_probe_$PID.tmp"
        Set-Content -Path $probeFile -Value "probe" -Encoding ascii -NoNewline
        Remove-Item -Path $probeFile -Force
        return $true
    }
    catch {
        return $false
    }
}

function Resolve-CacheRoot {
    param(
        [string] $RepoRoot,
        [string] $RepoName
    )

    $candidates = @()
    if ($env:AI_OPS_CACHE_ROOT) {
        $candidates += (Join-Path $env:AI_OPS_CACHE_ROOT $RepoName)
    }
    if ($env:USERPROFILE) {
        $candidates += (Join-Path $env:USERPROFILE ".ai_cache\$RepoName")
    }
    $candidates += (Join-Path $RepoRoot ".cache\ai_ops")
    if ($env:TEMP) {
        $candidates += (Join-Path $env:TEMP "ai_ops_cache\$RepoName")
    }

    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        if (Test-WritableDirectory -Path $candidate) {
            return $candidate
        }
    }

    throw "No writable lint cache path found. Checked: $($candidates -join ', ')"
}

if (-not $DryRun) {
    # Ensure tool caches are writable and outside synchronized folders.
    $aiCacheRoot = Resolve-CacheRoot -RepoRoot $repoRoot -RepoName $repoName
    $preCommitHome = Join-Path $aiCacheRoot "pre-commit"
    $ruffCacheDir = Join-Path $aiCacheRoot "ruff"

    foreach ($path in @($preCommitHome, $ruffCacheDir)) {
        if (-not (Test-Path $path)) {
            New-Item -ItemType Directory -Path $path -Force | Out-Null
        }
    }

    $env:PRE_COMMIT_HOME = $preCommitHome
    $env:RUFF_CACHE_DIR = $ruffCacheDir
    Write-Host "Lint cache root: $aiCacheRoot" -ForegroundColor DarkGray
}
else {
    Write-Host "DryRun mode: commands are validated but not executed." -ForegroundColor DarkGray
}

function Resolve-YamllintConfigPath {
    param(
        [string] $PrimaryRoot,
        [string] $FallbackRoot
    )

    $candidates = @(
        (Join-Path $PrimaryRoot ".yamllint"),
        (Join-Path $FallbackRoot ".yamllint")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate -PathType Leaf) {
            return $candidate
        }
    }

    throw "yamllint config not found. Expected one of: $($candidates -join ', ')"
}

function Resolve-TrustedMarkdownlint {
    $programFiles = [Environment]::GetEnvironmentVariable("ProgramFiles", "Process")
    $applicationData = [Environment]::GetFolderPath([Environment+SpecialFolder]::ApplicationData)
    if ([string]::IsNullOrWhiteSpace($programFiles) -or [string]::IsNullOrWhiteSpace($applicationData)) {
        throw "Trusted markdownlint roots are unavailable."
    }
    $nodePath = Join-Path $programFiles "nodejs\node.exe"
    $entrypoint = Join-Path $applicationData "npm\node_modules\markdownlint-cli\markdownlint.js"
    $packageJson = Join-Path (Split-Path -Parent $entrypoint) "package.json"
    foreach ($path in @($nodePath, $entrypoint, $packageJson)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Trusted markdownlint artifact is missing: $path"
        }
        $item = Get-Item -LiteralPath $path -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Trusted markdownlint artifact is a reparse point: $path"
        }
    }
    if ((Get-FileHash -LiteralPath $nodePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $trustedNodeSha256) {
        throw "Trusted Node executable hash mismatch."
    }
    if ((Get-FileHash -LiteralPath $entrypoint -Algorithm SHA256).Hash.ToLowerInvariant() -ne $trustedMarkdownlintSha256) {
        throw "Trusted markdownlint entrypoint hash mismatch."
    }
    if ((Get-FileHash -LiteralPath $packageJson -Algorithm SHA256).Hash.ToLowerInvariant() -ne $trustedMarkdownlintPackageSha256) {
        throw "Trusted markdownlint package metadata hash mismatch."
    }
    $package = Get-Content -LiteralPath $packageJson -Raw | ConvertFrom-Json
    if ($package.version -ne $trustedMarkdownlintVersion) {
        throw "Trusted markdownlint package version mismatch."
    }
    return @($nodePath, $entrypoint)
}

function Resolve-LintScope {
    param(
        [string] $RepoRoot,
        [string] $Scope
    )

    if ([string]::IsNullOrWhiteSpace($Scope) -or $Scope -in @(".", "./", ".\", "ai_ops")) {
        return @{
            Path = "."
            Display = "."
            InRepo = $true
            Root = $RepoRoot
        }
    }

    $token = $Scope.Trim()
    if ([System.IO.Path]::IsPathRooted($token)) {
        $candidate = $token
    }
    else {
        $candidate = Join-Path $RepoRoot $token
    }

    if (-not (Test-Path $candidate)) {
        throw "Scope '$Scope' does not exist. Use ai_ops, a relative path under repo root, or an explicit governed-repo path (for example ../<governed_repo>)."
    }

    $resolved = (Resolve-Path -LiteralPath $candidate).Path
    $repoResolved = (Resolve-Path -LiteralPath $RepoRoot).Path
    $sep = [System.IO.Path]::DirectorySeparatorChar
    $inRepo = ($resolved -eq $repoResolved) -or $resolved.StartsWith($repoResolved + $sep, [System.StringComparison]::OrdinalIgnoreCase)
    $resolvedItem = Get-Item -LiteralPath $resolved -Force
    if ($resolvedItem.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw "Scope resolves through a symlink/reparse point: $Scope"
    }

    if (-not $inRepo) {
        $isExplicitExternal = [System.IO.Path]::IsPathRooted($token) -or $token.StartsWith("..\") -or $token.StartsWith("../")
        if (-not $isExplicitExternal) {
            throw "Scope '$Scope' resolves outside repo root. For governed repos, pass an explicit external path (for example ../<governed_repo>)."
        }
    }

    $scopeRoot = if (Test-Path $resolved -PathType Leaf) { Split-Path -Parent $resolved } else { $resolved }
    $display = if ($inRepo) {
        try {
            Resolve-Path -LiteralPath $resolved -Relative
        }
        catch {
            $resolved
        }
    }
    else {
        $resolved
    }

    return @{
        Path = $resolved
        Display = $display
        InRepo = $inRepo
        Root = $scopeRoot
    }
}

function Invoke-Step {
    param(
        [string] $Name,
        [string[]] $CommandArgs,
        [switch] $DryRun
    )
    $cmd = $CommandArgs[0]
    if ([string]::IsNullOrWhiteSpace($cmd)) {
        throw "Lint step '$Name' has no command to run."
    }
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Warning "$Name skipped; '$cmd' not found. Install it or run pre-commit."
        $script:missing += $cmd
        return
    }
    Write-Host ">> $Name" -ForegroundColor Cyan
    Write-Host ("   " + ($CommandArgs -join " ")) -ForegroundColor DarkGray
    if ($DryRun) {
        return
    }
    if ($CommandArgs.Count -gt 1) {
        & $cmd @($CommandArgs[1..($CommandArgs.Count - 1)])
    } else {
        & $cmd
    }
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

Push-Location $repoRoot
try {
    $target = Resolve-LintScope -RepoRoot $repoRoot -Scope $Scope
    Write-Host "Lint scope: $($target.Display)" -ForegroundColor DarkGray

    $yamllintConfig = Resolve-YamllintConfigPath -PrimaryRoot $target.Root -FallbackRoot $repoRoot
    $markdownlintCommand = Resolve-TrustedMarkdownlint

    $ruffSkippableExts = @(".py", ".pyi", ".ipynb")
    $skipRuff = $false
    if (Test-Path $target.Path -PathType Leaf) {
        $ext = [System.IO.Path]::GetExtension($target.Path).ToLowerInvariant()
        if ($ruffSkippableExts -notcontains $ext) {
            $skipRuff = $true
        }
    }

    if ($skipRuff) {
        Write-Host ">> Ruff (skipped for non-Python file scope)" -ForegroundColor Cyan
    }
    else {
        $ruffArgs = @("ruff", "check", $target.Path)
        if (-not $NoFix) {
            $ruffArgs += "--fix"
        }
        Invoke-Step -Name "Ruff" -CommandArgs $ruffArgs -DryRun:$DryRun
    }

    if ($target.InRepo) {
        Invoke-Step -Name "markdownlint" -CommandArgs @($markdownlintCommand + @("--config", ".markdownlint.json", $target.Path)) -DryRun:$DryRun
    }
    else {
        Push-Location $target.Root
        try {
            Invoke-Step -Name "markdownlint" -CommandArgs @($markdownlintCommand + @("--config", ".markdownlint.json", ".")) -DryRun:$DryRun
        }
        finally {
            Pop-Location
        }
    }

    $yamlExts = @(".yaml", ".yml")
    $skipYamllint = $false
    if (Test-Path $target.Path -PathType Leaf) {
        $ext = [System.IO.Path]::GetExtension($target.Path).ToLowerInvariant()
        if ($yamlExts -notcontains $ext) {
            $skipYamllint = $true
        }
    }

    if ($skipYamllint) {
        Write-Host ">> yamllint (skipped for non-YAML file scope)" -ForegroundColor Cyan
    }
    else {
        Invoke-Step -Name "yamllint" -CommandArgs @("yamllint", "-c", $yamllintConfig, $target.Path) -DryRun:$DryRun
    }
    if ($target.InRepo) {
        Invoke-Step -Name "workflow-frontmatter" -CommandArgs @("python", "00_Admin/scripts/validate_workflow_frontmatter.py") -DryRun:$DryRun
    }
    else {
        Write-Host ">> workflow-frontmatter (skipped for non-ai_ops scope)" -ForegroundColor Cyan
    }
}
finally {
    Pop-Location
}

if ($missing.Count -gt 0) {
    Write-Warning "Install missing tools or enable pre-commit to keep CI green: $($missing -join ', ')"
    exit 1
}
