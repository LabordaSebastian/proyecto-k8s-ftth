# 🚀 Plataforma de Aprovisionamiento FTTH - Kubernetes PoC

![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=for-the-badge&logo=kubernetes&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white)

Este repositorio contiene una **Prueba de Concepto (PoC)** integral diseñada para orquestar y monitorear servicios de un proveedor de internet (ISP/FTTH) utilizando **Kubernetes**. 

El proyecto fue construido con un enfoque en las mejores prácticas de DevOps y la eficiencia de recursos, sirviendo como laboratorio práctico para los dominios de la certificación **Certified Kubernetes Administrator (CKA)**.

---

## 🏗️ Arquitectura de Microservicios

La plataforma está dividida en componentes ligeros (imágenes Alpine) para optimizar el consumo de hardware, demostrando que es posible operar una arquitectura compleja en entornos de recursos limitados (ej. < 3GB de RAM).

1. **🌐 Frontend (Web UI):** Deployment de Nginx. Sirve un dashboard moderno de monitoreo inyectado dinámicamente sin necesidad de reconstruir la imagen.
2. **⚙️ Backend (API Python):** Microservicio desarrollado en Flask que actúa como puente de comunicación para consultar el estado de la red.
3. **🗄️ Base de Datos (Caché):** Pod de Redis para el almacenamiento del estado simulado de los nodos de fibra óptica.
4. **🕵️ Agente de Monitoreo:** CronJob basado en `busybox` que automatiza pruebas de latencia y disponibilidad de la red a intervalos regulares.

---

## 🧠 Conceptos de Kubernetes Aplicados

Este proyecto no es solo un despliegue de contenedores, sino una demostración práctica de la administración avanzada de Kubernetes:

### 1. Workloads & Scheduling Avanzado
* **Deployments y Réplicas:** Garantizan la alta disponibilidad y la capacidad de auto-reparación (*Self-Healing*) del Frontend y Backend.
* **Node Affinity y Node Selectors:** Reglas estrictas (`requiredDuringSchedulingIgnoredDuringExecution`) para forzar que el motor de base de datos (Redis) se programe únicamente en nodos etiquetados con `role=database` o `disktype=ssd`.
* **Taints y Tolerations:** Comprensión de las restricciones del `control-plane` (`NoSchedule`) y cómo el planificador (Scheduler) asigna las cargas al nodo worker de forma segura.
* **CronJobs y Jobs:** Automatización de tareas efímeras de diagnóstico de red usando la sintaxis CRON estándar.

### 2. Networking y Resolución de Servicios
* **ClusterIP:** Exposición interna segura de la API y la Base de Datos, aislando componentes críticos de la red pública.
* **Resolución DNS Interna:** Los microservicios se comunican dinámicamente mediante los nombres DNS de Kubernetes (ej. `http://ftth-backend-service:5000`), evitando el uso de IPs efímeras.
* **NodePort:** Exposición de la interfaz gráfica web hacia el host local a través de un mapeo estático (puerto `30080`).

### 3. Configuración y Almacenamiento
* **ConfigMaps:** Desacoplamiento total del código y la configuración. El HTML y CSS del panel de control se inyectan como un volumen directamente en la ruta `/usr/share/nginx/html` de los Pods de Nginx.
* **Variables de Entorno (ENVs):** Inyección de parámetros de conexión de bases de datos desde manifiestos declarativos hacia las aplicaciones Python.

### 4. Gestión Eficiente de Recursos
* **Resource Requests & Limits:** Definición estricta de límites de CPU (ej. `50m`) y Memoria (ej. `128Mi`) a nivel de contenedor para proteger el clúster (prevención de OOMKilled) y asegurar una distribución equitativa de los recursos.

### 5. Integración y Despliegue Continuo (CI/CD)
* **GitHub Actions:** Preparación de un workflow `.github/workflows/ci-cd.yml` automatizado.
* Diseño de pipeline de dos fases: Integración Continua (construcción de imágenes Docker en la nube) y Despliegue Continuo mediante un **Self-Hosted Runner** local.

---

## 📂 Estructura del Repositorio

La infraestructura como código (IaC) está organizada de manera profesional para separar contextos y facilitar el mantenimiento:

```text
proyecto-k8s-ftth/
├── .github/
│   └── workflows/
│       └── ci-cd.yml          # Pipeline de GitHub Actions
├── src/
│   ├── frontend/              # Código e interfaces de usuario
│   └── backend/               # Código fuente de la API (Python/Flask)
└── k8s/                       # Manifiestos de Kubernetes
    ├── 01-namespaces-rbac/    # Espacios de nombres y control de acceso
    ├── 02-storage/            # Volúmenes y ConfigMaps (ej. Dashboard HTML)
    ├── 03-deployments/        # Nginx, Python API, Redis y CronJob
    ├── 04-security/           # Network Policies y Security Contexts
    └── 05-services/           # ClusterIPs y NodePorts
