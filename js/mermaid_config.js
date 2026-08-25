// Mermaid 11 configuration for Markdown fenced blocks.
// This file must be loaded after mermaid.min.js.
(function () {
  "use strict";

  function renderMermaid() {
    if (typeof mermaid === "undefined") {
      return;
    }

    // PyMdown SuperFences emits <pre class="mermaid"><code>...</code></pre>,
    // while Mermaid expects the diagram definition to be the direct text of
    // the .mermaid element. Remove the syntax-highlighting wrapper first so
    // Mermaid never tries to parse the <code> markup as diagram syntax.
    var nodes = document.querySelectorAll("pre.mermaid");
    nodes.forEach(function (node) {
      if (node.children.length === 1 && node.children[0].tagName === "CODE") {
        node.textContent = node.children[0].textContent.trim();
      }
    });

    mermaid.initialize({
      startOnLoad: false,
      securityLevel: "strict"
    });
    mermaid.run({ nodes: nodes });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderMermaid, { once: true });
  } else {
    renderMermaid();
  }
}());
