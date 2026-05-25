---
name: cicd
description: "Use for CI/CD pipeline changes: GitHub Actions workflows, manage-env.sh script, build steps, docker build/push, kind load-image, runner configuration, version tagging, checkout, secrets, actionlint, shellcheck. Trigger keywords: cicd, ci/cd, pipeline, workflow, github actions, manage-env, build, deploy, runner, actionlint, shellcheck, version tag, docker build, kind load, secret."
---

# CI/CD Agent — Conocimiento de Automatización

Carga el conocimiento de dominio leyendo los archivos fuente de Gemini:

```bash
# Lee las convenciones de CI/CD del proyecto
read .gemini/skills/cicd-agent/artifacts/cicd_skill.md

# Lee el protocolo de operación del agente
read .gemini/skills/cicd-agent/artifacts/agent_protocol.md
```

El contenido de esos archivos es la fuente de verdad actualizada. Esto incluye:

- **Mapa de automatización**: `ci-cd.yml`, `docs.yml`, `manage-env.sh`
- **Pipeline ci-cd.yml**: trigger (push a main), steps (checkout → docker build → kind load → kubectl apply → verify)
- **Patrones**: emojis en nombres de steps, tag `:latest` en CI vs `:v1` en manage-env.sh
- **Pipeline docs.yml**: exclusivo para MkDocs gh-deploy, runner ubuntu-latest
- **manage-env.sh**: constantes, funciones de log, pasos de `cmd_up()` y `cmd_down()`
- **Template para nuevo microservicio**: steps de build + kind load + constantes
- **Diferencias CI vs local**: tag de imagen, manifiestos aplicados, gestión del runner
