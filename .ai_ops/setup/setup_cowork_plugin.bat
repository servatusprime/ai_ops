@echo off
REM setup_cowork_plugin.bat
REM Package ai_ops skills into a Cowork .plugin file.
REM
REM Usage:
REM   setup_cowork_plugin.bat [--workspace | --repo] [--output <path>] [--dry-run] [--help]
REM
REM Options:
REM   --workspace   Package skills from <workspace_root>/.claude/skills/  (default)
REM   --repo        Package skills from <repo_root>/.claude/skills/
REM   --output      Output path for .plugin file (default: <workspace_root>/ai-ops-skills.plugin)
REM   --dry-run     Print resolved paths and skill count; do not write output file
REM   --help        Show this help
REM
REM Exit codes:
REM   0  Success (or dry-run complete)
REM   1  Error (zero skills found, manifest missing, Python unavailable)
REM
REM Manifest source: <repo_root>/.claude-plugin/plugin.json (tracked)
REM If not found, error is raised.

setlocal enableextensions enabledelayedexpansion

set "SCOPE=workspace"
set "DRY_RUN=0"
set "OUTPUT_PATH="

:parse_args
if "%~1"=="" goto :args_done
if /i "%~1"=="--workspace"  ( set "SCOPE=workspace" & shift & goto :parse_args )
if /i "%~1"=="--repo"       ( set "SCOPE=repo"      & shift & goto :parse_args )
if /i "%~1"=="--dry-run"    ( set "DRY_RUN=1"       & shift & goto :parse_args )
if /i "%~1"=="--output"     ( set "OUTPUT_PATH=%~2" & shift & shift & goto :parse_args )
if /i "%~1"=="--help"       ( goto :print_usage )
echo Unknown option: %~1
goto :print_usage
:args_done

REM Resolve repo root from script location (.ai_ops\setup\ -> ..\..\)
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
pushd "%SCRIPT_DIR%\..\.." >nul || (
    echo ERROR: Unable to resolve repo root from script directory: %SCRIPT_DIR%
    exit /b 1
)
set "REPO_ROOT=%CD%"
popd >nul

REM Fallback: if script-location resolution failed, walk upward from CWD until
REM the tracked plugin manifest is found. This keeps the helper portable while
REM supporting shells that invoke .bat files with unusual %~dp0 behavior.
if exist "!REPO_ROOT!\.claude-plugin\plugin.json" goto :repo_root_resolved
set "SEARCH_DIR=%CD%"
:find_repo_root
if exist "!SEARCH_DIR!\.claude-plugin\plugin.json" (
    set "REPO_ROOT=!SEARCH_DIR!"
    goto :repo_root_resolved
)
for %%I in ("!SEARCH_DIR!\..") do set "NEXT_DIR=%%~fI"
if /i "!NEXT_DIR!"=="!SEARCH_DIR!" goto :repo_root_resolved
set "SEARCH_DIR=!NEXT_DIR!"
goto :find_repo_root
:repo_root_resolved

REM Resolve workspace root (one level above repo root)
pushd "%REPO_ROOT%\.." >nul || (
    echo ERROR: Unable to resolve workspace root from repo root: %REPO_ROOT%
    exit /b 1
)
set "WORKSPACE_ROOT=%CD%"
popd >nul

REM Resolve skills source
if "%SCOPE%"=="workspace" (
    set "SKILLS_ROOT=%WORKSPACE_ROOT%\.claude\skills"
) else (
    set "SKILLS_ROOT=%REPO_ROOT%\.claude\skills"
)

REM Resolve manifest path
set "MANIFEST_PATH=%REPO_ROOT%\.claude-plugin\plugin.json"

REM Resolve output path
if "%OUTPUT_PATH%"=="" (
    set "OUTPUT_PATH=%WORKSPACE_ROOT%\ai-ops-skills.plugin"
)

echo Workspace root  : %WORKSPACE_ROOT%
echo Repo root       : %REPO_ROOT%
echo Scope           : %SCOPE%
echo Skills root     : %SKILLS_ROOT%
echo Manifest        : %MANIFEST_PATH%
echo Output          : %OUTPUT_PATH%
if "%DRY_RUN%"=="1" echo Dry-run mode: no files will be written.
echo.

REM Check manifest
if not exist "%MANIFEST_PATH%" (
    echo ERROR: Manifest not found: %MANIFEST_PATH%
    echo Create it at .claude-plugin\plugin.json in the ai_ops repo root.
    exit /b 1
)

REM Count skills
if not exist "%SKILLS_ROOT%" (
    echo ERROR: Skills directory not found: %SKILLS_ROOT%
    exit /b 1
)

set "SKILL_COUNT=0"
for /d %%D in ("%SKILLS_ROOT%\*") do (
    if exist "%%D\SKILL.md" (
        set /a SKILL_COUNT+=1
    )
)

echo Skills found: %SKILL_COUNT%

if %SKILL_COUNT% EQU 0 (
    echo ERROR: No skill directories containing SKILL.md found in %SKILLS_ROOT%
    exit /b 1
)

if "%DRY_RUN%"=="1" (
    echo [dry-run] Would create plugin file at: %OUTPUT_PATH%
    exit /b 0
)

REM Locate Python
set "PY="
where python >nul 2>&1 && set "PY=python"
if "!PY!"=="" where python3 >nul 2>&1 && set "PY=python3"
if "!PY!"=="" (
    echo ERROR: Python not found. Install Python and retry.
    exit /b 1
)

set "PACKAGER=%REPO_ROOT%\.ai_ops\setup\setup_cowork_plugin.py"
if not exist "%PACKAGER%" (
    echo ERROR: Packager helper not found: %PACKAGER%
    exit /b 1
)

"!PY!" "%PACKAGER%" --skills-root "%SKILLS_ROOT%" --manifest "%MANIFEST_PATH%" --output "%OUTPUT_PATH%"
exit /b !ERRORLEVEL!

:print_usage
echo.
echo Usage:
echo   setup_cowork_plugin.bat [--workspace ^| --repo] [--output ^<path^>] [--dry-run] [--help]
echo.
echo Options:
echo   --workspace   Package skills from ^<workspace_root^>/.claude/skills/  (default)
echo   --repo        Package skills from ^<repo_root^>/.claude/skills/
echo   --output      Output path for .plugin file
echo                 (default: ^<workspace_root^>/ai-ops-skills.plugin)
echo   --dry-run     Print resolved paths and skill count; do not write output file
echo   --help        Show this help
echo.
echo Exit 0 = success, Exit 1 = error
exit /b 0
