@echo off
REM Setup script for Codex skill installation.
REM Installs generated wrappers from tracked ai_ops workflow sources.
REM Runtime skill folders are downstream install surfaces, not source-of-truth.

setlocal enableextensions enabledelayedexpansion

REM Capture the script's own location BEFORE the arg-parse loop runs --
REM plain `shift` shifts %0 too, so resolving %~f0 after the loop can
REM silently produce a wrong path.
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
set "force=0"
set "install_compat=0"
set "dry_run=0"

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
if /I "%~1"=="--user" (
  set "scope=user"
  shift
  goto parse_args
)
if /I "%~1"=="--compat" (
  set "install_compat=1"
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
REM Resolve install target and workflow relative path based on scope
if /I "!scope!"=="workspace" (
  for %%I in ("%REPO_ROOT%\..") do set "WORKSPACE_ROOT=%%~fI"
  set "PRIMARY_SKILLS_DIR=!WORKSPACE_ROOT!\.agents\skills"
  set "COMPAT_SKILLS_DIR=!WORKSPACE_ROOT!\.codex\skills"
  set "WORKFLOW_REL=ai_ops/.ai_ops/workflows"
) else if /I "!scope!"=="user" (
  if "%USERPROFILE%"=="" (
    echo USERPROFILE is not set; cannot install user-scoped skills.
    exit /b 1
  )
  set "PRIMARY_SKILLS_DIR=%USERPROFILE%\.agents\skills"
  set "COMPAT_SKILLS_DIR=%USERPROFILE%\.codex\skills"
  set "WORKFLOW_REL=.ai_ops/workflows"
) else (
  set "PRIMARY_SKILLS_DIR=%REPO_ROOT%\.agents\skills"
  set "COMPAT_SKILLS_DIR=%REPO_ROOT%\.codex\skills"
  set "WORKFLOW_REL=.ai_ops/workflows"
)

if not exist "!WORKFLOW_DIR!\" (
  echo Missing workflow source directory.
  echo Expected: !WORKFLOW_DIR!
  exit /b 1
)

dir /b "!WORKFLOW_DIR!\*.md" >nul 2>&1
if errorlevel 1 (
  echo No workflow markdown files found in !WORKFLOW_DIR!.
  exit /b 1
)

echo Setting up ai_ops skills...
echo Scope:           !scope!
echo Workflow source: !WORKFLOW_DIR!
echo Install target:  !PRIMARY_SKILLS_DIR!
echo Managed-skill rule: tracked repo sources are authoritative; installed runtime wrappers are downstream outputs.
if "!dry_run!"=="1" (
  echo Dry-run mode enabled ^(no files will be written^).
)

REM Every scope routes through the real generator; --install-root lets
REM workspace/user scope write real, full-field wrappers via the same
REM renderer as repo scope. Confirmation prompt below: the generator
REM always overwrites and takes no force argument, so this is the only
REM protection against an unprompted clobber. Mirrors
REM setup_claude_skills.bat's equivalent block.
set "has_entries="
for /f %%A in ('dir /b "!PRIMARY_SKILLS_DIR!" 2^>nul') do set "has_entries=1"
if defined has_entries if not "!force!"=="1" (
  if "!dry_run!"=="1" (
    echo Would prompt: existing skills found in !PRIMARY_SKILLS_DIR!.
  ) else (
    echo Found existing skills in !PRIMARY_SKILLS_DIR!.
    choice /M "Overwrite with the current repo-generated set"
    if errorlevel 2 (
      echo Cancelled.
      endlocal
      exit /b 0
    )
  )
)

