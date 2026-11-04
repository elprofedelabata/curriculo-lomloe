# Segunda Lengua Extranjera: comparación de publicaciones de Cantabria

Fecha: 4 de noviembre de 2026. Decisión confirmada por el usuario: **CB-ESO-011** del [registro de Cantabria](../../incidencias/es-cb.md).

## Fuentes

- [Decreto 73/2022, anexo I-A](normativa/eso-bachillerato/2022-07-27-decreto-73-2022-curriculo-eso-bachillerato.pdf#page=271): Segunda Lengua Extranjera, páginas 271-292.
- [Corrección de la Orden EDU/40/2022, anexo II](normativa/eso/2022-08-23-correccion-orden-edu-40-2022-optativas.pdf#page=65): Segunda Lengua Extranjera, páginas 65-77.

Las páginas son posiciones del PDF completo. La coincidencia del título no implica que las dos publicaciones contengan el mismo desarrollo curricular.

## Diferencias comprobadas

Las introducciones difieren. Los enunciados de las CE 1, 2, 3, 5 y 6 coinciden al unificar espacios; el de la CE 4 cambia. Las descripciones de las CE 2 a 6 son diferentes incluso unificando los párrafos y los espacios. Los vínculos con descriptores difieren en las seis competencias.

La tabla siguiente reproduce los códigos publicados, incluidas sus erratas, para permitir su comprobación. La columna de la orden conserva «CCL5L» tal como se publica en la CE 2. En el JSON basado en el decreto se propone normalizar «CCCEC1» como «CCEC1» por separado, en CB-ESO-010.

| CE | Descriptores publicados en el decreto | Descriptores publicados en la orden |
| --- | --- | --- |
| 1 | CCL2, CCL3, CCL5, CP1, CP2, STEM2, CD1, CPSAA5, CCEC2 | CCL2, CCL3, CCL5, CP1, CP2, STEM1, STEM2, CD1, CD2, CD3, CPSAA1, CPSAA4, CPSAA5, CC1, CC2, CE1, CE3, CCEC2 |
| 2 | CCL1, CP1, CP2, STEM1, CD2, CPSAA5, CE1, CE3, CCEC3 | CCL1, CCL3, CCL5L, CP1, CP2, STEM1, STEM2, CD1, CD2, CD3, CPSAA1, CPSAA4, CPSAA5, CC1, CC2, CC3, CE1, CE3, CCEC3, CCEC4 |
| 3 | CCL5, CP1, CP2, STEM1, CPSAA3, CC3, CE1 | CCL1, CCL2, CCL5, CP1, CP2, STEM1, STEM2, CD3, CPSAA1, CPSAA3, CC1, CC2, CC3, CE1, CE2, CE3, CCEC3 |
| 4 | CCL5, CP1, CP2, CP3, STEM1, CPSAA1, CPSAA3, CCCEC1 | CCL1, CCL2, CCL3, CCL5, CP1, CP2, CP3, STEM1, STEM2, CD3, CPSAA1, CPSAA3, CC1, CC2, CC3, CE1, CE2, CE3, CCCEC1, CCEC3 |
| 5 | CP2, STEM1, CD2, CPSAA1, CPSAA5 | CP2, CP3, STEM1, STEM2, CD2, CPSAA1, CPSAA3, CPSAA4, CPSAA5, CC1, CC3, CE1, CE2, CE3, CCCEC1, CCEC2, CCEC3 |
| 6 | CCL5, CP3, CPSAA1, CPSAA3, CC3, CCCEC1 | CCL5, CP3, STEM1, CPSAA1, CPSAA3, CC2, CC3, CC4, CE1, CE3, CCCEC1, CCEC3 |

## Criterios

| Grupo publicado | Criterios por versión | Criterios cuyo texto difiere |
| --- | ---: | --- |
| 1.º y 2.º | 15 | 1.2, 2.2, 2.3, 3.1, 3.2, 4.1, 6.2, 6.3 |
| 3.º | 16 | 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 4.1, 4.2, 5.1, 5.2, 5.3, 6.1, 6.2, 6.3 |
| 4.º | 16 | 1.1, 1.3, 2.2, 2.3, 3.1, 3.2, 4.1, 5.1, 5.2, 5.3, 6.3 |

Por ejemplo, el criterio 1.1 del tercer curso se publica así:

- Decreto, página 284: «Extraer y analizar el sentido global y las ideas principales, y seleccionar información pertinente de textos orales, escritos y multimodales sobre temas cotidianos, de relevancia personal próximos a su experiencia, expresados de forma clara y en la lengua estándar a través de diversos soportes.»
- Orden, página 72: «Extraer el sentido global y las ideas principales, y seleccionar información pertinente de textos orales, escritos y multimodales sobre temas cotidianos, de relevancia personal o de interés público próximos a su experiencia, expresados de forma clara y en la lengua estándar a través de diversos soportes.»

La diferencia «Extraer y analizar» / «Extraer» y las menciones al interés público muestran que no se trata únicamente de cambios de maquetación. Los bloques y sus saberes también se han contrastado durante la lectura de las dos publicaciones; el JSON conserva íntegramente los del decreto, sin completar unos con los otros.

## Representación confirmada

Se genera **un único JSON**, [segunda-lengua-extranjera.json](../../data/es-cb/eso/materias/segunda-lengua-extranjera.json), con el anexo I-A del Decreto 73/2022 como base única confirmada por el usuario. Su artículo 6.1 identifica ese anexo como fuente de las competencias, criterios y saberes de las materias. La Orden EDU/40/2022, artículo 3.4, remite tanto al decreto como a su propio anexo II; no establece en ese apartado una regla para resolver la divergencia.

La decisión evita mezclar versiones y mantiene las dos fuentes enlazadas. Es una elección editorial del proyecto, confirmada por el usuario el 4 de noviembre de 2026, y no una corrección oficial de la Administración. El JSON está revisado; se conserva una única materia para el mismo ámbito de aplicación.
