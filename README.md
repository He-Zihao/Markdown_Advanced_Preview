# Markdown Advanced Preview for CudaText

English | [简体中文](README_CN.md)

Markdown Advanced Preview converts Markdown to a styled HTML document from
inside CudaText. It can open a live browser preview, export HTML to a CudaText
tab, save HTML to disk, or copy HTML to the clipboard.

The offline renderer, styles, Python dependencies, and default MathJax engine
are included. Formula typesetting therefore works locally for normal use.

## Installation

Install the release ZIP with **Plugins > Addons Manager > Install from ZIP
file**. Restart CudaText if the commands do not appear immediately. The ZIP
must contain `install.inf` at its root.

## Commands and basic use

Open a Markdown document and choose **Plugins > Markdown Advanced Preview**.
Alternatively, press `Ctrl+Shift+P`, type the command name (or
`Markdown Advanced Preview`), and select it from CudaText's command palette:

- **Preview** renders with the configured parser and opens a browser.
- **Preview - select parser...** asks which enabled parser to use.
- **Export HTML to CudaText tab...** creates an HTML tab.
- **Save as HTML...** writes the rendered document to a file.
- **Copy HTML to clipboard...** copies the rendered HTML.
- **Open Markdown cheatsheet** opens a syntax and rendering sample.
- **Settings...** creates or opens the user settings file.
- **Toggle automatic reload** enables or disables live preview rebuilding.

A non-empty editor selection is rendered instead of the whole document. Once
a browser preview is open, the plugin rebuilds it after edits and saves. The
browser reloads only after the generated HTML changes and restores its scroll
position by default.

## Configuration file

Choose **Settings...** to edit `cuda_markdown_advanced_preview.json` in the
CudaText settings directory. It is created from `settings_default.json` on
first use.

This file is strict JSON:

- comments are not allowed;
- trailing commas are not allowed;
- local paths are ordinary strings such as
  `C:/Users/name/mathjax-config.js`, not `file:///` URLs;
- `css` and `js` are objects containing a list for each parser, not one global
  list.

User values override packaged defaults. Nested objects are merged, while an
array replaces the complete default array. Copy the packaged value before
customizing a long array such as `markdown_extensions`.

### Settings reference

| Setting | Values and purpose |
| --- | --- |
| `browser` | `default`, or the absolute path of a browser executable |
| `parser` | `markdown`, `github`, `gitlab`, or a key in `markdown_binary_map` |
| `enabled_parsers` | Parsers shown by parser-selection commands |
| `theme` | `auto`, `light`, or `dark` |
| `enable_autoreload` | Rebuild an already-open browser preview after edits |
| `live_reload_interval_ms` | Browser change-check interval; minimum 500 ms |
| `preserve_scroll` | Restore browser scroll position after reload |
| `enable_mathjax` | Enable Arithmatex output and the default MathJax assets |
| `pygments_style` | A bundled Pygments style, or `github`, `github2014`, `github_dynamic` |
| `pygments_inject_css` | Embed syntax-highlighting CSS in complete HTML documents |
| `pygments_css_class` | Wrapper class used by generated highlighting CSS |
| `css` / `js` | Per-parser arrays of `default`, URLs, local files, or plugin resources |
| `allow_css_overrides` | Load a same-name `.css` file beside the Markdown file |
| `html_template` | Template containing `{{ HEAD }}`, `{{ BODY }}`, and optional `{{ THEME }}` |
| `image_path_conversion` | `absolute`, `relative`, `base64`, or `none` |
| `file_path_conversions` | `absolute`, `relative`, or `none` |
| `strip_yaml_front_matter` | Read YAML metadata and per-document overrides |
| `strip_critic_marks` | `accept`, `reject`, or `none` |
| `path_tempfile` | Absolute preview directory, or a path relative to the source file |
| `include_head` | Output targets that receive a complete HTML document |

