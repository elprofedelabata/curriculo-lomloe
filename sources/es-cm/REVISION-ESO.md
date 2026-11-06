# Revisión de ESO de Castilla-La Mancha

Los 31 JSON quedaron cotejados y revisados el 6 de noviembre de 2026. El [registro de Castilla-La Mancha](../../incidencias/es-cm.md#eso--decisiones-revisadas) recoge las once decisiones editoriales confirmadas y aplicadas.

## Alcance e inventario

- El [Decreto 82/2022, anexo II](normativa/eso/2022-07-12-decreto-82-2022-curriculo-eso-cfgb.pdf#page=34) contiene 28 materias. La [corrección de febrero de 2024](normativa/eso/2024-02-13-correccion-decreto-82-2022.pdf) rectifica pasajes de Artes Escénicas, Danza y Folclore, Biología y Geología, Emprendimiento, Sostenibilidad y Consumo Responsable, Música Activa, Movimiento y Folclore y Proyectos de Artes Plásticas y Visuales.
- El [Decreto 31/2024](normativa/eso/2024-06-25-decreto-31-2024-modificacion-eso.pdf#page=8) añade Unión Europea (páginas 9–13), sustituye dos párrafos de Desarrollo Digital y actualiza la oferta y los horarios. Los artículos 9 y 10 del Decreto 82/2022, en la redacción de 2024, y los horarios del anexo IV (páginas 13–14) fijan los cursos de la oferta ordinaria.
- El [anexo I de la Orden 166/2022](normativa/eso/2022-09-02-orden-166-2022-diversificacion-curricular.pdf#page=9) publica los currículos propios del Ámbito lingüístico y social y el Ámbito científico-tecnológico de Diversificación. La orden prevé un ámbito práctico potestativo que remite a aspectos básicos de Tecnología y Digitalización.
- La [Orden 179/2025](normativa/eso-bachillerato/2025-12-09-orden-179-2025-optativas-de-centro.pdf) regula el diseño y la autorización de las optativas definidas por los centros. Sus propuestas de centro y el ámbito práctico por remisión quedan fuera del recuento de desarrollos curriculares propios del inventario.

El [inventario](inventario.json) localiza los 31 currículos, con las páginas de las fuentes y sus modificaciones. Para Matemáticas, se cuenta la entrada del anexo. El inventario agrupa ahí el desarrollo común y las variantes A y B de 4.º.

## Representación y cobertura

Los 31 JSON suman 182 competencias específicas, 61 desarrollos por curso o variante, 1.050 criterios y 1.996 saberes. El recuento incluye las copias de los desarrollos comunes asignadas a los cursos de impartición.

- **Cursos compartidos.** Biología y Geología usa su desarrollo de «Cursos de primero a tercero» en 1.º y 3.º, Física y Química en 2.º y 3.º, y Música en 1.º y 2.º. Las tres materias conservan además su desarrollo de 4.º. Los dos ámbitos de Diversificación conservan las competencias del ámbito y el desarrollo común en 3.º y 4.º.
- **Matemáticas.** Un JSON mantiene las competencias comunes de etapa, los desarrollos de 1.º a 3.º y las variantes A y B de 4.º con identificadores distintos.
- **Saberes.** Los encabezados numerados se conservan como apartados. En Lengua Castellana y Literatura, los párrafos que enmarcan listas se guardan en `descripcion` del bloque o del apartado correspondiente. En Geografía e Historia, el pasaje sobre desarrollo urbano de la página 137 continúa el saber sobre aglomeraciones urbanas y ruralidad, como en el [anexo II del Real Decreto 217/2022](https://www.boe.es/buscar/act.php?id=BOE-A-2022-4975#aii).
- **Rectificaciones publicadas.** Se aplican los cambios de descriptores de Artes Escénicas, Danza y Folclore, Emprendimiento, Sostenibilidad y Consumo Responsable y Música Activa, Movimiento y Folclore, y la adición de «Salud y enfermedad» a la introducción de Biología y Geología. La rectificación del rótulo de descriptores de Proyectos de Artes Plásticas y Visuales queda recogida mediante la referencia a la corrección oficial. Desarrollo Digital incorpora los párrafos sustituidos de las competencias 3 y 4.

Los códigos de criterio y las letras de bloque proceden del decreto. Las abreviaturas de materia y los identificadores individuales de saber son internos. Los vínculos a descriptores se mantienen por competencia específica. El anexo presenta por separado criterios y saberes.

## Cotejo y reproducción

El auditor coteja con Poppler los tres anexos que contienen los currículos, contrasta las rectificaciones con las publicaciones correspondientes y comprueba los descriptores con el Perfil de salida. Verifica las páginas de procedencia, la igualdad de los desarrollos compartidos y los 31 JSON contra el esquema común.

```powershell
python scripts/extract-es-cm-eso.py --write
python scripts/audit-es-cm-eso.py
node scripts/build-site.mjs
node scripts/validate-site.mjs
```

El extractor requiere PyMuPDF. El auditor requiere `pdftotext` de Poppler y `jsonschema`, que puede cargarse desde una carpeta local con `--packages`.
