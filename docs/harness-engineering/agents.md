# Anatomía de los Agentes

## Visión General

El sistema Harness Engineering del proyecto está compuesto por 6 agentes especializados, cada uno con un contexto acotado y un protocolo de comunicación claro. Estos agentes están implementados para dos plataformas:

El estándar universal del proyecto centraliza todos los agentes en el directorio nativo `.gemini/skills/`, utilizando el formato `SKILL.md` con frontmatter YAML. Ambas plataformas (Opencode y Gemini/Antigravity) leen desde esta única fuente de la verdad.

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

Todos los agentes están consolidados en el directorio unificado `.gemini/skills/`.

```
.
├── opencode.json                         ← configuración que apunta a .gemini/skills/
├── AGENTS.md                             ← orquestador (instrucciones del sistema)
└── .gemini/skills/
    ├── infrastructure-agent/SKILL.md     ← conocimiento, convención y protocolo unificado
    ├── application-agent/SKILL.md
    ├── cicd-agent/SKILL.md
    ├── validation-agent/SKILL.md
    ├── documentation-agent/SKILL.md
    ├── evolution-agent/SKILL.md
    ├── cka-mentor/SKILL.md
    └── harness-memory/SKILL.md
```

---

## Instrucciones de Operación

### Inspección de la Configuración Interna

```bash
# Ver el orquestador (instrucciones del sistema)
cat AGENTS.md

# Ver la configuración raíz
cat opencode.json

# Ver el conocimiento de dominio unificado de un agente
cat .gemini/skills/application-agent/SKILL.md
```

### Modificación y Evolución de un Agente

Para alterar o mejorar el comportamiento de un agente, debes ajustar sus archivos de definición:

1. **Si quieres modificar el conocimiento o el comportamiento**: Edita su archivo `SKILL.md` unificado en `.gemini/skills/`.

!!! warning "Restricción de Contexto"
    Nunca le agregues instrucciones de código Python al `infra_skill.md`, ni comandos de Kubernetes al `app_skill.md`. Mantener las responsabilidades estrictamente separadas es la clave de Harness Engineering.

---

### Agente 6: CKA Mentor

#### Definición y Rol
Tutor teórico de Kubernetes orientado al examen **CKA**. Responde consultas conceptuales puras ("qué es un PV", "diferencia entre DaemonSet y Deployment"), clasificando cada respuesta por dominio del examen y citando siempre `kubernetes.io` como fuente de verdad.

#### Contexto y Archivos Asignados
- **Dominio**: Los 5 dominios del examen CKA (Cluster Architecture, Workloads, Services, Storage, Troubleshooting).
- **Conocimiento Base**: `.gemini/skills/cka-mentor/SKILL.md`
- **Protocolo**: `.gemini/skills/cka-mentor/SKILL.md`

#### Activación
- **Trigger**: "Explicame", "qué es", "cómo funciona", "diferencia entre", "dominio CKA".
- **Modo**: On-demand (solo cuando el usuario hace consultas teóricas).
- **Restricción**: NO genera manifiestos del proyecto. Para eso están los agentes de desarrollo.

---

### CKA Layer (Transversal)

#### Definición y Rol
No es un agente, sino una **capa de explicación automática** integrada en el Infrastructure Agent y el Validation Agent. Después de cada entrega de YAML o cada diagnóstico, estos agentes incluyen un bloque `CKA LEARNING` con el dominio del examen, concepto clave, explicación didáctica y referencia oficial.

#### Filosofía V3: "Build Fast, Learn Deep"

El arnés (harness) está diseñado bajo la filosofía **AI Pair Programming**. 
En versiones anteriores, el sistema actuaba como un tutor restrictivo (*Gatekeeping*), reteniendo respuestas para forzar al usuario a pensar. 

En la versión actual (v3), el sistema prioriza la **velocidad de desarrollo empírico**:
1. **Código Primero:** El agente entrega el manifiesto o código funcional, optimizado y listo para aplicar de forma inmediata.
2. **Validación Obligatoria:** Ningún código se da por finalizado ni se envía al repositorio (`git push`) sin haber sido validado en runtime (ej. probar el autoscalado con carga, matar un pod para probar resiliencia).
3. **Explicación Después (CKA Layer):** Inmediatamente después del código y la prueba, el agente anexa un bloque `CKA LEARNING` explicando qué hace el recurso, cómo se relaciona con el examen CKA y compartiendo tips oficiales.
4. **Documentación Automática:** Todo concepto nuevo aprendido se registra en el cheat-sheet automáticamente.

Esta separación ("la máquina escribe y prueba, el humano absorbe el concepto") aumenta radicalmente el *Time-to-Value* sin sacrificar el objetivo de certificación ni la calidad del código.

---

## Arquitectura Unificada

### Única Fuente de Verdad (Single Source of Truth)

Anteriormente se mantenía una dualidad de archivos entre `.gemini/skills` y `.opencode/skills`. Esta arquitectura fue modernizada: ahora **TODOS** los agentes viven de forma consolidada en la carpeta nativa `.gemini/skills/`, utilizando el formato estándar y universal `SKILL.md`.

- **Cero duplicación**: Las configuraciones duales fueron eliminadas.
- **Simetría perfecta**: Si agregas, modificas o borras un agente en `.gemini/skills/`, el cambio impacta automáticamente en ambas plataformas.

### CodeGraph — Carga y Mantenimiento del Contexto

Al iniciar cada sesión, el Orquestador ejecuta:

```bash
python3 .harness/scripts/codegraph-summary.py
```

Esto consulta `.codegraph/codegraph.db` (SQLite) y devuelve la estructura indexada del proyecto (archivos, nodos, relaciones). Reemplaza la exploración manual de directorios, ahorrando tokens.

**Sincronización Automática:**
Se ha instruido al Orquestador para que, si durante su trabajo realiza cambios estructurales (crea, borra o renombra archivos), ejecute automáticamente `npx @colbymchenry/codegraph sync`. Esto asegura que el mapa de código se mantenga vivo y nunca pierda coherencia con los archivos reales del proyecto.

### Flujo de Trabajo en opencode

```
1. Usuario hace un pedido
2. Orquestador ejecuta codegraph-summary.py → contexto del proyecto
3. Determina el dominio (infra/app/cicd/validation/docs)
4. Carga skill correspondiente con tool skill(name="<dominio>")
5. El skill indica qué archivos .gemini/skills/<agente>/SKILL.md leer
6. Lee esos archivos (contenido vivo, siempre actualizado)
7. Delega a task(subagent_type="general") con rol + skill content + pedido
8. Sub-agente devuelve propuesta
9. Orquestador consolida y presenta el resultado
```

### Mantenimiento

| Escenario | Acción |
|---|---|
| Se crea, edita o elimina un skill | Hacerlo directamente en la carpeta nativa `.gemini/skills/` (impacta globalmente) |
| Se crean o borran archivos en el proyecto | El Orquestador ejecuta `npx @colbymchenry/codegraph sync` automáticamente |
