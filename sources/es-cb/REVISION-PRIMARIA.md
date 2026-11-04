# Revisión de Primaria de Cantabria

Fecha: 4 de noviembre de 2026. Estado: Primaria completado. Los siete JSON están revisados y las quince decisiones del [registro de Cantabria](../../incidencias/es-cb.md#primaria--decisiones-revisadas) están confirmadas por el usuario: se conserva la redacción publicada en CB-PRIM-001 y se confirman las otras catorce correcciones.

## Cobertura

Se ha extraído el anexo II-A del [Decreto 66/2022](normativa/infantil-primaria/2022-07-07-decreto-66-2022-curriculo-infantil-primaria.pdf), páginas 56-175 del PDF completo.

| Área | Páginas del PDF | Competencias | Criterios, ciclos 1 / 2 / 3 | Saberes, ciclos 1 / 2 / 3 |
| --- | --- | ---: | ---: | ---: |
| Conocimiento del Medio Natural, Social y Cultural | 56-80 | 9 | 22 / 21 / 23 | 43 / 50 / 51 |
| Educación Artística | 80-92 | 4 | 9 / 9 / 10 | 24 / 32 / 34 |
| Educación Física | 92-108 | 5 | 15 / 15 / 15 | 26 / 27 / 29 |
| Educación en Valores Cívicos y Éticos | 108-116 | 4 | 11, solo 5.º | 22, solo 5.º |
| Lengua Castellana y Literatura | 116-137 | 10 | 19 / 19 / 19 | 29 / 32 / 34 |
| Lengua Extranjera | 137-153 | 6 | 14 / 15 / 15 | 16 / 21 / 23 |
| Matemáticas | 153-175 | 8 | 17 / 17 / 17 | 37 / 55 / 56 |

Total: **46 competencias específicas, 302 criterios y 641 saberes**, en 19 desarrollos: tres ciclos de seis áreas y un desarrollo de 5.º de Valores. Las páginas compartidas entre áreas contienen el final de una y el comienzo de la siguiente.

## Criterios de representación

- El artículo 17.2, página 12, sitúa Educación en Valores Cívicos y Éticos en 5.º. Se representa en ese curso, sin duplicarla en 6.º ni extenderla a todo el tercer ciclo.
- En las otras seis áreas, las competencias son comunes a la etapa y los desarrollos se conservan por ciclo, sin inventar una secuenciación por curso.
- Las introducciones y las descripciones de las competencias mantienen sus párrafos. Se conservan los descriptores operativos publicados para cada competencia, sin asignarlos a criterios ni crear relaciones criterio-saber ausentes en la fuente.
- Las abreviaturas CM, EA, EF, EVCE, LCL, LE y MAT y los identificadores individuales de saberes son internos del proyecto, no códigos oficiales. Los saberes se publican con viñetas: codigoOficial queda en null y no se les atribuye numeración oficial.
- Se mantienen las letras de bloques y los números de subapartados. La decisión confirmada CB-PRIM-003 restituye «4. Conciencia ecosocial» en el tercer ciclo de Conocimiento del Medio, donde aparece como una viñeta. El título no se cuenta como saber; sus seis contenidos ambientales se conservan íntegros. La interpretación se apoya en los otros dos ciclos y en el apartado homólogo del [anexo II del Real Decreto 157/2022](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2022-3296).
- Se reconstruyen ocho etiquetas de criterio omitidas, con la confirmación del usuario: 5.1 de Educación Física en los tres ciclos; 2.1 de Lengua en los tres ciclos; y 5.1 de Lengua en los dos primeros ciclos. Los textos están publicados bajo su competencia correspondiente. La restitución editorial de los números se documenta en el registro y está confirmada por el usuario.
- Las disposiciones finales primera y tercera, páginas 21-22, sitúan la implantación y la entrada en vigor en el curso 2022/2023, sin un día concreto. entradaEnVigor queda en null y aplicableDesdeCurso conserva 2022/2023. Los cursos 1.º, 3.º y 5.º se implantan en 2022/2023 y los cursos 2.º, 4.º y 6.º en 2023/2024.

## Cotejo y validación

El extractor usa texto y coordenadas del PDF mediante PyMuPDF y verifica su SHA-256 contra el catálogo de fuentes. Los fragmentos de una misma línea visual se reúnen antes de reconocer rótulos: algunos números de apartado se guardan como objetos separados en la capa de texto del PDF.

La auditoría independiente usa Poppler, sin importar ni ejecutar el extractor. Coteja **1.328 fragmentos**: 71 párrafos de introducción, 46 enunciados de competencias, 91 párrafos descriptivos, 302 criterios, 81 títulos de bloques, 96 títulos de subapartados y 641 saberes. Valida los siete documentos con el esquema común, sus identificadores, fuentes y referencias, los códigos de descriptores y la representación por ciclo o curso.

Además, reconstruye el texto completo de cada área, incluidos descriptores, rótulos y numeraciones, y lo compara en orden con el PDF. También cuenta de forma independiente los subapartados y las viñetas de cada desarrollo. Para el cotejo se restablecen exclusivamente las redacciones y formas publicadas de las catorce correcciones confirmadas; no se admiten otras diferencias. CB-PRIM-001 conserva «adaptados» tal como se publica, por decisión del usuario, que considera posible su referencia a los proyectos de diseño del apartado. No se detectan omisiones, duplicaciones ni diferencias adicionales.

Las decisiones se han contrastado visualmente en las páginas 67, 80, 85, 99, 102, 103, 106, 114, 125, 127, 128, 129, 133, 135, 151, 162 y 163. Los errores de extracción corregidos durante el cotejo no se incluyen en el registro de incidencias normativas.

Las quince decisiones están confirmadas por el usuario y los siete documentos tienen estado revisado. No quedan decisiones pendientes de Primaria.

## Reproducción

Requiere Python con PyMuPDF y jsonschema, y Poppler (`pdftotext`) en PATH.

```powershell
python scripts/extract-es-cb-primaria.py --write
python scripts/audit-es-cb-primaria.py
node scripts/build-site.mjs
node scripts/validate-site.mjs
```

Si jsonschema está instalado en un directorio específico, la auditoría admite `--packages RUTA`. Tanto el informe temporal como los diagnósticos del extractor pueden guardarse fuera de los JSON mediante `--report RUTA` y `--diagnostics RUTA`, respectivamente.

## Archivos

- [Conocimiento del Medio Natural, Social y Cultural](../../data/es-cb/primaria/materias/conocimiento-del-medio-natural-social-y-cultural.json)
- [Educación Artística](../../data/es-cb/primaria/materias/educacion-artistica.json)
- [Educación Física](../../data/es-cb/primaria/materias/educacion-fisica.json)
- [Educación en Valores Cívicos y Éticos](../../data/es-cb/primaria/materias/educacion-en-valores-civicos-y-eticos.json)
- [Lengua Castellana y Literatura](../../data/es-cb/primaria/materias/lengua-castellana-y-literatura.json)
- [Lengua Extranjera](../../data/es-cb/primaria/materias/lengua-extranjera.json)
- [Matemáticas](../../data/es-cb/primaria/materias/matematicas.json)
- [Catálogo de fuentes](normativa/catalogo.json)
- [Publicación oficial del Decreto 66/2022](https://boc.cantabria.es/boces/verAnuncioAction.do?idAnuBlob=374267)
