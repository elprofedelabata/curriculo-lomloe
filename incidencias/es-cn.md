# Incidencias de Canarias

[Volver al índice general](../INCIDENCIAS.md)

Registro de discrepancias detectadas al estructurar el currículo canario. Las erratas de Infantil y Primaria se han normalizado tras la revisión; los identificadores internos del proyecto siguen siendo únicos.

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
