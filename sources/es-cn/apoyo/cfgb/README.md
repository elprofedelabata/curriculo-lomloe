# Apoyo a la extracción de CFGB de Canarias

El [portal institucional de currículos de CFGB](https://www.gobiernodecanarias.org/educacion/web/formacion_profesional/ensenanzas/fpgb/curriculos_fpgb/) publica el ODT del anexo 1. Se archiva como apoyo para leer las tablas; la referencia normativa es el [PDF completo del Decreto 9/2023](../../normativa/cfgb/2023-01-26-decreto-9-2023-curriculo-cfgb.pdf).

| Ámbito | Páginas del PDF completo | Competencias | Criterios 1.º / 2.º | Entradas de saberes 1.º / 2.º |
| --- | --- | ---: | ---: | ---: |
| Ciencias Aplicadas | 16–60 | 11 | 34 / 20 | 65 / 58 |
| Comunicación y Ciencias Sociales | 61–98 | 8 | 26 / 26 | 88 / 90 |

Los dos JSON están extraídos, cotejados con el BOC y revisados. Las diez decisiones del [registro de Canarias](../../../../incidencias/es-cn.md) están confirmadas: se aplican las ocho propuestas aprobadas y se conserva la redacción publicada en 005 y 006. Las cifras cuentan entradas estructuradas, incluidos los epígrafes que encabezan sublistas; los elementos comunes se representan en ambos cursos.

## Representación

- Las competencias, criterios y descriptores se toman de las tablas de bloques competenciales. La elección de esas versiones frente a las del apartado narrativo está confirmada y documentada en el registro.
- Actividad Física y Bienestar Emocional forma parte de Ciencias Aplicadas solo en primero. En ese curso se incluyen CE9–CE11 y sus cuatro bloques de saberes.
- Los bloques A-K de Ciencias Aplicadas mantienen sus letras. Los bloques A-D de Actividad Física se identifican internamente como L-O para evitar colisiones; el nombre de cada bloque conserva la letra de la fuente.
- Las siglas de ámbito y los identificadores individuales de saberes son internos. `codigoOficial` es `null` para estos saberes y no se inventa `numeracionFuente`.
- La fuente declara orientativa y no cronológica la distribución de saberes. `cursoOrientativo` conserva las columnas o epígrafes que sugieren primero, segundo o ambos. Los bloques comunes de lengua castellana y extranjera, sin división por cursos, se representan en ambos desarrollos.
- Se conservan las explicaciones de los bloques competenciales y todos los párrafos introductorios, objetivos y orientaciones metodológicas. Las entradas guardadas como `list-header` en el ODT también se extraen.

La [Resolución de 30 de octubre de 2024](https://www.gobiernodecanarias.org/boc/2024/226/3747.html), apartado segundo del anexo II, sigue remitiendo al Decreto 9/2023 dentro de las instrucciones del nuevo sistema de FP. Esta extracción aborda los dos ámbitos comunes de su anexo 1; los módulos profesionales quedan fuera del alcance del proyecto.

## Repetir la extracción y el cotejo

El origen, fecha y huella del ODT se recogen en [manifest.json](manifest.json). El extractor requiere PyMuPDF; la auditoría requiere además Poppler (`pdftotext`) y `jsonschema`.

```powershell
python scripts/extract-es-cn-cfgb.py
python scripts/audit-es-cn-cfgb.py
```

La auditoría comprueba el esquema, identificadores, referencias, cursos, cobertura de los párrafos y correspondencia textual con el BOC. Usa el área visible del PDF para fijar las páginas de procedencia: la capa de texto completa contiene restos de tablas fuera de página. Siete entradas partidas o intercaladas se han cotejado visualmente y se protegen mediante huellas en el auditor para exigir un nuevo cotejo si cambia su texto.
