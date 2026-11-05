# Currículo LOMLOE en JSON

Datos estructurados y reutilizables del currículo LOMLOE. Actualmente incluye 609 JSON curriculares revisados, repartidos entre Andalucía (102), Aragón (116), el Principado de Asturias (87), Illes Balears (93), Canarias (109) y Cantabria (102). Canarias incluye las dos concreciones de Lengua para el silbo gomero de Primaria y ESO. Tres optativas asturianas de Bachillerato, cuyo desarrollo curricular queda abierto en el decreto, se documentan mediante fichas informativas separadas de los JSON curriculares. El avance se detalla en la [checklist](CHECKLIST.md) y las discrepancias detectadas durante el cotejo se reúnen en el [registro de incidencias](INCIDENCIAS.md).

## Progreso del proyecto

El objetivo es convertir a JSON los currículos oficiales de **Infantil, Primaria, ESO, Bachillerato y Ciclos Formativos de Grado Básico (CFGB)** de las 17 comunidades autónomas.

| Comunidad autónoma | Infantil | Primaria | ESO | Bachillerato | CFGB |
| --- | :---: | :---: | :---: | :---: | :---: |
| Andalucía | ✅ 3/3 | ✅ 7/7 | ✅ 32/32 | ✅ 58/58 | ✅ 2/2 |
| Aragón | ✅ 3/3 | ✅ 14/14 | ✅ 38/38 | ✅ 59/59 | ✅ 2/2 |
| Principado de Asturias | ✅ 3/3 | ✅ 10/10 | ✅ 24/24 | ✅ 48/48 | ✅ 2/2 |
| Illes Balears | ✅ 3/3 | ✅ 8/8 | ✅ 27/27 | ✅ 53/53 | ✅ 2/2 |
| Canarias | ✅ 3/3 | ✅ 10/10 | ✅ 27/27 | ✅ 67/67 | ✅ 2/2 |
| Cantabria | ✅ 3/3 | ✅ 7/7 | ✅ 37/37 | ✅ 53/53 | ✅ 2/2 |
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

**Leyenda:** ✅ JSON publicados y revisados (la fracción cuenta JSON curriculares, incluidas las concreciones complementarias) · 📝 JSON generado pendiente de revisión · 📚 fuentes oficiales recopiladas · 🚧 conversión en curso · ⬜ pendiente.

Para las Illes Balears se han recopilado los decretos curriculares de 2025 y la documentación de CFGB en [su catálogo de fuentes](sources/es-ib/normativa/catalogo.json). Sus 93 currículos de Infantil, Primaria, ESO, Bachillerato y los ámbitos comunes de CFGB están estructurados y revisados en JSON. Los textos se conservan en catalán; sus identificadores individuales de saberes y abreviaturas de materia son internos del proyecto, no códigos oficiales. La secuenciación de saberes por cursos de ESO y las aclaraciones de criterios tienen carácter orientativo según el artículo 10.3 del decreto de ESO; en Bachillerato, el artículo 10.1 declara orientativas las aclaraciones de criterios. Los PDF de CFGB proceden del portal institucional balear, no de un decreto curricular autonómico publicado en el BOIB; los desarrollos comunes se representan en ambos cursos sin atribuir a la fuente una secuenciación que no contiene.

Canarias cuenta con 109 JSON revisados: tres áreas de Infantil, nueve de Primaria, 23 materias de ESO, tres ámbitos de Diversificación, 67 materias de Bachillerato, dos ámbitos comunes de CFGB y dos concreciones complementarias de Lengua para el silbo gomero. Los [PDF oficiales del BOC](sources/es-cn/normativa/catalogo.json) incluyen la corrección de errores de Infantil y los decretos específicos de Diversificación y optativas de Bachillerato. Las 21 decisiones del [registro de Canarias](incidencias/es-cn.md) están revisadas.

Las concreciones de Lengua para el silbo gomero del Decreto 24/2026 añaden un JSON complementario en Primaria y otro en ESO: por eso sus columnas muestran diez y 27 archivos. Ambas están extraídas, cotejadas y revisadas. Se vinculan a Lengua y conservan la aplicación preceptiva en La Gomera y facultativa, con autorización, en las demás islas. La [revisión final](sources/es-cn/REVISION-FINAL.md) documenta las correcciones aplicadas y la conservación de los identificadores de Matemáticas.

