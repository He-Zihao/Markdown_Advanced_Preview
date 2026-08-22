"""CudaText adapter for the Markdown Advanced Preview engine."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from cudatext import *
from cudax_lib import safe_open_url


PLUGIN_DIR = Path(__file__).resolve().parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from .preview_core import PreviewError, Renderer, load_settings


SETTINGS_FILE = Path(app_path(APP_DIR_SETTINGS)) / "cuda_markdown_advanced_preview.json"
DEFAULT_SETTINGS_FILE = PLUGIN_DIR / "settings_default.json"
DEFAULT_TEMP_DIR = Path(tempfile.gettempdir()) / "cuda_markdown_advanced_preview"


def _status(message: str) -> None:
    msg_status("Markdown Advanced Preview: " + message)


def _error(message: str) -> None:
    msg_box("Markdown Advanced Preview\n\n" + message, MB_OK + MB_ICONERROR)


def _document_key(editor: Any) -> str:
    filename = editor.get_filename()
    if filename:
        return os.path.normcase(os.path.abspath(filename))
    return "tab:{}".format(editor.get_prop(PROP_TAB_ID))


def _document_title(editor: Any) -> str:
    filename = editor.get_filename()
    if filename:
        return os.path.splitext(os.path.basename(filename))[0]
    return editor.get_prop(PROP_TAB_TITLE) or "untitled"


def _preview_directory(settings: Dict[str, Any], filename: str) -> Path:
    configured = settings.get("path_tempfile", "")
    if configured:
        configured = os.path.expandvars(os.path.expanduser(str(configured)))
        path = Path(configured)
        if not path.is_absolute():
            base = Path(filename).resolve().parent if filename else PLUGIN_DIR
            path = base / path
    else:
        path = DEFAULT_TEMP_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _preview_path(editor: Any, settings: Dict[str, Any]) -> Path:
    filename = editor.get_filename()
    key = _document_key(editor)
    digest = hashlib.sha1(key.encode("utf-8", "surrogatepass")).hexdigest()[:12]
    stem = Path(filename).stem if filename else "untitled"
    safe_stem = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in stem)[:80]
    return _preview_directory(settings, filename) / "{}-{}.html".format(safe_stem or "preview", digest)


def _write_utf8(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        stream.write(content)
    os.replace(str(temporary), str(path))


def _write_live_marker(render_settings: Any) -> None:
    marker = getattr(render_settings, "live_reload_marker", None)
    token = getattr(render_settings, "live_reload_token", None)
    if marker and token:
        _write_utf8(
            Path(marker),
            "window.__cudaMdPreviewVersion={};\n".format(json.dumps(token)),
        )


def _browser_file_url(path: Path) -> str:
    """Build a file URL accepted by CudaText's Windows ``safe_open_url``.

    ``Path.as_uri`` percent-encodes non-ASCII text.  CudaText ultimately passes
    the URL through ``cmd.exe start``, which treats that encoded text as the
    literal local filename.  Preserve Unicode while still escaping unsafe
    ASCII characters such as spaces, percent signs, fragments and queries.
    """
    resolved = path.resolve()
    if os.name != "nt":
        return resolved.as_uri()
    unsafe = {"%", " ", '"', "#", "?", "<", ">", "`", "{", "}", "|", "\\", "^", "[", "]"}
    raw = resolved.as_posix()
    encoded = "".join(
        "%{:02X}".format(ord(char)) if char in unsafe or ord(char) < 32 else char
        for char in raw
    )
    return "file:///" + encoded


class Command:
    """Commands and event callbacks exposed to CudaText."""

    def __init__(self) -> None:
        self._sessions: Dict[str, Dict[str, Any]] = {}
        DEFAULT_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    def _settings(self) -> Dict[str, Any]:
        return load_settings(str(SETTINGS_FILE) if SETTINGS_FILE.is_file() else None)

    def _pick_parser(self, settings: Dict[str, Any]) -> Optional[str]:
        available = ["markdown", "github", "gitlab"]
        available.extend(settings.get("markdown_binary_map", {}).keys())
        enabled = sorted({
            name for name in settings.get("enabled_parsers", ["markdown"])
            if name in available
        })
        if not enabled:
            return "markdown"
        if len(enabled) == 1:
            return enabled[0]
        current = settings.get("parser", "markdown")
        focused = enabled.index(current) if current in enabled else 0
        selected = dlg_menu(DMENU_LIST, enabled, focused=focused, caption="Markdown parser")
        return enabled[selected] if selected is not None and selected >= 0 else None

    def _source(self, editor: Any, use_selection: bool = True) -> Tuple[str, bool]:
        if use_selection:
            selected = editor.get_text_sel()
            if selected and selected.strip():
                return selected, True
        return editor.get_text_all(), False

    def _render(
        self,
        editor: Any,
        target: str,
        parser: Optional[str] = None,
        use_selection: bool = True,
        live_reload: bool = False,
    ) -> Tuple[str, str, Path, Any, str, bool]:
        settings = self._settings()
        parser = parser or settings.get("parser", "markdown")
        source, selection = self._source(editor, use_selection)
        if not source:
            raise PreviewError("The document is empty.")
        path = _preview_path(editor, settings)
        complete, body, render_settings = Renderer(settings).render(
            source,
            editor.get_filename() or None,
            _document_title(editor),
            parser=parser,
            preview_path=str(path),
            preview=target == "browser",
            live_reload=live_reload,
        )
        include = settings.get("include_head", ["browser", "editor", "clipboard", "save"])
        content = complete if target in include else body
        return content, body, path, render_settings, parser, selection

    def _execute(self, target: str, choose_parser: bool = False) -> None:
        try:
            settings = self._settings()
            parser = self._pick_parser(settings) if choose_parser else settings.get("parser", "markdown")
            if parser is None:
                return
            live = target == "browser" and bool(settings.get("enable_autoreload", True))
            content, _, path, render_settings, parser, selection = self._render(
                ed, target, parser=parser, live_reload=live
            )
            if target == "browser":
                _write_utf8(path, content)
                _write_live_marker(render_settings)
                self._sessions[_document_key(ed)] = {
                    "path": str(path), "parser": parser, "selection": selection
                }
                self._open_browser(path, settings.get("browser", "default"))
                _status("preview opened in browser")
            elif target == "editor":
                self._open_editor(content)
                _status("HTML opened in a CudaText tab")
            elif target == "clipboard":
                app_proc(PROC_SET_CLIP, content)
                _status("HTML copied to clipboard")
            elif target == "save":
                destination = render_settings.get("builtin", {}).get("destination")
                if not destination:
                    source_name = ed.get_filename()
                    initial = str(Path(source_name).with_suffix(".html")) if source_name else "preview.html"
                    destination = dlg_file(
                        False, os.path.basename(initial), os.path.dirname(initial),
                        "HTML files|*.html;*.htm|All files|*.*", "Save Markdown as HTML"
                    )
                if destination:
                    _write_utf8(Path(destination), content)
                    _status("saved to " + destination)
        except PreviewError as exc:
            _error(str(exc))
        except Exception as exc:
            traceback.print_exc()
            _error("Unexpected error: {}".format(exc))

    def _open_browser(self, path: Path, browser: str) -> None:
        if not browser or browser == "default":
            safe_open_url(_browser_file_url(path))
            return
        executable = os.path.expandvars(os.path.expanduser(browser))
        if not os.path.isfile(executable):
            raise PreviewError("Configured browser does not exist: {}".format(executable))
        subprocess.Popen([executable, str(path)])

    def _open_editor(self, content: str, title: str = "Markdown Advanced Preview.html") -> None:
        file_open("")
        ed.set_text_all(content)
        ed.set_prop(PROP_LEXER_FILE, "HTML")
        ed.set_prop(PROP_TAB_TITLE, title)

    def run(self) -> None:
        """Preview with the configured default parser."""
        self._execute("browser")

    def run_select(self) -> None:
        self._execute("browser", choose_parser=True)

    def export_editor(self) -> None:
        self._execute("editor", choose_parser=True)

    def save_html(self) -> None:
        self._execute("save", choose_parser=True)

    def copy_html(self) -> None:
        self._execute("clipboard", choose_parser=True)

    def cheatsheet(self) -> None:
        try:
            sample = (PLUGIN_DIR / "samples" / "sample.md").read_text(encoding="utf-8-sig")
            self._open_editor(sample, "Markdown Cheatsheet.md")
            ed.set_prop(PROP_LEXER_FILE, "Markdown")
        except OSError as exc:
            _error("Cannot open the Markdown cheatsheet: {}".format(exc))

    def config(self) -> None:
        try:
            if not SETTINGS_FILE.exists():
                SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(str(DEFAULT_SETTINGS_FILE), str(SETTINGS_FILE))
            file_open(str(SETTINGS_FILE))
        except OSError as exc:
            _error("Cannot open settings: {}".format(exc))

    def config_live(self) -> None:
        """Compatibility command: toggle live reload in the user JSON file."""
        try:
            user = {}
            if SETTINGS_FILE.is_file():
                with SETTINGS_FILE.open("r", encoding="utf-8-sig") as stream:
                    user = json.load(stream)
            current = bool(self._settings().get("enable_autoreload", True))
            user["enable_autoreload"] = not current
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with SETTINGS_FILE.open("w", encoding="utf-8", newline="") as stream:
                json.dump(user, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            _status("automatic reload is now {}".format("enabled" if not current else "disabled"))
        except (OSError, ValueError) as exc:
            _error("Cannot update settings: {}".format(exc))

    def _update_session(self, editor: Any) -> None:
        session = self._sessions.get(_document_key(editor))
        if not session:
            return
        try:
            content, _, path, render_settings, _, _ = self._render(
                editor, "browser", parser=session["parser"],
                use_selection=session.get("selection", False), live_reload=True
            )
            _write_utf8(Path(session.get("path", path)), content)
            _write_live_marker(render_settings)
        except Exception:
            traceback.print_exc()

    def on_change_slow(self, ed_self: Any) -> None:
        try:
            if _document_key(ed_self) not in self._sessions:
                return
            if self._settings().get("enable_autoreload", True):
                self._update_session(ed_self)
        except Exception:
            traceback.print_exc()

    def on_save(self, ed_self: Any) -> None:
        self.on_change_slow(ed_self)

    def on_close(self, ed_self: Any) -> None:
        self._sessions.pop(_document_key(ed_self), None)

    def on_exit(self, ed_self: Any) -> None:
        try:
            expected = Path(tempfile.gettempdir()).resolve() / "cuda_markdown_advanced_preview"
            if DEFAULT_TEMP_DIR.resolve() == expected and DEFAULT_TEMP_DIR.is_dir():
                shutil.rmtree(str(DEFAULT_TEMP_DIR))
        except OSError:
            pass
