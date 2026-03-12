#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


DEFAULT_ARCHIVE_ROOT = Path(
    r"D:\ЯндексДиск\Yandex.Disk\ПРОЕКТЫ\AI_Workspace\project_archive"
)
OLD_GYM_ROOT = r"F:\ДИМА\ПРОЕКТЫ\Фантом Давыдова В.В\gymnasium_landing"


def read_text(path: Path) -> tuple[str, str]:
    data = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "cp1251"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace"), "utf-8"


def write_text(path: Path, text: str, encoding: str) -> None:
    with path.open("w", encoding=encoding, newline="") as handle:
        handle.write(text)


def upsert_import_os(text: str) -> str:
    if re.search(r"^import os\s*$", text, flags=re.MULTILINE):
        return text
    match = re.search(r"^(?:from\s+\S+\s+import\s+.+|import\s+.+)\r?\n", text)
    if match:
        return text[: match.end()] + "import os\n" + text[match.end() :]
    return "import os\n" + text


def patch_html_path_script(path: Path) -> bool:
    text, encoding = read_text(path)
    original = text
    text = upsert_import_os(text)
    if "BASE_DIR = os.path.dirname(os.path.abspath(__file__))" not in text:
        text = re.sub(
            r"^html_path\s*=.*$",
            "BASE_DIR = os.path.dirname(os.path.abspath(__file__))\n"
            "html_path = os.path.join(BASE_DIR, 'index.html')",
            text,
            flags=re.MULTILINE,
            count=1,
        )
    else:
        text = re.sub(
            r"^html_path\s*=.*$",
            "html_path = os.path.join(BASE_DIR, 'index.html')",
            text,
            flags=re.MULTILINE,
            count=1,
        )
    if text != original:
        write_text(path, text, encoding)
        return True
    return False


def patch_apply_changes(path: Path) -> bool:
    text, encoding = read_text(path)
    original = text
    text = upsert_import_os(text)
    text = re.sub(
        r"^html_path\s*=.*$",
        "BASE_DIR = os.path.dirname(os.path.abspath(__file__))\n"
        "html_path = os.path.join(BASE_DIR, 'index.html')",
        text,
        flags=re.MULTILINE,
        count=1,
    )
    text = re.sub(
        r"^images_dir\s*=.*$",
        "images_dir = os.path.join(BASE_DIR, 'images')",
        text,
        flags=re.MULTILINE,
        count=1,
    )
    text = re.sub(
        r"^photos_dir\s*=.*$",
        "photos_dir = os.path.join(BASE_DIR, 'фото')",
        text,
        flags=re.MULTILINE,
        count=1,
    )
    if text != original:
        write_text(path, text, encoding)
        return True
    return False


def patch_deploy_hero_images(path: Path) -> bool:
    text, encoding = read_text(path)
    original = text
    text = upsert_import_os(text)
    if "BASE_DIR = os.path.dirname(os.path.abspath(__file__))" not in text:
        text = text.replace(
            "import shutil\n\n"
            "artifacts = r'C:\\Users\\Admin\\.gemini\\antigravity\\brain\\06d2a6bb-4117-40b2-b0dc-da47d655191e'\n"
            "images_dir = r'F:\\ДИМА\\ПРОЕКТЫ\\Фантом Давыдова В.В\\gymnasium_landing\\images'\n",
            "import shutil\n\n"
            "BASE_DIR = os.path.dirname(os.path.abspath(__file__))\n"
            "DEFAULT_ARTIFACTS = os.path.join(BASE_DIR, 'artifacts')\n"
            "LEGACY_ARTIFACTS = r'C:\\Users\\Admin\\.gemini\\antigravity\\brain\\06d2a6bb-4117-40b2-b0dc-da47d655191e'\n"
            "artifacts = os.environ.get('HERO_ARTIFACTS_DIR', DEFAULT_ARTIFACTS)\n"
            "if not os.path.isdir(artifacts) and os.path.isdir(LEGACY_ARTIFACTS):\n"
            "    artifacts = LEGACY_ARTIFACTS\n"
            "if not os.path.isdir(artifacts):\n"
            "    raise FileNotFoundError(f'Artifacts directory not found: {artifacts}')\n"
            "images_dir = os.path.join(BASE_DIR, 'images')\n",
        )
    text = text.replace(
        f"html_path = os.path.join(r'{OLD_GYM_ROOT}', 'index.html')",
        "html_path = os.path.join(BASE_DIR, 'index.html')",
    )
    if text != original:
        write_text(path, text, encoding)
        return True
    return False


