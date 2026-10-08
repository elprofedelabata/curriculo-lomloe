# Currículo LOMLOE en JSON

Datos estructurados y reutilizables del currículo LOMLOE. Actualmente incluye los 88 currículos de Andalucía recogidos en los anexos II y III de ESO y Bachillerato, completados en la [checklist](CHECKLIST.md). Las discrepancias detectadas durante el cotejo se reúnen en el [registro de incidencias](INCIDENCIAS.md).

## Visualizador de prueba

El visor estático demuestra cómo una aplicación puede descargar el JSON, resolver sus referencias y recorrer el currículo en ambos sentidos.

```powershell
python -m http.server 8000
```

Después, abre `http://localhost:8000`. También se puede indicar otro documento compatible mediante `?src=URL_DEL_JSON` o cargar un archivo desde la propia interfaz.

## Estructura

- `data/`: documentos curriculares canónicos.
- `schemas/`: esquemas JSON para validarlos.
- `sources/`: PDF oficiales y catálogo de las fuentes normativas utilizadas.
- `index.html`, `styles.css`, `app.js`: visualizador sin dependencias ni proceso de compilación.
- `scripts/build-site.mjs`: prepara una copia publicable en `dist/`.

Los desarrollos pueden incluir el campo opcional `variante`. Se usa en 4.º de ESO para distinguir Matemáticas A y Matemáticas B sin duplicar el currículo común de la materia.

## Compilar el sitio estático

```powershell
node scripts/build-site.mjs
```