set "ran_generator=0"
set "generator_failed=0"
set "gen_compat_arg="
if "!install_compat!"=="1" set "gen_compat_arg=--codex-compat"
set "gen_dry_arg="
if "!dry_run!"=="1" set "gen_dry_arg=--dry-run"
if exist "%REPO_ROOT%\00_Admin\scripts\generate_workflow_exports.py" (
  where python >nul 2>&1
  if not errorlevel 1 (
    if /I "!scope!"=="workspace" (
      python "%REPO_ROOT%\00_Admin\scripts\generate_workflow_exports.py" --targets claude codex --scope workspace --install-root "!WORKSPACE_ROOT!" !gen_compat_arg! !gen_dry_arg!
    ) else if /I "!scope!"=="user" (
      REM user scope needs an absolute pointer -- %USERPROFILE% has no
      REM fixed relative path back to the repo.
      python "%REPO_ROOT%\00_Admin\scripts\generate_workflow_exports.py" --targets claude codex --scope user --install-root "%USERPROFILE%" !gen_compat_arg! !gen_dry_arg!
    ) else (
      python "%REPO_ROOT%\00_Admin\scripts\generate_workflow_exports.py" --targets plugin claude codex --scope repo !gen_compat_arg! !gen_dry_arg!
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
  echo Generated Codex wrappers via generate_workflow_exports.py.
  echo Primary install target: !PRIMARY_SKILLS_DIR!
  REM This call also includes the "claude" target and writes
  REM .claude\skills\ alongside .agents\skills\ -- disclose it explicitly.
  if /I "!scope!"=="workspace" (
    echo Also wrote Claude-surface skills to: !WORKSPACE_ROOT!\.claude\skills
  ) else if /I "!scope!"=="user" (
    echo Also wrote Claude-surface skills to: %USERPROFILE%\.claude\skills
  ) else (
    echo Also wrote Claude-surface skills to: %REPO_ROOT%\.claude\skills
  )
  if "!install_compat!"=="1" (
    echo Compatibility install target: !COMPAT_SKILLS_DIR!
  ) else (
    echo Compatibility install skipped ^(on-demand^). Use --compat to enable.
  )
  echo.
  echo Usage quick reference:
  echo   Workspace install ^(recommended^): .ai_ops\setup\setup_codex_skills.bat --workspace --force
  echo   Repo install ^(default^):          .ai_ops\setup\setup_codex_skills.bat
  echo   User install:                    .ai_ops\setup\setup_codex_skills.bat --user
  echo   Include compat mirror:           .ai_ops\setup\setup_codex_skills.bat --compat
  echo   Skip confirmation prompt:        .ai_ops\setup\setup_codex_skills.bat --force
  echo   Preview only:                    .ai_ops\setup\setup_codex_skills.bat --dry-run
  echo.
  echo In Codex VS Code chat, type "$" to browse skills or run "/skills".
  endlocal
  exit /b 0
)

echo Generator unavailable; refusing fallback writes because the generated export is authoritative.
endlocal
exit /b 127

:usage
echo Usage:
echo   .ai_ops\setup\setup_codex_skills.bat [--workspace^|--repo^|--user] [--compat] [-f^|--force] [--dry-run]
echo.
echo Options:
echo   -w, --workspace        Install to workspace root .agents\skills\ ^(cross-repo access^)
echo       --repo             Install to ai_ops repo .agents\skills\ ^(default^)
echo       --user             Install to %%USERPROFILE%%\.agents\skills
echo       --compat           Also install compatibility mirror to .codex\skills
echo   -f, --force            Skip the "existing skills found" confirmation prompt
echo   -n, --dry-run          Preview actions without writing files
echo   -h, --help             Show this help
echo.
echo Examples:
echo   Workspace install ^(recommended^): .ai_ops\setup\setup_codex_skills.bat --workspace --force
echo   Repo install ^(default^):          .ai_ops\setup\setup_codex_skills.bat
echo   User install:                    .ai_ops\setup\setup_codex_skills.bat --user
echo.
echo Managed-skill rule:
echo   Define retained ai_ops behavior in tracked repo sources first, then rerun
echo   /ai_ops_setup or this script. Do not hand-maintain installed .agents\skills\
echo   as the source-of-truth.
endlocal
exit /b 0

:usage_error
call :usage
exit /b 1
