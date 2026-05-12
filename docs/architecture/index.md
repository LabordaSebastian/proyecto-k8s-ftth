# Arquitectura

Esta sección desglosa cada uno de los componentes de la plataforma FTTH desde la perspectiva de Kubernetes.

Para cada componente encontrarás:

- El manifiesto YAML que lo define.
- La explicación de cada campo relevante.
- Un *Deep Dive* teórico con los conceptos del CKA asociados: cómo interactúa con el Control Plane, escenarios de fallo comunes y comandos de troubleshooting.

## Componentes documentados

| Componente | Recurso K8s | Sección |
|---|---|---|
| Dashboard Web | Deployment + ConfigMap (volumen) | [Frontend (Nginx)](frontend.md) |
| API de estado de red | Deployment + Variables de entorno | [Backend (Python)](backend.md) |
| Almacenamiento de estado | Deployment + Node Affinity | [Base de Datos (Redis)](redis.md) |
| Verificación de red | CronJob + RestartPolicy | [Agente de Monitoreo](cronjob.md) |
