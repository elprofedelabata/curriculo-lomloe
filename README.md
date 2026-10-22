# Currículo LOMLOE en JSON

Datos estructurados y reutilizables del currículo LOMLOE. Actualmente incluye los 102 currículos revisados de Andalucía, los tres currículos revisados de Educación Infantil de Aragón y los 15 currículos revisados de Infantil, Primaria y CFGB del Principado de Asturias. Aragón dispone además de 113 currículos en borrador y Asturias incorpora 72 JSON de ESO y Bachillerato pendientes de revisión. El avance se detalla en la [checklist](CHECKLIST.md) y las discrepancias detectadas durante el cotejo se reúnen en el [registro de incidencias](INCIDENCIAS.md).

## Progreso del proyecto

El objetivo es convertir a JSON los currículos oficiales de **Infantil, Primaria, ESO, Bachillerato y Ciclos Formativos de Grado Básico (CFGB)** de las 17 comunidades autónomas.

| Comunidad autónoma | Infantil | Primaria | ESO | Bachillerato | CFGB |
| --- | :---: | :---: | :---: | :---: | :---: |
| Andalucía | ✅ 3/3 | ✅ 7/7 | ✅ 32/32 | ✅ 58/58 | ✅ 2/2 |
| Aragón | ✅ 3/3 | 📝 14/14 | 📝 38/38 | 📝 59/59 | 📝 2/2 |
| Principado de Asturias | ✅ 3/3 | ✅ 10/10 | 📝 24/24 | 📝 48/51 | ✅ 2/2 |
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

**Leyenda:** ✅ currículo completo y revisado · 📝 JSON generado pendiente de revisión · 📚 fuentes oficiales recopiladas · 🚧 conversión en curso · ⬜ pendiente.

En CFGB se incluyen los ámbitos comunes de Ciencias Aplicadas y Comunicación y Ciencias Sociales del anexo V de la Orden de 30 de mayo de 2023. Los dos ámbitos cuentan con JSON revisados; los módulos profesionales quedan fuera de este alcance. Más adelante se podrá estudiar la incorporación del resto de enseñanzas de Formación Profesional.

## Sitio web

La [portada](https://elprofedelabata.github.io/curriculo-lomloe/) presenta el proyecto y las 17 comunidades autónomas en una cuadrícula de carpetas. La carpeta de cada comunidad con datos despliega, dentro de la misma cuadrícula, sus cinco etapas educativas. Cada etapa abre una lista sencilla de materias o ámbitos, con acceso directo a los JSON y detalles desplegables de fuentes e incidencias. Sus enlaces se pueden compartir para abrir una etapa o una materia concreta. Aragón cuenta con Infantil revisado y otros 113 currículos en borrador; el Principado de Asturias tiene revisados Infantil, Primaria y CFGB, y suma 24 currículos de ESO y 48 de Bachillerato en revisión. Illes Balears y Canarias siguen disponibles solo como maquetas. Los archivos JSON continúan accesibles directamente y el sitio genera un [`catalogo.json`](https://elprofedelabata.github.io/curriculo-lomloe/catalogo.json) para descubrirlos sin mantener una lista manual.

Las banderas de las carpetas se sirven desde el propio repositorio; sus fuentes y licencias están en [assets/flags/README.md](assets/flags/README.md).

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

Abre `http://localhost:8000` para previsualizar la portada.

## Estructura

- `assets/flags/`: miniaturas de las banderas y sus créditos.
- `data/`: documentos curriculares canónicos.
- `schemas/`: esquemas JSON para validarlos.
- `sources/`: PDF oficiales y catálogo de las fuentes normativas utilizadas.
- `INCIDENCIAS.md`: índice general de incidencias.
- `incidencias/`: registros de discrepancias y decisiones de revisión separados por comunidad autónoma.
- `index.html`, `styles.css` y `site.js`: portada y desplegable de Andalucía; `app.js` conserva el prototipo anterior, pero no se carga ni se publica.
- `scripts/build-site.mjs`: genera el sitio estático, el catálogo y los datos publicables en `dist/`.
- `scripts/validate-site.mjs`: comprueba rutas, datos y relaciones del sitio generado.
- `.github/workflows/pages.yml`: valida y publica GitHub Pages automáticamente desde `main`.

Los desarrollos pueden incluir el campo opcional `variante`. Se usa en 4.º de ESO para distinguir Matemáticas A y Matemáticas B sin duplicar el currículo común de la materia.

## Identificadores internos y códigos oficiales

El campo `codigoOficial` reproduce únicamente una nomenclatura publicada expresamente por la normativa. Cuando la fuente no asigna un código individual a un elemento, su valor es `null`.

El campo `id` siempre contiene un identificador estable del proyecto. En currículos como Educación Infantil de Aragón, donde los saberes se publican como listas sin numeración individual, se construye con la abreviatura oficial del área, el ciclo, el bloque y la posición del saber. Por ejemplo, `DEE.2.A.07` identifica internamente el séptimo saber del bloque A del segundo ciclo de Descubrimiento y Exploración del Entorno. Este identificador no debe interpretarse como un código oficial.
