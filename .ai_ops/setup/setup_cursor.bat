@echo off
REM Setup script for Cursor command installation.
REM This copies workflow files into .cursor\commands.

setlocal

echo Setting up ai_ops for Cursor ...

if not exist .cursor\commands mkdir .cursor\commands

set "has_entries="
for /f %%A in ('dir /b ".cursor\commands" 2^>nul') do set "has_entries=1"
if defined has_entries (
  echo Found existing files in .cursor\commands\.
  choice /M "Continue and copy new files"
  if errorlevel 2 (
    echo Cancelled.
    endlocal
    exit /b 0
  )
)

set "WORKFLOW_DIR="
if exist .ai_ops\workflows\ set "WORKFLOW_DIR=.ai_ops\workflows"
if not defined WORKFLOW_DIR (
  echo Missing workflow directory.
  echo Expected: .ai_ops\workflows
  exit /b 1
)

for %%f in (%WORKFLOW_DIR%\*.md) do (
  if exist ".cursor\commands\%%~nxf" (
    echo Skip existing: .cursor\commands\%%~nxf
  ) else (
    copy /Y "%%f" ".cursor\commands\%%~nxf" >nul
  )
)

echo Copied workflows to .cursor\commands\.

REM Create .ai_ops\local\work_state.yaml if it doesn't already exist (idempotent)
if not exist ".ai_ops\local\work_state.yaml" (
  if not exist ".ai_ops\local" mkdir ".ai_ops\local"
  (
    echo # ai_ops work state ? machine-local, gitignored.
    echo # Written by /work and /closeout. Never commit.
    echo schema_version: "1.0.0"
    echo work_context:
    echo   active_artifacts: []
    echo   updated_at: null
    echo   checkpoints: []
    echo telemetry:
    echo   last_bootstrap_mode: null
    echo   last_context_refresh: null
  ) > ".ai_ops\local\work_state.yaml"
  echo Created .ai_ops\local\work_state.yaml ^(empty initial state^).
)

endlocal
