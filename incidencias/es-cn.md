# Incidencias de Canarias

[Volver al índice general](../INCIDENCIAS.md)

Registro de discrepancias detectadas al estructurar el currículo canario. Las erratas de Infantil y Primaria se han normalizado tras la revisión; los identificadores internos del proyecto siguen siendo únicos.

Las páginas indicadas corresponden a la posición dentro del PDF completo, no al número impreso del boletín.

## Infantil — incidencias revisadas

| Revisada | ID | Materia | Incidencia | Decisión aplicada |
| --- | --- | --- | --- | --- |
| [X] | CN-INF-001 | [Crecimiento en Armonía](../data/es-cn/infantil/materias/crecimiento-en-armonia.json) | En el primer ciclo, bloque II de saberes, la página 39 del Decreto 196/2022 enumera tres entradas como `1`, `3` y `3`; falta el `2`. | Se normaliza el primer `3` como `2` en `numeracionFuente`, con lo que la secuencia queda `1`, `2`, `3`. Los identificadores internos posicionales permanecen únicos. |
| [X] | CN-INF-002 | [Descubrimiento y Exploración del Entorno](../data/es-cn/infantil/materias/descubrimiento-y-exploracion-del-entorno.json) | En el primer ciclo, bloque de la competencia específica 2, la página 57 vincula la competencia clave `CPSSAA`, en vez de la sigla habitual `CPSAA`. | Se normaliza la referencia a `CPSAA` en `competenciasClaveRefs`. |

## Primaria — incidencias revisadas

| Revisada | ID | Materia | Incidencia | Decisión aplicada |
| --- | --- | --- | --- | --- |
| [X] | CN-PRIM-001 | [Conocimiento del Medio Natural, Social y Cultural](../data/es-cn/primaria/materias/conocimiento-del-medio-natural-social-y-cultural.json) | En el segundo ciclo, el criterio `1.2` de la página 60 carece del punto tras el número. | Se normaliza su forma escrita como `1.2.`. En JSON, `codigoOficial` conserva únicamente el código `1.2`, como en todos los demás criterios, y el enunciado queda separado. |
| [X] | CN-PRIM-002 | [Lengua Extranjera](../data/es-cn/primaria/materias/lengua-extranjera.json) | En el segundo ciclo, el criterio `3.2` de la página 263 carece del punto tras el número. | Se normaliza su forma escrita como `3.2.`. En JSON, `codigoOficial` conserva únicamente el código `3.2` y el enunciado queda separado. |
| [X] | CN-PRIM-003 | [Educación en Valores Cívicos y Éticos](../data/es-cn/primaria/materias/educacion-en-valores-civicos-y-eticos.json) | En el tercer ciclo, los criterios `2.3` y `2.4` de la página 188 carecen del punto tras el número. | Se normaliza su forma escrita como `2.3.` y `2.4.`. En JSON, `codigoOficial` conserva los códigos `2.3` y `2.4`, con los enunciados separados. |
| [X] | CN-PRIM-004 | [Lengua Castellana y Literatura](../data/es-cn/primaria/materias/lengua-castellana-y-literatura.json) | En el primer ciclo, criterio `7.2` de la página 209, aparece `CCE3`, sigla que no corresponde a ningún descriptor habitual. La misma columna incluye `CCEC3` y la cabecera de la competencia específica incluye `CC3`. | Se normaliza el descriptor del criterio `7.2` como `CC3`, de acuerdo con la fila de la competencia específica 7. |
| [X] | CN-PRIM-005 | [Lengua Extranjera](../data/es-cn/primaria/materias/lengua-extranjera.json) | En la página 245 del PDF del Decreto 211/2022, la explicación de CPSAA enumera cinco dimensiones del alumnado y a continuación dice `Abordar estas tres dimensiones`. El ODT de apoyo y el JSON ya dicen `cinco`. | Corrección confirmada y aplicada: se mantiene `Abordar estas cinco dimensiones` en el JSON y se hace explícita la normalización en el extractor, de acuerdo con las cinco dimensiones enumeradas. |

