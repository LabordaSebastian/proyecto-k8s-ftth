# Iniciar el Entorno Local

Esta sección está dedicada a la configuración inicial y aprovisionamiento del clúster de Kubernetes en nuestro entorno local.

En un entorno real (o en el examen CKA), normalmente interactuamos con clústeres aprovisionados vía `kubeadm`, pero para desarrollo local utilizamos **Kind (Kubernetes IN Docker)** debido a su ligereza y rápidez.

Aquí encontrarás la documentación sobre los dos componentes clave de nuestra inicialización:

1. **`kind-config.yaml`**: La configuración declarativa de los nodos y mapeo de puertos.
2. **`manage-env.sh`**: Nuestro script Bash que automatiza la creación, despliegue e inyección de imágenes, simulando un aprovisionamiento real de infraestructura.
