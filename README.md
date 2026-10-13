# Currículo LOMLOE en JSON

Datos estructurados y reutilizables del currículo LOMLOE. Actualmente incluye 100 currículos revisados de Andalucía: Infantil, Primaria, ESO, Bachillerato y los dos ámbitos comunes de CFGB. El avance se detalla en la [checklist](CHECKLIST.md) y las discrepancias detectadas durante el cotejo se reúnen en el [registro de incidencias](INCIDENCIAS.md).

## Progreso del proyecto

El objetivo es convertir a JSON los currículos oficiales de **Infantil, Primaria, ESO, Bachillerato y Ciclos Formativos de Grado Básico (CFGB)** de las 17 comunidades autónomas.

| Comunidad autónoma | Infantil | Primaria | ESO | Bachillerato | CFGB |
| --- | :---: | :---: | :---: | :---: | :---: |
| Andalucía | ✅ 3/3 | ✅ 7/7 | ✅ 30/30 | ✅ 58/58 | ✅ 2/2 |
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

En CFGB se incluyen los ámbitos comunes de Ciencias Aplicadas y Comunicación y Ciencias Sociales del anexo V de la Orden de 30 de mayo de 2023. Los dos ámbitos cuentan con JSON revisados; los módulos profesionales quedan fuera de este alcance. Más adelante se podrá estudiar la incorporación del resto de enseñanzas de Formación Profesional.

## Sitio web

La [aplicación de página única](https://elprofedelabata.github.io/curriculo-lomloe/) permite elegir comunidad y etapa para consultar, sin salir de la portada:

- los enlaces directos a cada currículo JSON;
- sus cursos, métricas y estado de revisión;
- las fuentes oficiales y los PDF archivados;
- las incidencias documentadas y su resolución.

El sitio genera también un [`catalogo.json`](https://elprofedelabata.github.io/curriculo-lomloe/catalogo.json) para que otras aplicaciones descubran todos los currículos publicados sin mantener una lista manual.

## Uso directo de los datos

Cada currículo tiene una URL pública a su archivo JSON, sin necesidad de clave ni de una API propia. Por ejemplo, el ámbito de [Ciencias Aplicadas de CFGB](https://elprofedelabata.github.io/curriculo-lomloe/data/es-an/cfgb/materias/ciencias-aplicadas.json) puede leerse desde JavaScript así:

```js
const url = "https://elprofedelabata.github.io/curriculo-lomloe/data/es-an/cfgb/materias/ciencias-aplicadas.json";
const curriculo = await fetch(url).then((respuesta) => respuesta.json());
console.log(curriculo.materia.nombre.es);
```

Para localizar los demás archivos y consultar su etapa, estado de revisión y fuentes, utiliza el [`catalogo.json`](https://elprofedelabata.github.io/curriculo-lomloe/catalogo.json) generado por el sitio.

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