## ESO — incidencia revisada

| Revisada | ID | Materia | Incidencia | Decisión aplicada |
| --- | --- | --- | --- | --- |
| [X] | CN-ESO-001 | [Segunda Lengua Extranjera](../data/es-cn/eso/materias/segunda-lengua-extranjera.json) | En los cuatro cursos, el PDF del Decreto 30/2023 intercambia los textos de los criterios `5.1` y `6.1`: la CE5 trata el repertorio lingüístico y el aprendizaje, pero recibe el criterio sobre diversidad cultural; la CE6 trata la diversidad cultural, pero recibe el criterio sobre progresos de aprendizaje. Los descriptores de las cabeceras y de esos criterios también están cruzados. Se observa en las páginas 802–803, 813–814, 824–826 y 836–838. El ODT institucional ya alinea los textos de los criterios con sus competencias, aunque conserva el intercambio de descriptores. | Corrección confirmada y aplicada: `5.1` recoge los progresos de aprendizaje y `6.1` la diversidad cultural, siguiendo el ODT y las explicaciones de los bloques. Se intercambian también los descriptores de CE5/CE6 en las fichas de competencia, bloques competenciales y criterios, para mantener la vinculación coherente con sus enunciados. Decisión confirmada en la revisión manual. |

## Bachillerato — incidencias revisadas

| Revisada | ID | Materia | Incidencia | Decisión aplicada |
| --- | --- | --- | --- | --- |
| [X] | CN-BACH-001 | [Filosofía](../data/es-cn/bachillerato/materias/filosofia.json) | En el bloque III de saberes de primero, entrada `1.8` de la página 1263 del PDF del Decreto 30/2023, aparece un punto adicional pegado a la primera palabra: `1.8. .Búsqueda de información sobre la condición social del ser humano`. | Corrección confirmada y aplicada: eliminar el punto sobrante antes de `Búsqueda`, manteniendo la numeración `1.8`. Decisión confirmada en la revisión manual. |
| [X] | CN-BACH-002 | [Geografía](../data/es-cn/bachillerato/materias/geografia.json) | El criterio `5.1` de segundo, página 1340 del PDF del Decreto 30/2023, dice: `Investigar el sistema de relaciones económicas globalizadas y los sectores económicos, y planteando soluciones razonables.` El gerundio tras la conjunción no coordina con el infinitivo inicial. | Corrección confirmada y aplicada: `Investigar el sistema de relaciones económicas globalizadas y los sectores económicos y plantear soluciones razonables.` Se coordina `plantear` con `Investigar` y se elimina la coma anterior a `y`. Decisión confirmada en la revisión manual. |
| [X] | CN-BACH-003 | [Técnicas de Laboratorio](../data/es-cn/bachillerato/materias/tecnicas-de-laboratorio.json) | En el saber `5` del bloque III de primero, página 421 del PDF del Decreto 78/2025, aparece `proyectos divulgación científica`, sin la preposición que vincula el tipo de proyecto. | Corrección confirmada y aplicada: `proyectos de divulgación científica`. Se restituye únicamente `de` y se mantiene el resto del saber. Decisión confirmada en la revisión manual. |

## CFGB — incidencias revisadas

Todas las páginas de esta sección remiten al PDF completo del Decreto 9/2023. Las diez decisiones están confirmadas y aplicadas en los JSON revisados; en 005 y 006 se conserva la redacción publicada.

