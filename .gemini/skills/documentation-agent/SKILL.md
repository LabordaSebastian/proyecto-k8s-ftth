---
name: documentation
description: "Use for MkDocs documentation tasks: creating new doc pages, updating existing pages, writing architecture docs, operation guides, getting-started guides, manifest documentation, updating mkdocs.yml navigation, mermaid diagrams, documentation style and conventions. Trigger keywords: document, documentation, docs, mkdocs, readme, architecture, guide, manual, mermaid, diagram, navigation, mkdocs.yml."
---

# Documentation Agent — Conocimiento de Documentación MkDocs

Carga el conocimiento de dominio leyendo los archivos fuente de Gemini:

```bash
# Lee el protocolo de operación del agente de documentación

# Lee la guía de estilo de documentación
```

El contenido de esos archivos es la fuente de verdad actualizada. Esto incluye:

- **Protocolo**: cuándo activarse, contrato input/output, proceso de 5 pasos
- **Estilo**: convenciones MkDocs, plantillas, reglas de formato, checklist pre-entrega
- **Navegación**: cómo actualizar `mkdocs.yml` para nuevas páginas
- **Diagramas**: uso de Mermaid para flujos entre componentes
- **Separación**: `agent_protocol.md` define el proceso, `documentation_style_skill.md` define el estilo


## Content from agent_protocol.md

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
| Analytics / Salud del sistema | Ejecutar `harness-report.py` y actualizar `docs/harness-engineering/health-report.md` |
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

## Mi Proceso — 7 Pasos

### Paso 0 — Cargar memoria del proyecto (HarnessDB)
```bash
# Consultar decisiones relacionadas con el componente a documentar
python3 .harness/scripts/harness-query.py --decisions --domain [dominio-del-componente]

# Consultar lecciones aprendidas relacionadas
python3 .harness/scripts/harness-query.py --lessons --agent [agente-que-hizo-el-cambio]

# Buscar contexto específico
python3 .harness/scripts/harness-query.py --search "[componente]"
```
Incorporar las decisiones y lecciones relevantes en la documentación para que refleje no solo el "qué" sino el "por qué".

### Paso 1 — Cargar contexto de archivos
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

### Paso 6 — Ejecutar checklist pre-entrega
Antes de devolver control al Orquestador, verificar cada punto:

- [ ] H1 sigue el patrón `Nombre — Subtítulo`
- [ ] "Visión General" tiene tabla de artefactos/recursos
- [ ] El código es el código REAL del proyecto (extraído de los archivos de referencia)
- [ ] Las rutas usan el patrón correcto (`k8s/NN-tipo/nombre.yaml`)
- [ ] Hay sección "Instrucciones de Operación" con Aplicar / Verificar / Debugging
- [ ] El idioma de las explicaciones es español
- [ ] Si es página nueva → `mkdocs.yml` fue actualizado
- [ ] Las decisiones de HarnessDB relevantes están reflejadas en la documentación

Si algún punto falla → corregir antes de continuar. Si no tengo información para corregirlo → escalar al Orquestador.

### Paso 7 — Registrar en HarnessDB (obligatorio)

```bash
# Registrar la actividad de documentación:
python3 .harness/scripts/harness-write.py activity \
  --agent documentation \
  --action document \
  --target "[páginas creadas/actualizadas]" \
  --summary "[resumen de lo documentado]"
```

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


## Content from doc_skill.md

# Skill: Documentar el Proyecto FTTH-K8s

> **ROL**: Contexto primario de conocimiento del **Documentation Agent**.
> Contiene las convenciones, plantillas y reglas de estilo.
> El protocolo de activación y operación del agente está en:
> `.gemini/skills/documentation-agent/artifacts/agent_protocol.md`
>
> **USO DIRECTO** (sin agente): Leer este archivo al inicio de cualquier tarea
> de documentación en `LabordaSebastian/proyecto-k8s-ftth` para producir
> documentación consistente sin inspeccionar archivos existentes.

---

## 1. Contexto del Proyecto

- **Stack**: Kind + Kubernetes + Python/Flask + Redis + Nginx + BusyBox
- **Docs engine**: MkDocs Material (`mkdocs.yml` en la raíz)
- **Idioma de la documentación**: **Español** (100%). Código, comandos y nombres de recursos K8s permanecen en inglés.
- **Audiencia dual**: (1) reproducir el laboratorio, (2) estudiar para el CKA.

