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
| [X] | AR-ESO-004 | [Segunda Lengua Extranjera: Francés](../data/es-ar/eso/materias/segunda-lengua-extranjera-frances.json) | La disposición veintidós de la Orden ECD/867/2024 anuncia que se modifica «Segunda Lengua Extranjera (Francés)», pero el currículo sustitutivo adjunto conserva la cabecera «LENGUA EXTRANJERA: FRANCÉS» y utiliza el prefijo `CE.LEF`, en lugar de `CE.SLEF` como la orden de 2022. | Se aplica el currículo sustitutivo a Segunda Lengua Extranjera: Francés, atendiendo a la identificación expresa del apartado dispositivo. Lengua Extranjera: Francés conserva su currículo de 2022. |

## Bachillerato — incidencias revisadas

| Revisada | ID | Materia | Incidencia | Decisión aplicada |
| --- | --- | --- | --- | --- |
| [X] | AR-BACH-001 | [Biología](../data/es-ar/bachillerato/materias/biologia.json) | En la página 121 del PDF, después del criterio `5.1` aparece el enunciado de la competencia 6 y, a continuación, los criterios `6.1` y `6.2`, pero se ha omitido la cabecera `CE.B.6` que sí encabeza los demás bloques de la tabla. | Se interpreta que ambos criterios pertenecen a la competencia específica 6, de acuerdo con su numeración y con la secuencia de la tabla. El enunciado repetido no se incorpora al texto del criterio `5.1`. |
| [X] | AR-BACH-002 | [Dibujo Técnico](../data/es-ar/bachillerato/materias/dibujo-tecnico.json) | En la página 262 del PDF, el enunciado de la competencia 2 se rotula «CE.D.2», aunque la materia usa la sigla «DT» y su bloque de criterios se publica como «CE.DT.2». | Se interpreta «CE.D.2» como una errata y se modela como competencia 2 de Dibujo Técnico, manteniendo la nomenclatura «DT» del resto del currículo. |
| [X] | AR-BACH-003 | [Educación Física y Vida Activa](../data/es-ar/bachillerato/materias/educacion-fisica-y-vida-activa.json) | En la página 382 del PDF, la competencia 2 se imprime como «CE.EFVA 2», sin punto entre la sigla y el número. | Se normaliza como competencia 2 de Educación Física y Vida Activa, de acuerdo con «CE.EFVA.1» y con la tabla de criterios. |
| [X] | AR-BACH-004 | [Lenguas Propias de Aragón: Catalán](../data/es-ar/bachillerato/materias/lenguas-propias-de-aragon-catalan.json) | La cabecera de la materia en la página 907 del PDF dice «LENGUA PROPIAS DE ARAGÓN: CATALÁN», con discordancia de número. | Se usa la denominación «Lenguas Propias de Aragón: Catalán», coherente con el resto de la orden y con el plan de estudios. |
| [X] | AR-BACH-005 | [Proyecto de Investigación e Innovación Integrado](../data/es-ar/bachillerato/materias/proyecto-de-investigacion-e-innovacion-integrado.json) | La cabecera del currículo en la página 1157 del PDF dice «PROYECTO DE INNOVACIÓN E INVESTIGACIÓN INTEGRADO», invirtiendo el orden de «Investigación» e «Innovación» respecto de la denominación usada en el plan de estudios. La sustitución de 2024 conserva esa cabecera. | Se mantiene «Proyecto de Investigación e Innovación Integrado», que es la denominación de la materia en la distribución horaria y en el articulado. |
| [X] | AR-BACH-006 | [Cultura y Patrimonio de Aragón](../data/es-ar/bachillerato/materias/cultura-y-patrimonio-de-aragon.json) | En la página 18 del PDF de modificación de 2024 aparece directamente el enunciado «CE.CPA.6» después del desarrollo de la competencia 5, sin el encabezado narrativo «Competencia específica… 6» que precede a las demás. | Se incorpora como competencia específica 6 porque conserva su código propio y la tabla incluye el bloque «CE.CPA.6» con criterios «6.x». |
| [X] | AR-BACH-007 | [Historia del Mundo Contemporáneo](../data/es-ar/bachillerato/materias/historia-del-mundo-contemporaneo.json) | En la página 130 del PDF de modificación de 2024 aparece directamente el enunciado «CE.HMC.6» después del desarrollo de la competencia 5, sin el encabezado narrativo «Competencia específica… 6». | Se incorpora como competencia específica 6 porque conserva su código propio y la tabla incluye el bloque «CE.HMC.6» con criterios «6.x». |
| [X] | AR-BACH-008 | [Proyecto de Investigación e Innovación Integrado](../data/es-ar/bachillerato/materias/proyecto-de-investigacion-e-innovacion-integrado.json) | En la página 167 del PDF de modificación de 2024, la cabecera del cuarto bloque de criterios dice «CE.UE.4», sigla correspondiente a Unión Europea, aunque el enunciado y los criterios «4.x» pertenecen al Proyecto Integrado. | Se interpreta como una errata de copia y pega y se vinculan los criterios «4.x» a la competencia 4 del Proyecto Integrado («CE.PI.4»). |
| [X] | AR-BACH-009 | [Cultura Audiovisual](../data/es-ar/bachillerato/materias/cultura-audiovisual.json) | Tras la descripción de los bloques de saberes, la página 196 del PDF comienza directamente la tabla de concreción sin publicar el rótulo «III.2. Concreción de los saberes básicos». | Se interpreta la tabla como la concreción curricular de Cultura Audiovisual y se extraen sus cuatro bloques completos. |
| [X] | AR-BACH-010 | [Anatomía Aplicada](../data/es-ar/bachillerato/materias/anatomia-aplicada.json) | En la página 107 del PDF, la tabla del bloque E salta de «E.2. Sistema endocrino» a «E.4. Hábitos saludables de los sistemas coordinadores»; no publica un apartado E.3 ni contenido asociado a ese código. Las órdenes modificativas de 2024 y 2025 tampoco corrigen ni sustituyen este currículo. | Se confirma como una omisión no subsanada. Se conserva la numeración publicada y no se incorpora un apartado E.3 ni contenido que no figure en la normativa. |

