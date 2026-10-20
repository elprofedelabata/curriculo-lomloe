# Fuentes oficiales del Principado de Asturias

Corpus normativo de partida para estructurar en JSON los currículos LOMLOE de Educación Infantil, Educación Primaria, Educación Secundaria Obligatoria, Bachillerato y los ámbitos comunes de Ciclos Formativos de Grado Básico en el Principado de Asturias.

## Organización

- `infantil/`: Decreto 56/2022, que establece la ordenación y el currículo de Educación Infantil.
- `primaria/`: Decreto 57/2022, que establece la ordenación y el currículo de Educación Primaria.
- `eso/`: Decreto 59/2022, que establece la ordenación y el currículo de ESO e incluye el anexo V de CFGB.
- `bachillerato/`: Decreto 60/2022, que establece la ordenación y el currículo de Bachillerato.
- `cfgb/`: normativa de Formación Profesional y fuente estatal vigente de los ámbitos comunes de CFGB.
- `actualizaciones/`: disposiciones posteriores que modifican las normas curriculares.
- `catalogo.json`: inventario legible por máquinas con procedencia, URL oficial, número de páginas y SHA-256.

## Particularidades del corpus

El Decreto 104/2025 modifica el Decreto 56/2022 para incorporar una primera aproximación voluntaria a la lengua asturiana o al gallego-asturiano o eonaviego en el segundo ciclo de Educación Infantil. Se conserva separado para aplicar conjuntamente la norma de base y la modificación, sin sustituir ni duplicar el PDF original.

El Decreto 59/2022 incluye en su anexo V el currículo de los ámbitos comunes de CFGB. No obstante, el Decreto 103/2025 identifica como currículo aplicable de Ciencias Aplicadas y Comunicación y Ciencias Sociales el anexo V del Real Decreto 217/2022. Para la futura extracción de estos dos ámbitos se tomará este último como fuente curricular vigente y se conservará la normativa asturiana para la organización y trazabilidad de la oferta.

El proyecto solo convertirá a JSON esos dos ámbitos comunes de CFGB; los módulos profesionales y los proyectos intermodulares quedan fuera del alcance actual.

## Criterios de conservación

- Se guarda el PDF oficial auténtico del BOPA o del BOE, sin editar ni recomprimir.
- El nombre local es estable y descriptivo; la URL original permanece en el catálogo.
- La huella SHA-256 permite comprobar que el archivo no ha cambiado.
- Las modificaciones se conservan como documentos separados para mantener la trazabilidad jurídica.