| Revisada | ID | Materia | Incidencia | Decisión aplicada |
| --- | --- | --- | --- | --- |
| [X] | CN-CFGB-001 | [Ciencias Aplicadas](../data/es-cn/cfgb/materias/ciencias-aplicadas.json) | La competencia específica 2 termina con `comprobando su validez` en el apartado 5 (página 23) y con `asegurando su validez` en la tabla del bloque competencial (página 32). | Se toma el enunciado de la tabla, `asegurando su validez`, que acompaña a los criterios de evaluación. Se aplica a la competencia común de ambos cursos. |
| [X] | CN-CFGB-002 | [Ciencias Aplicadas](../data/es-cn/cfgb/materias/ciencias-aplicadas.json) | La competencia específica 5 del apartado 5 (página 23) se refiere al `entorno natural, social y profesional`. La tabla (página 36) añade `en formato analógico y digital` y termina con `entorno social y profesional`, omitiendo `natural`. | Se reproduce íntegramente el enunciado de la tabla en ambos cursos, sin combinar las dos versiones. |
| [X] | CN-CFGB-003 | [Ciencias Aplicadas](../data/es-cn/cfgb/materias/ciencias-aplicadas.json) | El saber de primero sobre los números, bloque B, página 49, dice `algunos número irracionales`. | Se normaliza como `algunos números irracionales` en `CA.1.B.1.1`. |
| [X] | CN-CFGB-004 | [Ciencias Aplicadas](../data/es-cn/cfgb/materias/ciencias-aplicadas.json) | El saber de primero sobre las propiedades de las expresiones algebraicas, bloque E, página 51, termina en `conmutativa y distributiva` sin punto final. | Se añade el punto final en `CA.1.E.2.2`, manteniendo el resto del texto. |
| [X] | CN-CFGB-005 | [Ciencias Aplicadas](../data/es-cn/cfgb/materias/ciencias-aplicadas.json) | En Actividad Física y Bienestar Emocional, bloque B, página 59, aparece `Prevención de la actividad física: descripción de las situaciones de riesgo…`. | Se conserva la redacción publicada, `Prevención de la actividad física: …`, en `CA.1.M.3`, por decisión de la revisión manual. |
| [X] | CN-CFGB-006 | [Ciencias Aplicadas](../data/es-cn/cfgb/materias/ciencias-aplicadas.json) | En el mismo bloque y página 59 aparece `Empleo de técnicas específicas e indicios de accidentes cardiovasculares (RCP, maniobra de Heimlich, señales de ictus y similares).` | Se conserva la redacción publicada, `Empleo de técnicas específicas e indicios de accidentes cardiovasculares…`, en `CA.1.M.5`, por decisión de la revisión manual. |
| [X] | CN-CFGB-007 | [Comunicación y Ciencias Sociales](../data/es-cn/cfgb/materias/comunicacion-y-ciencias-sociales.json) | Los descriptores de la competencia específica 2 incluyen `CCEC1` en el apartado 5 (página 67), pero la tabla del bloque competencial (página 77) y los criterios `2.1`, `2.2` y `2.3` no lo incluyen. | Se toman los descriptores de la tabla y se omite `CCEC1` en la ficha de la competencia y el bloque competencial. Se mantienen los descriptores publicados en cada criterio. |
| [X] | CN-CFGB-008 | [Comunicación y Ciencias Sociales](../data/es-cn/cfgb/materias/comunicacion-y-ciencias-sociales.json) | El criterio `2.2`, página 77, contiene `la lucha contra el cambio el climático`. | Se elimina el segundo `el` y se deja `la lucha contra el cambio climático` en ambos cursos. |
| [X] | CN-CFGB-009 | [Comunicación y Ciencias Sociales](../data/es-cn/cfgb/materias/comunicacion-y-ciencias-sociales.json) | El criterio `5.5`, página 82, dice `realizando exposiciones orales relacionados con temas de interés profesional`. El adjetivo no concuerda con `exposiciones`. | Se normaliza como `exposiciones orales relacionadas con temas de interés profesional` en ambos cursos. |
| [X] | CN-CFGB-010 | [Comunicación y Ciencias Sociales](../data/es-cn/cfgb/materias/comunicacion-y-ciencias-sociales.json) | En los saberes de segundo, bloque A, apartado III, página 93, se escribe `El reconocimiento de los derechos LTGBQ+`. El orden de las letras T y G está invertido respecto a la sigla habitual en español. | Se normaliza como `LGTBQ+` en `CCS.2.A.3.12`, reordenando las letras sin añadir ni eliminar ninguna. |
