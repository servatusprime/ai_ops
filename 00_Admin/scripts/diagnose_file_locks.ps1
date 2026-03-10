# Script to diagnose file locks on a repo workspace
# Focused on sync-client-related issues

function Get-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot '..\..'))
}

$RepoRoot = (Get-RepoRoot).Path

param(
    [string]$TargetPath = (Join-Path $RepoRoot '90_Sandbox'),
    [string]$SyncClientProcess = $env:SYNC_CLIENT_PROCESS
)

Write-Host "=== File Lock Diagnostic Tool ===" -ForegroundColor Cyan
Write-Host "Target Path: $TargetPath" -ForegroundColor Yellow
Write-Host ""

# Check if path exists
if (Test-Path $TargetPath) {
    Write-Host "[✓] Path exists" -ForegroundColor Green
} else {
    Write-Host "[✗] Path does not exist!" -ForegroundColor Red
    exit 1
}

# Check sync client status (if provided)
Write-Host "`n=== Sync Client Status ===" -ForegroundColor Cyan
try {
    $attrib = attrib $TargetPath
    Write-Host "Attributes: $attrib" -ForegroundColor Yellow
} catch {
    Write-Host "[!] Could not check file attributes: $_" -ForegroundColor Yellow
}

# Check file/folder properties
Write-Host "`n=== Folder Properties ===" -ForegroundColor Cyan
try {
    $item = Get-Item $TargetPath -Force
    Write-Host "Name: $($item.Name)" -ForegroundColor White
    Write-Host "Full Path: $($item.FullName)" -ForegroundColor White
    Write-Host "Attributes: $($item.Attributes)" -ForegroundColor White
    Write-Host "Last Write Time: $($item.LastWriteTime)" -ForegroundColor White
    Write-Host "Is ReadOnly: $($item.Attributes -match 'ReadOnly')" -ForegroundColor $(if ($item.Attributes -match 'ReadOnly') { 'Red' } else { 'Green' })
} catch {
    Write-Host "[✗] Error accessing folder properties: $_" -ForegroundColor Red
}

# List files in directory
Write-Host "`n=== Files in Directory ===" -ForegroundColor Cyan
try {
    Get-ChildItem $TargetPath | ForEach-Object {
        Write-Host "  - $($_.Name) ($($_.Length) bytes)" -ForegroundColor Gray
    }
} catch {
    Write-Host "[✗] Error listing files: $_" -ForegroundColor Red
}

# Check for processes that might be locking files
Write-Host "`n=== Potential Locking Processes ===" -ForegroundColor Cyan
$processesToCheck = @(
    "Code",
    "git",
    "SearchIndexer",
    "explorer"
)

if ($SyncClientProcess) {
    $processesToCheck = @($SyncClientProcess) + $processesToCheck
}

foreach ($procName in $processesToCheck) {
    $procs = Get-Process -Name $procName -ErrorAction SilentlyContinue
    if ($procs) {
        Write-Host "[!] Found $($procs.Count) instance(s) of $procName" -ForegroundColor Yellow
        $procs | ForEach-Object {
            Write-Host "    PID: $($_.Id), Memory: $([math]::Round($_.WorkingSet64/1MB, 2)) MB" -ForegroundColor Gray
        }
    }
}

# Suggest solutions
Write-Host "`n=== Suggested Solutions ===" -ForegroundColor Cyan
Write-Host "1. Pause your sync client temporarily (if applicable)." -ForegroundColor White
Write-Host ""
Write-Host "2. Close IDE and restart it" -ForegroundColor White
Write-Host ""
Write-Host "3. Try renaming the folder manually in File Explorer" -ForegroundColor White
Write-Host ""
Write-Host "4. Check if Windows Search is indexing this location:" -ForegroundColor White
Write-Host "   - Settings > Search > Searching Windows > Exclude this folder" -ForegroundColor Gray
Write-Host ""
Write-Host "5. If using antivirus, temporarily exclude this folder" -ForegroundColor White
Write-Host ""

# Offer to pause sync client (if provided)
if ($SyncClientProcess) {
    Write-Host "`n=== Sync Client Control ===" -ForegroundColor Cyan
    $response = Read-Host "Would you like to attempt to pause the sync client? (y/n)"
    if ($response -eq 'y') {
        try {
            Write-Host "Stopping sync client..." -ForegroundColor Yellow
            Stop-Process -Name $SyncClientProcess -Force -ErrorAction Stop
            Start-Sleep -Seconds 2
            Write-Host "[✓] Sync client stopped (it may auto-restart)" -ForegroundColor Green
            Write-Host "Try your git operation now while it restarts." -ForegroundColor Yellow
        } catch {
            Write-Host "[✗] Could not stop sync client: $_" -ForegroundColor Red
        }
    }
}

Write-Host "`n=== Diagnostic Complete ===" -ForegroundColor Cyan
