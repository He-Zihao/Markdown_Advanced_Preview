# CudaText Markdown Advanced Preview

[English](README.md) | 简体中文

Markdown Advanced Preview 可以在 CudaText 内将 Markdown 转换为带样式的
HTML 文档。它能够打开自动更新的浏览器预览、导出到 CudaText HTML 标签页、
保存 HTML 文件，或者将 HTML 复制到剪贴板。

离线解析器、样式和 Python 依赖均已包含在插件中。MathJax 默认启用并从公共
CDN 加载，因此公式排版默认需要网络；也可以自行配置本地资源。

## 安装

使用 **插件 > 插件管理器 > 从 ZIP 文件安装**（英文界面为 **Plugins >
Addons Manager > Install from ZIP file**）安装发布包。如果菜单没有立即出现，
请重启 CudaText。ZIP 根目录必须直接包含 `install.inf`。

## 命令与基本用法

打开 Markdown 文档，然后选择 **插件 > Markdown Advanced Preview**。也可以按
`Ctrl+Shift+P` 打开 CudaText 命令面板，输入具体命令名称或
`Markdown Advanced Preview`，再从候选结果中执行：

- **Preview**：使用当前解析器渲染并在浏览器中打开。
- **Preview - select parser...**：先选择一个已启用的解析器。
- **Export HTML to CudaText tab...**：新建一个 HTML 标签页。
- **Save as HTML...**：将渲染结果保存为文件。
- **Copy HTML to clipboard...**：将渲染结果复制到剪贴板。
- **Open Markdown cheatsheet**：打开语法与渲染示例。
- **Settings...**：创建或打开用户配置文件。
- **Toggle automatic reload**：启用或禁用自动重建预览。

编辑器中存在非空选区时，只渲染选区；否则渲染整个文档。浏览器预览打开后，
插件会在编辑或保存后重新生成 HTML。浏览器仅在内容真正变化后刷新，并默认
恢复原来的滚动位置。

## 配置文件

选择 **Settings...** 可编辑 CudaText 配置目录中的
`cuda_markdown_advanced_preview.json`。首次使用时，插件会根据
`settings_default.json` 创建它。

与 Sublime Text 的 `.sublime-settings` 文件不同，这里使用严格 JSON：

- 不允许注释；
- 不允许尾随逗号；
- 本地路径应写成 `C:/Users/name/mathjax-config.js` 这样的普通字符串，
  不使用 `file:///` URL；
- `css` 和 `js` 是按解析器分别保存数组的对象，不是全局数组。

用户值会覆盖内置默认值。嵌套对象递归合并，但数组会整体替换默认数组。因此，
修改 `markdown_extensions` 这类长数组时，应先复制完整的默认值。

### 设置项参考

| 设置项 | 取值与用途 |
| --- | --- |
| `browser` | `default`，或者浏览器可执行文件的绝对路径 |
| `parser` | `markdown`、`github`、`gitlab`，或 `markdown_binary_map` 中的名称 |
| `enabled_parsers` | 解析器选择菜单中显示的解析器 |
| `theme` | `auto`、`light` 或 `dark` |
| `enable_autoreload` | 编辑后重建已经打开的浏览器预览 |
| `live_reload_interval_ms` | 浏览器检查变化的间隔，最小 500 毫秒 |
| `preserve_scroll` | 刷新后恢复浏览器滚动位置 |
| `enable_mathjax` | 启用 Arithmatex 输出和默认 MathJax 资源 |
| `pygments_style` | 内置 Pygments 样式，或 `github`、`github2014`、`github_dynamic` |
| `pygments_inject_css` | 在完整 HTML 文档中嵌入代码高亮 CSS |
| `pygments_css_class` | 生成高亮 CSS 时使用的外层类名 |
| `css` / `js` | 按解析器设置的 `default`、URL、本地文件或插件资源数组 |
| `allow_css_overrides` | 加载 Markdown 文件旁边的同名 `.css` 文件 |
| `html_template` | 包含 `{{ HEAD }}`、`{{ BODY }}` 和可选 `{{ THEME }}` 的模板 |
| `image_path_conversion` | `absolute`、`relative`、`base64` 或 `none` |
| `file_path_conversions` | `absolute`、`relative` 或 `none` |
| `strip_yaml_front_matter` | 读取 YAML 元数据和文档级设置覆盖 |
| `strip_critic_marks` | `accept`、`reject` 或 `none` |
| `path_tempfile` | 预览目录的绝对路径，或相对于源文件的路径 |
| `include_head` | 哪些输出目标应获得完整 HTML 文档 |

`include_head` 接受 `browser`、`editor`、`clipboard` 和 `save`。未列出的目标
只会得到 HTML 正文片段。

高级设置项：

