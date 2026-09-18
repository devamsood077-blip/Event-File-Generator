"""Check GitHub Releases and replace the running portable app."""

from __future__ import annotations

import json
import os
import ssl
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

APP_VERSION = "1.1.0"
GITHUB_REPO = "devamsood077-blip/Event-File-Generator"
USER_AGENT = "EventFileGenerator-Updater"
WINDOWS_ASSET = "EventFileGenerator.exe"
MACOS_ASSET = "EventFileGenerator-macOS.zip"


class UpdateError(Exception):
    """User-facing update failure."""


class UpdateAuthError(UpdateError):
    """GitHub returned 401/403/404 — private repo or missing token."""


def parse_version(value):
    text = str(value or "").strip().lstrip("vV")
    parts = []
    for chunk in text.split("."):
        digits = ""
        for char in chunk:
            if char.isdigit():
                digits += char
            else:
                break
        parts.append(int(digits or 0))
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def is_newer(latest, current=APP_VERSION):
    return parse_version(latest) > parse_version(current)


def is_frozen():
    return bool(getattr(sys, "frozen", False))


def current_executable():
    return Path(sys.executable).resolve() if is_frozen() else None


def current_app_bundle():
    """Return the .app path on macOS, otherwise the frozen executable."""
    exe = current_executable()
    if exe is None:
        return None
    if sys.platform == "darwin":
        for parent in exe.parents:
            if parent.suffix == ".app":
                return parent
    return exe


def _ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def github_request(url, token=None, accept="application/vnd.github+json"):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=45, context=_ssl_context()) as response:
            return response.read(), dict(response.headers)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403, 404):
            raise UpdateAuthError(
                "Could not read GitHub releases. This repo is private, so Check for "
                "Updates needs a GitHub personal access token with repo read access."
            ) from exc
        raise UpdateError(f"GitHub request failed ({exc.code}).") from exc
    except urllib.error.URLError as exc:
        raise UpdateError(f"Could not reach GitHub: {exc.reason}") from exc


def fetch_latest_release(token=None):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    raw, _headers = github_request(url, token=token)
    data = json.loads(raw.decode("utf-8"))
    tag = data.get("tag_name") or ""
    assets = []
    for asset in data.get("assets") or []:
        assets.append(
            {
                "name": asset.get("name") or "",
                "id": asset.get("id"),
                "size": asset.get("size") or 0,
                "url": asset.get("url") or "",
            }
        )
    if not tag:
        raise UpdateError("Latest GitHub release has no version tag.")
    return {"tag": tag, "name": data.get("name") or tag, "assets": assets, "body": data.get("body") or ""}


def matching_asset(release):
    wanted = MACOS_ASSET if sys.platform == "darwin" else WINDOWS_ASSET
    for asset in release["assets"]:
        if asset["name"] == wanted:
            return asset
    names = ", ".join(a["name"] for a in release["assets"]) or "none"
    raise UpdateError(f"No {wanted} asset in the latest release (found: {names}).")


def download_asset(asset, dest: Path, token=None, progress_cb=None):
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/assets/{asset['id']}"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/octet-stream",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=120, context=_ssl_context()) as response:
            total = int(response.headers.get("Content-Length") or asset.get("size") or 0)
            read = 0
            with open(dest, "wb") as handle:
                while True:
                    chunk = response.read(256 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)
                    read += len(chunk)
                    if progress_cb:
                        progress_cb(read, total)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403, 404):
            raise UpdateAuthError(
                "Could not download the update. Add a GitHub token with repo read access."
            ) from exc
        raise UpdateError(f"Download failed ({exc.code}).") from exc


def _windows_replace_script(current: Path, new_file: Path, pid: int) -> Path:
    script = current.parent / "_efg_update.bat"
    script.write_text(
        "\r\n".join(
            [
                "@echo off",
                "setlocal",
                ":wait",
                f'tasklist /FI "PID eq {pid}" | findstr /I "{pid}" >nul',
                "if %ERRORLEVEL%==0 (",
                "  timeout /t 1 /nobreak >nul",
                "  goto wait",
                ")",
                f'move /Y "{new_file}" "{current}"',
                f'start "" "{current}"',
                'del "%~f0"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return script


def _macos_replace_script(app_bundle: Path, extracted_app: Path, pid: int) -> Path:
    script = Path(tempfile.gettempdir()) / "efg_update.sh"
    script.write_text(
        "\n".join(
            [
                "#!/bin/bash",
                f"while kill -0 {pid} 2>/dev/null; do sleep 1; done",
                f'rm -rf "{app_bundle}"',
                f'mv "{extracted_app}" "{app_bundle}"',
                f'xattr -cr "{app_bundle}" >/dev/null 2>&1 || true',
                f'open "{app_bundle}"',
                'rm -f "$0"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    script.chmod(0o755)
    return script


def prepare_downloaded_payload(download_path: Path):
    """Return the file/folder that should replace the running portable."""
    if sys.platform == "darwin":
        extract_dir = Path(tempfile.mkdtemp(prefix="efg_update_"))
        with zipfile.ZipFile(download_path) as archive:
            archive.extractall(extract_dir)
        apps = list(extract_dir.rglob("*.app"))
        if not apps:
            raise UpdateError("The macOS update zip did not contain EventFileGenerator.app.")
        return apps[0]
    return download_path


def launch_replacer(download_path: Path):
    if not is_frozen():
        raise UpdateError("Automatic replace only works for the portable app, not source runs.")
    payload = prepare_downloaded_payload(download_path)
    pid = os.getpid()
    if sys.platform == "win32":
        current = current_executable()
        script = _windows_replace_script(current, payload, pid)
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.Popen(["cmd", "/c", str(script)], close_fds=True, creationflags=creationflags)
    elif sys.platform == "darwin":
        current = current_app_bundle()
        script = _macos_replace_script(current, payload, pid)
        subprocess.Popen(["/bin/bash", str(script)], close_fds=True)
    else:
        raise UpdateError("Automatic updates are only supported on Windows and macOS.")
