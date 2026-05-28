# Evolution Skill — Guía de Meta-Ingeniería

Este documento contiene los lineamientos que el **Evolution Agent** debe seguir al auditar y modificar los skills de otros agentes.

## La Filosofía "Evolution Layer"

El objetivo del sistema no es ser perfecto desde el día 1, sino **nunca cometer el mismo error dos veces**. 

Las "Lecciones Aprendidas" (`lessons_learned` en HarnessDB) son el motor de esta evolución. Cuando un humano u otro agente registra que algo falló (ej: "olvidamos actualizar el VPA al cambiar los requests"), tu trabajo como Evolution Agent es modificar el `_skill.md` del agente correspondiente para incluir una regla que evite ese fallo en el futuro (ej: "Checklist pre-entrega: ¿Si modificaste requests/limits, actualizaste el VPA?").

## Mapeo de Dominios a Skills

Cuando audites HarnessDB, usa este mapa para saber qué skill actualizar:

| Dominio / Categoría de la Lección | Agente a evolucionar | Archivo a modificar |
|---|---|---|
| networking, storage, scheduling, cluster | Infrastructure Agent | `infra_skill.md` |
| architecture, API, frontend | Application Agent | `app_skill.md` |
| automation, ci-cd | CI/CD Agent | `cicd_skill.md` |
| testing, validation, health-check | Validation Agent | `validation_protocol.md` |
| documentation, style, conventions | Documentation Agent | `doc_skill.md` |
| tip, cka-theory | CKA Mentor | `cka_skill.md` |

## Patrones de Modificación Segura

Cuando el usuario apruebe tu propuesta de evolución y vayas a modificar un `_skill.md`, sigue estas reglas:

1. **No reescribas el documento entero:** Usa tu herramienta `multi_replace_file_content` para apuntar a las secciones exactas.
2. **Usa Checklists:** La mejor forma de incorporar una nueva regla o "gotcha" es agregándola a la sección de "Checklist pre-entrega" del protocolo del agente, o a la sección de "Reglas" de su skill.
3. **Mantén el tono:** Los skills están escritos de forma imperativa (ej: "Usa X", "No hagas Y"). Mantén ese estilo directo.
4. **Referencia la DB:** Cuando agregues una nueva regla basada en una lección, es buena práctica hacer referencia a ella (ej: "Regla: Siempre usa imagePullPolicy: Never (ver lección #2)").

## Formato del Reporte de Auditoría (Uso Interno)

Al terminar de cruzar datos entre la DB y los skills, puedes armar un "mapa de discrepancias" mental o temporal:

- **Decisión Activa X:** ¿Está en el skill? Sí/No. Si No -> Proponer agregarlo.
- **Lección Aprendida Y:** ¿Hay una regla en el skill que lo prevenga? Sí/No. Si No -> Proponer regla/checklist.