### Estructura de `docs/`

```
docs/
├── index.md                        ← Portada del site
├── getting-started/
│   ├── index.md                    ← Resumen de la sección
│   ├── kind-config.md
│   └── manage-env.md
├── architecture/
│   ├── index.md
│   ├── frontend.md
│   ├── backend.md
│   ├── redis.md
│   └── cronjob.md
├── manifests/
│   ├── index.md
│   ├── deployments.md
│   ├── services.md
│   ├── configmaps.md
│   └── metrics-server.md
├── operations/
│   ├── index.md
│   ├── ci-cd-pipeline.md
│   └── docs-pipeline.md
├── security/
│   ├── index.md
│   └── encryption-at-rest.md
├── harness-engineering/
│   └── index.md
├── skills/
│   ├── index.md
│   └── doc-style-guide.md
└── tools/
    ├── index.md
    └── codegraph.md
```

### Navegación en `mkdocs.yml`

Al agregar una nueva página, el patrón de entrada en `nav:` es:
```yaml
  - Nombre Visible: seccion/nombre-archivo.md
```

---

## 2. Reglas de Estilo (NO negociables)

### 2.1 Estructura de cada página

Toda página de arquitectura o componente DEBE tener estas secciones en este orden:

```
# Nombre del Componente — Subtítulo Descriptivo

## Visión General
[Párrafo de 2-4 oraciones que explica QUÉ es y PARA QUÉ sirve el componente]

| Recurso | Nombre | Propósito |
|---|---|---|
| `Kind` | `nombre-recurso` | Descripción breve |

[Diagrama Mermaid del flujo — OBLIGATORIO en páginas de arquitectura]

---

## Desglose Técnico

### [Nombre del artefacto] — `ruta/al/archivo.yaml`

[Bloque de código del artefacto completo]

#### [Subtítulo con pregunta "¿Por qué X?"]
[Explicación con enfoque CKA: el "por qué" de cada decisión]

[!!!-admonition relevante]

---
[... repetir por cada artefacto del componente ...]

## Instrucciones de Operación

### Aplicar los recursos
### Verificar el estado
### Debugging
```

### 2.2 Voz y tono

| Regla | Correcto | Incorrecto |
|---|---|---|
| Segunda persona informal | "Cuando ejecutas..." | "Cuando el usuario ejecuta..." |
| Presente indicativo | "El Service enruta el tráfico..." | "El Service enrutará el tráfico..." |
| Frases directas | "Esta es la decisión clave." | "Es importante mencionar que esta podría ser..." |
| Nombres K8s sin traducir | "`Deployment`", "`CronJob`" | "Despliegue", "TareaProgamada" |
| Énfasis con negrita | `**alta disponibilidad**` | ALTA DISPONIBILIDAD o _alta disponibilidad_ |

### 2.3 Preguntas retóricas como subtítulos

Las secciones de "por qué" usan el patrón `####`:
```
#### ¿Por qué `imagePullPolicy: Never`?
#### ¿Por qué ClusterIP y no NodePort?
#### ¿Por qué `host='0.0.0.0'` en Flask?
```

### 2.4 Tablas de comparación

Siempre que haya 3+ opciones o casos de uso, usar tabla:
```
| Tipo | Uso | Cuándo usarlo |
|---|---|---|
```

---

## 3. Componentes MkDocs Material permitidos

### Admonitions (!!!-bloques)

```markdown
!!! info "Título descriptivo"
    Información de contexto o explicación del "cómo funciona".

!!! tip "Título descriptivo"
    Buenas prácticas, optimizaciones, herramientas útiles.

!!! warning "Título descriptivo"
    Errores comunes, restricciones importantes, síntomas conocidos.
```

**Regla de uso**:
- `info`: para explicar mecanismos internos de Kubernetes (DNS, scheduling, etc.)
- `tip`: para optimizaciones, patrones de prod vs lab, herramientas externas
- `warning`: para trampas frecuentes, errores de sintaxis comunes en CKA, restricciones de Kind

### Diagramas Mermaid

```markdown
    ```mermaid
    sequenceDiagram
        participant A as NombreA
        participant B as NombreB
        A->>B: Mensaje de request
        B-->>A: Respuesta
    ```
```

- `sequenceDiagram`: para flujos de request/response entre componentes
- `graph LR`: para arquitectura de alto nivel (página index.md)
- Siempre incluir `<br/>` dentro de los labels de nodos para multilínea

