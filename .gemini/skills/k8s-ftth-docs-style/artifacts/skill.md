# Skill: Documentar el Proyecto FTTH-K8s

> **USO**: Leer este archivo al inicio de cualquier tarea de documentación en el proyecto  
> `LabordaSebastian/proyecto-k8s-ftth` (`/home/ing-laborda/Project_Kubernetes`)  
> para producir documentación consistente sin inspeccionar archivos existentes.

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
└── skills/
    ├── index.md
    └── doc-style-guide.md
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
