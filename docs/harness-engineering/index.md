# Harness Engineering — Arquitectura de Agentes Especializados

## Visión General

Harness Engineering es un principio de diseño aplicado a sistemas de Inteligencia Artificial donde cada agente tiene un **contexto acotado**, una **responsabilidad única**, un **contrato claro** (input/output) y produce **fallas observables**. En el proyecto FTTH-K8s, esto resuelve el problema de contexto excesivo y consumo de tokens al dividir la asistencia en agentes especialistas.

| Recurso | Nombre | Propósito |
|---|---|---|
| `Agente` | `Orquestador` | Router de intenciones. Delega tareas a los subagentes y consolida resultados. |
| `Agente` | `Infrastructure Agent` | Especialista en manifiestos declarativos (`k8s/`) y topología del clúster. |
| `Agente` | `Application Agent` | Especialista en código fuente (`src/`, Flask, Nginx) y dependencias. |
| `Agente` | `CI/CD Agent` | Especialista en pipelines (`.github/workflows/`) y script `manage-env.sh`. |
| `Agente` | `Validation Agent` | Verificador de estado post-deploy en el clúster Kind (requiere permisos). |
| `Agente` | `Documentation Agent`| Post-processing hook secuencial que mantiene `docs/` siempre actualizada. |

```mermaid
graph TD
    User["Usuario / Dev"] -->|Requerimiento| O["Orquestador (Router)"]
    
    subgraph Fase de Trabajo Paralela
        O -->|k8s/| IA["Infrastructure Agent"]
        O -->|src/| AA["Application Agent"]
        O -->|.github/| CA["CI/CD Agent"]
        O -->|Runtime| VA["Validation Agent"]
        
        IA -.->|Propuestas| O
        AA -.->|Propuestas| O
        CA -.->|Propuestas| O
        VA -.->|Validación| O
    end
    
    O -->|Workflow completado| DA["Documentation Agent"]
    DA -->|Actualiza| Docs["docs/"]
```

---

## Desglose Técnico

### Los Principios Aplicados — Estructura en `.gemini/skills/`

La arquitectura está completamente formalizada en la carpeta de skills. Cada agente tiene su propio `metadata.json` y `agent_protocol.md`, y los agentes técnicos cuentan con su propia `*_skill.md` (knowledge base).

#### ¿Por qué dividir el contexto (Contexto Acotado)?
Un agente no necesita leer todo el código fuente de Flask si solo va a modificar un manifiesto YAML de Kubernetes. Dividir el contexto reduce el consumo de tokens y minimiza las alucinaciones de la IA.

#### ¿Por qué usar un Orquestador (Responsabilidad Única)?
Evita que el usuario tenga que decidir qué agente usar en cada paso. El Orquestador funciona como una API unificada que descompone tareas complejas (ej. "Agregar un nuevo microservicio") en tareas que pueden ejecutarse en paralelo por los subagentes.

#### ¿Por qué el Documentation Agent es un paso secuencial obligatorio?
A diferencia de los agentes técnicos que corren en paralelo proponiendo soluciones, la documentación es una consecuencia de esas soluciones. El Documentation Agent actúa como un *hook* final, garantizando que el conocimiento del proyecto (`docs/`) nunca quede desactualizado respecto al código.

!!! info "Fase actual de implementación"
    El proyecto ya ha inicializado formalmente a los agentes y separado sus dominios en `.gemini/skills/` para Gemini (Antygravity) y `.opencode/skills/` para opencode. Los skills de opencode son "thin" y referencian el contenido de `.gemini/skills/` como fuente de verdad única. Esto provee una base firme, reglas claras y sincronización automática entre plataformas para que la IA colabore sin romper el estilo del código o de la infraestructura.

---

## Instrucciones de Operación

### Aplicar el flujo de agentes (Ejemplo Práctico)

1. **El Usuario solicita un cambio complejo**: "Agregar un endpoint `/metrics` al backend".
2. **El Orquestador descompone la tarea**:
    - Invoca al **Application Agent** para proponer el código Flask.
    - Invoca al **Infrastructure Agent** para validar el Service.
    - Invoca al **CI/CD Agent** para verificar el pipeline.
3. **Ejecución**: Los agentes responden, el Orquestador presenta los cambios combinados.
4. **Validación**: Una vez aplicados, el **Validation Agent** revisa los logs y el nuevo endpoint en el clúster.
5. **Documentación**: El **Documentation Agent** se activa automáticamente y añade la documentación técnica del cambio.

### Verificar el estado

Para inspeccionar la configuración y los contratos de cada agente, se pueden consultar sus protocolos individuales:

**Gemini (Antygravity):**
```bash
# Ver el protocolo de operación del Infrastructure Agent
cat .gemini/skills/infrastructure-agent/artifacts/agent_protocol.md

# Ver la knowledge base del Application Agent
cat .gemini/skills/application-agent/artifacts/app_skill.md
```

**opencode:**
```bash
# Ver el skill de infraestructura (thin que referencias a .gemini/)
cat .opencode/skills/infrastructure/SKILL.md

# Ver las instrucciones del orquestador
cat AGENTS.md
```

### Debugging

!!! warning "Fallas de Contexto"
    Si la IA provee una respuesta genérica sobre Kubernetes en lugar de usar los patrones del proyecto, significa que el Orquestador falló en invocar el subagente correcto (ej. el Infrastructure Agent y su archivo `infra_skill.md`). Simplemente indícale a la IA que actúe bajo el dominio de dicho agente.
