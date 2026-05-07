# Proyecto K8s FTTH - Laboratorio de Prácticas

¡Bienvenido a la documentación oficial de mi Prueba de Concepto (PoC) sobre Kubernetes!

## 🎯 Objetivo del Proyecto

Este repositorio no es solo una aplicación de prueba; su propósito principal es servir como un **laboratorio práctico intensivo** para mi preparación hacia la certificación **Certified Kubernetes Administrator (CKA)** de la CNCF.

A lo largo de este proyecto, mi meta es:
- **Aplicar conceptos teóricos a un entorno real:** Poner en práctica todo lo que estoy aprendiendo en el excelente curso de Udemy *"Certified Kubernetes Administrator (CKA) with Practice Tests"* dictado por **Mumshad Mannambeth (KodeKloud)**.
- **Demostrar conocimientos adquiridos:** Construir un portafolio técnico que evidencie mi capacidad para diseñar, desplegar, administrar y solucionar problemas en clústeres de Kubernetes desde cero.
- **Experimentar sin miedo:** Tener un entorno local robusto (basado en `kind`) donde pueda romper cosas, depurar errores (troubleshooting) y entender el comportamiento de los componentes internos de K8s.

## 🚀 ¿Qué es esta Prueba de Concepto (PoC)?

Para hacer el aprendizaje más entretenido y realista, diseñé el laboratorio alrededor de un caso de uso ficticio pero común en la industria de las telecomunicaciones: **Una plataforma de aprovisionamiento y monitoreo para una red de fibra óptica (FTTH - Fiber To The Home)**.

El sistema simula un entorno de microservicios con:
- Un **Frontend** (Nginx) para visualizar el estado de la red.
- Un **Backend** (API en Python/Flask) para la lógica de negocio.
- Una **Base de datos** (Redis) para mantener el estado.
- **Agentes de monitoreo** (CronJobs) que verifican la salud de la red simulada periódicamente.

## 📚 ¿Qué encontrarás en esta documentación?

A medida que avance en mi estudio y apruebe nuevas secciones del curso, iré documentando aquí las implementaciones:

- **Arquitectura y Diseño:** Cómo interactúan los microservicios.
- **Workloads y Scheduling:** Uso de Deployments, DaemonSets, Taints/Tolerations y Node Affinity.
- **Networking:** Servicios (ClusterIP, NodePort), Ingress y políticas de red.
- **Almacenamiento:** PersistentVolumes (PV) y PersistentVolumeClaims (PVC).
- **Configuraciones:** ConfigMaps y Secrets.
- **Operaciones:** Automatización del ciclo de vida del clúster y monitoreo con Metrics Server y KubeView.

---

*¡Gracias por pasarte por aquí! Si tienes sugerencias, ves algún área de mejora o simplemente quieres hablar sobre Kubernetes, no dudes en contactarme o abrir un issue en el repositorio.*
