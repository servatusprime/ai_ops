@echo off
REM Setup script for Gemini CLI and Antigravity command discovery.
REM This creates .toml command files in .gemini\commands and markdown wrappers
REM in .agents\workflows from workflow files.

setlocal

echo Setting up ai_ops for Gemini CLI and Antigravity ...

if not exist .gemini\commands mkdir .gemini\commands

set "has_entries="
for /f %%A in ('dir /b ".gemini\commands" 2^>nul') do set "has_entries=1"
if defined has_entries (
  echo Found existing files in .gemini\commands\.
  choice /M "Continue and copy new files"
  if errorlevel 2 (
    echo Cancelled.
    endlocal
    exit /b 0
  )
)

set "WORKFLOW_DIR="
set "WORKFLOW_REL="
if exist .ai_ops\workflows\ (
  set "WORKFLOW_DIR=.ai_ops\workflows"
  set "WORKFLOW_REL=.ai_ops/workflows"
)
if not defined WORKFLOW_DIR (
  echo Missing workflow directory.
  echo Expected: .ai_ops\workflows
  exit /b 1
)

set "AGENTS_ROOT=.agents"
set "WORKFLOW_POINTER_BASE=.ai_ops/workflows"
if exist "..\.agents\" (
  set "AGENTS_ROOT=..\.agents"
  set "WORKFLOW_POINTER_BASE=ai_ops/.ai_ops/workflows"
)
if not exist "%AGENTS_ROOT%\workflows" mkdir "%AGENTS_ROOT%\workflows"

for %%f in (%WORKFLOW_DIR%\*.md) do (
  if exist ".gemini\commands\%%~nf.toml" (
    echo Skip existing: .gemini\commands\%%~nf.toml
  ) else (
    >".gemini\commands\%%~nf.toml" echo name = "%%~nf"
    >>".gemini\commands\%%~nf.toml" echo description = "ai_ops %%~nf command"
    >>".gemini\commands\%%~nf.toml" echo prompt = "Read %WORKFLOW_REL%/%%~nf.md and follow the instructions."
    echo Created .gemini\commands\%%~nf.toml
  )
  if exist "%AGENTS_ROOT%\workflows\%%~nf.md" (
    echo Skip existing: %AGENTS_ROOT%\workflows\%%~nf.md
  ) else (
    >"%AGENTS_ROOT%\workflows\%%~nf.md" echo ---
    >>"%AGENTS_ROOT%\workflows\%%~nf.md" echo description: ai_ops %%~nf command wrapper for Antigravity/Gemini discovery.
    >>"%AGENTS_ROOT%\workflows\%%~nf.md" echo ---
    >>"%AGENTS_ROOT%\workflows\%%~nf.md" echo.
    >>"%AGENTS_ROOT%\workflows\%%~nf.md" echo # /%%~nf
    >>"%AGENTS_ROOT%\workflows\%%~nf.md" echo.
    >>"%AGENTS_ROOT%\workflows\%%~nf.md" echo Read %WORKFLOW_POINTER_BASE%/%%~nf.md and follow the instructions.
    echo Created %AGENTS_ROOT%\workflows\%%~nf.md
  )
)

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
