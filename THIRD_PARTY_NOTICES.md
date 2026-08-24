# Third-party notices

Markdown Advanced Preview includes or adapts the components and assets below.
The project's MIT license does not replace their licenses.

| Component or origin | Included content | License / notice |
| --- | --- | --- |
| MarkdownPreview 2.8.2 | Rendering design, CSS, JavaScript, and adapted implementation concepts | MIT; `vendor/LICENSE.MarkdownPreview.txt` |
| CudaText Markdown Preview by Alexey Torgashin | CudaText plugin reference implementation | MIT; `vendor/LICENSE.CudaText-Markdown-Preview.txt` |
| Python-Markdown 3.8.2 | `markdown/` | BSD 3-Clause; `readme/license.Python_Markdown.txt` |
| Pygments 2.19.2 with upstream security fix `24b8aa7` backported | `pygments/` | BSD 2-Clause; `readme/license.Pygments.txt` |
| PyYAML 5.1.1 | `vendor/yaml/` | MIT; `vendor/LICENSE.PyYAML.txt` |
| PyMdown Extensions 8.1.1 | `vendor/pymdownx/` | MIT; `vendor/LICENSE.pymdown-extensions.txt` |
| importlib-metadata compatibility code | `importlib_metadata/` | Apache License 2.0; `vendor/LICENSE.importlib-metadata.txt` |
| zipp compatibility code | `zipp.py` | MIT; `vendor/LICENSE.zipp.txt` |
| GitLab styles and rendering configuration | `css/gitlab.css`, `js/gitlab_config.js` | MIT; the full GitLab B.V. notice is retained in each file |
| Font Awesome font subset from MarkdownPreview | Embedded in `css/markdown.css` | SIL Open Font License 1.1; `vendor/LICENSE.Font-Awesome.txt` |
| GitHub Octicons link-icon font | Embedded in `css/github.css` | MIT; `vendor/LICENSE.Octicons.txt` |
| MathJax 4.1.3 | `js/tex-mml-chtml.js` | Apache License 2.0; `vendor/LICENSE.MathJax.txt` |

The default Markdown parser includes MathJax locally. The GitLab parser still
references KaTeX and Mermaid from public CDNs, and emoji images may be loaded
from GitHub. Those projects and service providers apply their own licenses and
terms.

When adding or upgrading a dependency or asset, preserve its upstream notices
and update this file.
