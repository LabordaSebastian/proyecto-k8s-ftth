-- ============================================================
-- HarnessDB Seed — Datos Iniciales del Proyecto FTTH
-- Decisiones históricas extraídas de los skills existentes
-- ============================================================

-- ─── DECISIONS ──────────────────────────────────────────────

-- D1: Tipo de clúster
INSERT INTO decisions (agent, domain, title, context, decision, alternatives, consequences, related_files, tags)
VALUES (
    'infrastructure',
    'cluster',
    'Usar Kind como clúster local de desarrollo',
    'Necesitamos un clúster Kubernetes local para desarrollo del FTTH Dashboard. Debe ser liviano, rápido de crear/destruir, y compatible con imágenes locales.',
    'Usar Kind (Kubernetes in Docker) con 2 nodos: 1 control-plane + 1 worker',
    '["minikube", "k3d", "MicroK8s", "Docker Desktop K8s"]',
    'Kind no soporta LoadBalancer nativo (necesita MetalLB). Las imágenes locales se cargan con kind load. Para exponer servicios se usa NodePort con extraPortMappings.',
    '["kind-config.yaml"]',
    '["kind", "cluster", "development", "local"]'
);

-- D2: Redis en worker node
INSERT INTO decisions (agent, domain, title, context, decision, alternatives, consequences, related_files, tags)
VALUES (
    'infrastructure',
    'scheduling',
    'Redis usa nodeAffinity al nodo worker',
    'El worker tiene labels role=database, disktype=ssd para simular un nodo optimizado para datos en un entorno de producción.',
    'Configurar requiredDuringSchedulingIgnoredDuringExecution con matchExpression role=database en el Deployment de Redis',
    '["nodeSelector simple", "tolerations + taints", "sin afinidad (scheduler libre)", "preferredDuringScheduling"]',
    'Redis SOLO puede correr en el worker. Si el worker cae, Redis no se reprograma hasta que el worker vuelva.',
    '["k8s/03-deployments/redis-deployment.yaml", "kind-config.yaml"]',
    '["redis", "scheduling", "affinity", "worker-node", "nodeAffinity"]'
);

-- D3: imagePullPolicy Never para locales
INSERT INTO decisions (agent, domain, title, context, decision, alternatives, consequences, related_files, tags)
VALUES (
    'infrastructure',
    'deployment',
    'imagePullPolicy Never para imágenes locales en Kind',
    'Las imágenes como ftth-backend:v1 se construyen localmente y se cargan con kind load docker-image. No existen en ningún registry.',
    'Usar imagePullPolicy: Never para toda imagen local. Usar IfNotPresent para imágenes públicas (nginx:alpine, redis:alpine).',
    '["Always (fallaría con ErrImagePull)", "IfNotPresent (funcionaría pero es engañoso)"]',
    'Si se cambia a Always, el kubelet intentará pull y fallará. Al hacer kind load, la imagen queda en el containerd del nodo.',
    '["k8s/03-deployments/backend-deployment.yaml"]',
    '["imagePullPolicy", "kind", "local-images", "kind-load"]'
);

-- D4: Frontend expuesto en NodePort 30080
INSERT INTO decisions (agent, domain, title, context, decision, alternatives, consequences, related_files, tags)
VALUES (
    'infrastructure',
    'networking',
    'Frontend expuesto en NodePort 30080',
    'Necesitamos acceder al FTTH Dashboard desde el navegador del host. Kind requiere extraPortMappings explícitos.',
    'Configurar el Service frontend como NodePort en puerto 30080, mapeado en kind-config.yaml con extraPortMappings.',
    '["LoadBalancer con MetalLB", "kubectl port-forward", "Ingress con nginx-ingress"]',
    'El puerto 30080 está reservado exclusivamente para el frontend. Agregar nuevos puertos requiere recrear el clúster.',
    '["k8s/05-services/frontend-service.yaml", "kind-config.yaml"]',
    '["nodeport", "frontend", "networking", "30080", "extraPortMappings"]'
);

-- D5: KubeView en NodePort 30088
INSERT INTO decisions (agent, domain, title, context, decision, alternatives, consequences, related_files, tags)
VALUES (
    'infrastructure',
    'networking',
    'KubeView expuesto en NodePort 30088',
    'KubeView proporciona visualización gráfica del clúster. Necesita acceso web desde el host.',
    'Desplegar KubeView via Helm chart con Service NodePort en puerto 30088.',
    '["Lens (herramienta desktop)", "k9s (TUI)", "kubectl proxy"]',
    'Puerto 30088 reservado para KubeView. Helm chart en deploy/helm-charts/kubeview/.',
    '["deploy/helm-charts/kubeview/values.yaml", "kind-config.yaml"]',
    '["kubeview", "visualization", "helm", "30088"]'
);

