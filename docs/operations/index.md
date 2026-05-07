# Operaciones y CI/CD

Esta sección documenta la automatización, despliegues continuos y flujos de trabajo que operan de forma automatizada sobre nuestro proyecto utilizando GitHub Actions.

La integración continua (CI) y el despliegue continuo (CD) son prácticas esenciales en la cultura DevOps. En este laboratorio, hemos configurado pipelines que demuestran cómo automatizar las cargas de trabajo repetitivas:

1. **Pipeline de Despliegue Local (`ci-cd.yml`)**: Cómo usamos un Runner `self-hosted` para interactuar con un clúster local de Kind, ideal para entornos de alta seguridad o desarrollo aislado.
2. **Pipeline de Documentación (`docs.yml`)**: La generación y publicación automatizada del sitio que estás leyendo actualmente a través de GitHub Pages.