### Bloques de código

```markdown
    ```bash
    # Comentario explicativo siempre antes del comando
    kubectl apply -f k8s/ruta/archivo.yaml
    ```
```

- Bash: `bash`
- YAML manifiestos: `yaml`
- Python: `python`
- Dockerfile: `dockerfile`
- Salida de comandos: ` ``` ` (sin lenguaje) o `text`
- JSON responses: `json`

---

## 4. Patrones Recurrentes de Contenido

### 4.1 Tabla de recursos de un componente

Siempre al inicio de "Visión General":
```markdown
| Recurso | Nombre | Propósito |
|---|---|---|
| `Deployment` | `ftth-COMPONENTE` | Gestiona las N réplicas del COMPONENTE |
| `Service` | `ftth-COMPONENTE-service` | Expone el puerto XXXX [alcance] |
```

### 4.2 Sección "Instrucciones de Operación" — comandos estándar

Siempre en este orden con estos subsections:

```markdown
## Instrucciones de Operación

### Aplicar los recursos

    ```bash
    kubectl apply -f k8s/XX-tipo/nombre-archivo.yaml
    ```

### Verificar el estado

    ```bash
    # Estado del Deployment o recurso principal
    kubectl get [recurso] [nombre]

    # Ver Pods y en qué nodo corren
    kubectl get pods -l app=ftth-COMPONENTE -o wide

    # Ver endpoints del Service
    kubectl get endpoints ftth-COMPONENTE-service
    ```

### Debugging

    ```bash
    # Ver logs en tiempo real
    kubectl logs -l app=ftth-COMPONENTE -f --tail=100

    # Ver eventos (para ImagePullBackOff, CrashLoopBackOff, etc.)
    kubectl describe [tipo] [nombre]
    kubectl get events --sort-by=.lastTimestamp | grep -i COMPONENTE
    ```

!!! warning "Síntoma común: [descripción del error más frecuente]"
    [Causa y cómo diagnosticarla con comandos específicos]
```

### 4.3 Explicar Resource Requests y Limits

Patrón estándar para cualquier bloque `resources:`:
```markdown
#### Resource Requests y Limits

El límite de `NNNMi` actúa como protección: si por alguna razón [el componente] tuviera un memory leak, el kernel terminaría el proceso (`OOMKilled`) antes de que afecte a otros Pods del nodo.

!!! warning "Pods sin limits son un riesgo operacional"
    Un Pod sin `limits` puede consumir todos los recursos del nodo, causando que otros Pods sean expulsados (`Evicted`) o que el nodo se vuelva inestable.
```

### 4.4 Sección `imagePullPolicy: Never` (imágenes locales Kind)

```markdown
#### `imagePullPolicy: Never` — La clave para entornos Kind

Esta directiva es crítica en este laboratorio. Por defecto, Kubernetes intenta descargar las imágenes desde un registry. La imagen `ftth-COMPONENTE:vX` es local y no existe en ningún registry público.

El flujo correcto para entornos Kind es:

    ```bash
    docker build -t ftth-COMPONENTE:v1 ./src/COMPONENTE/
    kind load docker-image ftth-COMPONENTE:v1 --name ftth-cluster
    kubectl apply -f k8s/03-deployments/COMPONENTE-deployment.yaml
    ```

!!! warning "Este patrón es exclusivo de entornos locales"
    En producción, siempre se utiliza un registry privado (ECR, GCR, GHCR) con `imagePullPolicy: IfNotPresent` o `Always`.