| 设置项 | 用途 |
| --- | --- |
| `markdown_extensions` | 完整的 Python-Markdown 扩展列表及扩展参数 |
| `markdown_binary_map` | 外部解析器名称及其可执行文件/参数数组 |
| `github_mode` | GitHub API 模式，通常为 `markdown` 或 `gfm` |
| `gitlab_mode` | 是否使用 GitLab GFM 行为 |
| `github_inject_header_ids` | 将 GitHub 生成的锚点 ID 注入标题元素 |
| `github_oauth_token` | 可选 GitHub API 令牌；只能放在用户配置中 |
| `gitlab_personal_token` | 可选 GitLab API 令牌；只能放在用户配置中 |
| `gitlab_highlight_theme` | GitLab 代码高亮块使用的主题类名 |
| `html_simple` | 返回简化 HTML，并省略完整文档外壳 |

## Markdown 扩展

默认离线解析器由 Python-Markdown 和 PyMdown Extensions 组合而成。默认启用
脚注、属性列表、定义列表、表格、缩写、HTML 内 Markdown、元数据、规范列表、
SmartyPants、WikiLinks、Admonition、Details、强调改进、公式、SuperFences、
自动链接、任务列表、删除线和 GitHub Emoji。

`markdown_extensions` 中的对象以扩展模块名为键，以扩展参数为值。内置默认
配置中的特殊 `!!python/name` 对象用于解析命名函数；它不是 PyYAML 标签直接
写入 JSON 的通常形式，只应指向可信的内置模块。

### 扩展兼容性

替代型扩展不能与被替代的扩展同时启用：

- `pymdownx.superfences` 替代 `markdown.extensions.fenced_code`；
- `pymdownx.betterem` 替代旧的 `markdown.extensions.smartstrong`；
- `pymdownx.extra` 替代 `markdown.extensions.extra`，而且自身已经包含多项扩展。

内置配置没有使用 `extra`，而是逐项列出所需组件，以便明确控制行为并避免重复。
当前随包版本由 SuperFences 自行调用 Pygments 高亮；再加入
`markdown.extensions.codehilite` 或另一套高亮链路，可能产生重叠结果。如果
决定以 `fenced_code` 替换 SuperFences，应同时配置 `codehilite`，并重新测试
整个扩展列表。

