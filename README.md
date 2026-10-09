# Currículo LOMLOE en JSON

Datos estructurados y reutilizables del currículo LOMLOE. Actualmente incluye los 88 currículos de Andalucía recogidos en los anexos II y III de ESO y Bachillerato, completados en la [checklist](CHECKLIST.md). Las discrepancias detectadas durante el cotejo se reúnen en el [registro de incidencias](INCIDENCIAS.md).

## Progreso del proyecto

El objetivo es convertir a JSON los currículos oficiales de **Infantil, Primaria, ESO, Bachillerato y Ciclos Formativos de Grado Básico (CFGB)** de las 17 comunidades autónomas.

| Comunidad autónoma | Infantil | Primaria | ESO | Bachillerato | CFGB |
| --- | :---: | :---: | :---: | :---: | :---: |
| Andalucía | 📚 | 📚 | ✅ 30/30 | ✅ 58/58 | ⬜ |
| Aragón | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Principado de Asturias | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Illes Balears | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Canarias | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Cantabria | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Castilla-La Mancha | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Castilla y León | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Cataluña | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Comunitat Valenciana | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Extremadura | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Galicia | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Comunidad de Madrid | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Región de Murcia | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Comunidad Foral de Navarra | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| País Vasco | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| La Rioja | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

**Leyenda:** ✅ currículo completo y revisado · 📚 fuentes oficiales recopiladas · 🚧 conversión en curso · ⬜ pendiente.

El alcance actual llega hasta CFGB. Más adelante se podrá estudiar la incorporación del resto de enseñanzas de Formación Profesional.

## Sitio web

La [aplicación de página única](https://elprofedelabata.github.io/curriculo-lomloe/) permite elegir comunidad y etapa para consultar, sin salir de la portada:

- los enlaces directos a cada currículo JSON;
- sus cursos, métricas y estado de revisión;
- las fuentes oficiales y los PDF archivados;
- las incidencias documentadas y su resolución.

El sitio genera también un [`catalogo.json`](https://elprofedelabata.github.io/curriculo-lomloe/catalogo.json) para que otras aplicaciones descubran todos los currículos publicados sin mantener una lista manual.

## Desarrollo local

Genera y valida el sitio estático:

```powershell
node scripts/build-site.mjs
node scripts/validate-site.mjs
```

Después sirve el directorio generado:

```powershell
python -m http.server 8000 --directory dist
```

Abre `http://localhost:8000`. La selección se conserva en la URL mediante los parámetros `territorio`, `etapa` y, opcionalmente, `materia`.

## Estructura

- `data/`: documentos curriculares canónicos.
- `schemas/`: esquemas JSON para validarlos.
- `sources/`: PDF oficiales y catálogo de las fuentes normativas utilizadas.
- `INCIDENCIAS.md`: registro único de discrepancias y decisiones de revisión.
- `index.html`, `styles.css`, `app.js`: plantilla y aplicación web sin dependencias externas.
- `scripts/build-site.mjs`: genera la aplicación de página única, el catálogo y los datos publicables en `dist/`.
- `scripts/validate-site.mjs`: comprueba rutas, datos y relaciones del sitio generado.
- `.github/workflows/pages.yml`: valida y publica GitHub Pages automáticamente desde `main`.

Los desarrollos pueden incluir el campo opcional `variante`. Se usa en 4.º de ESO para distinguir Matemáticas A y Matemáticas B sin duplicar el currículo común de la materia.