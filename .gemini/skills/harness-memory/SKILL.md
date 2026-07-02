---
name: harness-memory
description: "HarnessDB — Memoria persistente del proyecto. Consulta decisiones, lecciones, recursos y actividad. Trigger keywords: memoria, decisión, lección, contexto, historial, harness, db, decisiones, búsqueda."
---

# HarnessDB — Memoria Persistente del Proyecto

Cuando este skill es cargado:

1. **Session summary** — Ejecutar para obtener el brief de sesión:
   ```bash
   python3 .harness/scripts/harness-session.py
   ```

2. **Consultas** — Usar para buscar información específica:
   ```bash
   # Decisiones
   python3 .harness/scripts/harness-query.py --decisions [--domain X] [--agent X]
   
   # Lecciones aprendidas
   python3 .harness/scripts/harness-query.py --lessons [--category X] [--severity X]
   
   # Recursos K8s
   python3 .harness/scripts/harness-query.py --resources [--kind X]
   
   # Actividad de agentes
   python3 .harness/scripts/harness-query.py --activity [--agent X] [--last N]
   
   # Búsqueda full-text
   python3 .harness/scripts/harness-query.py --search "término"
   ```

3. **Escritura** — Registrar nueva información:
   ```bash
   python3 .harness/scripts/harness-write.py decision --agent X --domain X --title X --context X --decision X
   python3 .harness/scripts/harness-write.py lesson --agent X --category X --title X --description X
   python3 .harness/scripts/harness-write.py resource --kind X --name X --manifest-path X
   python3 .harness/scripts/harness-write.py activity --agent X --action X --target X --summary X
   python3 .harness/scripts/harness-write.py snapshot --trigger X --description X
   python3 .harness/scripts/harness-write.py update-status --kind X --name X --validation-status X
   ```

4. **Inicialización** (solo la primera vez):
   ```bash
   python3 .harness/scripts/harness-init.py
   ```

La DB es un archivo SQLite en `.harness/harness.db`. El schema versionado está en `.harness/schema.sql`.

Para más detalles, leer los artifacts del skill en Gemini:
- `.gemini/skills/infrastructure-agent/artifacts/agent_protocol.md` (ejemplo de integración)
- `.harness/schema.sql` (schema completo)