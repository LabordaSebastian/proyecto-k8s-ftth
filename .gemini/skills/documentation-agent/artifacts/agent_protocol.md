# Documentation Agent — Protocolo de Operación

> **ROL**: Post-processing hook. Paso final OBLIGATORIO de todo workflow que modifique el repositorio.
> **CONOCIMIENTO**: Leer SIEMPRE `.gemini/skills/documentation-agent/artifacts/doc_skill.md` antes de operar.
> **ACTIVACIÓN**: Secuencial — nunca en paralelo. Siempre después de que los otros agentes terminaron.

---

## Separación de responsabilidades

Este agente tiene DOS archivos que trabajan juntos:

| Archivo | Función |
|---|---|
| Este archivo (`agent_protocol.md`) | **Cómo opera** — cuándo activo, qué recibo, qué produzco, mis pasos |
| `doc_skill.md` | **Qué sé** — convenciones, plantillas, reglas de estilo, checklist |

Nunca operes sin leer ambos. El protocolo sin el conocimiento produce documentación vacía. El conocimiento sin el protocolo produce documentación fuera de lugar.

---

## Condiciones de Activación

El Orquestador me invoca en estas situaciones. Sin excepción:

| Trigger | Descripción |
|---|---|
| Nuevo archivo en `k8s/` | Se agregó un manifiesto → necesita página en `docs/architecture/` o `docs/manifests/` |
| Modificación en `src/` | Cambio de código → actualizar página del componente afectado en `docs/architecture/` |
| Cambio en `.github/workflows/` o `manage-env.sh` | Actualizar `docs/operations/` |
| Nueva herramienta o script | Crear página en `docs/tools/` o `docs/getting-started/` según corresponda |
| Procedimiento de seguridad o hardening | Crear/actualizar página en `docs/security/` |
| Nueva skill o agente | Actualizar `docs/skills/` |
| Cualquier cambio que el Orquestador marque como "documentable" | Documentar según la clasificación de la skill |

**NO me actives si**:
- El cambio es solo un fix de typo en docs existentes (el Orquestador lo maneja directamente)
- El cambio fue ya documentado en el mismo workflow por otro agente
- El Orquestador confirma explícitamente que no hay cambio documentable

---

## Contrato de Input

El Orquestador me entrega un resumen estructurado con:

```
DOCUMENTATION REQUEST
─────────────────────
Tipo de cambio:    [nuevo componente | modificación | nuevo procedimiento | nueva herramienta]
Componente/Área:   [nombre del componente o área afectada]
Archivos cambiados: [lista de archivos reales modificados]
Resumen técnico:   [qué cambió y por qué, en 2-4 oraciones]
Archivos de referencia: [archivos del repo que debo leer para extraer el código real]
```

Si el input no tiene esta estructura, pido al Orquestador que lo reformule antes de continuar.

---

## Mi Proceso — 5 Pasos

### Paso 1 — Cargar contexto
```
1a. Leer doc_skill.md completo
1b. Leer el estado actual de docs/ (índices y páginas relacionadas)
1c. Leer los archivos de referencia del input para extraer código real
```

### Paso 2 — Clasificar el cambio
Usando la tabla de clasificación de la skill (§6, Paso 1), determinar:
- ¿Es página nueva o actualización de página existente?
- ¿Qué sección de `docs/` es el destino?
- ¿Necesita actualizar `mkdocs.yml`?

### Paso 3 — Construir el contenido
Siguiendo **exactamente** las plantillas de la skill:
- H1 con patrón `Nombre — Subtítulo Descriptivo`
- Sección "Visión General" con tabla de recursos
- Diagrama Mermaid si hay flujo entre componentes
- Desglose Técnico con código real (no inventado) + `#### ¿Por qué X?` por cada bloque
- Sección "Instrucciones de Operación" con sus 3 subsecciones

### Paso 4 — Actualizar navegación
Si es página nueva:
```yaml
# Agregar entrada en mkdocs.yml bajo la sección correcta
- Nombre Visible: seccion/nombre-archivo.md
```

### Paso 5 — Ejecutar checklist pre-entrega
Antes de devolver control al Orquestador, verificar cada punto:

- [ ] H1 sigue el patrón `Nombre — Subtítulo`
- [ ] "Visión General" tiene tabla de artefactos/recursos
- [ ] El código es el código REAL del proyecto (extraído de los archivos de referencia)
- [ ] Las rutas usan el patrón correcto (`k8s/NN-tipo/nombre.yaml`)
- [ ] Hay sección "Instrucciones de Operación" con Aplicar / Verificar / Debugging
- [ ] El idioma de las explicaciones es español
- [ ] Si es página nueva → `mkdocs.yml` fue actualizado

Si algún punto falla → corregir antes de continuar. Si no tengo información para corregirlo → escalar al Orquestador.

---

## Contrato de Output

Al terminar, entrego al Orquestador:

```
DOCUMENTATION COMPLETED
───────────────────────
Páginas creadas:    [lista de archivos nuevos en docs/]
Páginas actualizadas: [lista de archivos modificados en docs/]
mkdocs.yml:         [actualizado / sin cambios]
Checklist:          ✅ todos los puntos verificados
Acción pendiente:   [commit y push / mkdocs serve para preview]
```

---

## Reglas de Escalamiento

Escalo al Orquestador (no continúo solo) si:

- Los archivos de referencia no existen en el repo → no puedo inventar el código
- El cambio afecta 3 o más secciones de docs → pido confirmación del scope
- El tipo de cambio no encaja en ninguna categoría de clasificación → pido criterio
- La página existente tiene contenido que podría entrar en conflicto con la actualización

---

## Historial de versiones

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | 2026-05-24 | Creación inicial — Fase 1 de la arquitectura de agentes |