```

---

## 5. Convenciones de Nomenclatura

| Elemento | Patrón | Ejemplo |
|---|---|---|
| Nombres de recursos K8s | `ftth-[componente]` | `ftth-backend`, `ftth-redis` |
| Nombres de Services | `ftth-[componente]-service` | `ftth-backend-service` |
| Tags de imágenes Docker | `ftth-[componente]:v[N]` | `ftth-backend:v1` |
| Labels `app:` | `ftth-[componente]` | `app: ftth-frontend` |
| Labels `tier:` | `frontend` / `backend` / `data` / `worker` | `tier: backend` |
| Rutas a manifiestos | `k8s/NN-tipo/nombre-componente-tipo.yaml` | `k8s/03-deployments/backend-deployment.yaml` |
| Puerto Frontend (NodePort) | `30080` | — |
| Puerto KubeView (NodePort) | `30088` | — |
| Nombre del clúster Kind | `ftth-cluster` | — |

---

## 6. Proceso para Documentar un Cambio

Cuando el usuario diga "documenta X" o "agrega la doc de X", seguir este proceso:

### Paso 1 — Clasificar el cambio

| Tipo de cambio | Acción |
|---|---|
| Nuevo componente K8s (Deployment, Service, etc.) | Crear página en `docs/architecture/` + agregar entrada en `mkdocs.yml` nav |
| Cambio a manifiesto YAML existente | Actualizar la sección de código en la página de arquitectura del componente + explicar el "¿por qué?" |
| Nuevo pipeline CI/CD o automatización | Crear/actualizar página en `docs/operations/` |
| Nueva herramienta (Helm chart, script) | Crear página en `docs/getting-started/` si es prerequisito, o en `docs/architecture/` si es un componente |
| Cambio al script `manage-env.sh` | Actualizar `docs/getting-started/manage-env.md` |
| Hardening, RBAC, cifrado, auditoría, NetworkPolicy | Crear/actualizar página en `docs/security/` |
| Herramienta auxiliar de desarrollo o IA | Crear/actualizar página en `docs/tools/` |
| Metodología de IA, Agentes o Harness Engineering | Crear/actualizar página en `docs/harness-engineering/` |

### Paso 2 — Construir la página

1. Usar la plantilla de la sección correspondiente (ver §4)
2. Leer el archivo real del proyecto para extraer el código exacto (no inventarlo)
3. Para cada sección de código → incluir al menos una subsección `####` con el "¿Por qué?"
4. Revisar que haya al menos un admonition por página (info, tip o warning)
5. Si hay flujo de datos entre componentes → incluir diagrama `sequenceDiagram`

### Paso 3 — Verificar antes de entregar

- [ ] El H1 (`#`) sigue el patrón `Nombre del Componente — Subtítulo`
- [ ] La sección "Visión General" tiene tabla de recursos
- [ ] El código YAML/Python/Bash es el código real del proyecto, no inventado
- [ ] Las rutas de archivos usan el patrón correcto (`k8s/NN-tipo/...`)
- [ ] Hay sección "Instrucciones de Operación" con los 3 subsections: Aplicar / Verificar / Debugging
- [ ] El idioma es español (excepto nombres técnicos de K8s)
- [ ] Si es página nueva → `mkdocs.yml` fue actualizado en `nav:`

---

## 7. Qué NO hacer

- ❌ **No usar** `kubectl create` en ejemplos; siempre `kubectl apply`
- ❌ **No inventar** nombres de recursos; leer el YAML real del proyecto
- ❌ **No usar** inglés para las explicaciones (las explicaciones van en español)
- ❌ **No omitir** el `#### ¿Por qué...?` en bloques de manifiestos nuevos
- ❌ **No crear** páginas sin actualizar `mkdocs.yml`
- ❌ **No usar** `caution` ni `danger` admonitions (no son parte del estilo establecido)
- ❌ **No escribir** párrafos de más de 5 líneas sin un ejemplo, tabla o bloque de código
- ❌ **No romper** la convención de secciones (Visión General → Desglose Técnico → Instrucciones de Operación)

---

## 8. Ejemplo Mínimo de Página Nueva

Si hay que documentar, por ejemplo, un nuevo componente `HPA (HorizontalPodAutoscaler)`:

```markdown
# Autoescalado — HorizontalPodAutoscaler

## Visión General

El HPA es el componente responsable de escalar automáticamente el número de réplicas
de un Deployment en función de métricas de CPU o memoria. En este laboratorio,
protege al Backend de picos de carga sin intervención manual.

| Recurso | Nombre | Propósito |
|---|---|---|
| `HorizontalPodAutoscaler` | `ftth-backend-hpa` | Escala `ftth-backend` entre 2 y 5 réplicas |

[diagrama mermaid del flujo HPA → metrics-server → Deployment]

---

## Desglose Técnico

### Manifiesto — `k8s/04-autoscaling/backend-hpa.yaml`

[código yaml completo]

#### ¿Por qué `minReplicas: 2` y no `1`?
[explicación de HA]

!!! info "Requisito: Metrics Server"
    El HPA requiere que el Metrics Server esté instalado...

---

## Instrucciones de Operación

### Aplicar el recurso
[comandos]

### Verificar el estado
[comandos]

### Debugging
[comandos]
```