-- D6: Estructura de directorios k8s/
INSERT INTO decisions (agent, domain, title, context, decision, alternatives, consequences, related_files, tags)
VALUES (
    'infrastructure',
    'organization',
    'Estructura de directorios k8s/ con numeración por capas',
    'Los manifiestos deben estar organizados de forma predecible para que los agentes y el equipo los encuentren fácilmente.',
    'Organizar k8s/ en subdirectorios numerados: 01-namespaces-rbac, 02-storage, 03-deployments, 04-security, 05-services, 06-metrics, 07-autoscaling',
    '["directorio plano", "agrupación por componente (backend/, frontend/)", "Helm charts para todo"]',
    'Los recursos se aplican en orden numérico. Cada agente sabe exactamente dónde va cada tipo de recurso.',
    '["k8s/"]',
    '["organization", "directory-structure", "convention"]'
);

-- D7: Naming convention ftth-*
INSERT INTO decisions (agent, domain, title, context, decision, alternatives, consequences, related_files, tags)
VALUES (
    'infrastructure',
    'convention',
    'Naming convention: prefijo ftth- para todos los recursos',
    'Necesitamos una convención clara y consistente para identificar recursos del proyecto vs. recursos del sistema.',
    'Usar prefijo ftth- para todo: ftth-backend, ftth-frontend-service, app: ftth-redis, etc. Label tier: indica la capa (frontend/backend/data/worker).',
    '["sin prefijo", "prefijo por namespace", "prefijo por equipo"]',
    'Todos los recursos del proyecto son fácilmente identificables con kubectl get all -l app=ftth-*',
    '[]',
    '["naming", "convention", "labels", "ftth"]'
);

-- D8: Arquitectura 3-tier
INSERT INTO decisions (agent, domain, title, context, decision, alternatives, consequences, related_files, tags)
VALUES (
    'application',
    'architecture',
    'Arquitectura 3-tier: Nginx + Flask + Redis',
    'El FTTH Dashboard necesita frontend estático, API backend, y cache. La arquitectura debe ser simple pero representativa de patrones reales de microservicios.',
    'Frontend: Nginx sirviendo HTML desde ConfigMap. Backend: Flask en Python con endpoints /health y /status. Cache: Redis accesible vía ftth-redis-service:6379.',
    '["monolito Node.js", "React + Express + PostgreSQL", "solo frontend estático"]',
    'El HTML se actualiza vía ConfigMap (no rebuild de imagen). Flask es liviano pero limitado en concurrencia. Redis no tiene persistencia (reiniciar = perder datos).',
    '["src/backend/app.py", "k8s/02-storage/frontend-configmap.yaml"]',
    '["architecture", "3-tier", "nginx", "flask", "redis", "microservices"]'
);

-- ─── LESSONS LEARNED ────────────────────────────────────────

-- L1: imagePullPolicy gotcha
INSERT INTO lessons_learned (agent, category, title, description, root_cause, resolution, prevention, related_files, severity, tags)
VALUES (
    'validation',
    'gotcha',
    'imagePullPolicy Always falla en Kind con imágenes locales',
    'Las imágenes cargadas con kind load docker-image no están en ningún registry. Si imagePullPolicy es Always, el kubelet intenta pull y falla con ErrImagePull/ImagePullBackOff.',
    'Kind usa containerd internamente. kind load inserta la imagen directamente en el containerd del nodo. No hay registry involucrado.',
    'Usar imagePullPolicy: Never para imágenes locales cargadas con kind load.',
    'El Infrastructure Agent debe verificar imagePullPolicy según el tipo de imagen antes de proponer cualquier Deployment.',
    '["k8s/03-deployments/backend-deployment.yaml"]',
    'warning',
    '["kind", "imagePullPolicy", "local-images", "ErrImagePull", "containerd"]'
);

-- L2: extraPortMappings requiere recrear clúster
INSERT INTO lessons_learned (agent, category, title, description, resolution, prevention, severity, tags)
VALUES (
    'infrastructure',
    'gotcha',
    'Agregar extraPortMappings en Kind requiere recrear el clúster',
    'Los extraPortMappings de Kind se configuran al momento de crear el clúster. No se pueden agregar después con kind update o similar.',
    'Destruir y recrear el clúster con kind delete cluster + kind create cluster --config kind-config.yaml. Luego re-aplicar todos los manifiestos y recargar imágenes.',
    'Planificar todos los puertos necesarios ANTES de crear el clúster. Documentar puertos reservados en kind-config.yaml y en infra_skill.md.',
    'warning',
    '["kind", "extraPortMappings", "nodeport", "cluster-recreation"]'
);

