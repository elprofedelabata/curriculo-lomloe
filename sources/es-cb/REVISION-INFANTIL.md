# Revisión de Infantil de Cantabria

Fecha: 3 de noviembre de 2026. Estado: Infantil completado. Los tres JSON están revisados y las siete decisiones de normalización están confirmadas por el usuario.

## Cobertura

| Área | Páginas del PDF | Competencias | Criterios, ciclo 1 / 2 | Saberes, ciclo 1 / 2 |
| --- | --- | ---: | ---: | ---: |
| Crecimiento en Armonía | 24-35 | 4 | 12 / 14 | 32 / 35 |
| Descubrimiento y Exploración del Entorno | 35-42 | 3 | 7 / 14 | 16 / 27 |
| Comunicación y Representación de la Realidad | 43-54 | 5 | 14 / 21 | 31 / 43 |

Total: **12 competencias específicas, 82 criterios y 184 saberes**, en seis desarrollos correspondientes a los dos ciclos de las tres áreas.

## Criterios de representación

- Las introducciones y las descripciones de las competencias conservan su separación por párrafos. Las competencias son comunes a ambos ciclos.
- Los elementos del primer ciclo tienen carácter orientativo según el artículo 8.2, página 6, del Decreto 66/2022.
- Las abreviaturas CA, DEE y CRR y los identificadores individuales de saberes son internos del proyecto. Los saberes solo tienen viñetas en la fuente: codigoOficial queda en null y no se les atribuye numeración oficial.
- Los descriptores operativos y las asociaciones entre criterios y saberes quedan vacíos porque no se publican de forma explícita.
- Las disposiciones finales primera y tercera, páginas 21-22, sitúan la implantación y la entrada en vigor en el curso 2022/2023. No fijan un día concreto: entradaEnVigor queda en null y aplicableDesdeCurso conserva 2022/2023.

## Cotejo y validación

El extractor usa texto y coordenadas del PDF mediante PyMuPDF. La auditoría independiente usa la extracción de Poppler, sin importar ni ejecutar el extractor.

Se han cotejado **371 fragmentos**: 35 párrafos de introducción, 12 enunciados de competencias, 27 párrafos descriptivos, 82 criterios, 31 títulos de bloques y 184 saberes. Los tres documentos cumplen el esquema común; sus identificadores y referencias son válidos.

Además, la auditoría reconstruye el contenido completo de cada área, con las etiquetas de sus competencias, ciclos, criterios y bloques, y lo compara en orden con el texto del PDF. Reconstruye únicamente las formas publicadas de las siete decisiones registradas para admitir esas normalizaciones; no se admiten otras diferencias. No se detectan omisiones, duplicaciones ni diferencias adicionales.

Las siete discrepancias se han comprobado visualmente en las páginas 25, 29, 37, 41, 45, 49 y 53. Las siete correcciones están aplicadas en los JSON revisados y confirmadas por el usuario en el [registro de Cantabria](../../incidencias/es-cb.md). No quedan incidencias pendientes de Infantil.

## Reproducción

Requiere Python con PyMuPDF y jsonschema, y Poppler (`pdftotext`) en PATH.

```powershell
python scripts/extract-es-cb-infantil.py --write
python scripts/audit-es-cb-infantil.py
node scripts/build-site.mjs
node scripts/validate-site.mjs
```

## Archivos

- [Crecimiento en Armonía](../../data/es-cb/infantil/materias/crecimiento-en-armonia.json)
- [Descubrimiento y Exploración del Entorno](../../data/es-cb/infantil/materias/descubrimiento-y-exploracion-del-entorno.json)
- [Comunicación y Representación de la Realidad](../../data/es-cb/infantil/materias/comunicacion-y-representacion-de-la-realidad.json)
- [Catálogo de fuentes](normativa/catalogo.json)
- [Publicación oficial del Decreto 66/2022](https://boc.cantabria.es/boces/verAnuncioAction.do?idAnuBlob=374267)
