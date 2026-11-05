# Revisión de Primaria de Castilla-La Mancha

El 5 de noviembre de 2026 quedaron cotejadas y revisadas las siete áreas. Las diez decisiones confirmadas y aplicadas están en el [registro de Castilla-La Mancha](../../incidencias/es-cm.md#primaria--decisiones-revisadas).

## Cobertura

Cada JSON contiene la introducción del área, sus competencias específicas con el desarrollo narrativo y los descriptores, y los criterios y saberes de cada ciclo o curso. Las páginas de la tabla son posiciones dentro del [PDF del Decreto 81/2022, anexo II](normativa/primaria/2022-07-12-decreto-81-2022-curriculo-primaria.pdf#page=26).

| Área | Páginas del PDF | Competencias | Criterios por ciclo o curso | Saberes por ciclo o curso |
| --- | ---: | ---: | ---: | ---: |
| Conocimiento del Medio Natural, Social y Cultural | 26–41 | 9 | 23 / 23 / 24 | 39 / 47 / 49 |
| Educación Artística | 42–49 | 4 | 9 / 9 / 10 | 24 / 32 / 34 |
| Educación Física | 50–60 | 5 | 14 / 14 / 14 | 27 / 28 / 29 |
| Educación en Valores Cívicos y Éticos | 61–65 | 4 | 11 (5.º) | 24 (5.º) |
| Lengua Castellana y Literatura | 66–78 | 10 | 19 / 19 / 19 | 28 / 30 / 32 |
| Lengua Extranjera | 79–89 | 6 | 13 / 15 / 15 | 17 / 22 / 26 |
| Matemáticas | 90–104 | 8 | 18 / 18 / 18 | 35 / 55 / 56 |
| Total | 26–104 | 46 | 305 | 634 |

## Representación

- **Educación en Valores Cívicos y Éticos.** El artículo 9.2 y los horarios del [anexo IV](normativa/primaria/2022-07-12-decreto-81-2022-curriculo-primaria.pdf#page=107) la sitúan en 5.º. Es el único desarrollo por curso. Las otras seis áreas conservan tres desarrollos por ciclo cada una.
- **Lengua Extranjera.** El anexo II publica un currículo común y su introducción incluye tanto la primera como la segunda lengua extranjera. La [Orden 75/2023](normativa/infantil-primaria/2023-04-03-orden-75-2023-segunda-lengua-extranjera.pdf) y su [corrección](normativa/infantil-primaria/2023-04-26-correccion-orden-75-2023.pdf) se enlazan como fuentes complementarias sobre las condiciones de oferta en centros autorizados.
- **Educación Artística.** El artículo 9.1.b permite desdoblarla en Educación Plástica y Visual y Música y Danza. El JSON recoge el currículo conjunto del anexo II.
- **Jerarquía de los saberes.** Las letras de los bloques y los números de los apartados proceden del PDF. Las abreviaturas de área y los identificadores individuales de saber son internos. En Matemáticas, el epígrafe «Organización y análisis de datos» del bloque E del primer ciclo (p. 96) tiene un identificador textual interno porque el decreto lo presenta sin número.
- **Viñetas y continuaciones.** En Valores (p. 65) los dos elementos sobre identidad de género y diferencia entre sexo y género llevan una viñeta con forma de punto y se conservan como saberes separados. En Educación Física (p. 57), el texto sobre lateralidad y coordinación continúa el saber de capacidades perceptivo-motrices, como en el [anexo II del Real Decreto 157/2022](https://www.boe.es/buscar/act.php?id=BOE-A-2022-3296#aii).

Los criterios quedan vinculados a la competencia específica que los encabeza. Las listas `saberesBasicosRefs` quedan vacías porque el decreto publica ambos elementos por separado. Los 331 enlaces a descriptores se cotejan con el Perfil de salida del anexo I.

La disposición final primera fija la implantación para 1.º, 3.º y 5.º en 2022/2023 y para 2.º, 4.º y 6.º en 2023/2024. La disposición final tercera fija la entrada en vigor el 15 de julio de 2022.

## Cotejo y reproducción

El extractor usa PyMuPDF para separar el texto según las coordenadas del PDF. El auditor usa Poppler de forma independiente y consume el texto del anexo en el orden publicado, comprueba las páginas de las 985 procedencias de competencias, criterios y saberes, y valida los siete JSON con el esquema común. Para la comparación reconstruye la redacción publicada en los pasajes con correcciones editoriales.

```powershell
python scripts/extract-es-cm-primaria.py --write
python scripts/audit-es-cm-primaria.py
node scripts/build-site.mjs
node scripts/validate-site.mjs
```

El auditor requiere `pdftotext` de Poppler y `jsonschema`, que admite cargarse desde una carpeta local con `--packages`.