def patch_get_mayor(path: Path) -> bool:
    text, encoding = read_text(path)
    original = text
    text = upsert_import_os(text)
    if "BASE_DIR = os.path.dirname(os.path.abspath(__file__))" not in text:
        text = text.replace(
            "headers = {'User-Agent': 'Mozilla/5.0'}\n",
            "headers = {'User-Agent': 'Mozilla/5.0'}\n"
            "BASE_DIR = os.path.dirname(os.path.abspath(__file__))\n"
            "images_dir = os.path.join(BASE_DIR, 'images')\n"
            "os.makedirs(images_dir, exist_ok=True)\n",
        )
    text = re.sub(
        r'filename\s*=\s*f"F:\\\\ДИМА\\\\ПРОЕКТЫ\\\\Фантом Давыдова В\.В\\\\gymnasium_landing\\\\images\\\\mayor_\{count\}\.png"',
        'filename = os.path.join(images_dir, f"mayor_{count}.png")',
        text,
        flags=re.MULTILINE,
        count=1,
    )
    if text != original:
        write_text(path, text, encoding)
        return True
    return False


def rewrite_ai_agent_core(base: Path) -> list[Path]:
    changed: list[Path] = []

    copaw_run = base / "_copaw_run.ps1"
    if copaw_run.exists():
        text, encoding = read_text(copaw_run)
        new_text = """$ErrorActionPreference = "Continue"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:NO_PROXY = "127.0.0.1,localhost"
$env:PYTHONWARNINGS = "ignore"
$copawExe = Join-Path $ScriptRoot "copaw-env\\Scripts\\copaw.exe"
$logPath = Join-Path $ScriptRoot "copaw_log.txt"
if (-not $env:HTTPS_PROXY) {
    Write-Warning "HTTPS_PROXY is not set"
}
if (-not $env:HTTP_PROXY -and $env:HTTPS_PROXY) {
    $env:HTTP_PROXY = $env:HTTPS_PROXY
}
if (-not $env:TAVILY_API_KEY) {
    Write-Warning "TAVILY_API_KEY is not set"
}
if (-not (Test-Path -LiteralPath $copawExe)) {
    Write-Error "copaw.exe not found: $copawExe"
    exit 1
}
& $copawExe app *>&1 | Tee-Object -FilePath $logPath
"""
        if text != new_text:
            write_text(copaw_run, new_text, encoding)
            changed.append(copaw_run)

    tg_bat = base / "start_telegram_agent.bat"
    if tg_bat.exists():
        text, encoding = read_text(tg_bat)
        new_text = """@echo off
chcp 65001 >nul
echo ========================================
echo   Telegram Agent - Start
echo ========================================
echo.

set PYTHONWARNINGS=ignore
set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
set "PYTHON_EXE=%PROJECT_DIR%\\copaw-env\\Scripts\\python.exe"
set "SCRIPT=%PROJECT_DIR%\\telegram_agent.py"

if not exist "%PYTHON_EXE%" (
    echo ERROR: python not found: "%PYTHON_EXE%"
    pause
    exit /b 1
)

echo Starting %SCRIPT%...
echo Close this window to stop.
echo.
"%PYTHON_EXE%" "%SCRIPT%"
pause
"""
        if text != new_text:
            write_text(tg_bat, new_text, encoding)
            changed.append(tg_bat)

    start_copaw = base / "start_copaw.bat"
    if start_copaw.exists():
        text, encoding = read_text(start_copaw)
        original = text
        if 'set "PROJECT_DIR=%~dp0"' not in text:
            text = text.replace(
                "set PYTHONWARNINGS=ignore\n",
                "set PYTHONWARNINGS=ignore\n"
                "set \"PROJECT_DIR=%~dp0\"\n"
                "if \"%PROJECT_DIR:~-1%\"==\"\\\" set \"PROJECT_DIR=%PROJECT_DIR:~0,-1%\"\n",
            )
        text = re.sub(
            r'start "" /B powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File ".*?_copaw_autoconfig\.ps1"',
            lambda _m: 'start "" /B powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File "%PROJECT_DIR%\\_copaw_autoconfig.ps1"',
            text,
            count=1,
        )
        text = re.sub(
            r'"[^"\r\n]*copaw-env\\Scripts\\copaw\.exe" app',
            lambda _m: '"%PROJECT_DIR%\\copaw-env\\Scripts\\copaw.exe" app',
            text,
            count=1,
        )
        if text != original:
            write_text(start_copaw, text, encoding)
            changed.append(start_copaw)

    backup = base / "backup_skills.bat"
    if backup.exists():
        text, encoding = read_text(backup)
        new_text = """@echo off
chcp 65001 >nul
echo ========================================
echo   Backup Agent Skills
echo ========================================
echo.

set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

set "SOURCE_SKILLS=%PROJECT_DIR%\\.agents\\skills"
set "SOURCE_WORKFLOWS=%PROJECT_DIR%\\.agents\\workflows"
set "SOURCE_CRITIC=%PROJECT_DIR%\\critic_agent.py"
set "GLOBAL_SKILLS=%USERPROFILE%\\.gemini\\skills"
set "BACKUP_DIR=%PROJECT_DIR%\\backups\\skills_%date:~-4%%date:~3,2%%date:~0,2%"

echo [1/4] Sync skills to global folder...
if not exist "%GLOBAL_SKILLS%" mkdir "%GLOBAL_SKILLS%"
xcopy /E /Y /I /Q "%SOURCE_SKILLS%\\task-executor" "%GLOBAL_SKILLS%\\task-executor" >nul
xcopy /E /Y /I /Q "%SOURCE_SKILLS%\\safety-guardrails" "%GLOBAL_SKILLS%\\safety-guardrails" >nul
xcopy /E /Y /I /Q "%SOURCE_SKILLS%\\skill-conductor" "%GLOBAL_SKILLS%\\skill-conductor" >nul
echo       OK: %GLOBAL_SKILLS%

echo [2/4] Create local backup...
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
xcopy /E /Y /I /Q "%SOURCE_SKILLS%" "%BACKUP_DIR%\\skills" >nul
xcopy /E /Y /I /Q "%SOURCE_WORKFLOWS%" "%BACKUP_DIR%\\workflows" >nul
copy /Y "%SOURCE_CRITIC%" "%BACKUP_DIR%\\critic_agent.py" >nul
echo       OK: %BACKUP_DIR%

echo [3/4] Sync with Yandex Disk...
set "YADISK=D:\\ЯндексДиск\\Yandex.Disk\\AgentSkillsBackup"
if exist "D:\\ЯндексДиск\\Yandex.Disk" (
    if not exist "%YADISK%" mkdir "%YADISK%"
    xcopy /E /Y /I /Q "%SOURCE_SKILLS%" "%YADISK%\\skills" >nul
    xcopy /E /Y /I /Q "%SOURCE_WORKFLOWS%" "%YADISK%\\workflows" >nul
    copy /Y "%SOURCE_CRITIC%" "%YADISK%\\critic_agent.py" >nul
    echo       OK: %YADISK%
) else (
    echo       SKIP: Yandex Disk not found
)

echo [4/4] Check OneDrive...
if exist "%USERPROFILE%\\OneDrive" (
    set "CLOUD_DIR=%USERPROFILE%\\OneDrive\\AgentSkillsBackup"
    if not exist "%CLOUD_DIR%" mkdir "%CLOUD_DIR%"
    xcopy /E /Y /I /Q "%SOURCE_SKILLS%" "%CLOUD_DIR%\\skills" >nul
    xcopy /E /Y /I /Q "%SOURCE_WORKFLOWS%" "%CLOUD_DIR%\\workflows" >nul
    copy /Y "%SOURCE_CRITIC%" "%CLOUD_DIR%\\critic_agent.py" >nul
    echo       OK: OneDrive synchronized
) else (
    echo       SKIP: OneDrive not found
)

echo.
echo ========================================
echo   Backup completed.
echo ========================================
pause
"""
        if text != new_text:
            write_text(backup, new_text, encoding)
            changed.append(backup)

    tg_py = base / "telegram_agent.py"
    if tg_py.exists():
        text, encoding = read_text(tg_py)
        original = text
        text = re.sub(
            r'^SKILLS_DIR\s*=\s*Path\(r".*?\.agents\\skills"\)\s*$',
            "PROJECT_ROOT = Path(__file__).resolve().parent\n"
            "SKILLS_DIR = Path(os.environ.get('ANTIGRAVITY_SKILLS_DIR', str(PROJECT_ROOT / '.agents' / 'skills')))\n"
            "if not SKILLS_DIR.exists():\n"
            "    fallback_skills = Path.home() / '.agents' / 'skills'\n"
            "    if fallback_skills.exists():\n"
            "        SKILLS_DIR = fallback_skills",
            text,
            flags=re.MULTILINE,
            count=1,
        )
        if text != original:
            write_text(tg_py, text, encoding)
            changed.append(tg_py)

    return changed


