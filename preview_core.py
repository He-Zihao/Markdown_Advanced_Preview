"""Editor-independent rendering core for Markdown Advanced Preview.

The module contains no CudaText API calls, so it can also be tested with a
normal Python interpreter.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import html
from html import parser as _html_parser
import importlib
import json
import mimetypes
import os
import re
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen


PLUGIN_DIR = Path(__file__).resolve().parent
VENDOR_DIR = PLUGIN_DIR / "vendor"

# Load this plugin's Markdown and Pygments packages first, then expose the
# bundled PyYAML and PyMdown packages from ``vendor``.
import pygments  # noqa: E402
import markdown  # noqa: E402


def _ensure_html_parser_binding() -> None:
    global _html_parser
    _html_parser = sys.modules.get("html.parser", _html_parser)
    sys.modules["html.parser"] = _html_parser
    html.parser = _html_parser


# Python-Markdown loads and monkey-patches html.parser during its own import.
# Some CudaText Linux/Python combinations leave the cached child module
# detached from the parent ``html`` package.  PyMdown later accesses
# ``html.parser.HTMLParser`` and fails even though ``html.parser`` remains in
# sys.modules.  Repair that parent/child binding in this adapter rather than
# changing either bundled third-party package.
_ensure_html_parser_binding()

if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

import yaml  # noqa: E402
from pygments.formatters import get_formatter_by_name  # noqa: E402


DEFAULT_SETTINGS_FILE = PLUGIN_DIR / "settings_default.json"

PYGMENTS_LOCAL = {
    "github": "css/pygments/github.css",
    "github2014": "css/pygments/github2014.css",
    "github_dynamic": "css/pygments/github_dynamic.css",
}

DEFAULT_CSS = {
    "markdown": ["css/markdown.css"],
    "github": ["css/github.css"],
    "gitlab": [
        "css/gitlab.css",
        "css/katex.min.css",
    ],
}

DEFAULT_MATHJAX_JS = [
    "js/mathjax4_config.js",
    "js/tex-mml-chtml.js",
]

DEFAULT_JS = {
    "markdown": DEFAULT_MATHJAX_JS,
    "github": [],
    "gitlab": [
        "js/katex.min.js",
        "js/mermaid.min.js",
        "js/gitlab_config.js",
    ],
}

BUILTIN_KEYS = ("basepath", "references", "destination")
LOCAL_SCHEMES = ("", "file")


class PreviewError(RuntimeError):
    """A conversion or configuration error suitable for showing to users."""


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        with path.open("r", encoding="utf-8-sig") as stream:
            data = json.load(stream)
    except (OSError, ValueError) as exc:
        raise PreviewError("Cannot read settings '{}': {}".format(path, exc)) from exc
    if not isinstance(data, dict):
        raise PreviewError("Settings root must be a JSON object: '{}'".format(path))
    return data


def load_settings(user_file: Optional[str] = None) -> Dict[str, Any]:
    """Load packaged defaults and recursively overlay user settings."""
    defaults = _load_json(DEFAULT_SETTINGS_FILE)
    if not user_file:
        return defaults
    return _deep_merge(defaults, _load_json(Path(user_file)))


def _decode_python_names(value: Any) -> Any:
    if isinstance(value, dict):
        if set(value) == {"!!python/name"}:
            dotted = value["!!python/name"]
            module_name, attribute = dotted.rsplit(".", 1)
            return getattr(importlib.import_module(module_name), attribute)
        return {key: _decode_python_names(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_decode_python_names(item) for item in value]
    return value


def _yaml_load_ordered(source: str) -> Dict[str, Any]:
    class OrderedSafeLoader(yaml.SafeLoader):
        pass

    def construct_mapping(loader: Any, node: Any) -> OrderedDict:
        loader.flatten_mapping(node)
        return OrderedDict(loader.construct_pairs(node))

    OrderedSafeLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
    )
    result = yaml.load(source, Loader=OrderedSafeLoader)
    return result if isinstance(result, dict) else {}


class Settings:
    """Settings plus per-document front-matter overrides."""

    def __init__(self, data: Dict[str, Any], file_name: Optional[str]):
        self.data = copy.deepcopy(data)
        self.file_name = file_name
        self.overrides: Dict[str, Any] = {
            "builtin": {"references": [], "basepath": self.get_base_path(None)},
            "meta": {},
        }

    def get(self, key: str, default: Any = None) -> Any:
        if key in self.overrides:
            return self.overrides[key]
        value = self.data.get(key, default)
        return _decode_python_names(copy.deepcopy(value)) if key == "markdown_extensions" else value

    def get_base_path(self, basepath: Optional[str]) -> Optional[str]:
        if basepath:
            candidate = Path(os.path.expandvars(os.path.expanduser(basepath)))
            if candidate.is_absolute() and candidate.is_dir():
                return str(candidate.resolve())
        if self.file_name and os.path.isfile(self.file_name):
            return os.path.dirname(os.path.abspath(self.file_name))
        return None

    def resolve_meta_path(self, target: Any) -> Optional[str]:
        if target is None:
            return None
        raw = os.path.expandvars(os.path.expanduser(str(target)))
        candidate = Path(raw)
        bases = []
        if self.file_name:
            bases.append(Path(self.file_name).resolve().parent)
        if self.overrides["builtin"].get("basepath"):
            bases.append(Path(self.overrides["builtin"]["basepath"]))
        candidates = [candidate] if candidate.is_absolute() else [base / candidate for base in bases]
        for item in candidates:
            if item.exists():
                return str(item.resolve())
        return str(candidate.resolve()) if candidate.is_absolute() else None

    def add_meta(self, meta: Dict[str, Any]) -> None:
        merged = dict(meta or {})
        merged.update(self.overrides.get("meta", {}))
        self.overrides["meta"] = merged

    def apply_frontmatter(self, frontmatter: Dict[str, Any]) -> None:
        values = copy.deepcopy(frontmatter)
        if "basepath" in values:
            self.overrides["builtin"]["basepath"] = self.get_base_path(values.pop("basepath"))
        for key, value in values.items():
            if key == "settings" and isinstance(value, dict):
                self.overrides.update(value)
            elif key == "references":
                refs = value if isinstance(value, list) else [value]
                self.overrides["builtin"][key] = [
                    resolved for resolved in (self.resolve_meta_path(ref) for ref in refs)
                    if resolved and not os.path.isdir(resolved)
                ]
            elif key == "destination":
                destination = self._resolve_destination(value)
                if destination:
                    self.overrides["builtin"][key] = destination
            elif key not in BUILTIN_KEYS:
                if isinstance(value, list):
                    value = [str(item) for item in value]
                elif value is not None:
                    value = str(value)
                self.overrides["meta"][str(key)] = value

    def _resolve_destination(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        raw = Path(os.path.expandvars(os.path.expanduser(str(value))))
        if raw.is_absolute():
            return str(raw)
        base = self.overrides["builtin"].get("basepath")
        return str(Path(base) / raw) if base else None


def _read_utf8(path: str) -> str:
    with open(path, "r", encoding="utf-8-sig") as stream:
        return stream.read()


def _resource_path(name: str) -> Path:
    prefix = "res://MarkdownAdvancedPreview/"
    relative = name[len(prefix):] if name.startswith(prefix) else name
    return PLUGIN_DIR / Path(relative.replace("/", os.sep))


def _is_web_url(value: str) -> bool:
    return bool(re.match(r"^https?://", value, re.I))


def _asset_tags(items: Any, kind: str) -> str:
    if items is None:
        return ""
    if isinstance(items, str):
        items = [items]
    result = []
    for item in items:
        item = os.path.expandvars(os.path.expanduser(str(item)))
        if _is_web_url(item):
            if kind == "css":
                result.append('<link href="{}" rel="stylesheet" type="text/css">'.format(html.escape(item, quote=True)))
            else:
                result.append('<script src="{}"></script>'.format(html.escape(item, quote=True)))
            continue
        path = _resource_path(item) if item.startswith("res://") else Path(item)
        if not path.is_absolute():
            path = PLUGIN_DIR / path
        if path.is_file():
            if kind == "css":
                result.append("<style>{}</style>".format(_read_utf8(str(path))))
            else:
                # Keep local JavaScript external. Apart from preventing large
                # bundles such as MathJax from being dumped into the generated
                # document, this preserves document.currentScript.src. MathJax
                # 4 uses that URL to determine its component/resource root.
                result.append('<script src="{}"></script>'.format(
                    html.escape(path.resolve().as_uri(), quote=True)
                ))
    return "\n".join(result)


def _expand_default_assets(configured: Any, compiler: str, defaults: Dict[str, List[str]]) -> List[str]:
    if isinstance(configured, dict):
        configured = configured.get(compiler, ["default"])
    if isinstance(configured, str):
        configured = [configured]
    result = list(configured or [])
    if "default" in result:
        index = result.index("default")
        result[index:index + 1] = defaults.get(compiler, [])
    return result


def _strip_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    match = re.search(r"^---\r?\n(?!\r?\n)(.*?)(?<=\n)(?:---|\.\.\.)\r?\n", text, re.S)
    if not match:
        return {}, text
    try:
        values = _yaml_load_ordered(match.group(1))
    except Exception:
        return {}, text
    return values, text[match.end():]


def _critic_markup(text: str, mode: str) -> str:
    accept = mode == "accept"
    text = re.sub(r"\{\+\+(.*?)\+\+\}", lambda m: m.group(1) if accept else "", text, flags=re.S)
    text = re.sub(r"\{--(.*?)--\}", lambda m: "" if accept else m.group(1), text, flags=re.S)
    text = re.sub(
        r"\{~~(.*?)~>(.*?)~~\}",
        lambda m: m.group(2) if accept else m.group(1),
        text,
        flags=re.S,
    )
    text = re.sub(r"\{>>(.*?)<<\}", "", text, flags=re.S)
    return re.sub(r"\{==(.*?)==\}", r"\1", text, flags=re.S)


def _local_path(url: str, base_path: Optional[str]) -> Optional[Path]:
    parts = urlsplit(html.unescape(url))
    if parts.scheme not in LOCAL_SCHEMES or parts.netloc not in ("", "localhost"):
        return None
    raw = unquote(parts.path)
    if parts.scheme == "file" and re.match(r"^/[A-Za-z]:/", raw):
        raw = raw[1:]
    candidate = Path(raw)
    if not candidate.is_absolute():
        if not base_path:
            return None
        candidate = Path(base_path) / candidate
    return candidate.resolve()


def _rewrite_paths(
    source: str,
    image_mode: str,
    file_mode: str,
    base_path: Optional[str],
    output_path: Optional[str],
) -> str:
    pattern = re.compile(r"(?P<attr>\b(?:src|href)\s*=\s*)(?P<quote>['\"])(?P<url>.*?)(?P=quote)", re.I | re.S)

    def replace(match: re.Match) -> str:
        attr = match.group("attr")
        url = match.group("url")
        url_parts = urlsplit(html.unescape(url))
        is_image = attr.lower().lstrip().startswith("src")
        mode = image_mode if is_image else file_mode
        if mode == "none" or url.startswith(("#", "data:", "mailto:", "javascript:")):
            return match.group(0)
        path = _local_path(url, base_path)
        if path is None:
            return match.group(0)
        if mode == "base64" and is_image and path.is_file():
            mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            new_url = "data:{};base64,{}".format(mime, encoded)
        elif mode == "absolute":
            try:
                new_url = path.as_uri()
            except ValueError:
                new_url = str(path).replace(os.sep, "/")
        elif mode == "relative" and output_path:
            new_url = os.path.relpath(str(path), os.path.dirname(output_path)).replace(os.sep, "/")
        else:
            return match.group(0)
        if mode != "base64":
            if url_parts.query:
                new_url += "?" + url_parts.query
            if url_parts.fragment:
                new_url += "#" + url_parts.fragment
        return "{}{}{}{}".format(attr, match.group("quote"), html.escape(new_url, quote=True), match.group("quote"))

    return pattern.sub(replace, source)


def _simple_html(source: str) -> str:
    source = re.sub(r"<!--.*?-->", "", source, flags=re.S)
    source = re.sub(r"\s+(?:id|class|style)=(['\"]).*?\1", "", source, flags=re.I | re.S)
    return re.sub(r"\s+on[a-z]+=(['\"]).*?\1", "", source, flags=re.I | re.S)


class Renderer:
    """Convert Markdown text to a complete HTML document and body fragment."""

    def __init__(self, settings_data: Dict[str, Any]):
        self.settings_data = settings_data

    def render(
        self,
        text: str,
        file_name: Optional[str],
        title: str = "untitled",
        parser: Optional[str] = None,
        preview_path: Optional[str] = None,
        preview: bool = True,
        live_reload: bool = False,
    ) -> Tuple[str, str, Settings]:
        settings = Settings(self.settings_data, file_name)
        if settings.get("strip_yaml_front_matter", False):
            frontmatter, text = _strip_frontmatter(text)
            settings.apply_frontmatter(frontmatter)
        for reference in settings.get("builtin", {}).get("references", []):
            try:
                text += "\n" + _read_utf8(reference)
            except OSError:
                pass
        critic_mode = settings.get("strip_critic_marks", "none")
        if critic_mode in ("accept", "reject"):
            text = _critic_markup(text, critic_mode)

        compiler = parser or settings.get("parser", "markdown")
        body = self._convert(text, compiler, settings)
        body = _rewrite_paths(
            body,
            settings.get("image_path_conversion", "absolute"),
            settings.get("file_path_conversions", "absolute"),
            settings.get("builtin", {}).get("basepath"),
            preview_path,
        )
        if settings.get("html_simple", False):
            body = _simple_html(body)
            return body, body, settings

        complete = self._document(body, title, compiler, settings, file_name)
        if live_reload:
            if preview_path:
                token = hashlib.sha1(complete.encode("utf-8")).hexdigest()
                marker_path = str(Path(preview_path).with_suffix(".version.js"))
                settings.live_reload_token = token
                settings.live_reload_marker = marker_path
                reload_script = self._reload_script(
                    settings, Path(marker_path).resolve().as_uri(), token
                )
            else:
                reload_script = self._reload_script(settings)
            complete = complete.replace("</body>", reload_script + "</body>")
        return complete, body, settings

    def _convert(self, text: str, compiler: str, settings: Settings) -> str:
        if compiler == "markdown":
            return self._convert_markdown(text, settings)
        if compiler == "github":
            return self._convert_online(text, compiler, settings)
        if compiler == "gitlab":
            return self._convert_online(text, compiler, settings)
        binary_map = settings.get("markdown_binary_map", {})
        if compiler in binary_map:
            return self._convert_external(text, compiler, binary_map[compiler])
        raise PreviewError("Unknown Markdown parser: {}".format(compiler))

    def _convert_markdown(self, text: str, settings: Settings) -> str:
        configured = settings.get("markdown_extensions", [])
        extensions: List[str] = []
        configs: Dict[str, Dict[str, Any]] = {}
        base_path = settings.get("builtin", {}).get("basepath") or ""
        math_enabled = bool(settings.get("enable_mathjax", True))
        for item in configured:
            if isinstance(item, str):
                name, config = item, {}
            elif isinstance(item, dict) and item:
                name = next(iter(item))
                config = item[name] or {}
            else:
                continue
            if name == "pymdownx.arithmatex" and not math_enabled:
                continue
            extensions.append(name)
            configs[name] = self._replace_base_path(config, base_path)
        # User setting files are full copies of earlier defaults.  Automatically
        # add Arithmatex so enabling MathJax also works with those older files.
        if math_enabled and "pymdownx.arithmatex" not in extensions:
            extensions.append("pymdownx.arithmatex")
            configs["pymdownx.arithmatex"] = {"generic": True}
        try:
            converter = markdown.Markdown(extensions=extensions, extension_configs=configs)
            result = converter.convert(text)
        except Exception as exc:
            raise PreviewError("Python-Markdown conversion failed: {}".format(exc)) from exc
        settings.add_meta(getattr(converter, "Meta", {}))
        return result

    def _replace_base_path(self, value: Any, base_path: str) -> Any:
        if isinstance(value, str):
            return value.replace("${BASE_PATH}", base_path)
        if isinstance(value, dict):
            return {key: self._replace_base_path(item, base_path) for key, item in value.items()}
        if isinstance(value, list):
            return [self._replace_base_path(item, base_path) for item in value]
        return value

    def _convert_online(self, text: str, compiler: str, settings: Settings) -> str:
        if compiler == "github":
            url = "https://api.github.com/markdown"
            payload = {"text": text, "mode": settings.get("github_mode", "markdown")}
            token = settings.get("github_oauth_token", "")
            headers = {"Content-Type": "application/json", "User-Agent": "CudaText-MarkdownAdvancedPreview"}
            if token:
                headers["Authorization"] = "token " + token
        else:
            url = "https://gitlab.com/api/v4/markdown"
            payload = {"text": text, "gfm": settings.get("gitlab_mode", "gfm") == "gfm"}
            token = settings.get("gitlab_personal_token", "")
            headers = {"Content-Type": "application/json"}
            if token:
                headers["Private-Token"] = token
        request = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise PreviewError("{} API returned HTTP {}: {}".format(compiler, exc.code, detail)) from exc
        except (URLError, OSError) as exc:
            raise PreviewError("Cannot connect to {} API: {}".format(compiler, exc)) from exc
        if compiler == "gitlab":
            try:
                result = json.loads(raw)["html"]
            except (ValueError, KeyError) as exc:
                raise PreviewError("GitLab API returned an invalid response") from exc
            result = re.sub(r'(<a.*?)(id="user-content-)(.*?>)', r'\1id="\3', result, flags=re.S)
            result = re.sub(
                r'(<img)([^>]*?)src="[^"]*"([^>]*?)data-src="([^"]*)"([^>]*?>)',
                r'\1\2src="\4"\3\5', result, flags=re.S,
            )
            if not settings.get("html_simple", False):
                result += '<script>const HIGHLIGHT_THEME = "{}";</script>'.format(
                    html.escape(settings.get("gitlab_highlight_theme", "white"), quote=True)
                )
            return result
        if settings.get("github_inject_header_ids", False):
            header_pattern = re.compile(
                r'(?P<open><h([1-6]) class="heading-element">)'
                r'(?P<text>.*?)(?P<close></h\2>\s*<a id="user-content-(?P<id>[^"]+)")',
                re.S,
            )
            raw = header_pattern.sub(
                lambda match: match.group("open")[:-1]
                + ' id="{}">'.format(match.group("id"))
                + match.group("text")
                + match.group("close"),
                raw,
            )
        return raw

    def _convert_external(self, text: str, name: str, command: Any) -> str:
        if isinstance(command, str):
            command = [command]
        if not isinstance(command, list) or not command:
            raise PreviewError("External parser '{}' has no command".format(name))
        executable = os.path.expandvars(os.path.expanduser(str(command[0])))
        if not os.path.isfile(executable):
            raise PreviewError("Cannot find external parser: {}".format(executable))
        args = [executable] + [str(value) for value in command[1:]]
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        process = subprocess.run(
            args,
            input=text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            check=False,
        )
        if process.returncode:
            error = process.stderr.decode("utf-8", "replace").strip()
            raise PreviewError("External parser '{}' failed: {}".format(name, error))
        return process.stdout.decode("utf-8", "replace")

    def _document(self, body: str, fallback_title: str, compiler: str, settings: Settings, file_name: Optional[str]) -> str:
        metadata = settings.get("meta", {}) or {}
        title_value = metadata.get("title", fallback_title)
        if isinstance(title_value, list):
            title_value = title_value[0] if title_value else fallback_title
        meta_tags = []
        for key, value in metadata.items():
            if key.lower() == "title" or value is None:
                continue
            if isinstance(value, list):
                value = ",".join(str(item) for item in value)
            meta_tags.append('<meta name="{}" content="{}">'.format(
                html.escape(str(key), quote=True), html.escape(str(value), quote=True)
            ))

        css_items = _expand_default_assets(settings.get("css", {}), compiler, DEFAULT_CSS)
        if settings.get("allow_css_overrides", True) and file_name:
            source = Path(file_name)
            override = source.with_suffix(".css")
            if override.is_file():
                css_items.append(str(override))
        head = "\n".join(meta_tags)
        head += "\n" + _asset_tags(css_items, "css")
        js_items = _expand_default_assets(settings.get("js", {}), compiler, DEFAULT_JS)
        if compiler == "markdown" and not settings.get("enable_mathjax", True):
            # The packaged settings spell out the default paths so users can see
            # exactly what is loaded.  Continue to let this switch remove those
            # assets, as it did when the settings used the "default" sentinel.
            default_mathjax = set(DEFAULT_MATHJAX_JS)
            js_items = [item for item in js_items if item not in default_mathjax]
        head += "\n" + _asset_tags(js_items, "js")
        if compiler == "markdown" and settings.get("pygments_inject_css", True):
            head += "\n" + self._highlight_css(settings)
        head += "\n<title>{}</title>".format(html.escape(str(title_value)))

        template = settings.get("html_template", "")
        if template:
            path = Path(os.path.expandvars(os.path.expanduser(template)))
            if path.is_file():
                return (
                    _read_utf8(str(path))
                    .replace("{{ HEAD }}", head, 1)
                    .replace("{{ THEME }}", str(settings.get("theme", "auto")))
                    .replace("{{ BODY }}", body, 1)
                )
        return (
            '<!DOCTYPE html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            + head
            + '</head><body data-theme="{}"><article class="markdown-body">'.format(
                html.escape(str(settings.get("theme", "auto")), quote=True)
            )
            + body
            + "</article></body></html>"
        )

    def _highlight_css(self, settings: Settings) -> str:
        style_name = settings.get("pygments_style", "github_dynamic")
        css_class = "".join(
            "." + item for item in str(settings.get("pygments_css_class", "highlight")).split() if item
        )
        if style_name in PYGMENTS_LOCAL:
            source = _read_utf8(str(_resource_path(PYGMENTS_LOCAL[style_name])))
            source = source % {"css_class": css_class}
        else:
            try:
                source = get_formatter_by_name("html", style=style_name).get_style_defs(css_class)
            except Exception:
                source = _read_utf8(str(_resource_path(PYGMENTS_LOCAL["github"]))) % {"css_class": css_class}
        return "<style>{}</style>".format(source)

    def _reload_script(
        self,
        settings: Settings,
        marker_url: Optional[str] = None,
        baseline: Optional[str] = None,
    ) -> str:
        interval = settings.get("live_reload_interval_ms", 1500)
        try:
            interval = max(500, int(interval))
        except (TypeError, ValueError):
            interval = 1500
        preserve = "true" if settings.get("preserve_scroll", True) else "false"
        if not marker_url or not baseline:
            return """<script>(function(){
var keep=%s,key='cuda-md-preview:'+location.pathname;
if(keep){try{var p=JSON.parse(sessionStorage.getItem(key));if(p)scrollTo(p.x,p.y)}catch(e){}}
setTimeout(function(){if(keep){try{sessionStorage.setItem(key,JSON.stringify({x:scrollX,y:scrollY}))}catch(e){}}location.reload()},%d);
})();</script>""" % (preserve, interval)
        return """<script>(function(){
var keep=%s,key='cuda-md-preview:'+location.pathname,baseline=%s,marker=%s;
if(keep){try{var p=JSON.parse(sessionStorage.getItem(key));if(p)scrollTo(p.x,p.y)}catch(e){}}
function remember(){if(keep){try{sessionStorage.setItem(key,JSON.stringify({x:scrollX,y:scrollY}))}catch(e){}}}
function check(){
  window.__cudaMdPreviewVersion='';
  var script=document.createElement('script');
  script.src=marker+'?t='+Date.now();
  script.onload=function(){
    var changed=window.__cudaMdPreviewVersion && window.__cudaMdPreviewVersion!==baseline;
    script.remove();
    if(changed){remember();location.reload();}else{setTimeout(check,%d);}
  };
  script.onerror=function(){script.remove();setTimeout(check,%d);};
  document.head.appendChild(script);
}
setTimeout(check,%d);
})();</script>""" % (
            preserve,
            json.dumps(baseline),
            json.dumps(marker_url),
            interval,
            interval,
            interval,
        )
