# Currículo LOMLOE en JSON

Datos estructurados y reutilizables del currículo LOMLOE. La primera materia incluida es Física y Química de 2.º, 3.º y 4.º de ESO en Andalucía.

## Visualizador de prueba

El visor estático demuestra cómo una aplicación puede descargar el JSON, resolver sus referencias y recorrer el currículo en ambos sentidos.

```powershell
python -m http.server 8000
```

Después, abre `http://localhost:8000`. También se puede indicar otro documento compatible mediante `?src=URL_DEL_JSON` o cargar un archivo desde la propia interfaz.

## Estructura

- `data/`: documentos curriculares canónicos.
- `schemas/`: esquemas JSON para validarlos.
- `index.html`, `styles.css`, `app.js`: visualizador sin dependencias ni proceso de compilación.
- `scripts/build-site.mjs`: prepara una copia publicable en `dist/`.

## Compilar el sitio estático

```powershell
node scripts/build-site.mjs
```
