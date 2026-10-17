# Incidencias de Aragón

[Volver al índice general](../INCIDENCIAS.md)

Registro de las incidencias detectadas durante la extracción y revisión del currículo aragonés. Las tablas distinguen las incidencias ya resueltas de las que siguen pendientes de revisión manual.

## Infantil — incidencias revisadas

| Revisada | ID | Materia | Incidencia | Decisión aplicada |
| --- | --- | --- | --- | --- |
| [X] | AR-INF-001 | [Crecimiento en Armonía](../data/es-ar/infantil/materias/crecimiento-en-armonia.json) | El desarrollo de la competencia específica 1 contiene «superar restos» en un contexto referido a afrontar desafíos motores. | Se conserva sin cambios la redacción publicada. |
| [X] | AR-INF-002 | [Crecimiento en Armonía](../data/es-ar/infantil/materias/crecimiento-en-armonia.json) | El desarrollo de la competencia específica 2 contiene «vinculadas al desarrollo del “yo” y a conocimiento de las normas». | Se conserva sin cambios la redacción publicada. |
| [X] | AR-INF-003 | [Crecimiento en Armonía](../data/es-ar/infantil/materias/crecimiento-en-armonia.json) | El desarrollo de la competencia específica 2 contiene «la confianza en los demás o que incide». | Se conserva sin cambios la redacción publicada. |
| [X] | AR-INF-004 | [Descubrimiento y Exploración del Entorno](../data/es-ar/infantil/materias/descubrimiento-y-exploracion-del-entorno.json) | La introducción contiene «y partir de la identificación», sin la preposición «a». | Se añade la preposición omitida: «y a partir de la identificación». |
| [X] | AR-INF-005 | [Descubrimiento y Exploración del Entorno](../data/es-ar/infantil/materias/descubrimiento-y-exploracion-del-entorno.json) | La introducción contiene «hábitos ecosaludabes». | Se corrige la errata como «hábitos ecosaludables». |
| [X] | AR-INF-006 | [Descubrimiento y Exploración del Entorno](../data/es-ar/infantil/materias/descubrimiento-y-exploracion-del-entorno.json) | El criterio `3.1` del primer ciclo dice «mostrando respeto hacia ello y hacia los animales», aunque el antecedente es plural («los elementos naturales del entorno»). | Se corrige la concordancia como «mostrando respeto hacia ellos y hacia los animales». |
| [X] | AR-INF-007 | [Descubrimiento y Exploración del Entorno](../data/es-ar/infantil/materias/descubrimiento-y-exploracion-del-entorno.json) | El saber con identificador interno `DEE.2.A.07` imprime dos comas consecutivas entre «calendario» y «antes». | Se elimina la coma duplicada. El identificador es una referencia interna del proyecto, no un código oficial. |

## Primaria — incidencias revisadas

| Revisada | ID | Materia | Incidencia | Decisión aplicada |
| --- | --- | --- | --- | --- |
| [X] | AR-PRIM-001 | [Ciencias Sociales](../data/es-ar/primaria/materias/ciencias-sociales.json) | En la tabla de criterios de la competencia específica 2, tercer ciclo, después de `2.3` aparece un criterio impreso como `6.4`: «Identificar problemas ligados al desarrollo sostenible, analizarlos y extraer conclusiones». Su posición, contenido y secuencia apuntan a que se trata de `2.4`. | Se corrige el código como `2.4` y se mantiene vinculado a `CE.CS.2`. |
| [X] | AR-PRIM-002 | [Educación en Valores Cívicos y Éticos](../data/es-ar/primaria/materias/educacion-en-valores-civicos-y-eticos.json) | La concreción de saberes está rotulada «Primer ciclo de Educación Primaria», aunque la ordenación de la etapa sitúa el área en quinto y sexto curso. | Se interpreta como una referencia errónea y el currículo se modela en el tercer ciclo, de acuerdo con los cursos en los que se imparte. |
| [X] | AR-PRIM-003 | [Lengua Extranjera: Inglés](../data/es-ar/primaria/materias/lengua-extranjera-ingles.json) | La cabecera de la tabla de criterios imprime «Tercer ciclo)», con un paréntesis de cierre sin apertura. | Se corrige como «Tercer ciclo» sin trasladar el signo espurio al JSON. |

## ESO — incidencias revisadas

| Revisada | ID | Materia | Incidencia | Decisión aplicada |
| --- | --- | --- | --- | --- |
| [X] | AR-ESO-001 | [Lengua Extranjera: Alemán](../data/es-ar/eso/materias/lengua-extranjera-aleman.json) | En las páginas 537–539 del PDF, las tablas encabezadas por `CE.LEA.2` a `CE.LEA.6` repiten literalmente los criterios y los códigos `1.1`, `1.2` y, en 3.º y 4.º, `1.3` publicados bajo `CE.LEA.1`. El cotejo con Francés e Inglés confirma la anomalía: en esas materias cada bloque contiene criterios propios numerados `2.x`, `3.x`, `4.x`, `5.x` y `6.x`. | Se reconstruyen los criterios `2.x`–`6.x` con la redacción de las tablas homólogas de Lengua Extranjera: Francés, cuyo bloque válido `CE.LEF.1` coincide literalmente con `CE.LEA.1` en todos los cursos. Se mantienen la vinculación a `CE.LEA.2`–`CE.LEA.6` y las páginas de procedencia alemanas. Es una corrección inferida, no una transcripción literal de esas tablas. |
| [X] | AR-ESO-002 | [Ámbito Científico-Tecnológico](../data/es-ar/eso/materias/ambito-cientifico-tecnologico.json) | La competencia 8 se imprime en la página 972 del PDF como `CE.ACT. 8`, sin punto entre la sigla y el número. | Se normaliza como competencia `8`, de acuerdo con la secuencia `CE.ACT.1`–`CE.ACT.12`. |
| [X] | AR-ESO-003 | [Ámbito Científico-Tecnológico](../data/es-ar/eso/materias/ambito-cientifico-tecnologico.json) | Dos referencias internas de las páginas 973 y 974 del PDF invierten las letras de la sigla: `CE.ATC. 9` y `CE.ATC.1`/`CE.ATC.2`, en lugar de `CE.ACT`. | Se corrigen todas como `CE.ACT.9`, `CE.ACT.1` y `CE.ACT.2` para mantener la nomenclatura uniforme del ámbito. |

## Fuentes para el cotejo

- [Orden de Infantil de Aragón](../sources/es-ar/normativa/infantil/2022-06-13-orden-ecd-853-2022-curriculo-infantil.pdf)
- [Orden de Primaria de Aragón](../sources/es-ar/normativa/primaria/2022-07-18-orden-ecd-1112-2022-curriculo-primaria.pdf)
- [Modificación de Primaria de 2024](../sources/es-ar/normativa/actualizaciones/2024-07-25-orden-ecd-866-2024-modifica-primaria.pdf)
- [Orden de ESO y ámbitos comunes de CFGB de Aragón](../sources/es-ar/normativa/eso/2022-08-02-orden-ecd-1172-2022-curriculo-eso.pdf)
- [Modificación de ESO de 2024](../sources/es-ar/normativa/actualizaciones/2024-07-25-orden-ecd-867-2024-modifica-eso.pdf)
