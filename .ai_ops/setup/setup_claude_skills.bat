@echo off
REM Setup script for Claude Code skills.
REM Also generates GitHub Copilot-compatible project skills in .claude\skills
REM on supported Copilot surfaces.

setlocal enableextensions enabledelayedexpansion

REM Capture the script's own location BEFORE the arg-parse loop runs.
REM Plain `shift` shifts %0 along with %1-%9 in Windows batch; resolving
REM %~f0 after the loop can silently produce a wrong-but-plausible path
REM once flags are parsed.
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

set "scope=repo"
set "dry_run=0"
set "assume_yes=0"
set "force=0"
set "approve_preview="

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
if /I "%~1"=="--approve-preview" (
  shift
  if "%~1"=="" (
    echo --approve-preview requires the token printed by a prior dry run.
    exit /b 1
  )
  set "approve_preview=%~1"
  shift
  goto parse_args
)
if /I "%~1"=="-h" goto usage
if /I "%~1"=="--help" goto usage
echo Unknown option: %~1
goto usage_error

:args_done
if defined approve_preview (
  set "invalid_preview="
  if "!approve_preview:~15,1!"=="" set "invalid_preview=1"
  if not "!approve_preview:~16,1!"=="" set "invalid_preview=1"
  for /f "delims=0123456789ABCDEF" %%A in ("!approve_preview!") do set "invalid_preview=1"
  if defined invalid_preview (
    echo --approve-preview must be exactly 16 uppercase hexadecimal characters.
    exit /b 2
  )
)
REM Resolve install target and workflow relative path based on scope
if /I "!scope!"=="workspace" (
  for %%I in ("%REPO_ROOT%\..") do set "WORKSPACE_ROOT=%%~fI"
  set "INSTALL_TARGET=!WORKSPACE_ROOT!\.claude\skills"
  set "WORKFLOW_REL=ai_ops/.ai_ops/workflows"
) else (
  set "INSTALL_TARGET=%REPO_ROOT%\.claude\skills"
  set "WORKFLOW_REL=.ai_ops/workflows"
)

echo Setting up ai_ops skills in .claude\skills...
echo Compatible surfaces: Claude Code, and GitHub Copilot where .claude\skills is supported.
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

where python >nul 2>&1
if errorlevel 1 (
  echo Python is required to validate setup destinations and generate skills.
  exit /b 1
)
python "%REPO_ROOT%\00_Admin\scripts\validate_setup_destination.py" --path "!INSTALL_TARGET!"
if errorlevel 1 exit /b 2

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

REM Both scopes route through the real generator; --install-root lets
REM workspace scope use the same full-field renderer as repo scope. The
REM setup fails closed when the generator is unavailable.
set "ran_generator=0"
set "generator_failed=0"
if exist "%REPO_ROOT%\00_Admin\scripts\generate_workflow_exports.py" (
  where python >nul 2>&1
  if not errorlevel 1 (
    if /I "!scope!"=="workspace" (
      set "gen_approval_arg="
      if defined approve_preview set "gen_approval_arg=--approve-preview !approve_preview!"
      if "!dry_run!"=="1" (
        python "%REPO_ROOT%\00_Admin\scripts\generate_workflow_exports.py" --targets claude --scope workspace --install-root "!WORKSPACE_ROOT!" --dry-run !gen_approval_arg!
      ) else (
        python "%REPO_ROOT%\00_Admin\scripts\generate_workflow_exports.py" --targets claude --scope workspace --install-root "!WORKSPACE_ROOT!" !gen_approval_arg!
      )
    ) else (
      if "!dry_run!"=="1" (
        python "%REPO_ROOT%\00_Admin\scripts\generate_workflow_exports.py" --targets plugin claude --dry-run
      ) else (
        python "%REPO_ROOT%\00_Admin\scripts\generate_workflow_exports.py" --targets plugin claude
      )
    )
    set "generator_status=!ERRORLEVEL!"
    if "!generator_status!"=="0" (
      set "ran_generator=1"
    ) else (
      set "generator_failed=1"
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

if "!generator_failed!"=="1" (
  echo Generator refused the setup request; no fallback writes will be attempted.
  endlocal
  exit /b 1
)

echo Generator unavailable; refusing fallback writes because the generated export is authoritative.
endlocal
exit /b 127

:usage
echo Usage:
echo   .ai_ops\setup\setup_claude_skills.bat [--workspace^|--repo] [--force] [--dry-run] [--yes] [--approve-preview TOKEN]
echo.
echo Options:
echo   -w, --workspace        Install to workspace root .claude\skills\ ^(cross-repo access^)
echo       --repo             Install to ai_ops repo .claude\skills\ ^(default^)
echo   -f, --force            Overwrite existing skill wrappers
echo   -n, --dry-run          Preview actions without writing files
echo   -y, --yes              Non-interactive mode; skip confirmation prompt
echo       --approve-preview  Apply an exact external-install preview token
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
