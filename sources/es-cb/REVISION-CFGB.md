# Revisión de CFGB de Cantabria

Fecha: 5 de noviembre de 2026. Los **dos JSON están revisados** y las **12 decisiones están confirmadas y aplicadas**. [Registro de Cantabria](../../incidencias/es-cb.md#cfgb--decisiones-revisadas).

## Fuentes y alcance

- [Decreto 73/2022, anexo I-C, pp. 320–352](normativa/eso-bachillerato/2022-07-27-decreto-73-2022-curriculo-eso-bachillerato.pdf#page=320): núcleo curricular de los dos ámbitos.
- [Orden EDU/47/2024, artículo 6 y anexo XXI, pp. 586–626](normativa/cfgb/2024-09-30-orden-edu-47-2024-cfgb.pdf#page=586): base de extracción. Publica el núcleo y los dos componentes alternativos de actividad física; los artículos 2.4 y 6 remiten al decreto y el artículo 19 regula la oferta de adultos y la adaptación.
- [Orden EDU/99/2025, disposición final primera.5, p. 8 y anexo VI, pp. 35–71](normativa/cfgb/2025-10-24-orden-edu-99-2025-modificacion-cfgb.pdf#page=8): actualiza los códigos en la orden de 2024 y reproduce los ámbitos para el título de Fabricación de Elementos Metálicos. Su anexo VI se utiliza como contraste, no como una sustitución general tácita del anexo XXI.

Solo se extraen Ciencias Aplicadas y Comunicación y Ciencias Sociales. Los módulos profesionales, Proyecto intermodular, tutoría e Itinerario personal para la empleabilidad no se convierten en currículos de este conjunto.

El texto de 2024 mantiene el núcleo del decreto de 2022, con pequeñas diferencias de puntuación y redacción. Algunas decisiones restituyen formas del decreto y otras se apoyan en la publicación de 2025. El registro documenta el fundamento de cada modificación editorial confirmada.

## Configuraciones y cursos

| Ámbito o configuración | Cursos representados | Competencias aplicables | Criterios por curso | Saberes por curso |
| --- | --- | ---: | ---: | ---: |
| Ciencias Aplicadas, ordinaria | 1 y 2 | 13: 8 del núcleo y 5 de Educación Físico-Deportiva | 35 | 98 |
| Ciencias Aplicadas, DEVAS | 1 y 2 | 16: 8 del núcleo y 8 de DEVAS | 38 | 154 |
| Comunicación y Ciencias Sociales | 1 y 2 | 8 | 27 | 66 |

Los dos archivos reúnen 29 competencias distintas y seis desarrollos, con 200 criterios y 636 saberes contando repeticiones por curso y alternativa. **Esos totales no son un currículo único exigible a cada alumno.** Debe seleccionarse el curso y la configuración aplicable; no se suman Educación Físico-Deportiva y DEVAS.

La norma publica los contenidos sin repartirlos por curso. El artículo 6 asigna I a primero y II a segundo; se conserva el desarrollo compartido en ambos, sin inventar secuenciación. La cabecera «Cursos tercero y cuarto» que permanece dentro de Educación Físico-Deportiva identifica el currículo de ESO al que se remite, no nuevos cursos de CFGB.

### Condiciones de DEVAS

El [artículo 19.1 y 19.3, p. 9](normativa/cfgb/2024-09-30-orden-edu-47-2024-cfgb.pdf#page=9) establece DEVAS para la oferta autorizada de personas adultas mayores de diecisiete años cuando su historia escolar lo aconseje o que hayan superado una o varias formaciones de Grado C.

El [artículo 19.5, p. 10](normativa/cfgb/2024-09-30-orden-edu-47-2024-cfgb.pdf#page=10) permite que determinados centros soliciten autorización para adaptar el componente de actividad física. Se conservan ambas condiciones de su redacción: menciona no disponer de instalaciones propias o cercanas y/o de profesorado de la especialidad, y añade que no podrá solicitarse la autorización si se dispone de instalaciones o colaboración con instalaciones cercanas. No se transforma esa redacción en una regla automática de elegibilidad ni se presenta la falta de profesorado como autorización suficiente por sí sola.

La Orden de 2025 recoge un supuesto equivalente en su artículo 4.2 para Fabricación de Elementos Metálicos y su [anexo IX, p. 78](normativa/cfgb/2025-10-24-orden-edu-99-2025-modificacion-cfgb.pdf#page=78) contiene la solicitud y autorización. El JSON conserva la base general de 2024 y exige autorización para la oferta o adaptación que activa la variante. No es una optativa de libre elección.

## Identificadores y componentes

Los códigos oficiales por curso, vigentes desde el 1 de noviembre de 2025 por la modificación publicada el día anterior, son:

| Ámbito | Primero | Segundo | Códigos sustituidos |
| --- | --- | --- | --- |
| Ciencias Aplicadas | 3163 | 3164 | 3009 / 3010 |
| Comunicación y Ciencias Sociales | 3161 | 3162 | 3011 / 3012 |

Se guardan en `materia.cursos[].codigoOficial`. La vigencia de la orden base es el 9 de octubre de 2024 y su implantación es en primero en 2024/2025 y segundo en 2025/2026. La codificación actual de 2025 no se atribuye retrospectivamente a años anteriores.

En Ciencias Aplicadas, `ce-1` a `ce-8` identifican el núcleo; `ce-9` a `ce-13`, Educación Físico-Deportiva; y `ce-14` a `ce-21`, DEVAS. Son identificadores internos. `codigoOficial` conserva los números originales repetidos entre componentes, y `componente` permite distinguirlos. Los criterios enlazan mediante `competenciaEspecificaRef`, no por una igualdad supuesta entre el número oficial y el identificador interno.

Los bloques del núcleo A–K conservan sus letras. Los A–F de cada componente de actividad física reciben letras internas L–Q y conservan su letra publicada en el nombre. Los identificadores CAO y CAD distinguen los saberes de las dos configuraciones. Se conserva la jerarquía de viñetas que la fuente marca mediante sangría; cuando conviven encabezados con hijos y elementos sueltos, estos últimos se representan mediante un apartado interno con un único saber idéntico a su título. Los títulos de grupo no se pierden ni se inventan relaciones criterio-saber.

Los descriptores de DEVAS se mantienen según la publicación, incluidas las subdivisiones de Bachillerato del currículo incorporado. No se convierten automáticamente a descriptores de la enseñanza básica. La validación distingue este componente del núcleo y de Educación Físico-Deportiva, cuyas referencias se contrastan con el Perfil de salida de ESO.

## Formato y compatibilidad

El esquema 0.9.0 añade propiedades opcionales: `codigoOficial` por curso, `componente` en competencias y bloques de saberes, y `condicionesAplicacion`, `requiereAutorizacion` y `procedencia` en variantes. No se modifican los requisitos ni los patrones de los formatos anteriores. El catálogo 1.10.0 incorpora los códigos por curso; las condiciones completas y los componentes están en los JSON. No se añaden referencias a incidencias en los archivos curriculares.

## Cotejo

El extractor usa texto y coordenadas de PyMuPDF. El auditor independiente usa Poppler y no importa ni ejecuta el extractor. Comprueba el anexo XXI completo, en orden, con sus introducciones, enunciados, explicaciones, descriptores, criterios, bloques, subapartados y saberes; también verifica todas las copias compartidas por curso y variante.

La edición de 2024 imprime algunos enunciados y sus explicaciones en el mismo párrafo. Se separan por el final del enunciado, cotejado con las materias originales remitidas; se conserva todo el resto como explicación. Es una recuperación de estructura, no una modificación curricular ni una incidencia normativa.

Se han cotejado **651 fragmentos**, con **915 comprobaciones por páginas de procedencia**, cero diferencias de cobertura, cero errores de esquema y cero referencias de descriptor inválidas en su contexto. El contraste independiente de publicaciones comprueba seis cuerpos completos: los dos núcleos frente a 2022 y los cuatro componentes frente a 2025. Solo admite las diferencias de redacción y puntuación documentadas y cuatro familias de compuestos con o sin guion; estas variaciones gráficas no se trasladan como cambios al JSON.

Se han revisado visualmente 13 recortes correspondientes a las 12 decisiones, además de las páginas de estructura y jerarquía. Los códigos vigentes y los supuestos del artículo 19 se comprueban también sobre la extracción de sus páginas legales. Los SHA-256 de los tres PDF se contrastan con el catálogo; los originales se mantienen intactos.

## Reproducción

Requiere Python con PyMuPDF, fontTools y jsonschema, y Poppler (`pdftotext`) en PATH.

```powershell
python scripts/extract-es-cb-cfgb.py --write
python scripts/audit-es-cb-cfgb.py
node scripts/build-site.mjs
node scripts/validate-site.mjs
```

El auditor admite `--packages RUTA` y `--report RUTA`; el extractor, `--diagnostics RUTA`. Los diagnósticos y las justificaciones no se incorporan al contenido curricular.
