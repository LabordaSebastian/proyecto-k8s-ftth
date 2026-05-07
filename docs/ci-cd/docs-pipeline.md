# Pipeline de Documentación (docs.yml)

Este flujo se encarga de convertir nuestros archivos Markdown (`.md`) en una página web hermosa y profesional usando MkDocs, y luego subirla a GitHub Pages.

```yaml
name: docs
on:
  push:
    branches:
      - main
permissions:
  contents: write
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Configure Git Credentials
        run: |
          git config user.name github-actions[bot]
          git config user.email 41898282+github-actions[bot]@users.noreply.github.com
      - uses: actions/setup-python@v5
        with:
          python-version: 3.x
      - run: pip install mkdocs mkdocs-material
      - run: mkdocs gh-deploy --force
```

### Explicación sección por sección:

1. **`permissions: contents: write`**: Autoriza al bot de GitHub Actions a modificar el repositorio. Es necesario porque el flujo creará archivos compilados y hará un commit de ellos de forma automática.
2. **`runs-on: ubuntu-latest`**: A diferencia del anterior, este sí se ejecuta en la nube de GitHub, en un servidor Linux efímero gratuito.
3. **Configure Git Credentials**: Le damos una identidad al bot ("github-actions[bot]") para que GitHub sepa quién está haciendo el commit de la página generada.
4. **`setup-python@v5`**: Instala Python en el servidor de GitHub (necesario ya que MkDocs es una herramienta construida en Python).
5. **Instalación de herramientas**: Descarga e instala `mkdocs` y el tema visual `mkdocs-material` vía `pip`.
6. **`mkdocs gh-deploy --force`**: El comando mágico. MkDocs lee nuestros archivos Markdown, los convierte en una página web interactiva con HTML/CSS/JS, y automáticamente sube esos archivos a una rama oculta de nuestro repositorio llamada `gh-pages` para publicarlos en internet.