Cantabria tiene recopilados los [14 PDF oficiales de partida](sources/es-cb/normativa/catalogo.json) para las cinco etapas, incluidas las optativas, ESPADE, la organización de Diversificación y la normativa de los ámbitos comunes de CFGB. El [inventario actualizado](sources/es-cb/inventario.json) reúne 102 currículos revisados. Las versiones con competencias distintas se representan por separado. Infantil ya tiene sus tres áreas extraídas y cotejadas en JSON, con ambos ciclos, 12 competencias, 82 criterios y 184 saberes. Las tres áreas están revisadas y sus siete decisiones están confirmadas. Primaria tiene sus siete áreas extraídas y cotejadas, con 46 competencias, 302 criterios y 641 saberes: seis áreas se desarrollan por los tres ciclos y Educación en Valores Cívicos y Éticos únicamente en 5.º, según el artículo 17.2 del decreto. Las quince decisiones de Primaria del [registro de Cantabria](incidencias/es-cb.md) están confirmadas: se conserva la redacción publicada en CB-PRIM-001 y se confirman las otras catorce correcciones. Los siete JSON están revisados. El [informe de Primaria](sources/es-cb/REVISION-PRIMARIA.md) detalla la cobertura y el cotejo. ESO tiene 37 JSON extraídos, cotejados y revisados: 223 competencias, 71 desarrollos, 1.295 criterios y 2.334 saberes contando la representación por curso. Sus 41 decisiones están confirmadas y aplicadas: Segunda Lengua Extranjera usa el decreto como base única y se han retirado las referencias inexistentes CCEC5/CCEC6 de dos optativas, sin inventar equivalencias. Los dos ámbitos de Diversificación se documentan en [fichas por remisión](data/es-cb/eso/ambitos-por-remision.json), sin inventar un currículo autónomo. El [informe de ESO](sources/es-cb/REVISION-ESO.md) explica las decisiones. Bachillerato tiene 53 JSON extraídos, cotejados y revisados: 321 competencias, 67 desarrollos, 1.037 criterios y 2.016 saberes. Se incluyen las optativas, DEVAS y Tecnificación Deportiva Avanzada. Segunda Lengua Extranjera I y II se representan por separado porque el enunciado de la CE 3 difiere. Sus 34 decisiones están confirmadas y aplicadas. El registro de Cantabria distingue las erratas, las inferencias editoriales y las referencias retiradas, con las listas de descriptores antes y después de cada cambio. El [informe de Bachillerato](sources/es-cb/REVISION-BACHILLERATO.md) detalla el cotejo y las decisiones. CFGB tiene los dos ámbitos extraídos, cotejados y revisados, con sus 12 decisiones confirmadas y aplicadas. Ciencias Aplicadas conserva las configuraciones ordinaria y DEVAS con sus condiciones de aplicación; no se suman como exigencias simultáneas para un alumno. El [informe de CFGB](sources/es-cb/REVISION-CFGB.md) detalla las tres publicaciones contrastadas, los códigos por curso y los componentes.

En Asturias hay además [tres optativas de Bachillerato con desarrollo abierto](data/es-as/bachillerato/optativas-abiertas.json): se inventarían y muestran como fichas informativas, sin inventar competencias, criterios o saberes comunes.

En Andalucía, CFGB incluye los ámbitos comunes de Ciencias Aplicadas y Comunicación y Ciencias Sociales del anexo V de la Orden de 30 de mayo de 2023. Los dos ámbitos cuentan con JSON revisados; los módulos profesionales quedan fuera de este alcance. Más adelante se podrá estudiar la incorporación del resto de enseñanzas de Formación Profesional.

## Sitio web

