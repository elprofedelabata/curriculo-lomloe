# Currículo LOMLOE en JSON

Datos estructurados y reutilizables del currículo LOMLOE. Actualmente incluye 398 currículos revisados: 102 de Andalucía, 116 de Aragón, 87 del Principado de Asturias y 93 de Illes Balears. También están generados en borrador los tres JSON de Infantil y las nueve áreas de Primaria de Canarias. Tres optativas asturianas de Bachillerato, cuyo desarrollo curricular queda abierto en el decreto, se documentan mediante fichas informativas separadas de los JSON curriculares. El avance se detalla en la [checklist](CHECKLIST.md) y las discrepancias detectadas durante el cotejo se reúnen en el [registro de incidencias](INCIDENCIAS.md).

## Progreso del proyecto

El objetivo es convertir a JSON los currículos oficiales de **Infantil, Primaria, ESO, Bachillerato y Ciclos Formativos de Grado Básico (CFGB)** de las 17 comunidades autónomas.

| Comunidad autónoma | Infantil | Primaria | ESO | Bachillerato | CFGB |
| --- | :---: | :---: | :---: | :---: | :---: |
| Andalucía | ✅ 3/3 | ✅ 7/7 | ✅ 32/32 | ✅ 58/58 | ✅ 2/2 |
| Aragón | ✅ 3/3 | ✅ 14/14 | ✅ 38/38 | ✅ 59/59 | ✅ 2/2 |
| Principado de Asturias | ✅ 3/3 | ✅ 10/10 | ✅ 24/24 | ✅ 48/48 | ✅ 2/2 |
| Illes Balears | ✅ 3/3 | ✅ 8/8 | ✅ 27/27 | ✅ 53/53 | ✅ 2/2 |
| Canarias | 📝 3/3 | 📝 9/9 | 📚 | 📚 | 📚 |
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

**Leyenda:** ✅ JSON publicados y revisados (la fracción cuenta currículos con desarrollo cerrado) · 📝 JSON generado pendiente de revisión · 📚 fuentes oficiales recopiladas · 🚧 conversión en curso · ⬜ pendiente.

Para las Illes Balears se han recopilado los decretos curriculares de 2025 y la documentación de CFGB en [su catálogo de fuentes](sources/es-ib/normativa/catalogo.json). Sus 93 currículos de Infantil, Primaria, ESO, Bachillerato y los ámbitos comunes de CFGB están estructurados y revisados en JSON. Los textos se conservan en catalán; sus identificadores individuales de saberes y abreviaturas de materia son internos del proyecto, no códigos oficiales. La secuenciación de saberes por cursos de ESO y las aclaraciones de criterios tienen carácter orientativo según el artículo 10.3 del decreto de ESO; en Bachillerato, el artículo 10.1 declara orientativas las aclaraciones de criterios. Los PDF de CFGB proceden del portal institucional balear, no de un decreto curricular autonómico publicado en el BOIB; los desarrollos comunes se representan en ambos cursos sin atribuir a la fuente una secuenciación que no contiene.

Para Canarias se han recopilado los [PDF oficiales del BOC](sources/es-cn/normativa/catalogo.json) de las cinco etapas, incluida la corrección de errores de Infantil y el decreto específico de Diversificación Curricular de ESO. El anexo 1 del decreto de CFGB desarrolla los ámbitos comunes. Las tres áreas de Infantil y las nueve de Primaria ya tienen JSON en borrador, extraídos de los anexos curriculares de los Decretos 196/2022 y 211/2022. Las seis erratas detectadas y resueltas se documentan en [incidencias de Canarias](incidencias/es-cn.md).

En Asturias hay además [tres optativas de Bachillerato con desarrollo abierto](data/es-as/bachillerato/optativas-abiertas.json): se inventarían y muestran como fichas informativas, sin inventar competencias, criterios o saberes comunes.

En CFGB se incluyen los ámbitos comunes de Ciencias Aplicadas y Comunicación y Ciencias Sociales del anexo V de la Orden de 30 de mayo de 2023. Los dos ámbitos cuentan con JSON revisados; los módulos profesionales quedan fuera de este alcance. Más adelante se podrá estudiar la incorporación del resto de enseñanzas de Formación Profesional.

## Sitio web

La [portada](https://elprofedelabata.github.io/curriculo-lomloe/) presenta el proyecto y las 17 comunidades autónomas en una cuadrícula de carpetas. La carpeta de cada comunidad con datos despliega, dentro de la misma cuadrícula, sus cinco etapas educativas. Cada etapa abre una lista sencilla de materias o ámbitos, con acceso directo a los JSON y detalles desplegables de fuentes e incidencias. Sus enlaces se pueden compartir para abrir una etapa o una materia concreta. Aragón tiene revisados los 116 JSON de sus cinco etapas; el Principado de Asturias tiene revisados los 87 JSON publicados de sus cinco etapas. Su Bachillerato muestra además las tres optativas de desarrollo abierto como fichas informativas con acceso al decreto, sin presentarlas como JSON curriculares. Illes Balears tiene revisados sus 93 JSON de las cinco etapas; Canarias ofrece ya Infantil y Primaria en borrador y conserva las fuentes oficiales de las demás etapas. Los archivos JSON continúan accesibles directamente y el sitio genera un [`catalogo.json`](https://elprofedelabata.github.io/curriculo-lomloe/catalogo.json) para descubrirlos sin mantener una lista manual.

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

Los desarrollos pueden incluir el campo opcional `variante`. Se usa en 4.º de ESO para distinguir Matemáticas A y Matemáticas B sin duplicar el currículo común de la materia. En Infantil de Canarias, cada desarrollo incluye `bloquesCompetenciales`: la explicación y la vinculación con las competencias clave que la fuente publica por competencia específica y ciclo. Su numeración local de saberes se registra en `numeracionFuente`, mientras `codigoOficial` queda en `null`; los `id` posicionales del proyecto son únicos. Una errata de numeración se ha normalizado y documentado en el registro de incidencias. En Primaria de Canarias, los descriptores operativos publicados se conservan por ciclo y por criterio; los códigos individuales de los saberes son internos porque la fuente no los proporciona.

## Identificadores internos y códigos oficiales

El campo `codigoOficial` reproduce únicamente una nomenclatura publicada expresamente por la normativa. Cuando la fuente no asigna un código individual a un elemento, su valor es `null`.

El campo `id` siempre contiene un identificador estable del proyecto. En currículos como Educación Infantil de Aragón, donde los saberes se publican como listas sin numeración individual, se construye con la abreviatura interna del área, el ciclo, el bloque y la posición del saber. Por ejemplo, `DEE.2.A.07` identifica internamente el séptimo saber del bloque A del segundo ciclo de Descubrimiento y Exploración del Entorno. Este identificador no debe interpretarse como un código oficial.
