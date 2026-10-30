"""Extrae las tres áreas de Infantil del anexo 2 del Decreto 196/2022 (Canarias)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "sources/es-cn/normativa/infantil/2022-10-13-decreto-196-2022-curriculo-infantil.pdf"
OUTPUT = ROOT / "data/es-cn/infantil/materias"
SOURCE_ID = "boc-2022-212-decreto-196-2022"

AREAS = (
    {
        "number": 1,
        "name": "Crecimiento en Armonía",
        "slug": "crecimiento-en-armonia",
        "code": "CA",
        "narrative": (26, 33),
        "cycles": ((1, 34, 40, 12, 4, 31), (2, 41, 48, 18, 4, 37)),
        "pages": (26, 48),
    },
    {
        "number": 2,
        "name": "Descubrimiento y Exploración del Entorno",
        "slug": "descubrimiento-y-exploracion-del-entorno",
        "code": "DEE",
        "narrative": (49, 55),
        "cycles": ((1, 56, 60, 8, 3, 14), (2, 61, 67, 13, 3, 31)),
        "pages": (49, 67),
    },
    {
        "number": 3,
        "name": "Comunicación y Representación de la Realidad",
        "slug": "comunicacion-y-representacion-de-la-realidad",
        "code": "CRR",
        "narrative": (68, 77),
        "cycles": ((1, 78, 87, 16, 5, 35), (2, 88, 99, 28, 5, 46)),
        "pages": (68, 99),
    },
)

HEADER_PREFIXES = (
    "https://sede.gobiernodecanarias.org/boc",
    "boc-a-2022-212-3215",
    "Boletín Oficial de Canarias núm. 212",
)
CE_HEADING = re.compile(r"^Competencia específica (\d+) \(C\d+\)\.$")
CRITERION = re.compile(r"^(\d+\.\d+)\.\s*(.*)$")
SABER = re.compile(r"^(\d+(?:\.\d+)*)\.\s+(.*)$")
ROMAN = re.compile(r"^([IVX]+)\s*\.\s*(.*)$")
KEY_HEADING = re.compile(r"^Vinculación con las competencias clave$", re.I)


def clean(lines: list[tuple[int, str]]) -> str:
    return re.sub(r"\s+", " ", " ".join(text.strip() for _, text in lines)).strip()


def page_numbers(lines: list[tuple[int, str]]) -> list[int]:
    return sorted({page for page, _ in lines})


def provenance(lines: list[tuple[int, str]]) -> dict:
    pages = page_numbers(lines)
    assert pages, "Procedencia sin páginas"
    return {"fuenteRef": SOURCE_ID, "paginas": pages}


def source_lines(reader: PdfReader, start: int, end: int) -> list[tuple[int, str]]:
    output = []
    for number in range(start, end + 1):
        for raw in (reader.pages[number - 1].extract_text() or "").splitlines():
            line = raw.strip()
            if line and not line.startswith(HEADER_PREFIXES):
                output.append((number, line))
    return output


def find(lines: list[tuple[int, str]], label: str) -> int:
    hits = [i for i, (_, line) in enumerate(lines) if line == label]
    assert len(hits) == 1, (label, hits)
    return hits[0]


def narrative(reader: PdfReader, area: dict) -> tuple[str, dict[int, tuple[str, list[tuple[int, str]]]]]:
    lines = source_lines(reader, *area["narrative"])
    intro_start = find(lines, "Introducción.") + 1
    intro_end = find(lines, "Competencias específicas y criterios de evaluación.")
    intro = clean(lines[intro_start:intro_end])
    assert intro
    description_end = find(lines, "Saberes básicos.")
    headings = [(i, int(match.group(1))) for i, (_, line) in enumerate(lines) if (match := CE_HEADING.fullmatch(line))]
    assert len(headings) == (4 if area["number"] == 1 else 3 if area["number"] == 2 else 5)
    descriptions = {}
    for index, (position, number) in enumerate(headings):
        end = headings[index + 1][0] if index + 1 < len(headings) else description_end
        segment = lines[position + 1:end]
        assert segment and number not in descriptions
        descriptions[number] = (clean(segment), segment)
    return intro, descriptions


def table_sections(reader: PdfReader, start: int, end: int) -> tuple[list[dict], list[tuple[int, str]]]:
    sections = []
    current = None
    state = None
    sabers = []
    for page, line in source_lines(reader, start, end):
        if line == "Competencia específica":
            current = {"enunciado": [], "claves": [], "criterios": [], "explicacion": []}
            sections.append(current)
            state = "enunciado"
        elif KEY_HEADING.fullmatch(line):
            assert current is not None
            state = "claves"
        elif line == "Criterios de evaluación":
            assert current is not None
            state = "criterios"
        elif line == "Explicación del bloque competencial":
            assert current is not None
            state = "explicacion"
        elif line == "Saberes básicos.":
            state = "saberes"
        elif state == "saberes":
            sabers.append((page, line))
        elif current is not None and state:
            current[state].append((page, line))
    assert sections and sabers, (start, end)
    return sections, sabers


def numbered_criteria(lines: list[tuple[int, str]], cycle: int, ce_number: int) -> list[dict]:
    groups = []
    for page, line in lines:
        match = CRITERION.fullmatch(line)
        if match:
            groups.append((match.group(1), [(page, match.group(2))]))
        else:
            assert groups, (page, line)
            groups[-1][1].append((page, line))
    criteria = []
    for code, words in groups:
        assert int(code.split(".")[0]) == ce_number
        text = clean(words)
        assert text
        criteria.append({
            "id": f"cri-{cycle}-{code.replace('.', '-')}",
            "codigoOficial": code,
            "competenciaEspecificaRef": f"ce-{ce_number}",
            "texto": {"es": text},
            "saberesBasicosRefs": [],
            "procedencia": provenance(words),
        })
    return criteria


def numbered_sabers(lines: list[tuple[int, str]], area_code: str, cycle: int) -> list[dict]:
    blocks = []
    current = None
    active_item = None

    def flush_item() -> None:
        nonlocal active_item
        if active_item is None:
            return
        assert current is not None
        code, words = active_item
        text = clean(words)
        assert text
        current["saberes"].append({
            "id": f"{area_code}.{cycle}.{current['codigo']}.{len(current['saberes']) + 1:02d}",
            "codigoOficial": None,
            "numeracionFuente": code,
            "texto": {"es": text},
            "procedencia": provenance(words),
        })
        active_item = None

    for page, line in lines:
        heading = ROMAN.fullmatch(line)
        item = SABER.fullmatch(line)
        if heading:
            flush_item()
            assert heading.group(1) == ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX")[len(blocks)]
            current = {"codigo": chr(65 + len(blocks)), "nombre": {"es": heading.group(2)}, "saberes": []}
            current["_name_lines"] = [(page, heading.group(2))]
            blocks.append(current)
        elif item:
            flush_item()
            assert current is not None
            active_item = (item.group(1), [(page, item.group(2))])
        elif active_item is not None:
            active_item[1].append((page, line))
        else:
            assert current is not None, (page, line)
            current["_name_lines"].append((page, line))
    flush_item()
    for block in blocks:
        block["nombre"]["es"] = clean(block.pop("_name_lines")).rstrip(".")
        assert block["saberes"]
        ids = [item["id"] for item in block["saberes"]]
        assert len(ids) == len(set(ids)), ids
    if area_code == "CA" and cycle == 1:
        affective = blocks[1]["saberes"]
        assert [item["numeracionFuente"] for item in affective] == ["1", "3", "3"]
        assert affective[1]["texto"]["es"].startswith("Aceptación y control progresivo de las emociones")
        affective[1]["numeracionFuente"] = "2"
    return blocks


def cycle_data(reader: PdfReader, area: dict, cycle_spec: tuple) -> tuple[dict, dict[int, tuple[str, list[tuple[int, str]]]]]:
    cycle, start, end, expected_criteria, expected_blocks, expected_sabers = cycle_spec
    sections, saber_lines = table_sections(reader, start, end)
    assert len(sections) == expected_blocks, (area["name"], cycle, len(sections))
    criteria = []
    blocks = []
    enunciados = {}
    for section in sections:
        enunciado_lines = section["enunciado"][:]
        keys = re.findall(r"\b[A-Z]{2,6}\b", clean(section["claves"]))
        assert keys, (area["name"], cycle)
        extra = re.sub(r"\b[A-Z]{2,6}\b|[,\s]", "", clean(section["claves"]))
        if extra:
            # El enunciado de CRR C3 (primer ciclo) termina en la página siguiente,
            # debajo de la cabecera de vinculación con competencias clave.
            assert area["number"] == 3 and cycle == 1 and len(sections) >= 3
            continuation = [(page, line) for page, line in section["claves"] if not re.fullmatch(r"[A-Z,\s]+", line)]
            enunciado_lines.extend(continuation)
        enunciado = clean(enunciado_lines)
        match = re.match(r"^(\d+)\.\s+(.+)$", enunciado)
        assert match, (area["name"], cycle, enunciado)
        ce_number = int(match.group(1))
        assert ce_number == len(blocks) + 1
        if area["number"] == 2 and cycle == 1 and ce_number == 2:
            assert keys == ["CCL", "STEM", "CD", "CE", "CPSSAA"]
            keys[-1] = "CPSAA"
        enunciados[ce_number] = (match.group(2), enunciado_lines)
        current_criteria = numbered_criteria(section["criterios"], cycle, ce_number)
        assert current_criteria
        criteria.extend(current_criteria)
        explanation = clean(section["explicacion"])
        assert explanation, (area["name"], cycle, ce_number)
        blocks.append({
            "competenciaEspecificaRef": f"ce-{ce_number}",
            "competenciasClaveRefs": keys,
            "explicacion": {"es": [explanation]},
            "procedencia": provenance(
                enunciado_lines + section["claves"] + section["criterios"] + section["explicacion"]
            ),
        })
    knowledge = numbered_sabers(saber_lines, area["code"], cycle)
    assert len(criteria) == expected_criteria, (area["name"], cycle, len(criteria))
    assert sum(len(block["saberes"]) for block in knowledge) == expected_sabers
    assert len({item["id"] for item in criteria}) == len(criteria)
    return {
        "ciclo": cycle,
        "criteriosEvaluacion": criteria,
        "bloquesCompetenciales": blocks,
        "bloquesSaberes": knowledge,
    }, enunciados


def sources(area: dict) -> list[dict]:
    return [
        {
            "id": SOURCE_ID,
            "tipo": "decreto",
            "titulo": "Decreto 196/2022, de 13 de octubre, por el que se establece la ordenación y el currículo de la Educación Infantil en la Comunidad Autónoma de Canarias",
            "publicacion": "Boletín Oficial de Canarias",
            "numero": "212",
            "fechaPublicacion": "2022-10-26",
            "cve": "BOC-A-2022-212-3215",
            "urlOficial": "https://sede.gobiernodecanarias.org/boc/boc-a-2022-212-3215.pdf",
            "urlVerificacion": "https://www.gobiernodecanarias.org/boc/2022/212/001.html",
            "anexo": "2",
            "paginasMateria": {"desde": area["pages"][0], "hasta": area["pages"][1]},
        },
        {
            "id": "boc-2022-214-correccion-196-2022",
            "tipo": "otro",
            "titulo": "Corrección de errores del Decreto 196/2022, de 13 de octubre",
            "publicacion": "Boletín Oficial de Canarias",
            "numero": "214",
            "fechaPublicacion": "2022-10-28",
            "cve": "BOC-A-2022-214-3245",
            "urlOficial": "https://sede.gobiernodecanarias.org/boc/boc-a-2022-214-3245.pdf",
            "urlVerificacion": "https://www.gobiernodecanarias.org/boc/2022/214/002.html",
        },
    ]


def main() -> None:
    reader = PdfReader(str(PDF))
    assert len(reader.pages) == 102
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for area in AREAS:
        intro, descriptions = narrative(reader, area)
        developments = []
        table_enunciados = {}
        for spec in area["cycles"]:
            development, enunciados = cycle_data(reader, area, spec)
            developments.append(development)
            table_enunciados[spec[0]] = enunciados
        competencies = []
        for number in sorted(descriptions):
            first, first_lines = table_enunciados[1][number]
            second, second_lines = table_enunciados[2][number]
            assert first == second, (area["name"], number, first, second)
            description, description_lines = descriptions[number]
            competencies.append({
                "id": f"ce-{number}",
                "codigoOficial": str(number),
                "enunciado": {"es": first},
                "descripcion": {"es": [description]},
                "descriptoresOperativosRefs": [],
                "procedencia": provenance(first_lines + second_lines + description_lines),
            })
        document = {
            "$schema": "../../../../schemas/materia.schema.json",
            "schemaVersion": "0.5.0",
            "id": f"es-cn.infantil.{area['slug']}",
            "territorio": "es-cn",
            "etapa": "infantil",
            "materia": {
                "codigo": area["code"],
                "nombre": {"es": area["name"]},
                "ciclos": [
                    {"ciclo": 1, "caracter": "obligatoria"},
                    {"ciclo": 2, "caracter": "obligatoria"},
                ],
            },
            "vigencia": {
                "entradaEnVigor": "2022-10-27",
                "aplicableDesdeCurso": "2022/2023",
                "hasta": None,
                "estado": "vigente",
            },
            "fuentes": sources(area),
            "introduccion": {"es": [intro]},
            "competenciasEspecificas": competencies,
            "desarrollos": developments,
            "revision": {
                "estado": "borrador",
                "fuenteComprobada": True,
                "fechaUltimaRevision": "2026-10-29",
                "metodo": "Extracción estructurada de las tablas y del desarrollo narrativo del PDF oficial, con cotejo de recuentos y páginas; pendiente de revisión manual.",
                "notas": [
                    "El anexo 2 organiza criterios y saberes por primer y segundo ciclo.",
                    "Las letras de bloque y las abreviaturas de área son internas; la fuente usa números romanos para los bloques y números locales para los saberes.",
                    "La numeración local de los saberes se registra en numeracionFuente; codigoOficial queda a null y los id posicionales son internos del proyecto.",
                    "La fuente vincula cada bloque competencial con competencias clave sin numerar descriptores operativos; por eso descriptoresOperativosRefs queda vacío.",
                    "No se publican asociaciones individualizadas entre criterios de evaluación y saberes básicos.",
                    "La corrección de errores de 28 de octubre de 2022 afecta al preámbulo, no al anexo 2.",
                ],
            },
        }
        output = OUTPUT / f"{area['slug']}.json"
        output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{output.relative_to(ROOT)}: {len(competencies)} competencias, "
              f"{sum(len(d['criteriosEvaluacion']) for d in developments)} criterios, "
              f"{sum(len(b['saberes']) for d in developments for b in d['bloquesSaberes'])} saberes")


if __name__ == "__main__":
    main()