def patch_gymnasium(base: Path) -> list[Path]:
    changed: list[Path] = []
    simple_html_files = [
        "fix_hero_awards.py",
        "fix_hero_hard.py",
        "fix_hero_very_hard.py",
        "fix_hero_very_hard2.py",
        "fix_icons.py",
        "fix_label.py",
        "fix_nav_css.py",
        "fix_visuals2.py",
        "fix_wreaths.py",
        "swap_cards.py",
    ]
    for name in simple_html_files:
        path = base / name
        if path.exists() and patch_html_path_script(path):
            changed.append(path)

    apply_changes = base / "apply_changes.py"
    if apply_changes.exists() and patch_apply_changes(apply_changes):
        changed.append(apply_changes)

    deploy_hero_images = base / "deploy_hero_images.py"
    if deploy_hero_images.exists() and patch_deploy_hero_images(deploy_hero_images):
        changed.append(deploy_hero_images)

    get_mayor = base / "get_mayor.py"
    if get_mayor.exists() and patch_get_mayor(get_mayor):
        changed.append(get_mayor)

    return changed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Repair absolute path references in project_archive scripts."
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=DEFAULT_ARCHIVE_ROOT,
        help=f"Archive root path (default: {DEFAULT_ARCHIVE_ROOT})",
    )
    args = parser.parse_args()

    archive_root = args.archive_root
    ai_agent_core = archive_root / "agents" / "ai_agent_core"
    gymnasium = archive_root / "education" / "gymnasium_landing"

    changed_files: list[Path] = []
    if ai_agent_core.exists():
        changed_files.extend(rewrite_ai_agent_core(ai_agent_core))
    if gymnasium.exists():
        changed_files.extend(patch_gymnasium(gymnasium))

    print(f"ARCHIVE_ROOT: {archive_root}")
    print(f"CHANGED_FILES: {len(changed_files)}")
    for path in changed_files:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
