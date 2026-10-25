# Fuentes oficiales de las Illes Balears

Corpus normativo de partida para estructurar en JSON los currículos LOMLOE de Infantil, Primaria, ESO y Bachillerato, y para estudiar los dos ámbitos comunes de CFGB. Los PDF se conservan sin editar. El [catálogo](catalogo.json) registra su procedencia, URL oficial, número de páginas y huella SHA-256.

| Etapa | Fuente principal | Ubicación |
| --- | --- | --- |
| Infantil | Decret 40/2025 | `infantil/` |
| Primaria | Decret 41/2025 | `primaria/` |
| ESO, incluido el programa de diversificación curricular | Decret 42/2025 | `eso/` |
| Bachillerato | Decret 43/2025 | `bachillerato/` |
| CFGB | Decret 39/2025 (ordenación) y anexo V del Real Decreto 217/2022 (enseñanzas mínimas) | `cfgb/` |

Los decretos curriculares de 2025 sustituyen a los de 2022 para las cuatro primeras etapas. El texto oficial recopilado está en catalán; los [tres JSON revisados de Infantil](../../../data/es-ib/infantil/materias/) y los [ocho borradores de Primaria](../../../data/es-ib/primaria/materias/) conservan esa lengua en los campos localizados, sin presentar una traducción como transcripción oficial.

**CFGB requiere una comprobación adicional antes de la extracción.** El artículo 45 del Decret 39/2025 organiza los ámbitos de Comunicación y Ciencias Sociales I y II y Ciencias Aplicadas I y II, pero no desarrolla sus competencias, criterios y saberes. Se conserva también el anexo estatal de enseñanzas mínimas. La web de FP balear identifica currículos propios de ciclos en fase de borrador; esos borradores no se han tratado como normativa aprobada. El alcance del proyecto sigue limitado a los dos ámbitos comunes, no a los módulos profesionales.
