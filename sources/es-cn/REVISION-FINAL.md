# Revisión final de Canarias

Fecha: 3 de noviembre de 2026. Las 21 decisiones de incidencias están confirmadas. Las reparaciones de extracción y la incorporación de las concreciones del silbo gomero están aplicadas.

## Resultado

Canarias dispone de 109 JSON: 3 de Infantil, 10 de Primaria, 27 de ESO y Diversificación, 67 de Bachillerato y 2 de CFGB. Los 109 documentos están revisados, incluidas las dos concreciones de Lengua para el silbo gomero; el usuario ha confirmado el cierre de Canarias tras el cotejo final.

Los 109 documentos cumplen el esquema. No se han encontrado identificadores duplicados dentro de un documento, referencias inexistentes ni diferencias entre los cursos o ciclos declarados y los desarrollos. Las nueve fuentes normativas archivadas coinciden con las huellas del catálogo. La web y el catálogo se generan y validan con 507 documentos curriculares del proyecto y 239 incidencias, de las que 21 corresponden a Canarias y están revisadas.

Las cinco diferencias de transcripción están corregidas tanto en los JSON como en el extractor. La reconstrucción de Matemáticas recuperó seis enunciados superiores: el cotejo inicial había identificado cinco; el sexto, de cálculo mental, estaba enmascarado por un texto repetido en otro ciclo. Se conservan los identificadores y textos de los 244 saberes anteriores, y el documento completo contiene ahora 250 entradas.

Las secciones siguientes documentan los hallazgos resueltos. Los fallos de extracción no se han añadido al registro de erratas normativas.

## Diferencias de transcripción en Primaria

La referencia es el [PDF del Decreto 211/2022](normativa/primaria/2022-11-10-decreto-211-2022-curriculo-primaria.pdf). Las páginas son posiciones dentro del PDF completo.

| Materia y localización | Redacción del JSON | Redacción del PDF recuperada | Página |
| --- | --- | --- | ---: |
| [Conocimiento del Medio](../../data/es-cn/primaria/materias/conocimiento-del-medio-natural-social-y-cultural.json), descripción de CE6 | `de manera que que comprenda` | `de manera que comprenda` | 41 |
| [Educación Emocional y para la Creatividad](../../data/es-cn/primaria/materias/educacion-emocional-y-para-la-creatividad.json), introducción | `Competencia en conciencia y expresiones culturales (CEC)` | `Competencia en conciencia y expresiones culturales (CCEC)` | 119 |
| Educación Emocional y para la Creatividad, primer ciclo, título del bloque I | `percepción, identificación, validación y aceptación` | `percepción, identificación, comprensión y aceptación` | 128 |
| [Educación en Valores Cívicos y Éticos](../../data/es-cn/primaria/materias/educacion-en-valores-civicos-y-eticos.json), descripción de CE3 | `archipélago canario` | `archipiélago canario` | 183 |
| [Lengua Extranjera](../../data/es-cn/primaria/materias/lengua-extranjera.json), introducción | `violencia o discrimación` | `violencia o discriminación` | 243 |

Estas diferencias procedían del ODT de apoyo. Las cinco están corregidas en los JSON y en el extractor, y el cotejo posterior con el BOC no presenta diferencias.

## Enunciados omitidos de Matemáticas

En [Matemáticas](../../data/es-cn/primaria/materias/matematicas.json), el lector de sublistas conservaba los hijos, pero omitía el enunciado superior. Los seis enunciados siguientes se han recuperado del ODT y contrastado con el PDF. La numeración de esta tabla es la numeración local publicada, no un identificador oficial completo del proyecto.

| Ciclo | Bloque y número publicado | Enunciado recuperado | Página |
| --- | --- | --- | ---: |
| Segundo | I, 2.2 | Empleo de estrategias de cálculo para la suma. | 304 |
| Segundo | I, 2.3 | Empleo de estrategias de cálculo para la resta. | 304 |
| Segundo | I, 2.10 | Empleo de estrategias de cálculo mental. | 305 |
| Segundo | I, 2.12 | Interpretación de la división como reparto y como agrupamiento de números naturales, con flexibilidad y sentido, contextualizados (al menos dos algoritmos diferentes para la división). | 305 |
| Tercero | I, 2.2 | Comprensión y uso de estrategias de cálculo con números naturales y decimales en contextos multiplicativos (al menos dos algoritmos diferentes para la multiplicación). | 316 |
| Tercero | I, 2.3 | Utilización de algoritmos flexibles para la división, usando al menos dos diferentes, analizando el significado del resto en situaciones contextualizadas. | 317 |

