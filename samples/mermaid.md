# Mermaid local rendering test

This document uses the local Python-Markdown parser and the bundled Mermaid
11.16.1 assets. Select the `markdown` parser when previewing it.

## Flowchart

```mermaid
flowchart LR
    A[Open Markdown] --> B{Parser}
    B -->|markdown| C[Python-Markdown]
    C --> D[Mermaid fenced block]
    D --> E[Local Mermaid rendering]
```

## Sequence diagram

```mermaid
sequenceDiagram
    participant U as User
    participant C as CudaText
    participant P as Preview plugin
    participant M as Mermaid
    U->>C: Open mermaid.md
    C->>P: Preview with markdown parser
    P->>M: Load local mermaid.min.js
    M-->>U: Render SVG diagrams
```
