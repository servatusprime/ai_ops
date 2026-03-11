@echo off
REM Setup script for Codex skill installation.
REM Default install target is repo-scoped .agents\skills.

setlocal enableextensions enabledelayedexpansion

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
if "!dry_run!"=="1" (
  echo Dry-run mode enabled ^(no files will be written^).
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
  if "!force!"=="1" (
    if exist "%REPO_ROOT%\00_Admin\scripts\generate_workflow_exports.py" (
      where python >nul 2>&1
      if not errorlevel 1 (
        if "!install_compat!"=="1" (
          if "!dry_run!"=="1" (
            python "%REPO_ROOT%\00_Admin\scripts\generate_workflow_exports.py" --targets plugin claude codex --codex-compat --dry-run
          ) else (
            python "%REPO_ROOT%\00_Admin\scripts\generate_workflow_exports.py" --targets plugin claude codex --codex-compat
          )
        ) else (
          if "!dry_run!"=="1" (
            python "%REPO_ROOT%\00_Admin\scripts\generate_workflow_exports.py" --targets plugin claude codex --dry-run
          ) else (
            python "%REPO_ROOT%\00_Admin\scripts\generate_workflow_exports.py" --targets plugin claude codex
          )
        )
        if not errorlevel 1 (
          set "ran_generator=1"
        )
      )
    )
  )
)

if "!ran_generator!"=="1" (
  echo Generated Codex wrappers via generate_workflow_exports.py.
  echo Primary install target: !PRIMARY_SKILLS_DIR!
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
  echo   Overwrite existing:              .ai_ops\setup\setup_codex_skills.bat --force
  echo   Preview only:                    .ai_ops\setup\setup_codex_skills.bat --dry-run
  echo.
  echo In Codex VS Code chat, type "$" to browse skills or run "/skills".
  endlocal
  exit /b 0
)

call :install_to_dir "!PRIMARY_SKILLS_DIR!"
if errorlevel 1 exit /b 1
echo Primary install target: !PRIMARY_SKILLS_DIR!

if /I not "!install_compat!"=="1" (
  echo Compatibility install skipped ^(on-demand^). Use --compat to enable.
) else (
  goto install_compat
)
goto after_compat

:install_compat
call :install_to_dir "!COMPAT_SKILLS_DIR!"
if errorlevel 1 exit /b 1
echo Compatibility install target: !COMPAT_SKILLS_DIR!

:after_compat

echo.
echo Usage quick reference:
echo   Workspace install ^(recommended^): .ai_ops\setup\setup_codex_skills.bat --workspace --force
echo   Repo install ^(default^):          .ai_ops\setup\setup_codex_skills.bat
echo   User install:                    .ai_ops\setup\setup_codex_skills.bat --user
echo   Include compat mirror:           .ai_ops\setup\setup_codex_skills.bat --compat
echo   Overwrite existing:              .ai_ops\setup\setup_codex_skills.bat --force
echo   Preview only:                    .ai_ops\setup\setup_codex_skills.bat --dry-run
echo.
echo In Codex VS Code chat, type "$" to browse skills or run "/skills".
endlocal
exit /b 0

:install_to_dir
set "SKILLS_DIR=%~1"
if "!dry_run!"=="1" (
  echo [dry-run] Would target install root: !SKILLS_DIR!
) else (
  if not exist "!SKILLS_DIR!" mkdir "!SKILLS_DIR!"
)

for %%f in (!WORKFLOW_DIR!\*.md) do (
  set "skill_name=%%~nf"
  set "skill_dir=!SKILLS_DIR!\!skill_name!"
  set "write_skill=1"

  if exist "!skill_dir!\SKILL.md" (
    if "!force!"=="0" (
      echo Skip existing: !skill_dir!
      set "write_skill=0"
    )
  )

  if "!write_skill!"=="1" (
    if "!dry_run!"=="1" (
      echo [dry-run] Would create: !skill_dir!\SKILL.md
      echo [dry-run] Would create: !skill_dir!\agents\openai.yaml
    ) else (
      if not exist "!skill_dir!" mkdir "!skill_dir!"

      REM Extract description from workflow frontmatter (first match only)
      set "desc="
      for /f "tokens=1,* delims=:" %%a in ('findstr /B "description:" "%%f"') do (
        if not defined desc set "desc=%%b"
      )
      if not defined desc set "desc= Run ai_ops workflow !skill_name!"

      REM Trim leading space from desc
      for /f "tokens=*" %%d in ("!desc!") do set "desc=%%d"

      > "!skill_dir!\SKILL.md" (
        echo ---
        echo name: !skill_name!
        echo description: !desc!
        echo metadata:
        echo   short-description: !desc!
        echo ---
        echo.
        echo # !skill_name!
        echo.
        echo Read `!WORKFLOW_REL!/!skill_name!.md` and follow its instructions.
      )
      if not exist "!skill_dir!\agents" mkdir "!skill_dir!\agents"
      > "!skill_dir!\agents\openai.yaml" (
        echo interface:
        echo   display_name: "!skill_name!"
        echo   short_description: "!desc!"
      )
      echo Installed: !skill_dir!
    )
  )
)
exit /b 0

:usage
echo Usage:
echo   .ai_ops\setup\setup_codex_skills.bat [--workspace^|--repo^|--user] [--compat] [-f^|--force] [--dry-run]
echo.
echo Options:
echo   -w, --workspace        Install to workspace root .agents\skills\ ^(cross-repo access^)
echo       --repo             Install to ai_ops repo .agents\skills\ ^(default^)
echo       --user             Install to %%USERPROFILE%%\.agents\skills
echo       --compat           Also install compatibility mirror to .codex\skills
echo   -f, --force            Overwrite existing skill wrappers
echo   -n, --dry-run          Preview actions without writing files
echo   -h, --help             Show this help
echo.
echo Examples:
echo   Workspace install ^(recommended^): .ai_ops\setup\setup_codex_skills.bat --workspace --force
echo   Repo install ^(default^):          .ai_ops\setup\setup_codex_skills.bat
echo   User install:                    .ai_ops\setup\setup_codex_skills.bat --user
endlocal
exit /b 0

:usage_error
call :usage
exit /b 1
