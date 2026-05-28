---
name: evolution-agent
description: "Evolution Agent — Meta-agente encargado de auditar y actualizar los conocimientos de los demás agentes basándose en la base de datos de HarnessDB. Trigger keywords: evaluar skills, actualizar agentes, evolución, auditoría."
---

# Evolution Agent

Este skill es un espejo "thin" de la configuración principal del agente en Gemini.
Si se necesita modificar el comportamiento de este agente, editar los siguientes archivos:

- `.gemini/skills/evolution-agent/metadata.json`
- `.gemini/skills/evolution-agent/artifacts/agent_protocol.md`
- `.gemini/skills/evolution-agent/artifacts/evolution_skill.md`

## Comandos Útiles para el Agente

Este agente se basa intensamente en consultar HarnessDB:

```bash
# Leer lecciones
python3 .harness/scripts/harness-query.py --lessons

# Leer decisiones
python3 .harness/scripts/harness-query.py --decisions
```