修改默认列表前，建议阅读
[PyMdown 兼容性说明](https://facelessuser.github.io/pymdown-extensions/usage_notes/)。

### 常用语法

任务列表：

```markdown
- [x] 已完成
- [ ] 待处理
```

Admonition 的正文需要缩进：

```markdown
!!! warning "警告"
    正文需要缩进四个空格。
```

Admonition 的 HTML 效果很好，但不属于标准 Markdown，Pandoc 等解析器未必
支持。如果强调可移植性，可以改用包含 Emoji 和粗体标题的引用块。

默认 `pymdownx.tilde` 配置支持 `~~删除线~~`。下标语法已特意禁用，因为它的
可移植性较差，而且包含空格时的处理容易产生意外结果。

### 代码围栏与 SuperFences

普通代码围栏可以直接使用：

````markdown
```python
print("hello")
```
````

需要行号和行高亮时，随包扩展版本要求使用花括号形式的语言类：

````markdown
```{.python linenums="1" hl_lines="1 3"}
print("第一行")
print("第二行")
print("第三行")
```
````

常见的 ```` ```python { ... } ```` 写法不被当前随包 PyMdown 版本接受。这种
花括号头部也可能无法被编辑器语法高亮器或其他 Markdown 处理器正确识别。

默认配置会识别 `mermaid`、`flow` 和 `sequence` 自定义围栏，并添加相应 HTML
类名，但“识别”本身不会绘制图表。还需要通过 `js` 加载兼容的浏览器端绘图
引擎和初始化脚本。不同 Mermaid 版本的初始化 API 有差异，因此离线解析器
没有默认启用一个不锁定版本的 Mermaid 配置。

### Arithmatex

`pymdownx.arithmatex` 负责在 MathJax 或其他浏览器公式引擎运行前识别公式。
默认使用 `generic: true`，把行内公式统一输出为 `\(...\)`，把行间公式统一
输出为 `\[...\]`。这更适合可配置的 MathJax 3/4 及其他客户端公式引擎。

### Emoji

默认的 `:warning:` 风格 Emoji 配置使用 GitHub 的 Emoji 索引和图片服务器，
生成小尺寸 PNG，并通过明确的宽高避免图片过大；浏览器仍然需要联网。修改
`pymdownx.emoji` 时需要确认生成器与资源来源相匹配，因为 sprite、PNG 和 SVG
生成器所需的参数并不相同。

## MathJax

默认配置依次加载：

1. `res://MarkdownAdvancedPreview/js/mathjax4_config.js`；
2. jsDelivr 上的 MathJax 4.1.1 `tex-mml-chtml.js`。

支持行内 `$...$` 与 `\(...\)`、行间 `$$...$$` 与 `\[...\]`，并支持
`equation`、`align`、`gather` 等环境的 AMS 风格编号。预加载配置会将
`tex.tags` 设置为 `ams`。

### MathJax 3 和 4

MathJax 3/4 会在引擎启动时读取 `window.MathJax`，因此配置脚本必须排在引擎
URL 前面。例如：

```json
{
  "js": {
    "markdown": [
      "res://MarkdownAdvancedPreview/js/mathjax4_config.js",
      "https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js"
    ]
  }
}
```

公式编号最重要的配置是：

```javascript
window.MathJax = {
  tex: { tags: "ams" },
  options: { enableMenu: true }
};
```

如果希望公式输出更接近可选择的 HTML 文本，建议使用
`tex-mml-chtml.js` 这样的 CHTML 组件。SVG 组件的文字选择和字体缓存行为不同。
详见 MathJax 官方的
[加载说明](https://docs.mathjax.org/en/latest/web/loading.html)。

### MathJax 2

内置旧版配置文件会调用 `MathJax.Hub.Config`，因此这里需要先加载 MathJax 2
引擎，再加载配置文件：

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

### 本地 MathJax 与 KaTeX

完全离线使用时，可以自行下载 MathJax，再把 CDN URL 替换为本地绝对路径。
CudaText 配置使用 `C:/path/to/file.js`，不是 Sublime 使用的
`file:///C:/path/to/file.js`。

离线 `markdown` 解析器没有 `enable_katex` 设置。可以通过自定义 `css` 和
`js` 数组使用 KaTeX，但必须同时配置样式表、引擎，以及能够处理 Arithmatex
输出的初始化脚本。GitLab 解析器另有用于 GitLab API 输出的内置 KaTeX 与
Mermaid 资源。

将 `enable_mathjax` 设为 `false` 可移除默认的 Arithmatex 自动启用行为和
MathJax 资源；用户在 `js` 中明确加入的自定义资源仍由用户自行管理。

## CSS、JavaScript 与模板

`default` 会展开为当前解析器的内置资源。其他项目可以是 HTTPS URL、本地绝对
路径，或 `res://MarkdownAdvancedPreview/css/markdown.css` 这样的插件资源。

```json
{
  "theme": "dark",
  "css": {
    "markdown": ["default", "C:/Users/name/markdown-override.css"]
  },
  "html_template": "C:/Users/name/markdown-template.html"
}
```

本地 CSS 和 JavaScript 会嵌入生成的 HTML；远程 URL 保持外链，由浏览器请求。
`allow_css_overrides` 为 `true` 时，还会追加源文件旁边的同名 CSS，例如
`notes.md` 对应 `notes.css`。

按名称生成的 Pygments 样式是静态样式。内置 `github_dynamic` 通过媒体查询
跟随系统深浅色偏好。其他第三方 Pygments 样式若需要动态切换，应自行编写 CSS。

## 在线与外部解析器

`github` 和 `gitlab` 解析器会把选区或文档文本发送到对应的 Markdown API。
可选令牌只能写在用户配置文件中：

```json
{
  "github_oauth_token": "",
  "gitlab_personal_token": ""
}
```

不要把真实令牌放入 `settings_default.json` 或共享的 Markdown 文档。

外部解析器从标准输入读取 Markdown，并将 HTML 正文片段写到标准输出：

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

数组第一项必须是确实存在的可执行文件，其余项目作为参数直接传入，不经过命令
Shell。使用解析器专属语法时，仍需要设置对应的 Pandoc 输入扩展或过滤器。

## YAML Front Matter

`strip_yaml_front_matter` 为 `true` 时，文档开头的 YAML 块可以设置 `title`、
`author` 等 HTML 元数据，以及 `basepath`、`references`、`destination` 或嵌套
的 `settings`：

```yaml
---
title: 示例
author: Ada
settings:
  theme: dark
---
```

此功能默认关闭。文档级设置可以选择本地/远程资源和输出路径，因此处理不可信
Markdown 时，应先审查 Front Matter 再启用。

## 网络与安全说明

- 离线 `markdown` 解析器不会上传文档文本；默认浏览器页面会从 jsDelivr 请求
  MathJax，并可能从 GitHub 请求 Emoji 图片。
- `github` 与 `gitlab` 解析器会把待转换的 Markdown 上传到对应服务，其 API
  政策和限制同样适用。
- 自定义 JavaScript、模板、外部解析器命令和 YAML 设置覆盖均属于可信配置，
  可能执行代码或读取文件。
- 生成的 HTML 可以包含 Markdown 文档中的原始 HTML。打开不可信文档时，应当
  像对待不可信网页一样谨慎。

## 来源与许可证

本插件是
[MarkdownPreview 2.8.2](https://github.com/facelessuser/MarkdownPreview)
面向 CudaText 的移植与改编，也参考了 Alexey Torgashin 制作的原 CudaText
Markdown Preview 插件。CudaText 适配开发过程中使用了生成式 AI 辅助。

Markdown Advanced Preview 项目代码遵循
[MIT License](LICENSE)。版权声明 `Copyright (c) 2026 He Zihao` 适用于
CudaText 移植、重写的适配层、文档，以及其他由你新增或修改的原创内容；它不
替代上游版权，也不表示你独占上游已有材料的版权。

MarkdownPreview 与原 CudaText Markdown Preview 继续保留各自的版权和 MIT
通知，随包库和资源也继续适用各自的许可证。所有这些通知均由
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) 索引，重新分发本插件时
必须一并保留。
