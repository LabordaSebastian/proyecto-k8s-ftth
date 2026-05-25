# Anatomía de los Agentes

## Visión General

Esta página desglosa la definición interna, rol, contexto asignado y protocolos de activación de cada uno de los agentes que componen la arquitectura de Harness Engineering del proyecto. Cada agente tiene un diseño interno (`metadata.json`, `agent_protocol.md` y `knowledge_base.md`) que asegura su bounded context.

| Recurso | Nombre | Propósito |
|---|---|---|
| `Agente` | `Orquestador` | Coordina a los subagentes (Punto de entrada). |
| `Agente` | `Infrastructure` | Especialista en recursos declarativos K8s. |
| `Agente` | `Application` | Especialista en código fuente (Python, Nginx). |
| `Agente` | `CI/CD` | Especialista en automatización y scripts de ciclo de vida. |
| `Agente` | `Validation` | Tester en runtime contra el clúster vivo. |
| `Agente` | `Documentation` | Hook de actualización de documentación MkDocs. |

!!! info "Implementación dual"
    Cada agente está implementado para dos plataformas: **Gemini** (Antygravity) via `.gemini/skills/` y **opencode** via `.opencode/skills/`. Los skills de opencode son "thin" — su contenido instruye leer los archivos fuente de `.gemini/skills/`, garantizando que el conocimiento de dominio sea siempre el mismo sin importar la plataforma.

---

## Desglose Técnico

### Agente 0: Orquestador

#### Definición y Rol
Es el **Router + Coordinador**. Es el único agente que interactúa directamente con el usuario. No ejecuta tareas técnicas complejas por sí mismo, sino que interpreta la intención, la descompone y delega a los subagentes especializados. Consolida las respuestas antes de mostrarlas.

#### Contexto y Archivos Asignados
- **Dominio**: Repositorio completo (visión de alto nivel estructural).
- **Archivos clave**: `README.md`, `mkdocs.yml`, y el mapa del repo `.codegraph.db`.
- **opencode (Orquestador)**: `AGENTS.md` (instrucciones del sistema) + `opencode.json` (config raíz)

#### Activación
- **Trigger**: Siempre activo al recibir un mensaje del usuario.
- **Modo**: Coordina en paralelo a los agentes técnicos y de forma secuencial al Documentation Agent.

#### ¿Por qué el Orquestador no programa?
Si el Orquestador escribe código directamente, se contamina su contexto y corre el riesgo de romper patrones arquitectónicos. Su trabajo es entender el requerimiento general y usar las "APIs" (protocolos) de los subagentes.

---

### Agente 1: Infrastructure Agent

#### Definición y Rol
Especialista en **manifiestos de Kubernetes**. Valida la coherencia de los archivos YAML, propone nuevos recursos declarativos y asegura que la topología del clúster mantenga las convenciones de etiquetas y puertos del proyecto.

#### Contexto y Archivos Asignados
- **Dominio**: `k8s/` y la configuración de Kind (`kind-config.yaml`).
- **Conocimiento Base**: `.gemini/skills/infrastructure-agent/artifacts/infra_skill.md`
- **Protocolo**: `.gemini/skills/infrastructure-agent/artifacts/agent_protocol.md`
- **opencode Skill**: `.opencode/skills/infrastructure/SKILL.md` (thin → lee los archivos de `.gemini/skills/infrastructure-agent/artifacts/`)

#### Activación
- **Trigger**: "Necesito un nuevo microservicio", "Faltan limits de CPU", "Exponer un puerto".
- **Modo**: Paralelo (modo lectura y propuesta, no aplica cambios directamente).

---

### Agente 2: Application Agent

#### Definición y Rol
Especialista en **código fuente**. Conoce profundamente la lógica del Backend (Flask), la configuración del Frontend (Nginx), dependencias de Python y Dockerfiles. Valida contratos de API y maneja variables de entorno a nivel código.

#### Contexto y Archivos Asignados
- **Dominio**: `src/`
- **Conocimiento Base**: `.gemini/skills/application-agent/artifacts/app_skill.md`
- **Protocolo**: `.gemini/skills/application-agent/artifacts/agent_protocol.md`
- **opencode Skill**: `.opencode/skills/application/SKILL.md` (thin → lee los archivos de `.gemini/skills/application-agent/artifacts/`)

#### Activación
- **Trigger**: "Agregar endpoint `/health`", "Actualizar la librería de Redis", "Mejorar las capas del Dockerfile".
- **Modo**: Paralelo (modo lectura y propuesta).

