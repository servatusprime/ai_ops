@echo off
REM Setup script for Claude Code skill installation.
REM Creates shallow wrapper skills in .claude\skills that point to workflow sources.

setlocal enableextensions enabledelayedexpansion

set "scope=repo"
set "dry_run=0"
set "assume_yes=0"
set "force=0"

:parse_args
if "%~1"=="" goto args_done
if /I "%~1"=="--workspace" (
  set "scope=workspace"
  shift
  goto parse_args
)
if /I "%~1"=="-w" (
  set "scope=workspace"
  shift
  goto parse_args
)
if /I "%~1"=="--repo" (
  set "scope=repo"
  shift
  goto parse_args
)
if /I "%~1"=="-n" (
  set "dry_run=1"
  shift
  goto parse_args
)
if /I "%~1"=="--dry-run" (
  set "dry_run=1"
  shift
  goto parse_args
)
if /I "%~1"=="-y" (
  set "assume_yes=1"
  shift
  goto parse_args
)
if /I "%~1"=="--yes" (
  set "assume_yes=1"
  shift
  goto parse_args
)
if /I "%~1"=="-f" (
  set "force=1"
  shift
  goto parse_args
)
if /I "%~1"=="--force" (
  set "force=1"
  shift
  goto parse_args
)
if /I "%~1"=="-h" goto usage
if /I "%~1"=="--help" goto usage
echo Unknown option: %~1
goto usage_error

:args_done
set "REPO_ROOT="
set "SCRIPT_DIR="
for %%I in ("%~f0") do set "SCRIPT_DIR=%%~dpI"
if defined SCRIPT_DIR (
  set "AIOPS_DOT="
  for %%I in ("!SCRIPT_DIR!..") do set "AIOPS_DOT=%%~fI"
  if defined AIOPS_DOT if exist "!AIOPS_DOT!\workflows\" (
    for %%I in ("!AIOPS_DOT!\..") do set "REPO_ROOT=%%~fI"
  )
)
if not defined REPO_ROOT if exist "%CD%\ai_ops\.ai_ops\workflows\" (
  set "REPO_ROOT=%CD%\ai_ops"
)
if not defined REPO_ROOT if exist "%CD%\..\ai_ops\.ai_ops\workflows\" (
  set "REPO_ROOT=%CD%\..\ai_ops"
)
if not defined REPO_ROOT if exist "%CD%\.ai_ops\workflows\" (
  set "REPO_ROOT=%CD%"
)
if not defined REPO_ROOT (
  echo Could not resolve ai_ops repo root from script or current directory.
  echo Script directory: !SCRIPT_DIR!
  echo Current directory: !CD!
  exit /b 1
)
set "WORKFLOW_DIR=%REPO_ROOT%\.ai_ops\workflows"

REM Resolve install target and workflow relative path based on scope
if /I "!scope!"=="workspace" (
  for %%I in ("%REPO_ROOT%\..") do set "WORKSPACE_ROOT=%%~fI"
  set "INSTALL_TARGET=!WORKSPACE_ROOT!\.claude\skills"
  set "WORKFLOW_REL=ai_ops/.ai_ops/workflows"
) else (
  set "INSTALL_TARGET=%REPO_ROOT%\.claude\skills"
  set "WORKFLOW_REL=.ai_ops/workflows"
)

echo Setting up ai_ops skills for Claude Code...
echo Scope:           !scope!
echo Workflow source: !WORKFLOW_DIR!
echo Install target:  !INSTALL_TARGET!
if "!dry_run!"=="1" (
  echo Dry-run mode enabled ^(no files will be written^).
)

if not exist "!WORKFLOW_DIR!\" (
  echo Missing workflow source directory.
  echo Expected: !WORKFLOW_DIR!
  exit /b 1
)

if not "!dry_run!"=="1" (
  if not exist "!INSTALL_TARGET!" mkdir "!INSTALL_TARGET!"
)

set "has_entries="
for /f %%A in ('dir /b "!INSTALL_TARGET!" 2^>nul') do set "has_entries=1"
if defined has_entries if "!assume_yes!"=="0" if not "!force!"=="1" (
  if "!dry_run!"=="1" (
    echo Would prompt: existing skills found in !INSTALL_TARGET!.
  ) else (
    echo Found existing skills in !INSTALL_TARGET!.
    choice /M "Continue and add/update ai_ops skills"
    if errorlevel 2 (
      echo Cancelled.
      endlocal
      exit /b 0
    )
  )
)

