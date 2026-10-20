# Incidencias de Asturias

[Volver al índice general](../INCIDENCIAS.md)

Registro de las incidencias detectadas durante la extracción y el cotejo del currículo asturiano. Todas las incidencias de Infantil y Primaria han sido revisadas; las correcciones aprobadas se han aplicado a los JSON.

## Infantil — incidencias revisadas

| Revisada | ID | Materia | Incidencia | Decisión aplicada |
| --- | --- | --- | --- | --- |
| [X] | AS-INF-001 | [Crecimiento en Armonía](../data/es-as/infantil/materias/crecimiento-en-armonia.json) | La introducción publica «La diversidad étnica y cultural posibilita el acceso de niñas y niños acceso a los diversos usos y costumbres sociales». Se repite «acceso». | Se corrige como «posibilita el acceso de niñas y niños a los diversos usos y costumbres sociales». |
| [X] | AS-INF-002 | [Crecimiento en Armonía](../data/es-as/infantil/materias/crecimiento-en-armonia.json) | El desarrollo de la competencia específica 4 contiene «entender que la inclusión es enriquecedora De esta manera». Falta la puntuación entre ambas oraciones. | Se normaliza como «enriquecedora. De esta manera». |
| [X] | AS-INF-003 | [Descubrimiento y Exploración del Entorno](../data/es-as/infantil/materias/descubrimiento-y-exploracion-del-entorno.json) | La introducción contiene «hábitos ecosaludabes». | Se corrige la errata como «hábitos ecosaludables». |
| [X] | AS-INF-004 | [Descubrimiento y Exploración del Entorno](../data/es-as/infantil/materias/descubrimiento-y-exploracion-del-entorno.json) | La introducción dice «Se utilizará los diferentes lenguajes y formas de expresión». El verbo no concuerda con el sujeto plural. | Se normaliza como «Se utilizarán los diferentes lenguajes y formas de expresión». |

## Primaria — incidencias revisadas

| Revisada | ID | Materia | Incidencia | Tratamiento actual o propuesto |
| --- | --- | --- | --- | --- |
| [X] | AS-PRIM-001 | [Educación Física](../data/es-as/primaria/materias/educacion-fisica.json) | En la página 74, el criterio 4.1 del segundo ciclo omite el punto tras el código, aunque el mismo criterio sí lo incluye en los otros ciclos. | Se restituye el punto separador. En el JSON, `codigoOficial` conserva el identificador normalizado `4.1`, sin puntuación terminal, y `texto` contiene el enunciado. |
| [X] | AS-PRIM-002 | [Lengua Castellana y Literatura](../data/es-as/primaria/materias/lengua-castellana-y-literatura.json) | En las páginas 97 y 98, los criterios 6.2 y 7.2 del segundo ciclo omiten el punto tras el código. | Se restituyen los puntos separadores; los códigos normalizados se almacenan como `6.2` y `7.2`. |
| [X] | AS-PRIM-003 | [Lengua Castellana y Literatura](../data/es-as/primaria/materias/lengua-castellana-y-literatura.json) | En la página 100, la cabecera «Competencia específica 9:» usa dos puntos, mientras que las demás emplean punto. | Se normaliza la cabecera como «Competencia específica 9.». |
| [X] | AS-PRIM-004 | [Lengua Extranjera](../data/es-as/primaria/materias/lengua-extranjera.json) | En las páginas 117 y 118, los 17 criterios de las competencias específicas 5 y 6 omiten sistemáticamente el punto tras el código en los tres ciclos. | Se restituyen sistemáticamente los puntos separadores; `codigoOficial` conserva únicamente cada identificador normalizado. |
| [X] | AS-PRIM-005 | [Matemáticas](../data/es-as/primaria/materias/matematicas.json) | En las páginas 130 y 134, los criterios 3.1, 8.1 y 8.2 del tercer ciclo omiten el punto tras el código. | Se restituyen los puntos separadores; los códigos normalizados permanecen sin puntuación terminal. |
| [X] | AS-PRIM-006 | [Lengua Asturiana y Literatura](../data/es-as/primaria/materias/lengua-asturiana-y-literatura.json) | En la página 148, la primera cabecera dice «Competencias Específica 1.» en lugar de «Competencia específica 1.». | Se normaliza la cabecera como «Competencia específica 1.». |
| [X] | AS-PRIM-007 | [Lengua Asturiana y Literatura](../data/es-as/primaria/materias/lengua-asturiana-y-literatura.json) | En las páginas 154 y 155, el criterio 6.1 del primer y del tercer ciclo omite el punto tras el código. | Se restituyen los puntos separadores; el código normalizado se almacena como `6.1`. |
| [X] | AS-PRIM-008 | [Cultura Asturiana](../data/es-as/primaria/materias/cultura-asturiana.json) | En la página 168, tras los descriptores de la competencia específica 1 se omite la cabecera «Criterios de evaluación» y el documento pasa directamente a «Primer ciclo». | Se confirma la omisión editorial del encabezado. Los criterios publicados a continuación se estructuran como criterios de evaluación de la competencia específica 1. |
| [X] | AS-PRIM-009 | [Cultura Asturiana](../data/es-as/primaria/materias/cultura-asturiana.json) | En la página 172, el criterio 2.1 del tercer ciclo omite el punto tras el código. | Se restituye el punto separador; el código normalizado se almacena como `2.1`. |
| [X] | AS-PRIM-010 | [Ciencias Sociales](../data/es-as/primaria/materias/ciencias-sociales.json) | En la página 47 aparece «la Constitución española y La Unión Europea», con mayúscula interna en «La». | Se normaliza como «la Constitución española y la Unión Europea». |
| [X] | AS-PRIM-011 | [Ciencias Sociales](../data/es-as/primaria/materias/ciencias-sociales.json) | En la página 47, el criterio 5.1 del tercer ciclo publica «y de la de Unión Europea». | Se corrige como «y de la Unión Europea». |
| [X] | AS-PRIM-012 | [Educación en Valores Cívicos y Éticos](../data/es-as/primaria/materias/educacion-en-valores-civicos-y-eticos.json) | En la página 82 se publica «a las modelos jurídicos», con discordancia de género. | Se corrige como «a los modelos jurídicos». |
| [X] | AS-PRIM-013 | [Lengua Asturiana y Literatura](../data/es-as/primaria/materias/lengua-asturiana-y-literatura.json) | En la página 161 aparece «la literatura Asturiana», con mayúscula interna en el adjetivo. | Se normaliza como «la literatura asturiana». |
| [X] | AS-PRIM-014 | [Cultura Asturiana](../data/es-as/primaria/materias/cultura-asturiana.json) | En la página 178 se publica «maternidades y paternidades corresponsables Las celebraciones y los ritos de paso», sin puntuación entre ambas ideas. | Se añade el punto: «corresponsables. Las celebraciones y los ritos de paso». |