## CFGB — incidencias revisadas

| Revisada | ID | Materia | Incidencia | Decisión aplicada |
| --- | --- | --- | --- | --- |
| [X] | AR-CFGB-001 | [Ciencias Aplicadas](../data/es-ar/cfgb/materias/ciencias-aplicadas.json) | En la página 1094 del PDF de la Orden ECD/1172/2022, una referencia interna de la competencia 1 aparece como `C3.CCAA.8`, aunque el resto del currículo utiliza el prefijo `CE.CCAA`. | Se normaliza como `CE.CCAA.8`, interpretando el carácter `3` como una errata tipográfica. |
| [X] | AR-CFGB-002 | [Ciencias Aplicadas](../data/es-ar/cfgb/materias/ciencias-aplicadas.json) | En la página 1100, el criterio `4.1` concatena tras su primera oración el texto completo del criterio `3.2`, y el criterio `4.2` reproduce el texto de `3.3`. El Real Decreto 217/2022 publica para la competencia 4 dos criterios propios y coherentes con su enunciado. | Se reconstruyen `4.1` y `4.2` con la redacción del anexo V del Real Decreto 217/2022 y se atribuye su procedencia a esa fuente estatal. |
| [X] | AR-CFGB-003 | [Comunicación y Ciencias Sociales](../data/es-ar/cfgb/materias/comunicacion-y-ciencias-sociales.json) | En la introducción de la página 1119 se alude a los «retos del siglo XX», aunque el contexto curricular y el Perfil de salida se refieren a los retos actuales del siglo XXI. | Se corrige la referencia como «retos del siglo XXI». |
| [X] | AR-CFGB-004 | [Comunicación y Ciencias Sociales](../data/es-ar/cfgb/materias/comunicacion-y-ciencias-sociales.json) | El criterio `2.2`, en la página 1125, contiene la expresión «la lucha contra el cambio el climático». | Se elimina el artículo duplicado y se normaliza como «la lucha contra el cambio climático». |

## Fuentes para el cotejo

- [Orden de Infantil de Aragón](../sources/es-ar/normativa/infantil/2022-06-13-orden-ecd-853-2022-curriculo-infantil.pdf)
- [Orden de Primaria de Aragón](../sources/es-ar/normativa/primaria/2022-07-18-orden-ecd-1112-2022-curriculo-primaria.pdf)
- [Modificación de Primaria de 2024](../sources/es-ar/normativa/actualizaciones/2024-07-25-orden-ecd-866-2024-modifica-primaria.pdf)
- [Orden de ESO y ámbitos comunes de CFGB de Aragón](../sources/es-ar/normativa/eso/2022-08-02-orden-ecd-1172-2022-curriculo-eso.pdf)
- [Modificación de ESO de 2024](../sources/es-ar/normativa/actualizaciones/2024-07-25-orden-ecd-867-2024-modifica-eso.pdf)
- [Orden de Bachillerato de Aragón](../sources/es-ar/normativa/bachillerato/2022-08-03-orden-ecd-1173-2022-curriculo-bachillerato.pdf)
- [Modificación de Bachillerato de 2024](../sources/es-ar/normativa/actualizaciones/2024-07-25-orden-ecd-886-2024-modifica-bachillerato.pdf)
- [Orden de CFGB de Aragón](../sources/es-ar/normativa/cfgb/2024-07-25-orden-ecd-841-2024-curriculos-cfgb.pdf)
- [Real Decreto 217/2022, anexo V](https://www.boe.es/buscar/pdf/2022/BOE-A-2022-4975-consolidado.pdf)
