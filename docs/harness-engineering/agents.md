# Anatomía de los Agentes

## Visión General

El sistema Harness Engineering del proyecto está compuesto por 6 agentes especializados, cada uno con un contexto acotado y un protocolo de comunicación claro. Estos agentes están implementados para dos plataformas:

| Plataforma | Configuración | Formato |
|---|---|---|
| **Antygravity** (Gemini) | `.gemini/skills/` | `metadata.json` + `agent_protocol.md` + `*_skill.md` |
| **opencode** | `.opencode/skills/` + `AGENTS.md` + `opencode.json` | `SKILL.md` (thin → referencia a `.gemini/skills/`) |

Independientemente de la plataforma, los agentes son los mismos, tienen el mismo rol y siguen el mismo flujo de trabajo.

---

## Desglose Técnico

### Agente 0: Orquestador

#### Definición y Rol
Es el **Router + Coordinador**. Es el único agente que interactúa directamente con el usuario. No ejecuta tareas técnicas complejas por sí mismo, sino que interpreta la intención, la descompone y delega a los subagentes especializados. Consolida las respuestas antes de mostrarlas.

#### Contexto y Archivos Asignados
- **Dominio**: Repositorio completo (visión de alto nivel estructural).
- **Archivos clave**: `README.md`, `mkdocs.yml`, y el mapa del repo `.codegraph.db`.

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

#### Activación
- **Trigger**: "Necesito un nuevo microservicio", "Faltan limits de CPU", "Exponer un puerto".
- **Modo**: Paralelo (modo lectura y propuesta, no aplica cambios directamente).

---

### Agente 2: Application Agent

#### Definición y Rol
Especialista en **código fuente**. Conoce profundamente la lógica del Backend (Flask), la configuración del Frontend (Nginx), dependencias de Python y Dockerfiles. Valida contratos de API y maneja variables de entorno a nivel código.

#### Contexto y Archivos Asignados
- **Dominio**: `src/`

#### Activación
- **Trigger**: "Agregar endpoint `/health`", "Actualizar la librería de Redis", "Mejorar las capas del Dockerfile".
- **Modo**: Paralelo (modo lectura y propuesta).

---

### Agente 3: CI/CD Agent

#### Definición y Rol
Especialista en **automatización**. Garantiza que cualquier cambio en código o manifiestos tenga su correspondencia en los flujos de integración y despliegue continuo. Conoce la sintaxis de GitHub Actions y Bash.

#### Contexto y Archivos Asignados
- **Dominio**: `.github/workflows/` y el script de bootstrap `manage-env.sh`.

#### Activación
- **Trigger**: "El pipeline de build falla", "Agregar el microservicio nuevo a manage-env.sh".
- **Modo**: Paralelo (modo lectura y propuesta).

---

### Agente 4: Validation Agent

#### Definición y Rol
Verificador en **runtime**. Es el único agente diseñado para ejecutar comandos reales contra el clúster vivo, validando que el estado actual coincida con el declarado. 

#### Contexto y Archivos Asignados
- **Dominio**: Comandos `kubectl` y `curl` contra `ftth-cluster`.

#### Activación
- **Trigger**: Post-deploy. Se invoca para verificar health checks (`CrashLoopBackOff`), endpoints respondiendo HTTP 200, y resiliencia de pods.
- **Modo**: Secuencial. Actúa después de que los cambios de infraestructura fueron aplicados. **Requiere permisos explícitos de ejecución.**

---

### Agente 5: Documentation Agent

#### Definición y Rol
El **guardián del conocimiento**. Actúa como un *hook* (evento disparador) automático. Traduce el output técnico de los demás agentes en documentación MkDocs, manteniéndola siempre viva y fiel al código.

#### Contexto y Archivos Asignados
- **Dominio**: `docs/` y navegación `mkdocs.yml`.

#### Activación
- **Trigger**: Finalización exitosa de cualquier workflow que modifique el repositorio.
- **Modo**: Secuencial (obligatorio, siempre al final).

---

## Estructura de Archivos

Cada plataforma organiza los archivos de configuración de los agentes de forma distinta, pero el contenido del conocimiento de dominio es el mismo.

### Gemini (Antygravity)

