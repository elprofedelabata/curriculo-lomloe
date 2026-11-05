# Revisión de Infantil de Castilla-La Mancha

Fecha: 5 de noviembre de 2026. Las tres áreas están cotejadas y revisadas. Las once decisiones confirmadas y aplicadas se documentan en el [registro de Castilla-La Mancha](../../incidencias/es-cm.md).

## Cobertura

El [anexo II del Decreto 80/2022](normativa/infantil/2022-07-12-decreto-80-2022-curriculo-infantil.pdf#page=19) es la fuente de los tres JSON. Cada archivo contiene la introducción propia del área, sus competencias con el desarrollo narrativo y los descriptores, y los criterios y saberes de cada ciclo. El texto de apertura común al anexo se consulta en la fuente.

| Área | Páginas del PDF | Competencias | Criterios por ciclo | Saberes por ciclo |
| --- | ---: | ---: | ---: | ---: |
| Crecimiento en Armonía | 19–26 | 4 | 12 / 15 | 27 / 31 |
| Descubrimiento y Exploración del Entorno | 26–31 | 3 | 8 / 16 | 15 / 27 |
| Comunicación y Representación de la Realidad | 31–39 | 5 | 14 / 25 | 31 / 43 |
| Total | 19–39 | 12 | 34 / 56 | 73 / 101 |

## Representación

Las competencias específicas son comunes a ambos ciclos. El artículo 10.2 da carácter orientativo a los descriptores operativos. El artículo 10.3 da carácter orientativo a los elementos curriculares del primer ciclo. Los 77 enlaces a descriptores mantienen las listas que publica el anexo II y sus códigos se cotejan con el anexo I.

Los criterios conservan su código publicado y su vínculo con la competencia correspondiente. Las letras de bloque se toman del PDF. Las abreviaturas de área y los identificadores de los saberes son internos. Las listas `saberesBasicosRefs` quedan vacías porque la fuente presenta ambos elementos por separado.

La disposición final primera fija la implantación para 2022/2023. La disposición final tercera fija la entrada en vigor el 15 de julio de 2022, día siguiente a la publicación.

## Cotejo y reproducción

El extractor usa PyMuPDF y las coordenadas del PDF para separar los párrafos, los criterios y las viñetas. El auditor usa Poppler de forma independiente. Compara el contenido íntegro de las tres áreas en el orden publicado, comprueba la página exacta de las 276 procedencias de competencias, criterios y saberes, y valida los JSON contra el esquema común. Para comparar con el PDF, el auditor reconstruye la redacción publicada en los pasajes donde se aplicaron las correcciones editoriales confirmadas.

```powershell
python scripts/extract-es-cm-infantil.py --write
python scripts/audit-es-cm-infantil.py
node scripts/build-site.mjs
node scripts/validate-site.mjs
```

El extractor requiere PyMuPDF. El auditor requiere `pdftotext` de Poppler y `jsonschema`, que puede cargarse desde una carpeta local con `--packages`.
