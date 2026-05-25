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
- **Conocimiento Base**: `.gemini/skills/infrastructure-agent/artifacts/infra_skill.md`
- **Protocolo**: `.gemini/skills/infrastructure-agent/artifacts/agent_protocol.md`

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

#### Activación
- **Trigger**: Finalización exitosa de cualquier workflow que modifique el repositorio.
- **Modo**: Secuencial (obligatorio, siempre al final).

---

## Instrucciones de Operación

### Inspección de la Configuración Interna

Cada agente es una entidad modular en el sistema de archivos de configuración (`.gemini/`). Para ver exactamente cómo están definidos sus metadatos (triggers, dependencias de archivos, rol):

```bash
# Ver metadatos del Application Agent
cat .gemini/skills/application-agent/metadata.json

# Ver metadatos del Validation Agent
cat .gemini/skills/validation-agent/metadata.json
```

### Modificación y Evolución de un Agente

Para alterar o mejorar el comportamiento de un agente, no necesitas "reprogramarlo" con código, ya que operan basados en prompts estructurales. Debes ajustar sus archivos de definición:

1. **Si quieres que aprenda una nueva convención técnica** (ej. cómo escribir un StatefulSet): Edita su archivo `[agente]_skill.md`.
2. **Si quieres que se active bajo nuevas condiciones** (ej. que responda a comandos de Terraform): Edita su archivo `agent_protocol.md`.

!!! warning "Restricción de Contexto"
    Nunca le agregues instrucciones de código Python al `infra_skill.md`, ni comandos de Kubernetes al `app_skill.md`. Mantener las responsabilidades estrictamente separadas es la clave de Harness Engineering.