---

### Agente 3: CI/CD Agent

#### Definición y Rol
Especialista en **automatización**. Garantiza que cualquier cambio en código o manifiestos tenga su correspondencia en los flujos de integración y despliegue continuo. Conoce la sintaxis de GitHub Actions y Bash.

#### Contexto y Archivos Asignados
- **Dominio**: `.github/workflows/` y el script de bootstrap `manage-env.sh`.
- **Conocimiento Base**: `.gemini/skills/cicd-agent/artifacts/cicd_skill.md`
- **Protocolo**: `.gemini/skills/cicd-agent/artifacts/agent_protocol.md`
- **opencode Skill**: `.opencode/skills/cicd/SKILL.md` (thin → lee los archivos de `.gemini/skills/cicd-agent/artifacts/`)

#### Activación
- **Trigger**: "El pipeline de build falla", "Agregar el microservicio nuevo a manage-env.sh".
- **Modo**: Paralelo (modo lectura y propuesta).

---

### Agente 4: Validation Agent

#### Definición y Rol
Verificador en **runtime**. Es el único agente diseñado para ejecutar comandos reales contra el clúster vivo, validando que el estado actual coincida con el declarado. 

#### Contexto y Archivos Asignados
- **Dominio**: Comandos `kubectl` y `curl` contra `ftth-cluster`.
- **Protocolo**: `.gemini/skills/validation-agent/artifacts/agent_protocol.md`
- **opencode Skill**: `.opencode/skills/validation/SKILL.md` (thin → lee el protocolo de `.gemini/skills/validation-agent/artifacts/`)
- **⚠️ opencode Permission**: `"bash": "ask"` en `opencode.json` — requiere aprobación del usuario para ejecutar comandos en el clúster

#### Activación
- **Trigger**: Post-deploy. Se invoca para verificar health checks (`CrashLoopBackOff`), endpoints respondiendo HTTP 200, y resiliencia de pods.
- **Modo**: Secuencial. Actúa después de que los cambios de infraestructura fueron aplicados. **Requiere permisos explícitos de ejecución.**

---

### Agente 5: Documentation Agent

#### Definición y Rol
El **guardián del conocimiento**. Actúa como un *hook* (evento disparador) automático. Traduce el output técnico de los demás agentes en documentación MkDocs, manteniéndola siempre viva y fiel al código.

#### Contexto y Archivos Asignados
- **Dominio**: `docs/` y navegación `mkdocs.yml`.
- **Conocimiento Base**: `.gemini/skills/documentation-agent/artifacts/doc_skill.md`
- **Protocolo**: `.gemini/skills/documentation-agent/artifacts/agent_protocol.md`
- **Guía de Estilo**: `.gemini/skills/k8s-ftth-docs-style/artifacts/documentation_style_skill.md`
- **opencode Skill**: `.opencode/skills/documentation/SKILL.md` (thin → lee protocolo + guía de estilo de `.gemini/skills/`)

#### Activación
- **Trigger**: Finalización exitosa de cualquier workflow que modifique el repositorio.
- **Modo**: Secuencial (obligatorio, siempre al final).

---

## Instrucciones de Operación

### Inspección de la Configuración Interna

Cada agente es una entidad modular en el sistema de archivos de configuración. Su implementación difiere según la plataforma:

**Gemini (Antygravity)** — archivos en `.gemini/`:
```bash
# Ver metadatos del Application Agent
cat .gemini/skills/application-agent/metadata.json

# Ver metadatos del Validation Agent
cat .gemini/skills/validation-agent/metadata.json
```

**opencode** — archivos en `.opencode/`:
```bash
# Ver el skill de infraestructura (thin → apunta a .gemini/)
cat .opencode/skills/infrastructure/SKILL.md

# Ver el orquestador (instrucciones del sistema)
cat AGENTS.md

# Ver la configuración raíz de opencode
cat opencode.json
```

### Modificación y Evolución de un Agente

Para alterar o mejorar el comportamiento de un agente, no necesitas "reprogramarlo" con código, ya que operan basados en prompts estructurales. Debes ajustar sus archivos de definición:

1. **Si quieres que aprenda una nueva convención técnica** (ej. cómo escribir un StatefulSet): Edita su archivo `[agente]_skill.md`.
2. **Si quieres que se active bajo nuevas condiciones** (ej. que responda a comandos de Terraform): Edita su archivo `agent_protocol.md`.

