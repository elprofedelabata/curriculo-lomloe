# Fuentes oficiales de Aragón

Corpus normativo de partida para estructurar en JSON los currículos LOMLOE de Educación Infantil, Educación Primaria, Educación Secundaria Obligatoria, Bachillerato y los ámbitos comunes de Ciclos Formativos de Grado Básico en Aragón.

## Organización

- infantil/: Orden ECD/853/2022, que establece la ordenación, el currículo y la evaluación de Educación Infantil.
- primaria/: Orden ECD/1112/2022, que establece la ordenación, el currículo y la evaluación de Educación Primaria.
- eso/: Orden ECD/1172/2022, que contiene los currículos de ESO y los ámbitos comunes de CFGB.
- bachillerato/: Orden ECD/1173/2022, que establece la ordenación, el currículo y la evaluación de Bachillerato.
- cfgb/: marco autonómico vigente y normativa organizativa específica de los ciclos formativos de grado básico.
- actualizaciones/: disposiciones posteriores que modifican las normas curriculares y de ordenación.
- catalogo.json: inventario legible por máquinas con procedencia, URL oficial, número de páginas y SHA-256.

## Particularidades del corpus

Las órdenes curriculares aragonesas reúnen en un único PDF el articulado y sus anexos. Para Primaria, ESO y Bachillerato deben aplicarse conjuntamente las órdenes originales de 2022 y sus modificaciones curriculares de 2024.

El currículo de los ámbitos comunes de CFGB -Comunicación y Ciencias Sociales y Ciencias Aplicadas- está incluido en el anexo II de la Orden ECD/1172/2022 de ESO. La Orden ECD/841/2024 remite expresamente a ese anexo. El proyecto conservará la normativa propia de CFGB, pero solo convertirá a JSON esos dos ámbitos comunes; los módulos profesionales se reservan para una futura ampliación de FP.

La Orden ECD/739/2025 de Bachillerato modifica la organización de materias y los anexos horarios, pero no sustituye el desarrollo curricular del anexo II. Las dos correcciones de la Orden ECD/841/2024 afectan a ciclos y horarios concretos, no a los ámbitos comunes.

## Criterios de conservación

- Se guarda el PDF oficial auténtico del BOA, sin editar ni recomprimir.
- Las firmas electrónicas publicadas por separado por el BOA no se duplican como PDF.
- El nombre local es estable y descriptivo; la URL original permanece en el catálogo.
- La huella SHA-256 permite comprobar que el archivo no ha cambiado.
- Las modificaciones y correcciones se conservan como documentos separados para mantener la trazabilidad jurídica.
