# Concreciones curriculares del silbo gomero

Los dos ODT institucionales se usan para recuperar las tablas y las listas de los anexos I y II del [Decreto 24/2026](../../normativa/primaria-eso/2026-03-09-decreto-24-2026-lenguaje-silbado-gomera.pdf). La referencia normativa es el PDF del BOC; la procedencia y las huellas de los ODT se conservan en [manifest.json](manifest.json).

| Etapa | Anexo y páginas del PDF completo | Desarrollo | Criterios | Saberes |
| --- | --- | --- | ---: | ---: |
| Primaria | I, 8–29 | Tres ciclos | 7 por ciclo, 21 en total | 20 comunes, representados en los tres ciclos |
| ESO | II, 30–60 | Cuatro cursos | 7 por curso, 28 en total | 20 comunes, representados en los cuatro cursos |

Los JSON son desarrollos complementarios de Lengua Castellana y Literatura. El campo opcional `concrecionCurricular` los vincula al documento base y conserva las condiciones de aplicación: preceptiva en La Gomera, facultativa en las demás islas y con autorización para esta extensión facultativa. Las condiciones proceden de los artículos 1 y 4, páginas 6–7. El carácter `obligatoria` de `materia.cursos` o `materia.ciclos` se refiere a Lengua, no a una materia independiente de silbo.

Se mantienen las cinco competencias publicadas (1, 2, 3, 9 y 10), los números de los criterios seleccionados, sus descriptores y explicaciones. Los saberes se publican en una sola relación común: repetirlos por curso o ciclo es una decisión de representación del proyecto. `codigoOficial` es `null` para los saberes; `numeracionFuente` conserva sus números locales. Los apartados internos de Comunicación distinguen Contexto, Géneros discursivos y los Procesos de Comprensión y Producción.

La norma entra en vigor el 18 de marzo de 2026 y no fija un curso escolar de implantación: `aplicableDesdeCurso` queda en `null`. La errata `iniciaciándose` del ODT de Primaria se ajusta al BOC, que dice `iniciándose`; no se registra como errata normativa. Las comas duplicadas entre descriptores se eliminan al representar estos como listas de códigos.

Las dos concreciones están revisadas tras el cierre confirmado por el usuario; sus textos, numeración y cobertura han sido cotejados con el PDF. Los 109 JSON de Canarias quedan revisados.

```powershell
python scripts/extract-es-cn-silbo.py
python scripts/audit-es-cn-correcciones.py
```

La auditoría requiere `jsonschema`, PyMuPDF y Poppler. Comprueba el esquema y las referencias de los 109 JSON canarios, las reparaciones de Primaria, la recuperación de las seis entradas superiores de Matemáticas y el contenido completo de las dos concreciones.