La reparación de `saber_tree`, en `scripts/extract-es-cn-primaria.py`, recorre las sublistas conservando también los enunciados superiores. Sus identificadores nuevos usan números internos libres; los 244 anteriores se conservan. `numeracionFuente` guarda la jerarquía publicada del bloque A, como `2.2` y `2.2.1`, separada de los identificadores internos.

## Normalización confirmada del documento normativo

Está revisada como **CN-PRIM-005** en [incidencias de Canarias](../../incidencias/es-cn.md).

En la página 245, la introducción de Lengua Extranjera enumera cinco dimensiones del alumnado —agente social, aprendiente autónomo, hablante intercultural, sujeto emocional y creativo, y consciente y reflexivo— y a continuación dice `Abordar estas tres dimensiones`. El ODT de apoyo y el JSON ya dicen `cinco`. La normalización está confirmada y es explícita en el extractor. Segunda Lengua Extranjera dice `Abordar estas dimensiones`, sin numeral, y no necesita este cambio.

## Concreciones curriculares incorporadas: silbo gomero

El [Decreto 24/2026, de 9 de marzo](normativa/primaria-eso/2026-03-09-decreto-24-2026-lenguaje-silbado-gomera.pdf), publicado el 17 de marzo de 2026, contiene dos desarrollos que ya están extraídos:

- Anexo I: [concreción de Lengua de Primaria](../../data/es-cn/primaria/materias/lengua-castellana-y-literatura-silbo-gomero.json), tres ciclos y 21 criterios.
- Anexo II: [concreción de Lengua de ESO](../../data/es-cn/eso/materias/lengua-castellana-y-literatura-silbo-gomero.json), cuatro cursos y 28 criterios.

Los artículos 1 y 2, páginas 6–7, establecen su relación con Lengua y su alcance: impartición preceptiva en los centros de La Gomera y facultativa, mediante autorización, en las demás islas. Entró en vigor el 18 de marzo de 2026. El PDF queda archivado e incorporado al catálogo de fuentes, con sus 60 páginas y huella SHA-256.

Se representan en documentos complementarios con el campo opcional `concrecionCurricular`: `materiaBaseRef` los vincula a Lengua de su etapa, y `aplicacion` conserva el alcance preceptivo y facultativo y la autorización para la extensión facultativa. Los veinte saberes comunes de cada anexo se reproducen por ciclo o curso sin atribuirles una secuenciación que la fuente no contiene. Su estado es revisado tras la confirmación del cierre por el usuario. La diferencia del ODT `iniciaciándose` se ajustó al BOC, que dice `iniciándose`.

Fuente oficial: [publicación del Decreto 24/2026 en el BOC](https://www.gobiernodecanarias.org/boc/2026/052/853.html).

## Comprobaciones realizadas

- Validación de los 109 documentos con el esquema común y comprobación de identificadores, referencias, procedencia y cobertura de cursos y ciclos.
- Cotejo inicial de 8025 fragmentos de Infantil, Primaria y ESO: introducciones, enunciados y descripciones de competencias, criterios, explicaciones, títulos y saberes. Se distinguen las normalizaciones ya aprobadas de los restos de paginación y firmas electrónicas.
- Comprobación independiente de 3326 párrafos de listas de los ODT de Primaria y ESO. La comprobación por ciclo permitió recuperar los seis enunciados superiores de Matemáticas.
- Auditoría completa de las 67 materias de Bachillerato: sin diferencias nuevas de texto, numeración, estructura ni cobertura de saberes.
- Auditoría completa de CFGB: esquema y cotejo correctos, incluidas las decisiones de conservar la redacción de CN-CFGB-005 y 006.
- Revisión visual de los fragmentos que la capa de texto del PDF intercala con otras celdas o páginas. Las explicaciones de ACT de 3.º, CE4, y ALS de 4.º, CE7, coinciden con las páginas 71 y 45 del PDF de Diversificación. No se consideran incidencias.
- Búsqueda de normativa y contraste con los portales oficiales; se detectó el Decreto 24/2026, ausente del inventario anterior.

La comprobación posterior a las reparaciones coteja 2328 fragmentos de Primaria y de las nuevas concreciones, sin diferencias de texto ni numeración y sin omisiones de los ODT. Puede repetirse con `python scripts/audit-es-cn-correcciones.py` (requiere jsonschema, PyMuPDF y Poppler).

## Estado de cierre

Los 109 documentos de las cinco etapas están revisados, incluidas las dos concreciones del silbo gomero. CN-PRIM-005 y las veinte decisiones anteriores están cerradas. El usuario ha confirmado el cierre de Canarias tras el cotejo final. No quedan tareas de revisión ni reparaciones pendientes de este informe; el README y la checklist reflejan Canarias completada.