-- L3: Labels selector mismatch
INSERT INTO lessons_learned (agent, category, title, description, root_cause, resolution, prevention, severity, tags)
VALUES (
    'validation',
    'error',
    'Service no encuentra pods si el selector no matchea labels del Deployment',
    'Un Service con selector app: X no enviará tráfico a pods que tengan label app: Y. kubectl get endpoints mostrará <none>.',
    'Typo o inconsistencia entre el label del Pod template y el selector del Service.',
    'Verificar con kubectl get endpoints <service-name> que los endpoints están populados. Si aparece <none>, comparar selector del Service vs labels del Pod.',
    'El Infrastructure Agent siempre verifica coherencia selector-labels antes de proponer un Service. Patrón fijo: app: ftth-[componente].',
    'critical',
    '["service", "selector", "labels", "endpoints", "debugging"]'
);

-- L4: CronJob como health checker
INSERT INTO lessons_learned (agent, category, title, description, related_files, severity, tags)
VALUES (
    'infrastructure',
    'pattern',
    'CronJob como health checker periódico del backend',
    'Se usa un CronJob con BusyBox que hace wget al endpoint /health del backend cada 2 minutos. Permite verificar conectividad interna sin depender de herramientas externas. El CronJob usa restartPolicy: OnFailure para reintentar si falla.',
    '["k8s/03-deployments/network-checker-cronjob.yaml"]',
    'info',
    '["cronjob", "health-check", "busybox", "pattern", "monitoring"]'
);

-- ─── RESOURCE REGISTRY ──────────────────────────────────────

INSERT INTO resource_registry (kind, name, namespace, manifest_path, labels, dependencies, exposed_ports, validation_status, notes)
VALUES
    ('Deployment', 'ftth-frontend', 'default', 'k8s/03-deployments/frontend-deployment.yaml',
     '{"app": "ftth-frontend", "tier": "frontend"}',
     '["ConfigMap/ftth-dashboard-html"]',
     '["80"]', 'unknown', 'Nginx sirviendo HTML desde ConfigMap'),

    ('Deployment', 'ftth-backend', 'default', 'k8s/03-deployments/backend-deployment.yaml',
     '{"app": "ftth-backend", "tier": "backend"}',
     '["Service/ftth-redis-service"]',
     '["5000"]', 'unknown', 'Flask API con /health y /status'),

    ('Deployment', 'ftth-redis', 'default', 'k8s/03-deployments/redis-deployment.yaml',
     '{"app": "ftth-redis", "tier": "data"}',
     '[]',
     '["6379"]', 'unknown', 'Redis cache, programado en worker con nodeAffinity'),

    ('CronJob', 'ftth-network-checker', 'default', 'k8s/03-deployments/network-checker-cronjob.yaml',
     '{"app": "ftth-network-checker", "tier": "worker"}',
     '["Service/ftth-backend-service"]',
     '[]', 'unknown', 'Health check cada 2 min via wget al backend'),

    ('Service', 'ftth-frontend-service', 'default', 'k8s/05-services/frontend-service.yaml',
     '{}',
     '["Deployment/ftth-frontend"]',
     '["80", "30080"]', 'unknown', 'NodePort 30080 → Frontend'),

    ('Service', 'ftth-backend-service', 'default', 'k8s/05-services/backend-service.yaml',
     '{}',
     '["Deployment/ftth-backend"]',
     '["5000"]', 'unknown', 'ClusterIP interno para el backend'),

    ('Service', 'ftth-redis-service', 'default', 'k8s/05-services/redis-service.yaml',
     '{}',
     '["Deployment/ftth-redis"]',
     '["6379"]', 'unknown', 'ClusterIP interno para Redis'),

    ('ConfigMap', 'ftth-dashboard-html', 'default', 'k8s/02-storage/frontend-configmap.yaml',
     '{}',
     '[]',
     '[]', 'unknown', 'HTML del dashboard montado como volumen en Nginx'),

    ('PodDisruptionBudget', 'ftth-backend-pdb', 'default', 'k8s/03-deployments/pod-disruption-budgets.yaml',
     '{}',
     '["Deployment/ftth-backend"]',
     '[]', 'unknown', 'PDB para el backend'),

    ('VPA', 'ftth-redis-vpa', 'default', 'k8s/07-autoscaling/redis-vpa.yaml',
     '{}',
     '["Deployment/ftth-redis"]',
     '[]', 'unknown', 'Vertical Pod Autoscaler para Redis');
