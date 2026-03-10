@echo off
REM Setup script for Claude Code command installation (legacy).
REM Copies workflow files into .claude\commands.
REM
REM NOTE: As of Claude Code v2.1.3, slash commands were merged into the
REM skills system. The .claude\commands path still works (backward-compatible)
REM but .claude\skills is now the recommended mechanism.
REM Prefer setup_claude_skills.bat for new installations.

setlocal

echo.
echo NOTE: .claude\commands is backward-compatible but skills are now preferred.
echo       Consider using setup_claude_skills.bat instead.
echo.

set "WORKFLOW_DIR="
if exist .ai_ops\workflows\ set "WORKFLOW_DIR=.ai_ops\workflows"
if not defined WORKFLOW_DIR (
  echo Missing workflow directory; run this from the repo root.
  echo Expected: .ai_ops\workflows
  exit /b 1
)

if not exist .claude\commands mkdir .claude\commands

set "has_entries="
for /f %%A in ('dir /b ".claude\commands" 2^>nul') do set "has_entries=1"
if defined has_entries (
  echo Found existing files in .claude\commands\.
  choice /M "Continue and copy new files"
  if errorlevel 2 (
    echo Cancelled.
    endlocal
    exit /b 0
  )
)

for %%f in (%WORKFLOW_DIR%\*.md) do (
  findstr /B /C:"description:" "%%f" >nul 2>&1
  if errorlevel 1 (
    echo Skip missing description frontmatter: %%f
  ) else if exist ".claude\commands\%%~nxf" (
    echo Skip existing: .claude\commands\%%~nxf
  ) else (
    copy /Y "%%f" ".claude\commands\%%~nxf" >nul
  )
)

echo.
echo Copied workflows to .claude\commands\.
echo.
echo Recommended: use setup_claude_skills.bat for the skills-based approach.
echo See: https://code.claude.com/docs/en/skills
echo.

REM Create .ai_ops\local\work_state.yaml if it doesn't already exist (idempotent)
if not exist ".ai_ops\local\work_state.yaml" (
  if not exist ".ai_ops\local" mkdir ".ai_ops\local"
  (
    echo # ai_ops work state — machine-local, gitignored.
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