!!! warning "Restricción de Contexto"
    Nunca le agregues instrucciones de código Python al `infra_skill.md`, ni comandos de Kubernetes al `app_skill.md`. Mantener las responsabilidades estrictamente separadas es la clave de Harness Engineering.

---

## Implementación en opencode

### Visión General

Los mismos agentes de Harness Engineering están configurados para **opencode**, permitiendo trabajar con el mismo paradigma cuando se usa opencode como alternativa a Antygravity. La arquitectura es idéntica: el Orquestador recibe el pedido, determina el dominio, carga el skill, delega a un sub-agente vía `task()`, y consolida el resultado.

| Componente | En Gemini (Antygravity) | En opencode |
|---|---|---|
| **Orquestador** | `AGENTS.md` + sistema de prompts de Gemini | `AGENTS.md` (instrucciones del sistema) + `opencode.json` |
| **Infrastructure Agent** | `.gemini/skills/infrastructure-agent/` | `.opencode/skills/infrastructure/SKILL.md` (thin) |
| **Application Agent** | `.gemini/skills/application-agent/` | `.opencode/skills/application/SKILL.md` (thin) |
| **CI/CD Agent** | `.gemini/skills/cicd-agent/` | `.opencode/skills/cicd/SKILL.md` (thin) |
| **Validation Agent** | `.gemini/skills/validation-agent/` | `.opencode/skills/validation/SKILL.md` (thin) |
| **Documentation Agent** | `.gemini/skills/documentation-agent/` | `.opencode/skills/documentation/SKILL.md` (thin) |

### Skills Thin — Sincronización Automática

Los skills de opencode son **thin**: su contenido no duplica el conocimiento de dominio, sino que instruyen al Orquestador leer los archivos fuente de `.gemini/skills/`. Esto garantiza:

- **Actualización automática**: si se edita un skill en Gemini, opencode toma la nueva versión en la próxima carga
- **Cero duplicación**: el conocimiento de dominio vive una sola vez en `.gemini/skills/`
- **Independencia de plataforma**: Antygravity y opencode comparten la misma fuente de verdad

```
.gemini/skills/infrastructure-agent/artifacts/infra_skill.md  ← fuente de verdad
.opencode/skills/infrastructure/SKILL.md                       ← thin: "leé el archivo de arriba"
```

### CodeGraph — Carga de Contexto del Proyecto

Al iniciar cada sesión, el Orquestador ejecuta:

```bash
python3 .opencode/scripts/codegraph-summary.py
```

Esto consulta `.codegraph/codegraph.db` (SQLite) y devuelve la estructura indexada del proyecto (archivos, nodos, relaciones). Reemplaza la exploración manual de directorios, ahorrando tokens.

### Archivos de Configuración

| Archivo | Propósito |
|---|---|
| `opencode.json` | Config raíz: activa `AGENTS.md`, registra skills, permisos (`bash: ask`) |
| `AGENTS.md` | Define el Orquestador: reglas, ruteo por dominio, workflow de delegación |
| `.opencode/scripts/codegraph-summary.py` | Script que consulta `.codegraph/codegraph.db` |
| `.opencode/skills/<dominio>/SKILL.md` | Skills thin que referencian `.gemini/skills/<agente>/artifacts/` |

### Flujo de Trabajo en opencode

```
1. Usuario hace un pedido
2. Orquestador ejecuta codegraph-summary.py → contexto del proyecto
3. Determina el dominio (infra/app/cicd/validation/docs)
4. Carga skill correspondiente con tool skill(name="<dominio>")
5. El skill indica qué archivos .gemini/skills/<agente>/artifacts/ leer
6. Lee esos archivos (contenido vivo, siempre actualizado)
7. Delega a task(subagent_type="general") con rol + skill content + pedido
8. Sub-agente devuelve propuesta
9. Orquestador consolida y presenta el resultado
```

### Mantenimiento

| Escenario | Acción |
|---|---|
| Se actualiza un skill en Gemini | No requiere acción — opencode lee la nueva versión automáticamente |
| Se agrega un nuevo agente en Gemini | Crear `.opencode/skills/<nuevo>/SKILL.md` apuntando a sus archivos |
| Se elimina un agente en Gemini | Eliminar su skill de `.opencode/skills/` |
| Se modifica el CodeGraph DB | El script `codegraph-summary.py` lo consulta tal cual está |
