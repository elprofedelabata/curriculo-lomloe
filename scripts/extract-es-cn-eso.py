"""Extrae las materias de ESO de Canarias y coteja los textos con el BOC.

Los ODT institucionales facilitan la lectura de tablas y listas. El PDF del
Decreto 30/2023 y el Decreto 86/2025 son las fuentes normativas de referencia.
El manifiesto recoge las 23 materias y los tres ámbitos de Diversificación.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
SUPPORT = ROOT / "sources/es-cn/apoyo/eso"
PDF = ROOT / "sources/es-cn/normativa/eso-bachillerato/2023-03-16-decreto-30-2023-curriculo-eso-bachillerato.pdf"
PDC_PDF = ROOT / "sources/es-cn/normativa/eso/2025-06-30-decreto-86-2025-diversificacion-curricular.pdf"
OUTPUT = ROOT / "data/es-cn/eso/materias"
SOURCE_ID = "boc-2023-058-decreto-30-2023"
START_PAGES = [65, 113, 138, 158, 174, 190, 215, 232, 271, 312, 328, 340,
               382, 399, 474, 498, 520, 611, 668, 743, 786, 842, 860, 901]
MATTER_COUNT = 23
CHARACTER = {
    "BG": {1: "obligatoria", 3: "obligatoria", 4: "optativa"},
    "CC": {3: "optativa"},
    "CCD": {3: "optativa"},
    "DIG": {4: "optativa"},
    "EPS": {3: "optativa"},
    "EE": {4: "optativa"},
    "EVCE": {1: "obligatoria"},
    "EF": {1: "obligatoria", 2: "obligatoria", 3: "obligatoria", 4: "obligatoria"},
    "EPVA": {1: "obligatoria", 2: "obligatoria", 3: "optativa"},
    "EAR": {4: "optativa"},
    "FIL": {4: "optativa"},
    "FQ": {2: "obligatoria", 3: "obligatoria", 4: "optativa"},
    "FOPP": {4: "optativa"},
    "GH": {1: "obligatoria", 2: "obligatoria", 3: "obligatoria", 4: "obligatoria"},
    "HGC": {3: "obligatoria"},
    "LAT": {4: "optativa"},
    "LCL": {1: "obligatoria", 2: "obligatoria", 3: "obligatoria", 4: "obligatoria"},
    "LE": {1: "obligatoria", 2: "obligatoria", 3: "obligatoria", 4: "obligatoria"},
    "MAT": {1: "obligatoria", 2: "obligatoria", 3: "obligatoria", 4: "obligatoria"},
    "MUS": {1: "obligatoria", 2: "obligatoria", 3: "optativa", 4: "optativa"},
    "SLE": {1: "obligatoria", 2: "obligatoria", 3: "obligatoria", 4: "optativa"},
    "TEC": {4: "optativa"},
    "TD": {1: "obligatoria", 2: "obligatoria", 3: "optativa"},
}

spec = importlib.util.spec_from_file_location("canarias_primaria", ROOT / "scripts/extract-es-cn-primaria.py")
assert spec and spec.loader
utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils)
OFFICE, TEXT, TABLE = utils.OFFICE, utils.TEXT, utils.TABLE
REF = utils.REF
NUMBERED = utils.NUMBERED


def pdf_pages(path: Path = PDF, count: int = 1953) -> tuple[list[str], dict[str, list[int]]]:
    result = subprocess.run(["pdftotext", "-raw", "-enc", "UTF-8", str(path), "-"], check=True, capture_output=True)
    pages = result.stdout.decode("utf-8").split("\f")
    assert len(pages) == count + 1, len(pages)
    headings: dict[str, list[int]] = {str(course): [] for course in range(1, 5)}
    headings.update({"4a": [], "4b": []})
    for number, page in enumerate(pages, 1):
        for match in re.finditer(r"(?m)^\s*([1-4])\.\s*[ºo]\s*ESO\s*$", page):
            headings[match.group(1)].append(number)
        for match in re.finditer(r"(?mi)^\s*Matemáticas\s+([AB])\s*$", page):
            headings[f"4{match.group(1).lower()}"].append(number)
        for match in re.finditer(r"(?mi)^Curso\s+([12])\.\s*º\.?\s+Ámbito", page):
            headings[str(int(match.group(1)) + 2)].append(number)
    return [utils.normal(page) for page in pages], headings


def provenance(page_numbers: list[int]) -> dict:
    return {"fuenteRef": SOURCE_ID, "paginas": sorted(set(page_numbers))}


def cell_text(node: ET.Element) -> str:
    return " ".join(utils.direct_paragraphs(node)) or utils.plain(node)


def saber_count(document: dict) -> int:
    return sum(len(block.get("saberes", [])) + sum(len(part["saberes"]) for part in block.get("apartados", []))
               for development in document["desarrollos"] for block in development["bloquesSaberes"])


def children_of_odt(filename: str) -> list[ET.Element]:
    with ZipFile(SUPPORT / filename) as archive:
        root = ET.fromstring(archive.read("content.xml"))
    body = root.find(f".//{OFFICE}body/{OFFICE}text")
    assert body is not None
    section = next((child for child in body if child.tag == TEXT + "section"), body)
    return list(section)


def course_heading(value: str) -> tuple[int, str | None] | None:
    match = re.match(r"^([1-4])\.\s*[ºo]\s*ESO$", value)
    if match:
        return int(match.group(1)), None
    match = re.fullmatch(r"Matemáticas ([AB])", value)
    if match:
        return 4, match.group(1).lower()
    match = re.match(r"^Curso ([12])\.\s*º\.?\s+Ámbito", value)
    return (int(match.group(1)) + 2, None) if match else None


def saber_heading(value: str) -> tuple[str, str] | None:
    match = re.match(r"^(?:Bloque )?([IVX]+)\.?\s+(.+)$", value)
    if not match:
        return None
    roman, label = match.groups()
    letter = utils.ROMAN.get(roman)
    return (letter, label.rstrip(".")) if letter else None


def parse_sabers(nodes: list[ET.Element], code: str, course: int, lo: int, hi: int, pages: list[str]) -> list[dict]:
    def saber_pages(statement: str) -> list[int]:
        if len(utils.normal(statement)) >= 20:
            return utils.page_hits(pages, statement, lo, hi)
        hits = [page for page in range(lo, hi + 1) if utils.normal(statement) in pages[page - 1]]
        assert hits, (code, course, statement)
        return [hits[0]]

    def items_in_lists(lists: list[ET.Element], letter: str) -> list[dict]:
        entries: list[dict] = []
        counters: dict[str, int] = {}
        last_top: str | None = None

        def add_list(listing: ET.Element, parent: str = "") -> None:
            nonlocal last_top
            for item in listing:
                if item.tag != TEXT + "list-item":
                    continue
                paragraphs = utils.direct_paragraphs(item)
                nested = [child for child in item if child.tag == TEXT + "list"]
                if not paragraphs and not nested:
                    continue
                if paragraphs:
                    counters[parent] = counters.get(parent, 0) + 1
                    local = str(counters[parent])
                    number = f"{parent}.{local}" if parent else local
                    statement = " ".join(paragraphs)
                    entries.append({
                        "id": f"{code}.{course}.{letter}.{number}", "codigoOficial": None,
                        "numeracionFuente": number, "texto": {"es": statement},
                        "procedencia": provenance(saber_pages(statement)),
                    })
                    if not parent:
                        last_top = number
                else:
                    assert last_top, (code, course, letter, "Sublista sin saber superior")
                    number = last_top
                for subtree in nested:
                    add_list(subtree, number)

        for listing in lists:
            add_list(listing)
        return entries

    blocks = []
    positions = [(i, saber_heading(utils.plain(node))) for i, node in enumerate(nodes) if node.tag == TEXT + "p"]
    positions = [(i, result) for i, result in positions if result]
    assert positions, (code, course, "No hay bloques de saberes")
    for ix, (position, (letter, label)) in enumerate(positions):
        stop = positions[ix + 1][0] if ix + 1 < len(positions) else len(nodes)
        lists = [node for node in nodes[position + 1:stop] if node.tag == TEXT + "list"]
        entries = items_in_lists(lists, letter)
        assert entries, (code, course, letter, "No hay saberes")
        block = {"codigo": letter, "nombre": {"es": label}}
        subtitles = [utils.plain(node) for node in nodes[position + 1:stop]
                     if node.tag == TEXT + "p" and utils.plain(node)]
        if subtitles:
            block["apartados"] = [{"codigo": "1", "nombre": {"es": " ".join(subtitles)}, "saberes": entries}]
        else:
            block["saberes"] = entries
        blocks.append(block)
    assert len({block["codigo"] for block in blocks}) == len(blocks), (code, course, "Bloques duplicados")
    return blocks


def parse_table(table: ET.Element, course: int, variant: str | None, code: str, lo: int, criterion_lo: int, hi: int, pages: list[str]) -> tuple[list[dict], list[dict], list[dict]]:
    rows = table.findall(f"./{TABLE}table-row")
    first = rows[0].findall(f"./{TABLE}table-cell")
    paragraphs = utils.direct_paragraphs(first[0])
    enunciados = [p for p in paragraphs if re.match(r"^\d+\.", p)]
    assert enunciados, paragraphs[:3]
    descriptors = list(dict.fromkeys(REF.findall(cell_text(first[1]))))
    competences = []
    for entry in enunciados:
        match = re.match(r"^(\d+)\.\s*(.*)$", entry)
        assert match, entry
        number, statement = match.groups()
        competences.append({
            "id": f"ce-{number}", "codigoOficial": number, "enunciado": {"es": statement},
            "descriptoresOperativosRefs": descriptors,
            "procedencia": provenance(utils.page_hits(pages, statement, lo, hi)),
        })
    criteria = []
    for row in rows[2:-1]:
        cells = row.findall(f"./{TABLE}table-cell")
        if not cells or not utils.plain(cells[0]):
            continue
        raw = cell_text(cells[0])
        match = NUMBERED.match(raw)
        assert match, raw[:110]
        major, minor, statement = match.groups()
        lookup = raw
        if code == "SLE" and major in ("5", "6"):
            # El BOC intercambia estos criterios; el ODT institucional los alinea
            # con sus competencias. Corrección confirmada en CN-ESO-001.
            lookup = re.sub(r"^[56]", "6" if major == "5" else "5", raw)
        assert utils.page_hits(pages, lookup, criterion_lo, hi), (course, lookup[:100])
        refs = list(dict.fromkeys(REF.findall(cell_text(cells[1])))) if len(cells) > 1 else []
        criteria.append({
            "id": f"cri-{course}{('-' + variant) if variant else ''}-{major}-{minor}", "codigoOficial": f"{major}.{minor}",
            "competenciaEspecificaRef": f"ce-{major}", "texto": {"es": statement},
            "descriptoresOperativosRefs": refs, "saberesBasicosRefs": [],
            "procedencia": provenance(utils.page_hits(pages, lookup, criterion_lo, hi)),
        })
    explanation = utils.direct_paragraphs(rows[-1].find(f"./{TABLE}table-cell"))
    assert explanation and explanation[0].startswith("Explicación del bloque competencial"), explanation[:1]
    explanation = [p for p in explanation if p != "Explicación del bloque competencial"]
    assert explanation
    block_pages = utils.page_hits(pages, explanation[0], criterion_lo, hi)
    blocks = [{
        "competenciaEspecificaRef": ce["id"],
        "competenciasClaveRefs": list(dict.fromkeys(re.match(r"^[A-Z]+", ref).group() for ref in descriptors)),
        "descriptoresOperativosRefs": descriptors,
        "explicacion": {"es": explanation}, "procedencia": provenance(block_pages),
    } for ce in competences]
    return competences, criteria, blocks


def parse_area(meta: dict, first_page: int, last_page: int, pages: list[str], page_headings: dict[str, list[int]]) -> dict:
    children = children_of_odt(meta["odt"])
    headings = [(i, course_heading(utils.plain(node))) for i, node in enumerate(children) if node.tag == TEXT + "p"]
    headings = [(i, course) for i, course in headings if course is not None]
    expected_courses = meta["cursos"] + ([4] if meta["codigoInterno"] == "MAT" else [])
    assert [item[0] for _, item in headings] == expected_courses, (meta["nombre"], headings, expected_courses)
    first_course = headings[0][0]
    intro_start = next(i for i in range(first_course) if utils.plain(children[i]) == "Introducción") + 1
    ce_start = next(i for i in range(intro_start, first_course) if re.match(r"^Competencias? específicas? y criterios de evaluación$", utils.plain(children[i])))
    desc_start = next(i for i in range(ce_start, first_course) if re.match(r"^Competencias? específicas? \d+", utils.plain(children[i])))
    desc_end = next(i for i in range(desc_start, first_course) if utils.plain(children[i]) == "Saberes básicos")
    intro = []
    for node in children[intro_start:desc_start] + children[desc_end:first_course]:
        paragraphs = [node] if node.tag == TEXT + "p" else list(node.iter(TEXT + "p")) if node.tag == TEXT + "list" else []
        intro.extend(utils.plain(paragraph) for paragraph in paragraphs if utils.plain(paragraph))
    descriptions: dict[int, list[str]] = {}
    for i in range(desc_start, desc_end):
        heading = utils.plain(children[i])
        if not re.match(r"^Competencias? específicas? \d+", heading):
            continue
        numbers = [int(x) for x in re.findall(r"C(\d+)", heading)]
        assert numbers, heading
        end = next((j for j in range(i + 1, desc_end) if re.match(r"^Competencias? específicas? \d+", utils.plain(children[j]))), desc_end)
        narrative = [utils.plain(node) for node in children[i + 1:end] if node.tag == TEXT + "p" and utils.plain(node)]
        assert narrative, (meta["nombre"], numbers)
        for number in numbers:
            descriptions[number] = narrative
    boundaries = [next((page for page in page_headings[f"{course}{variant or ''}"]
                        if first_page <= page <= last_page), None)
                  for _, (course, variant) in headings]
    assert all(boundary is not None for boundary in boundaries), (meta["nombre"], boundaries)
    assert boundaries == sorted(boundaries), (meta["nombre"], boundaries)
    competences: dict[int, dict] = {}
    next_internal = max(descriptions) + 1
    developments = []
    for ix, (position, (course, variant)) in enumerate(headings):
        next_pos = headings[ix + 1][0] if ix + 1 < len(headings) else len(children)
        segment = children[position:next_pos]
        sabers_position = next(i for i, node in enumerate(segment) if utils.plain(node) == "Saberes básicos")
        course_lo = boundaries[ix]
        course_hi = boundaries[ix + 1] - 1 if ix + 1 < len(boundaries) else last_page
        criterion_lo = course_lo
        tables = [node for node in segment[:sabers_position] if node.tag == TABLE + "table"]
        assert tables, (meta["nombre"], course)
        criteria, blocks = [], []
        for table in tables:
            ce_list, criterion_list, block_list = parse_table(table, course, variant, meta["codigoInterno"], course_lo, criterion_lo, course_hi, pages)
            criteria.extend(criterion_list)
            blocks.extend(block_list)
            for ce in ce_list:
                number = int(ce["codigoOficial"])
                matching = next((key for key, existing in competences.items()
                                 if existing["codigoOficial"] == ce["codigoOficial"] and
                                 utils.normal(existing["enunciado"]["es"]) == utils.normal(ce["enunciado"]["es"])), None)
                if matching is not None:
                    existing = competences[matching]
                    existing["descriptoresOperativosRefs"] = list(dict.fromkeys(existing["descriptoresOperativosRefs"] + ce["descriptoresOperativosRefs"]))
                    existing["procedencia"]["paginas"] = sorted(set(existing["procedencia"]["paginas"] + ce["procedencia"]["paginas"]))
                    target_id = existing["id"]
                else:
                    key = number
                    if number in competences:
                        assert meta["pdc"], (meta["nombre"], number, "Cambio de competencia no previsto")
                        key, next_internal = next_internal, next_internal + 1
                    target_id = f"ce-{key}"
                    ce["id"] = target_id
                    competences[key] = ce
                for entry in criterion_list + block_list:
                    if entry["competenciaEspecificaRef"] == f"ce-{number}":
                        entry["competenciaEspecificaRef"] = target_id
        assert len({criterion["id"] for criterion in criteria}) == len(criteria), (meta["nombre"], course, "Criterios duplicados")
        headings_in_pdf = [page for page in range(course_lo, course_hi + 1) if "saberesbasicos" in pages[page - 1]]
        saber_lo = max(headings_in_pdf) if headings_in_pdf else max(p for criterion in criteria for p in criterion["procedencia"]["paginas"])
        saber_code = f"MAT{variant.upper()}" if variant else meta["codigoInterno"]
        sabers = parse_sabers(segment[sabers_position + 1:], saber_code, course, saber_lo, course_hi, pages)
        development = {"curso": course, "criteriosEvaluacion": criteria, "bloquesCompetenciales": blocks, "bloquesSaberes": sabers}
        if variant:
            development["variante"] = {"codigo": variant, "nombre": {"es": f"Matemáticas {variant.upper()}"}}
        developments.append(development)
    for ce in competences.values():
        number = int(ce["codigoOficial"])
        assert number in descriptions, (meta["nombre"], number, "Sin descripción")
        ce["descripcion"] = {"es": descriptions[number]}
        ce["procedencia"]["paginas"] = sorted(set(ce["procedencia"]["paginas"] + utils.page_hits(pages, descriptions[number][0], first_page, boundaries[0])))
    earliest_course = min(meta["cursos"])
    document = {
        "$schema": "../../../../schemas/materia.schema.json", "schemaVersion": "0.6.0",
        "id": f"es-cn.eso.{meta['slug']}", "territorio": "es-cn", "etapa": "eso",
        "materia": {"codigo": meta["codigoInterno"], "nombre": {"es": meta["nombre"]},
                    "cursos": [{"curso": course, "caracter": "ambito" if meta["pdc"] else CHARACTER[meta["codigoInterno"]][course]} for course in meta["cursos"]]},
        "vigencia": {"entradaEnVigor": "2023-03-24", "aplicableDesdeCurso": "2023/2024" if earliest_course in (2, 4) else "2022/2023", "hasta": None, "estado": "vigente"},
        "fuentes": [{"id": SOURCE_ID, "tipo": "decreto",
                     "titulo": "Decreto 30/2023, de 16 de marzo, por el que se establece la ordenación y el currículo de la Educación Secundaria Obligatoria y del Bachillerato en la Comunidad Autónoma de Canarias",
                     "publicacion": "Boletín Oficial de Canarias", "numero": "58", "fechaPublicacion": "2023-03-23",
                     "cve": "BOC-A-2023-058-848", "urlOficial": "https://sede.gobiernodecanarias.org/boc/boc-a-2023-058-848.pdf",
                     "urlVerificacion": "https://www.gobiernodecanarias.org/boc/2023/058/001.html",
                     "anexo": "2", "paginasMateria": {"desde": first_page, "hasta": last_page}}],
        "introduccion": {"es": intro},
        "competenciasEspecificas": [competences[n] for n in sorted(competences)],
        "desarrollos": developments,
        "revision": {"estado": "borrador", "fuenteComprobada": True, "fechaUltimaRevision": "2026-10-30",
                     "metodo": "Extracción estructurada del ODT institucional y cotejo de los textos con el PDF publicado en el BOC.",
                     "notas": ["Los códigos de saber y las abreviaturas de materia son internos del proyecto; la fuente no publica códigos individuales para los saberes.",
                               "Calendario de implantación: 1.º y 3.º en 2022/2023; 2.º y 4.º en 2023/2024."]},
    }
    if meta["pdc"]:
        document["vigencia"] = {"entradaEnVigor": "2025-07-08", "aplicableDesdeCurso": "2025/2026", "hasta": None, "estado": "vigente"}
        source = document["fuentes"][0]
        source.update({
            "titulo": "Decreto 86/2025, de 30 de junio, por el que se establece el currículo de los ámbitos de los Programas de Diversificación Curricular en la Comunidad Autónoma de Canarias",
            "numero": "133", "fechaPublicacion": "2025-07-07", "cve": "BOC-A-2025-133-2484",
            "urlOficial": "https://sede.gobiernodecanarias.org/boc/boc-a-2025-133-2484.pdf",
            "urlVerificacion": "https://www.gobiernodecanarias.org/boc/2025/133/2484.html",
            "anexo": {"ALS": "1", "ACT": "2", "AP": "3"}[meta["codigoInterno"]],
        })
        document["revision"]["notas"][-1] = "Los cursos 1.º y 2.º del programa se representan como 3.º y 4.º de ESO. El Ámbito Práctico solo se imparte en 2.º del programa (4.º de ESO)."
        document["revision"]["notas"].append("Cuando el enunciado de una competencia cambia entre cursos, se conserva cada versión con un id interno distinto y el mismo codigoOficial; los criterios y bloques remiten a la versión de su curso.")
        document["introduccion"]["es"] = [p.replace("art. 21", "artículo 21") for p in document["introduccion"]["es"]]
    # Diferencias del ODT de apoyo: se sigue la redacción publicada en el BOC.
    if meta["codigoInterno"] == "ACT":
        for development in document["desarrollos"]:
            for block in development["bloquesCompetenciales"]:
                block["explicacion"]["es"] = [p.replace("contribuición", "contribución") for p in block["explicacion"]["es"]]
    if meta["codigoInterno"] == "ALS":
        for development in document["desarrollos"]:
            for block in development["bloquesCompetenciales"]:
                block["explicacion"]["es"] = [p.replace("interlingüísitca", "interlingüística") for p in block["explicacion"]["es"]]
        # La capa de texto contiene restos fuera del área visible de la tabla.
        # El bloque de CE7 de 4.º está completo en la página 45 del BOC.
        next(b for d in document["desarrollos"] if d["curso"] == 4 for b in d["bloquesCompetenciales"]
             if b["competenciaEspecificaRef"] == "ce-7")["procedencia"]["paginas"] = [45]
    if meta["codigoInterno"] == "AP":
        document["introduccion"]["es"] = [p.replace("Los objetivos se referencian", "Los objetivos de etapa se referencian") for p in document["introduccion"]["es"]]
    if meta["codigoInterno"] == "TD":
        document["introduccion"]["es"] = [p.replace("aprendizaje basado en proyectos (ABP)", "aprendizaje por proyectos (ABP)") for p in document["introduccion"]["es"]]
    if meta["codigoInterno"] == "SLE":
        # Corrección confirmada en CN-ESO-001: alinear también
        # los descriptores con los enunciados y explicaciones de CE5 y CE6.
        for development in document["desarrollos"]:
            blocks = {b["competenciaEspecificaRef"]: b for b in development["bloquesCompetenciales"]}
            criteria = {c["codigoOficial"]: c for c in development["criteriosEvaluacion"]}
            for left, right in [(blocks["ce-5"], blocks["ce-6"]), (criteria["5.1"], criteria["6.1"])]:
                left["descriptoresOperativosRefs"], right["descriptoresOperativosRefs"] = right["descriptoresOperativosRefs"], left["descriptoresOperativosRefs"]
            for key in ("ce-5", "ce-6"):
                blocks[key]["competenciasClaveRefs"] = list(dict.fromkeys(re.match(r"^[A-Z]+", ref).group() for ref in blocks[key]["descriptoresOperativosRefs"]))
        for ce in document["competenciasEspecificas"]:
            if ce["id"] in ("ce-5", "ce-6"):
                ce["descriptoresOperativosRefs"] = list(dict.fromkeys(ref for d in document["desarrollos"] for b in d["bloquesCompetenciales"]
                                                                      if b["competenciaEspecificaRef"] == ce["id"] for ref in b["descriptoresOperativosRefs"]))
    return document


def main() -> None:
    global SOURCE_ID
    manifest = json.loads((SUPPORT / "manifest.json").read_text(encoding="utf-8"))
    pages, page_headings = pdf_pages()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for index, meta in enumerate(manifest[:MATTER_COUNT]):
        document = parse_area(meta, START_PAGES[index], START_PAGES[index + 1] - 1, pages, page_headings)
        target = OUTPUT / f"{meta['slug']}.json"
        target.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        criteria = sum(len(item["criteriosEvaluacion"]) for item in document["desarrollos"])
        sabers = saber_count(document)
        print(meta["nombre"], len(document["competenciasEspecificas"]), criteria, sabers)
    SOURCE_ID = "boc-2025-133-decreto-86-2025"
    pages, page_headings = pdf_pages(PDC_PDF, 118)
    starts = [7, 52, 100, 119]
    for index, meta in enumerate(manifest[MATTER_COUNT:]):
        document = parse_area(meta, starts[index], starts[index + 1] - 1, pages, page_headings)
        (OUTPUT / f"{meta['slug']}.json").write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(meta["nombre"], len(document["competenciasEspecificas"]), sum(len(d["criteriosEvaluacion"]) for d in document["desarrollos"]), saber_count(document))


if __name__ == "__main__":
    main()
