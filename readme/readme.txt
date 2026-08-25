Markdown Advanced Preview for CudaText
======================================

Markdown Advanced Preview converts Markdown to styled HTML. It can open a
live browser preview, export HTML to a CudaText tab, save HTML to disk, or copy
HTML to the clipboard. The offline renderer and its Python dependencies are
included in the plugin.

Installation
------------

Install the release ZIP with CudaText's "Plugins > Addons Manager > Install
from ZIP file" command. Restart CudaText if the commands do not appear
immediately.

Commands
--------

Open a Markdown document and choose "Plugins > Markdown Advanced Preview".
You can also press Ctrl+Shift+P, type a command name or "Markdown Advanced
Preview", and execute it from CudaText's command palette:

* Preview: render with the configured parser and open the result in a browser.
* Preview - select parser: choose one of the enabled parsers.
* Export HTML to CudaText tab: create an HTML tab.
* Save as HTML: write the result to a file.
* Copy HTML to clipboard: copy the rendered HTML.
* Open Markdown cheatsheet: open a syntax sample.
* Settings: create or open the user settings file.
* Toggle automatic reload: enable or disable live preview rebuilding.

A non-empty editor selection is rendered instead of the whole document. Once
a browser preview is open, the plugin rebuilds it after edits and saves. The
browser reloads only after the generated HTML changes and restores its scroll
position by default.

Configuration
-------------

The Settings command opens cuda_markdown_advanced_preview.json in CudaText's
settings directory. It is created from settings_default.json on first use. It
is recreated on startup if deleted. It must be strict JSON: comments and
trailing commas are not accepted. Nested
objects are merged with defaults; arrays replace the complete default array.

Linux compatibility
-------------------

The plugin adapter repairs a CudaText embedded-Python state where html.parser
is cached but is no longer attached to the html package. This fixes the
PyMdown import error without modifying bundled third-party libraries and stays
compatible with older zipimporter loaders. Restart CudaText after upgrading.

Important settings:

* browser: "default" or an absolute browser executable path.
* parser: "markdown", "github", "gitlab", or an external parser name.
* enabled_parsers: parsers shown in parser-selection menus.
* theme: "auto", "light", or "dark".
* enable_autoreload: rebuild an open preview after edits.
* live_reload_interval_ms: browser check interval, at least 500 ms.
* preserve_scroll: restore the browser scroll position after reload.
* enable_mathjax: enable formula processing and default MathJax assets.
* pygments_style: syntax highlighting style.
* css and js: per-parser lists of plugin-relative paths, "default", URLs,
  absolute local files, or res://MarkdownAdvancedPreview/... resources.
* allow_css_overrides: load a same-name .css file beside the Markdown file.
* html_template: template with {{ HEAD }}, {{ BODY }}, and optionally
  {{ THEME }} placeholders.
* image_path_conversion: "absolute", "relative", "base64", or "none".
* file_path_conversions: "absolute", "relative", or "none".
* strip_yaml_front_matter: read YAML metadata and per-document overrides.
* strip_critic_marks: "accept", "reject", or "none".
* path_tempfile: preview directory; blank uses the system temporary directory.
* include_head: any of "browser", "editor", "clipboard", and "save" that
  should receive a complete HTML document instead of an HTML body fragment.

Math and custom assets
----------------------

MathJax is enabled by default and its 4.1.3 combined component is bundled in
the plugin. Inline $...$ and \(...\), and display $$...$$ and \[...\], are
supported. Set enable_mathjax to false to disable it. Rare dynamic font
ranges, optional TeX packages, or accessibility data may still need extra
MathJax files or network access when used.

The GitLab parser bundles KaTeX 0.18.1 (CSS, JavaScript, and fonts) and Mermaid
11.16.1. settings_default.json loads those local files before
js/gitlab_config.js; the default GitLab assets do not use their former CDNs.

Local CSS files are embedded in generated HTML. Local JavaScript files use
absolute file:// script URLs so large bundles stay out of the HTML and MathJax
4 can detect its resource root. Remote URLs are requested by the browser.
Custom templates, JavaScript, and external parser commands are trusted
configuration and may execute code or read local files.

Online and external parsers
---------------------------

The github and gitlab parsers upload the Markdown being converted to the
corresponding Markdown API. Optional github_oauth_token and
gitlab_personal_token values must be kept only in the user's settings file.

External parsers are configured in markdown_binary_map. Each value is an array
whose first item is the absolute executable path and whose remaining items are
arguments. Markdown is sent through standard input and the parser must return
an HTML body fragment through standard output. No command shell is used.

YAML front matter and untrusted files
-------------------------------------

When strip_yaml_front_matter is true, a leading YAML block can set title and
other HTML metadata, base paths, references, a save destination, and nested
per-document settings. This is disabled by default. Review front matter before
enabling it for untrusted documents because overrides can select assets and
output paths. Generated HTML may also contain raw HTML from the source.

Privacy
-------

The offline markdown parser does not upload document text. The default page
uses bundled MathJax but may contact GitHub for emoji images. Rare MathJax
font ranges, optional packages, or accessibility data may also need network
access unless installed locally. The github and gitlab parsers send the
converted Markdown to those services.

More information
----------------

README.md contains JSON examples for custom CSS, MathJax versions, external
parsers, extensions, and YAML front matter. README_CN.md provides the same
documentation in Simplified Chinese. LICENSE contains only this project's MIT
license. THIRD_PARTY_NOTICES.md lists upstream works, bundled dependencies,
asset origins, and their separate license files.

This plugin is a CudaText port and adaptation of MarkdownPreview 2.8.2 and
also references Alexey Torgashin's original CudaText Markdown Preview plugin.
Development of the adaptation was assisted by generative AI.

The Markdown Advanced Preview project code is released under the MIT License.
Copyright (c) 2026 He Zihao covers the CudaText port and original additions or
modifications, not pre-existing upstream material. Upstream and dependency
notices listed in THIRD_PARTY_NOTICES.md must remain with redistributed copies.