La [portada](https://elprofedelabata.github.io/curriculo-lomloe/) presenta el proyecto y las 17 comunidades autónomas en una cuadrícula de carpetas. La carpeta de cada comunidad con datos despliega, dentro de la misma cuadrícula, sus cinco etapas educativas. Cada etapa abre una lista sencilla de materias o ámbitos, con acceso directo a los JSON y detalles desplegables de fuentes e incidencias. Sus enlaces se pueden compartir para abrir una etapa o una materia concreta. Aragón tiene revisados los 116 JSON de sus cinco etapas; el Principado de Asturias tiene revisados los 87 JSON publicados de sus cinco etapas. Su Bachillerato muestra además las tres optativas de desarrollo abierto como fichas informativas con acceso al decreto, sin presentarlas como JSON curriculares. Illes Balears tiene revisados sus 93 JSON de las cinco etapas. Canarias ofrece sus 109 JSON revisados, incluidas las dos concreciones del silbo gomero. Los detalles de estas concreciones indican su relación con Lengua y su ámbito de aplicación. Los archivos JSON continúan accesibles directamente y el sitio genera un [`catalogo.json`](https://elprofedelabata.github.io/curriculo-lomloe/catalogo.json) para descubrirlos sin mantener una lista manual.

Las banderas de las carpetas se sirven desde el propio repositorio; sus fuentes y licencias están en [assets/flags/README.md](assets/flags/README.md).

## Uso directo de los datos

Cada currículo tiene una URL pública a su archivo JSON, sin necesidad de clave ni de una API propia. Por ejemplo, el ámbito de [Ciencias Aplicadas de CFGB](https://elprofedelabata.github.io/curriculo-lomloe/data/es-an/cfgb/materias/ciencias-aplicadas.json) puede leerse desde JavaScript así:

```js
const url = "https://elprofedelabata.github.io/curriculo-lomloe/data/es-an/cfgb/materias/ciencias-aplicadas.json";
const curriculo = await fetch(url).then((respuesta) => respuesta.json());
console.log(curriculo.materia.nombre.es);
```

Para localizar los demás archivos y consultar su etapa, estado de revisión y fuentes, utiliza el [`catalogo.json`](https://elprofedelabata.github.io/curriculo-lomloe/catalogo.json) generado por el sitio.

En Infantil y Primaria de Cantabria, `fuenteRef` enlaza con el `id` de la fuente en `documentosNormativos`. Para resolver referencias de descargas anteriores, consulta también `idsAnteriores` cuando esté presente. El Decreto 66/2022 de Cantabria usa `es-cb-infantil-primaria-decreto-66-2022` y conserva `boc-2022-135-decreto-66-2022` como identificador anterior.

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

Los desarrollos pueden incluir el campo opcional `variante`. Se usa en 4.º de ESO para distinguir Matemáticas A y Matemáticas B sin duplicar el currículo común de la materia. En Infantil de Canarias, cada desarrollo incluye `bloquesCompetenciales`: la explicación y la vinculación con las competencias clave que la fuente publica por competencia específica y ciclo. Su numeración local de saberes se registra en `numeracionFuente`, mientras `codigoOficial` queda en `null`; los `id` posicionales del proyecto son únicos. Una errata de numeración se ha normalizado y documentado en el registro de incidencias.

En Primaria de Canarias, los descriptores operativos publicados se conservan por ciclo y por criterio; los códigos individuales de los saberes son internos porque la fuente no los proporciona. En ESO, los cursos primero y segundo de Diversificación se representan como tercero y cuarto de ESO; el Ámbito Práctico solo tiene desarrollo en cuarto. Cuando un ámbito cambia el enunciado de una competencia entre cursos, cada versión recibe un `id` interno único y conserva el mismo `codigoOficial`; las referencias de los criterios identifican la versión de su curso. La numeración jerárquica de los saberes se conserva en `numeracionFuente`.

## Identificadores internos y códigos oficiales

El campo `codigoOficial` reproduce únicamente una nomenclatura publicada expresamente por la normativa. Cuando la fuente no asigna un código individual a un elemento, su valor es `null`.

El campo `id` siempre contiene un identificador estable del proyecto. En currículos como Educación Infantil de Aragón, donde los saberes se publican como listas sin numeración individual, se construye con la abreviatura interna del área, el ciclo, el bloque y la posición del saber. Por ejemplo, `DEE.2.A.07` identifica internamente el séptimo saber del bloque A del segundo ciclo de Descubrimiento y Exploración del Entorno. Este identificador no debe interpretarse como un código oficial.

El campo opcional `concrecionCurricular` (schemaVersion 0.7.0) vincula un desarrollo complementario con su currículo base mediante `materiaBaseRef`. `aplicacion` conserva los ámbitos preceptivos y facultativos y si la extensión facultativa requiere autorización. El catálogo 1.8.0 expone estos mismos metadatos.


## Apartados anidados y ámbitos por remisión

Desde `schemaVersion` 0.8.0, un apartado de saberes puede contener `apartados` subordinados en lugar de `saberes`, conservando todos los niveles publicados. Los lectores deben recorrer la jerarquía de forma recursiva; los formatos anteriores siguen admitidos. Por ejemplo:

```js
const recogerSaberes = (nodo) =>
  nodo.saberes ?? (nodo.apartados ?? []).flatMap(recogerSaberes);
const saberes = desarrollo.bloquesSaberes.flatMap(recogerSaberes);
```

El catálogo 1.9.0 añade `ambitosPorRemision`, separado de `materias` y de `optativasAbiertas`. Estas fichas enlazan las materias base y las incorporaciones opcionales publicadas para Diversificación. No contienen competencias, criterios o saberes inventados del ámbito; su esquema es [ambitos-por-remision.schema.json](schemas/ambitos-por-remision.schema.json).

**Componentes, códigos y variantes condicionadas**

Desde `schemaVersion` 0.9.0, cada entrada de `materia.cursos` puede incluir `codigoOficial` cuando la norma asigna un código específico a ese curso. El campo opcional `componente` de competencias y bloques de saberes distingue partes de un ámbito que repiten numeración oficial. Los identificadores `id` siguen siendo internos: deben utilizarse las referencias de los criterios para enlazarlos, sin deducirlas del número oficial.

Una `variante` de desarrollo puede incorporar `condicionesAplicacion`, `requiereAutorizacion` y `procedencia`. No siempre representa una elección libre: deben leerse sus condiciones antes de utilizarla. Las competencias generales del documento reúnen todos los componentes; en cada desarrollo solo aparecen los criterios y saberes de los componentes aplicables. Por ejemplo, Ciencias Aplicadas de Cantabria mantiene separadas la configuración ordinaria y DEVAS. Los recuentos de ambas no se suman como un currículo único exigible a cada alumno.

Estas propiedades son opcionales y mantienen los formatos anteriores. El catálogo 1.10.0 incorpora los códigos oficiales por curso; las condiciones completas de las variantes se consultan en los JSON curriculares.
