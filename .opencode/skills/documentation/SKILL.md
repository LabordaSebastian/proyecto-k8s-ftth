---
name: documentation
description: "Use for MkDocs documentation tasks: creating new doc pages, updating existing pages, writing architecture docs, operation guides, getting-started guides, manifest documentation, updating mkdocs.yml navigation, mermaid diagrams, documentation style and conventions. Trigger keywords: document, documentation, docs, mkdocs, readme, architecture, guide, manual, mermaid, diagram, navigation, mkdocs.yml."
---

# Documentation Agent — Conocimiento de Documentación MkDocs

Carga el conocimiento de dominio leyendo los archivos fuente de Gemini:

```bash
# Lee el protocolo de operación del agente de documentación
read .gemini/skills/documentation-agent/artifacts/agent_protocol.md

# Lee la guía de estilo de documentación
read .gemini/skills/k8s-ftth-docs-style/artifacts/documentation_style_skill.md
```

El contenido de esos archivos es la fuente de verdad actualizada. Esto incluye:

- **Protocolo**: cuándo activarse, contrato input/output, proceso de 5 pasos
- **Estilo**: convenciones MkDocs, plantillas, reglas de formato, checklist pre-entrega
- **Navegación**: cómo actualizar `mkdocs.yml` para nuevas páginas
- **Diagramas**: uso de Mermaid para flujos entre componentes
- **Separación**: `agent_protocol.md` define el proceso, `documentation_style_skill.md` define el estilo