REM Create .ai_ops\local\work_state.yaml if it doesn't already exist (idempotent)
set "WORK_STATE_FILE=%REPO_ROOT%\.ai_ops\local\work_state.yaml"
if "!dry_run!"=="1" (
  if not exist "!WORK_STATE_FILE!" (
    echo [dry-run] Would create: !WORK_STATE_FILE!
  )
) else (
  if not exist "!WORK_STATE_FILE!" (
    if not exist "%REPO_ROOT%\.ai_ops\local" mkdir "%REPO_ROOT%\.ai_ops\local"
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
    ) > "!WORK_STATE_FILE!"
    echo Created .ai_ops\local\work_state.yaml ^(empty initial state^).
  )
)

REM Workspace scope bypasses the generator (generator resolves to repo scope only).
set "ran_generator=0"
if /I not "!scope!"=="workspace" (
  if exist "%REPO_ROOT%\00_Admin\scripts\generate_workflow_exports.py" (
    where python >nul 2>&1
    if not errorlevel 1 (
      if "!dry_run!"=="1" (
        python "%REPO_ROOT%\00_Admin\scripts\generate_workflow_exports.py" --targets plugin claude --dry-run
      ) else (
        python "%REPO_ROOT%\00_Admin\scripts\generate_workflow_exports.py" --targets plugin claude
      )
      if not errorlevel 1 (
        set "ran_generator=1"
      )
    )
  )
)

if "!ran_generator!"=="1" (
  echo.
  echo Generated wrapper exports from .ai_ops\workflows via generate_workflow_exports.py.
  echo Installed skills to !INSTALL_TARGET!.
  echo Skills are now available as /work, /health, /closeout, etc.
  echo.
  endlocal
  exit /b 0
)

if /I not "!scope!"=="workspace" (
  echo Generator unavailable; falling back to legacy wrapper creation path.
)

for %%f in (!WORKFLOW_DIR!\*.md) do (
  set "skill_name=%%~nf"
  set "skill_dir=!INSTALL_TARGET!\!skill_name!"
  set "write_skill=1"

  if exist "!skill_dir!\SKILL.md" (
    if "!force!"=="0" (
      echo Skip existing: !skill_dir!
      set "write_skill=0"
    )
  )

  if "!write_skill!"=="1" (
    if "!dry_run!"=="1" (
      echo Would create: !skill_dir!\SKILL.md
    ) else (
      mkdir "!skill_dir!" 2>nul

      REM Extract description from frontmatter (first match only)
      set "desc="
      for /f "tokens=1,* delims=:" %%a in ('findstr /B "description:" "%%f"') do (
        if not defined desc set "desc=%%b"
      )
      if not defined desc set "desc= Run ai_ops workflow !skill_name!"

      > "!skill_dir!\SKILL.md" (
        echo ---
        echo name: !skill_name!
        echo description:!desc!
        echo ---
        echo.
        echo Read `!WORKFLOW_REL!/!skill_name!.md` and follow its instructions.
      )
      echo Created: !skill_dir!
    )
  )
)

echo.
echo Installed skills to !INSTALL_TARGET!.
echo Skills are now available as /work, /health, /closeout, etc.
echo.

endlocal
exit /b 0

:usage
echo Usage:
echo   .ai_ops\setup\setup_claude_skills.bat [--workspace^|--repo] [--force] [--dry-run] [--yes]
echo.
echo Options:
echo   -w, --workspace        Install to workspace root .claude\skills\ ^(cross-repo access^)
echo       --repo             Install to ai_ops repo .claude\skills\ ^(default^)
echo   -f, --force            Overwrite existing skill wrappers
echo   -n, --dry-run          Preview actions without writing files
echo   -y, --yes              Non-interactive mode; skip confirmation prompt
echo   -h, --help             Show this help
echo.
echo Examples:
echo   Workspace install ^(recommended^): .ai_ops\setup\setup_claude_skills.bat --workspace --force
echo   Repo install ^(default^):          .ai_ops\setup\setup_claude_skills.bat
echo   Preview only:                    .ai_ops\setup\setup_claude_skills.bat --dry-run
endlocal
exit /b 0

:usage_error
call :usage
exit /b 1