The target names for `include_head` are `browser`, `editor`, `clipboard`, and
`save`. Omitted targets receive only an HTML body fragment.

Advanced settings:

| Setting | Purpose |
| --- | --- |
| `markdown_extensions` | Complete Python-Markdown extension list and per-extension options |
| `markdown_binary_map` | External parser names mapped to executable/argument arrays |
| `github_mode` | GitHub API mode, normally `markdown` or `gfm` |
| `gitlab_mode` | Select GitLab GFM behavior |
| `github_inject_header_ids` | Copy GitHub-generated anchor IDs onto heading elements |
| `github_oauth_token` | Optional GitHub API token; keep it only in user settings |
| `gitlab_personal_token` | Optional GitLab API token; keep it only in user settings |
| `gitlab_highlight_theme` | Theme class applied to GitLab highlighted code |
| `html_simple` | Return simplified HTML and omit the document wrapper |

## Markdown extensions

The default offline parser combines Python-Markdown with PyMdown Extensions.
It enables footnotes, attribute lists, definition lists, tables,
abbreviations, Markdown inside HTML, metadata, sane lists, SmartyPants,
WikiLinks, admonitions, details, improved emphasis, formulas, SuperFences,
automatic links, task lists, deletion syntax, and GitHub emoji.

Objects inside `markdown_extensions` use an extension module name as the key
and its options as the value. The special `!!python/name` object used by the
packaged defaults resolves a named function; it is not standard JSON syntax
from PyYAML and should only point to trusted bundled modules.

### Extension compatibility

Do not combine replacement extensions with the extensions they replace:

- `pymdownx.superfences` replaces `markdown.extensions.fenced_code`;
- `pymdownx.betterem` replaces the legacy
  `markdown.extensions.smartstrong`;
- `pymdownx.extra` replaces `markdown.extensions.extra` and already includes
  several other extensions.

The packaged configuration lists individual components instead of enabling
`extra`, which makes conflicts and behavior explicit. SuperFences performs
Pygments highlighting itself in the bundled version; adding
`markdown.extensions.codehilite` or another highlighting pipeline may produce
overlapping output. If you replace SuperFences with `fenced_code`, configure
`codehilite` as a pair and test your complete extension list.