```
.gemini/skills/
├── orquestador/                          ← (implícito en el sistema de prompts de Gemini)
├── infrastructure-agent/
│   ├── metadata.json                     ← metadatos del agente
│   └── artifacts/
│       ├── agent_protocol.md             ← protocolo de operación
│       └── infra_skill.md               ← conocimiento de dominio K8s
├── application-agent/
│   ├── metadata.json
│   └── artifacts/
│       ├── agent_protocol.md
│       └── app_skill.md                 ← conocimiento de dominio Flask/Nginx
├── cicd-agent/
│   ├── metadata.json
│   └── artifacts/
│       ├── agent_protocol.md
│       └── cicd_skill.md               ← conocimiento de dominio CI/CD
├── validation-agent/
│   ├── metadata.json
│   └── artifacts/
│       └── agent_protocol.md
    └── artifacts/
        ├── agent_protocol.md
        └── doc_skill.md
└── cka-mentor/                           ← tutor teórico CKA
    ├── metadata.json
    └── artifacts/
        ├── agent_protocol.md
        └── cka_skill.md                  ← 5 dominios del examen CKA
```

### opencode

```
.
├── opencode.json                         ← configuración raíz
├── AGENTS.md                             ← orquestador (instrucciones del sistema)
└── .opencode/
    ├── scripts/
    │   └── codegraph-summary.py          ← consulta .codegraph/codegraph.db
    └── skills/
        ├── project-context/SKILL.md      ← carga estructura del proyecto desde CodeGraph
        ├── infrastructure/SKILL.md       ← thin → .gemini/skills/infrastructure-agent/
        ├── application/SKILL.md          ← thin → .gemini/skills/application-agent/
        ├── cicd/SKILL.md                 ← thin → .gemini/skills/cicd-agent/
        ├── validation/SKILL.md           ← thin → .gemini/skills/validation-agent/
        └── documentation/SKILL.md        ← thin → .gemini/skills/documentation-agent/ + k8s-ftth-docs-style/
```

---

## Instrucciones de Operación

### Inspección de la Configuración Interna

**Gemini (Antygravity):**
```bash
# Ver metadatos del Application Agent
cat .gemini/skills/application-agent/metadata.json

# Ver conocimiento de dominio del Infrastructure Agent
cat .gemini/skills/infrastructure-agent/artifacts/infra_skill.md
```

**opencode:**
```bash
# Ver el orquestador (instrucciones del sistema)
cat AGENTS.md

# Ver la configuración raíz
cat opencode.json

# Ver un skill thin (ej: infrastructure)
cat .opencode/skills/infrastructure/SKILL.md
```

### Modificación y Evolución de un Agente

Para alterar o mejorar el comportamiento de un agente, debes ajustar sus archivos de definición:

1. **Si quieres que aprenda una nueva convención técnica** (ej. cómo escribir un StatefulSet): Edita su archivo `*_skill.md` (Gemini) → opencode lo toma automáticamente.
2. **Si quieres que se active bajo nuevas condiciones** (ej. que responda a comandos de Terraform): Edita su archivo `agent_protocol.md`.

!!! warning "Restricción de Contexto"
    Nunca le agregues instrucciones de código Python al `infra_skill.md`, ni comandos de Kubernetes al `app_skill.md`. Mantener las responsabilidades estrictamente separadas es la clave de Harness Engineering.

---

### Agente 6: CKA Mentor

#### Definición y Rol
Tutor teórico de Kubernetes orientado al examen **CKA**. Responde consultas conceptuales puras ("qué es un PV", "diferencia entre DaemonSet y Deployment"), clasificando cada respuesta por dominio del examen y citando siempre `kubernetes.io` como fuente de verdad.

#### Contexto y Archivos Asignados
- **Dominio**: Los 5 dominios del examen CKA (Cluster Architecture, Workloads, Services, Storage, Troubleshooting).
- **Conocimiento Base**: `.gemini/skills/cka-mentor/artifacts/cka_skill.md`
- **Protocolo**: `.gemini/skills/cka-mentor/artifacts/agent_protocol.md`

#### Activación
- **Trigger**: "Explicame", "qué es", "cómo funciona", "diferencia entre", "dominio CKA".
- **Modo**: On-demand (solo cuando el usuario hace consultas teóricas).
- **Restricción**: NO genera manifiestos del proyecto. Para eso están los agentes de desarrollo.

---

### CKA Layer (Transversal)

#### Definición y Rol
No es un agente, sino una **capa de explicación automática** integrada en el Infrastructure Agent y el Validation Agent. Después de cada entrega de YAML o cada diagnóstico, estos agentes incluyen un bloque `CKA LEARNING` con el dominio del examen, concepto clave, explicación didáctica y referencia oficial.

#### Filosofía: "Build Fast, Learn Deep"
La IA entrega el código funcional primero (sin gatekeeping) y explica después. El aprendizaje CKA ocurre como consecuencia natural del desarrollo real, no como una actividad separada.

---

## Implementación en opencode

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
| Se elimina un agente en Gemini | Eliminar su skill correspondiente en `.opencode/skills/` |
| Se modifica el CodeGraph DB | El script `codegraph-summary.py` lo consulta tal cual está |
