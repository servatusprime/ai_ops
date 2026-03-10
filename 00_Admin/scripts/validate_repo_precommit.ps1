<#!
.SYNOPSIS
  Lightweight repo QA checks for a repo workspace.

.DESCRIPTION
  Runs non-destructive checks:
    - Scans Markdown/YAML files for control characters.
    - Verifies minimum YAML front-matter on AI workbooks and specs.
    - Intended as a starting point; extend over time.

.PARAMETER RepoRoot
  Path to the repo root. Defaults to current directory.

.NOTES
  Safe to run manually or wire into a pre-commit hook.
#!>

param(
    [string]$RepoRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path $RepoRoot).Path
$RepoName = Split-Path $RepoRoot -Leaf
Write-Host "Running pre-commit QA for $RepoName at $RepoRoot" -ForegroundColor Cyan

function Test-ControlChars {
    param([string]$Path)

    $bytes = [System.IO.File]::ReadAllBytes($Path)
    $bad = @()

    foreach ($b in $bytes) {
        # Allow: LF(10), CR(13), TAB(9)
        if ($b -lt 32 -and $b -notin 9,10,13) {
            $bad += $b
        }
    }

    if ($bad.Count -gt 0) {
        Write-Host "[CTRL] $Path contains control characters: $($bad | Sort-Object -Unique -join ', ')" -ForegroundColor Yellow
        return $true
    }
    return $false
}

function Test-YamlFrontMatter {
    param(
        [string]$Path,
        [string[]]$RequiredKeys
    )

    $content = Get-Content $Path -Raw
    if (-not $content.StartsWith("---")) {
        Write-Host "[META] $Path is missing YAML front-matter delimiter '---'" -ForegroundColor Yellow
        return $false
    }

    $endIdx = $content.IndexOf("---", 3)
    if ($endIdx -lt 0) {
        Write-Host "[META] $Path front-matter not properly closed with '---'" -ForegroundColor Yellow
        return $false
    }

    $yaml = $content.Substring(3, $endIdx - 3)

    foreach ($k in $RequiredKeys) {
        if ($yaml -notmatch "^\s*$k\s*:" -and $yaml -notmatch "\n\s*$k\s*:") {
            Write-Host "[META] $Path missing required key '$k' in front-matter" -ForegroundColor Yellow
            return $false
        }
    }
    return $true
}

# Discover files
$mdFiles = Get-ChildItem -Path $RepoRoot -Recurse -Include *.md -File -ErrorAction SilentlyContinue
$yamlFiles = Get-ChildItem -Path $RepoRoot -Recurse -Include *.yaml,*.yml -File -ErrorAction SilentlyContinue

$hasError = $false

# 2) Control character check
foreach ($file in $mdFiles + $yamlFiles) {
    if (Test-ControlChars -Path $file.FullName) {
        $hasError = $true
    }
}

# 3) Metadata checks for key file types

# 3.1 AI workbooks: 90_Sandbox/ai_workbooks/wb_*.md
$workbookFiles = $mdFiles | Where-Object {
    $_.FullName -match "90_Sandbox[\\/]+ai_workbooks[\\/]+wb_.*\.md$"
}

foreach ($file in $workbookFiles) {
    $ok = Test-YamlFrontMatter -Path $file.FullName -RequiredKeys @(
        "title", "id", "status", "version", "created", "updated", "owner"
    )
    if (-not $ok) { $hasError = $true }
}

# 3.2 Specs: 00_Admin/specs/spec_*.md
$specFiles = $mdFiles | Where-Object {
    $_.FullName -match "00_Admin[\\/]+specs[\\/]+spec_.*\.md$"
}

foreach ($file in $specFiles) {
    $ok = Test-YamlFrontMatter -Path $file.FullName -RequiredKeys @(
        "title", "id", "module", "status", "version", "created", "owner", "ai_generated"
    )
    if (-not $ok) { $hasError = $true }
}

# 4) GIS layer + metadata validation (optional)
if ($env:SKIP_RE_QC -eq "1") {
    Write-Host "Skipping GIS QC (SKIP_RE_QC=1 set)." -ForegroundColor Yellow
} else {
    $pythonCmd = "python"
    $validatorModule = $env:GIS_VALIDATOR_MODULE

    $localConfig = Join-Path $RepoRoot ".ai_ops/local/config.yaml"
    $workRepos = @()
    if (Test-Path $localConfig) {
        $configLines = Get-Content $localConfig
        foreach ($line in $configLines) {
            if ($line -match "^\s*-\s*path:\s*['\"]?([^'\"\s]+)['\"]?\s*$") {
                $workRepos += $Matches[1]
            }
        }
    }

    $workspaceRoot = Resolve-Path (Join-Path $RepoRoot "..")
    $gisRepoRoot = $null
    $gisModuleName = "gis_workflow"
    foreach ($repo in $workRepos) {
        $candidate = Join-Path $workspaceRoot $repo
        if (Test-Path (Join-Path $candidate "02_Modules/$gisModuleName/src")) {
            $gisRepoRoot = $candidate
            break
        }
    }

    if (-not $gisRepoRoot) {
        Write-Host "Skipping GIS QC: no GIS module repo found via .ai_ops/local/config.yaml work_repos." -ForegroundColor DarkGray
    } else {
        $pythonPathRoot = Join-Path $gisRepoRoot "02_Modules/$gisModuleName/src"
        if (-not $validatorModule) {
            $validatorModule = "$gisModuleName.operations.op_validate_layer_metadata"
        }

        function Get-ChangedPaths {
            param([string]$Root)
            try {
                return git -C $Root diff --cached --name-only --diff-filter=ACM 2>$null
            } catch {
                return @()
            }
        }

        $changedPaths = Get-ChangedPaths -Root $RepoRoot
        if (-not $changedPaths) {
            Write-Host "No staged GIS/metadata files detected for validation." -ForegroundColor DarkGray
        } else {
            $targetExts = @(".gpkg", ".geojson", ".shp", ".tif", ".tiff", ".vrt", ".gdb", ".fgb", ".zip", ".yml", ".yaml", ".json")
            $targetDirs = @("02_Modules/$gisModuleName/", "01_Resources/qgis/")

            $targets = @()
            foreach ($p in $changedPaths) {
                foreach ($dir in $targetDirs) {
                    if ($p -like "$dir*") {
                        $ext = [System.IO.Path]::GetExtension($p).ToLower()
                        if ($targetExts -contains $ext) {
                            $targets += (Join-Path $RepoRoot $p)
                        }
                    }
                }
            }

            if ($targets.Count -gt 0) {
                Write-Host "Running GIS metadata validation on staged files..." -ForegroundColor Cyan
                $env:PYTHONPATH = if ($env:PYTHONPATH) { "$pythonPathRoot;$env:PYTHONPATH" } else { $pythonPathRoot }
                $cmd = @($pythonCmd, "-m", $validatorModule, "--targets") + $targets
                try {
                    & $cmd[0] $cmd[1..($cmd.Count - 1)]
                    if ($LASTEXITCODE -ne 0) { $hasError = $true }
                } catch {
                    Write-Host "Skipping GIS QC: failed to invoke validator ($($_.Exception.Message))." -ForegroundColor Yellow
                }
            } else {
                Write-Host "No staged GIS/metadata files detected for validation." -ForegroundColor DarkGray
            }
        }
    }
}

if ($hasError) {
    Write-Host "`nPre-commit QA completed with warnings. Please fix the above issues before committing." -ForegroundColor Red
    exit 1
}

Write-Host "`nPre-commit QA completed with no blocking issues." -ForegroundColor Green
exit 0