See the [PyMdown compatibility notes](https://facelessuser.github.io/pymdown-extensions/usage_notes/)
before replacing the default list.

### Useful syntax

Task lists:

```markdown
- [x] Complete
- [ ] Pending
```

Admonitions use an indented body:

```markdown
!!! warning "Warning"
    The body is indented by four spaces.
```

Admonitions are attractive in HTML but are not part of standard Markdown and
may not work in Pandoc or other renderers. A portable alternative is a
blockquote containing an emoji and a bold heading.

The default `pymdownx.tilde` configuration supports `~~deleted~~`. Subscript
syntax is deliberately disabled because it is less portable and whitespace
handling can be surprising.

### Code fences and SuperFences

Ordinary fences work as expected:

````markdown
```python
print("hello")
```
````

For line numbers and highlighted lines, this bundled extension version expects
the brace-style language class:

````markdown
```{.python linenums="1" hl_lines="1 3"}
print("first")
print("second")
print("third")
```
````

The common form ```` ```python { ... } ```` is not accepted by this bundled
PyMdown version. Brace-style headers may also be less well understood by
editor syntax highlighters and other Markdown processors.

The defaults recognize `mermaid`, `flow`, and `sequence` custom fences and add
corresponding HTML classes, but recognition does not render a diagram by
itself. A compatible browser-side diagram engine and initialization script
must be added through `js`. Mermaid versions differ in their initialization
API, so no unpinned Mermaid configuration is enabled for the offline parser.

### Arithmatex

`pymdownx.arithmatex` identifies formulas before MathJax or another browser
engine renders them. The default uses `generic: true`, which normalizes inline
formula output to `\(...\)` and display output to `\[...\]`. This is reliable
for the configurable MathJax 3/4 pipeline and other client-side engines.

### Emoji

The default `:warning:`-style emoji configuration creates small PNG images
using GitHub's emoji index and image host. It avoids oversized images by
setting explicit dimensions, but the browser still needs network access.
Change `pymdownx.emoji` only after checking that the chosen generator and image
source match; sprite and SVG generators require different options.

## MathJax

The default configuration loads:

1. `js/mathjax4_config.js`;
2. the bundled MathJax 4.1.3 `js/tex-mml-chtml.js`.

It supports inline `$...$` and `\(...\)`, display `$$...$$` and `\[...\]`,
and AMS-style numbering for environments such as `equation`, `align`, and
`gather`. The bundled pre-load configuration sets `tex.tags` to `ams`.

### How `mathjax4_config.js` is configured

MathJax 3 and 4 read the global `window.MathJax` object only while the engine
starts. Consequently, `mathjax4_config.js` must be loaded before
`tex-mml-chtml.js`, exactly as ordered in `settings_default.json`. The bundled
file contains:

```javascript
window.MathJax = {
  tex: {
    tags: "ams"
  },
  options: {
    enableMenu: true
  }
};
```

- `tex.tags: "ams"` enables automatic numbering for AMS environments such as
  `equation`, `align`, and `gather`, and provides the numbering required by
  `\label`, `\ref`, and `\eqref`. Use `"none"` to disable automatic numbering,
  or `"all"` to number all displayed equations.
- `options.enableMenu: true` enables MathJax's contextual menu. Change it to
  `false` if the menu is not wanted.
- `inlineMath` and `displayMath` are intentionally not repeated here. The
  enabled `pymdownx.arithmatex` extension, configured with `generic: true`,
  recognizes `$...$`, `$$...$$`, `\(...\)`, and `\[...\]` first and emits the
  normalized delimiters that MathJax consumes. Define these options only when
  deliberately overriding that pipeline.
- `tex-mml-chtml.js` accepts TeX and MathML input and produces CommonHTML
  (CHTML). This is why the default output behaves more like selectable HTML
  text than the SVG component.

To keep a custom configuration across plugin upgrades, copy the configuration
to another file and put it immediately before the engine in the `js.markdown`
list. For example:

```json
{
  "js": {
    "markdown": [
      "C:/Users/name/my_mathjax4_config.js",
      "js/tex-mml-chtml.js"
    ]
  }
}
```

CudaText paths may be absolute as above or relative to the plugin directory;
do not use a `file:///` URL. See the official
[MathJax loading documentation](https://docs.mathjax.org/en/latest/web/loading.html).

### Other MathJax versions

The bundled configuration uses the MathJax 3/4 configuration API and can also
precede a compatible MathJax 3 CHTML component. Check any custom component's
packages and configuration API before replacing the bundled 4.1.3 engine.

### MathJax 2

The bundled legacy file calls `MathJax.Hub.Config`, so load the MathJax 2
engine first and that configuration second:

```json
{
  "js": {
    "markdown": [
      "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.9/MathJax.js",
      "res://MarkdownAdvancedPreview/js/math_config.js"
    ]
  }
}
```

### Local MathJax and KaTeX

The default Markdown parser already uses the bundled MathJax component and
does not need to fetch its main engine from a CDN. MathJax's official 4.x npm
filename is `tex-mml-chtml.js`; the distributed file is already minified, so
there is no separate `tex-mml-chtml.min.js` in the package. Rare dynamically
loaded font ranges, optional TeX packages, or accessibility data can still
require additional MathJax packages or network access when used.

For another local version, use a path relative to the plugin directory or an
absolute path such as `C:/path/to/file.js`.

There is no `enable_katex` setting for the offline `markdown` parser. KaTeX can
be used through custom `css` and `js` lists, but it needs its stylesheet,
engine, and an initialization script compatible with Arithmatex output. The
GitLab parser has separate built-in KaTeX/Mermaid assets for GitLab API output.

Set `enable_mathjax` to `false` to remove the default Arithmatex activation and
MathJax assets. Explicit custom assets in `js` are still your responsibility.

## CSS, JavaScript, and templates

`settings_default.json` lists the built-in assets explicitly with paths such
as `css/markdown.css` and `js/mathjax4_config.js`. Paths are relative to the
plugin directory. HTTPS URLs, absolute local paths, and packaged `res://`
resources are also supported. The legacy `default` value remains supported in
user settings and expands to the same built-in list.

```json
{
  "theme": "dark",
  "css": {
    "markdown": ["default", "C:/Users/name/markdown-override.css"]
  },
  "html_template": "C:/Users/name/markdown-template.html"
}
```

Local CSS and JavaScript are embedded into generated HTML. Remote URLs remain
external and are requested by the browser. A same-name CSS file beside the
source (for example, `notes.css` beside `notes.md`) is appended when
`allow_css_overrides` is true.

Pygments styles generated by name are static. The bundled `github_dynamic`
style uses media queries so it can follow the system light/dark preference.
Use custom CSS when a third-party Pygments style must switch dynamically.

## Online and external parsers

The `github` and `gitlab` parsers send the selected text or document text to
the corresponding Markdown API. Optional access tokens belong only in the
user settings file:

```json
{
  "github_oauth_token": "",
  "gitlab_personal_token": ""
}
```

Do not put secrets in `settings_default.json` or a shared Markdown document.

External parsers read Markdown from standard input and must write an HTML body
fragment to standard output:

```json
{
  "markdown_binary_map": {
    "pandoc": [
      "C:/Program Files/Pandoc/pandoc.exe",
      "-f", "markdown+emoji", "-t", "html"
    ]
  },
  "enabled_parsers": ["markdown", "pandoc"]
}
```

The first item must resolve to an existing executable. Arguments are passed
directly without a shell. Parser-specific syntax still needs matching Pandoc
input extensions or filters.

## YAML front matter

When `strip_yaml_front_matter` is true, a leading YAML block can set HTML
metadata such as `title` and `author`, plus `basepath`, `references`,
`destination`, or a nested `settings` object:

```yaml
---
title: Example
author: Ada
settings:
  theme: dark
---
```

This feature is disabled by default. Per-document settings can select local or
remote assets and output paths, so review front matter before enabling it for
untrusted Markdown.

## Network and security notes

- The offline `markdown` parser does not upload document text. The default
  page uses bundled MathJax, but may request emoji images from GitHub. Rare
  MathJax font ranges, optional packages, or accessibility data can also make
  network requests unless their supporting packages are installed locally.
- The `github` and `gitlab` parsers upload the Markdown being converted to
  those services. Their API policies and limits apply.
- Custom JavaScript, templates, external parser commands, and YAML setting
  overrides are trusted configuration and may execute code or read files.
- Generated HTML can contain raw HTML from the Markdown document. Open
  untrusted documents with the same care as untrusted web pages.

## Origins and licenses

This plugin is a CudaText port and adaptation of
[MarkdownPreview 2.8.2](https://github.com/facelessuser/MarkdownPreview), and
also references Alexey Torgashin's original CudaText Markdown Preview plugin.
Development of the CudaText adaptation was assisted by generative AI.

The Markdown Advanced Preview project code is released under the
[MIT License](LICENSE). The copyright notice
`Copyright (c) 2026 He Zihao` applies to the CudaText port, rewritten adapter,
documentation, and other original additions and modifications. It does not
replace or claim exclusive ownership of pre-existing upstream material.

MarkdownPreview and the original CudaText Markdown Preview retain their own
copyright and MIT notices. Bundled libraries and assets also retain their own
licenses. All of these notices are indexed in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and must remain in
redistributed copies of the plugin.
