"""Extrae Bachillerato de Canarias a partir del ODT institucional y el BOC.

Por defecto genera las 67 materias. --limit permite seleccionar una tanda inicial.
Las competencias con enunciados diferentes entre I y II conservan versiones
internas distintas, con la misma numeración oficial y referencias por curso.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = ROOT / "sources/es-cn/apoyo/bachillerato"
OUTPUT = ROOT / "data/es-cn/bachillerato/materias"
PDF = ROOT / "sources/es-cn/normativa/eso-bachillerato/2023-03-16-decreto-30-2023-curriculo-eso-bachillerato.pdf"
OPT_PDF = ROOT / "sources/es-cn/normativa/bachillerato/2025-06-02-decreto-78-2025-optativas-bachillerato.pdf"
SOURCE_ID = "boc-2023-058-decreto-30-2023"
spec = importlib.util.spec_from_file_location("canarias_eso", ROOT / "scripts/extract-es-cn-eso.py")
assert spec and spec.loader
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
shared.SUPPORT = SUPPORT
utils, TEXT, TABLE = shared.utils, shared.TEXT, shared.TABLE
# Algunas celdas unen el código al enunciado sin un espacio intermedio.
shared.NUMBERED = re.compile(r"^(\d+)\.(\d+)\.?\s*(.*)$")
utils.ROMAN.update({"VIII": "H", "IX": "I", "X": "J", "XI": "K", "XII": "L"})


def read_odt_nodes(filename):
    with ZipFile(SUPPORT / filename) as archive:
        root = ET.fromstring(archive.read("content.xml"))
    body = root.find(f".//{shared.OFFICE}body/{shared.OFFICE}text")
    assert body is not None
    def visible_children(parent):
        for node in parent:
            if node.tag == TEXT + "section":
                yield from visible_children(node)
            elif node.tag in (TEXT + "p", TEXT + "list", TABLE + "table"):
                yield node
    return list(visible_children(body))


def prepare_saber_nodes(nodes):
    """Integra los padres numerados escritos fuera de su lista automática."""
    result = list(nodes)
    for index in range(len(result) - 1):
        paragraph, listing = result[index:index + 2]
        if paragraph.tag != TEXT + "p" or listing.tag != TEXT + "list":
            continue
        match = re.fullmatch(r"\d+\.\s+(.+)", utils.plain(paragraph))
        first_item = listing.find(TEXT + "list-item")
        if not match or first_item is None or utils.direct_paragraphs(first_item):
            continue
        if first_item.find(TEXT + "list") is None:
            continue
        parent = ET.Element(TEXT + "p")
        parent.text = match.group(1)
        first_item.insert(0, parent)
        result[index] = None
    return [node for node in result if node is not None]


def page_hits(pages, value, lo, hi):
    """Localiza también finales breves de una tabla partida entre páginas."""
    target = utils.normal(value)
    assert len(target) >= 20, value
    for length in (85, 65, 45, 25):
        matches = [p for p in range(lo, hi + 1) if target[:length] in pages[p - 1]]
        if not matches:
            continue
        first = matches[0]
        if target[-40:] in pages[first - 1]:
            return [first]
        end = next((p for p in range(first + 1, min(first + 2, hi) + 1) if target[-40:] in pages[p - 1]), first)
        return list(range(first, end + 1))
    raise ValueError(f"No consta en el PDF (páginas {lo}-{hi}): {value[:110]}")


# Los lectores de tablas y saberes compartidos consultan este localizador.
utils.page_hits = page_hits


def course_heading(value):
    match = re.fullmatch(r"([12])\.\s*º\s+Bachillerato", value, re.I)
    return int(match.group(1)) if match else None


def pdf_pages(path=PDF, count=1953):
    raw = subprocess.run(["pdftotext", "-raw", "-enc", "UTF-8", str(path), "-"], check=True, capture_output=True).stdout.decode("utf-8").split("\f")
    assert len(raw) == count + 1
    headings = {1: [], 2: []}
    for number, page in enumerate(raw, 1):
        for match in re.finditer(r"(?mi)^\s*([12])\.\s*º\s+Bachillerato\s*$", page):
            headings[int(match.group(1))].append(number)
    return [utils.normal(page) for page in raw], headings


def parse_area(meta, pages, page_headings):
    source_id = "boc-2025-112-decreto-78-2025" if meta["optativa"] else SOURCE_ID
    shared.SOURCE_ID = source_id
    first_page, last_page = meta["paginas"]["desde"], meta["paginas"]["hasta"]
    nodes = read_odt_nodes(meta["odt"])
    headings = [(i, course_heading(utils.plain(n))) for i, n in enumerate(nodes) if n.tag == TEXT + "p"]
    headings = [(i, c) for i, c in headings if c is not None]
    assert [c for _, c in headings] == meta["cursos"], (meta["nombre"], headings)
    first_course = headings[0][0]
    start = next(i for i in range(first_course) if utils.plain(nodes[i]).rstrip(".") == "Introducción") + 1
    description_heading = re.compile(r"^Competencias? específicas? \d+")
    description_start = next(i for i in range(start, first_course) if description_heading.match(utils.plain(nodes[i])))
    description_end = next(i for i in range(description_start, first_course) if utils.plain(nodes[i]) == "Saberes básicos")
    intro = []
    for node in nodes[start:description_start] + nodes[description_end:first_course]:
        paragraphs = [node] if node.tag == TEXT + "p" else list(node.iter(TEXT + "p")) if node.tag == TEXT + "list" else []
        intro.extend(utils.plain(p) for p in paragraphs if utils.plain(p))
    descriptions = {}
    for i in range(description_start, description_end):
        heading = utils.plain(nodes[i])
        if not description_heading.match(heading):
            continue
        numbers = [int(n) for n in re.findall(r"C(\d+)", heading)] or [int(n) for n in re.findall(r"\d+", heading.split("(", 1)[0])]
        assert numbers, (meta["nombre"], heading)
        end = next((j for j in range(i + 1, description_end) if description_heading.match(utils.plain(nodes[j]))), description_end)
        narrative = [utils.plain(n) for n in nodes[i + 1:end] if n.tag == TEXT + "p" and utils.plain(n)]
        assert narrative
        for number in numbers:
            descriptions[number] = narrative
    boundaries = [next((p for p in page_headings[course] if first_page <= p <= last_page), None) for _, course in headings]
    assert all(boundaries) and boundaries == sorted(boundaries), (meta["nombre"], boundaries)
    competences, developments = {}, []
    next_internal = max(descriptions) + 1
    for ix, (position, course) in enumerate(headings):
        stop = headings[ix + 1][0] if ix + 1 < len(headings) else len(nodes)
        segment = nodes[position:stop]
        saber_position = next(i for i, n in enumerate(segment) if utils.plain(n) == "Saberes básicos")
        lo = boundaries[ix]
        hi = boundaries[ix + 1] - 1 if ix + 1 < len(boundaries) else last_page
        criteria, blocks = [], []
        for table in [n for n in segment[:saber_position] if n.tag == TABLE + "table"]:
            ce_list, cri_list, block_list = shared.parse_table(table, course, None, meta["codigoInterno"], lo, lo, hi, pages, normalize_sle=False)
            for ce in ce_list:
                number = int(ce["codigoOficial"])
                existing = next((c for c in competences.values() if c["codigoOficial"] == ce["codigoOficial"] and utils.normal(c["enunciado"]["es"]) == utils.normal(ce["enunciado"]["es"])), None)
                if existing:
                    existing["descriptoresOperativosRefs"] = list(dict.fromkeys(existing["descriptoresOperativosRefs"] + ce["descriptoresOperativosRefs"]))
                    existing["procedencia"]["paginas"] = sorted(set(existing["procedencia"]["paginas"] + ce["procedencia"]["paginas"]))
                    target_id = existing["id"]
                else:
                    key = number
                    if key in competences:
                        key, next_internal = next_internal, next_internal + 1
                    target_id = f"ce-{key}"
                    ce["id"] = target_id
                    competences[key] = ce
                for entry in cri_list + block_list:
                    if entry["competenciaEspecificaRef"] == f"ce-{number}":
                        entry["competenciaEspecificaRef"] = target_id
            criteria.extend(cri_list)
            blocks.extend(block_list)
        assert criteria and len({c["id"] for c in criteria}) == len(criteria)
        saber_pages = [p for p in range(lo, hi + 1) if "saberesbasicos" in pages[p - 1]]
        saber_lo = max(saber_pages) if saber_pages else max(p for c in criteria for p in c["procedencia"]["paginas"])
        sabers = shared.parse_sabers(prepare_saber_nodes(segment[saber_position + 1:]), meta["codigoInterno"], course, saber_lo, hi, pages)
        developments.append({"curso": course, "criteriosEvaluacion": criteria, "bloquesCompetenciales": blocks, "bloquesSaberes": sabers})
    for ce in competences.values():
        number = int(ce["codigoOficial"])
        assert number in descriptions
        ce["descripcion"] = {"es": descriptions[number]}
        ce["procedencia"]["paginas"] = sorted(set(ce["procedencia"]["paginas"] + utils.page_hits(pages, descriptions[number][0], first_page, boundaries[0])))
    character = "obligatoria" if meta["codigoInterno"] in ("EF", "FIL", "HE", "HFI", "LCL", "LE") else "optativa" if meta["optativa"] or meta["codigoInterno"] == "SLE" else "modalidad"
    document = {
        "$schema": "../../../../schemas/materia.schema.json", "schemaVersion": "0.6.0",
        "id": f"es-cn.bachillerato.{meta['slug']}", "territorio": "es-cn", "etapa": "bachillerato",
        "materia": {"codigo": meta["codigoInterno"], "nombre": {"es": meta["nombre"]}, "cursos": [{"curso": c, "caracter": character} for c in meta["cursos"]]},
        "vigencia": {"entradaEnVigor": "2023-03-24", "aplicableDesdeCurso": "2022/2023" if 1 in meta["cursos"] else "2023/2024", "hasta": None, "estado": "vigente"},
        "fuentes": [{"id": source_id, "tipo": "decreto", "titulo": "Decreto 30/2023, de 16 de marzo, por el que se establece la ordenación y el currículo de la Educación Secundaria Obligatoria y del Bachillerato en la Comunidad Autónoma de Canarias", "publicacion": "Boletín Oficial de Canarias", "numero": "58", "fechaPublicacion": "2023-03-23", "cve": "BOC-A-2023-058-848", "urlOficial": "https://sede.gobiernodecanarias.org/boc/boc-a-2023-058-848.pdf", "urlVerificacion": "https://www.gobiernodecanarias.org/boc/2023/058/001.html", "anexo": "3", "paginasMateria": meta["paginas"]}],
        "introduccion": {"es": intro}, "competenciasEspecificas": [competences[n] for n in sorted(competences)], "desarrollos": developments,
        "revision": {"estado": "revisado", "fuenteComprobada": True, "fechaUltimaRevision": "2026-11-03", "metodo": "Extracción estructurada del ODT institucional y cotejo con el PDF publicado en el BOC.", "notas": ["Las abreviaturas de materia y los códigos individuales de saberes son internos del proyecto. numeracionFuente conserva la numeración local impresa.", "Cada versión de una competencia cuyo enunciado cambia entre I y II conserva un id interno distinto y el mismo codigoOficial; las referencias de criterios y bloques identifican la versión del curso.", "Calendario de implantación: primero en 2022/2023 y segundo en 2023/2024."]},
    }
    if meta["optativa"]:
        document["vigencia"] = {"entradaEnVigor": "2025-06-10", "aplicableDesdeCurso": None, "hasta": None, "estado": "vigente"}
        document["fuentes"][0].update({
            "titulo": "Decreto 78/2025, de 2 de junio, por el que se establece el currículo de las materias optativas de la etapa del Bachillerato en la Comunidad Autónoma de Canarias",
            "numero": "112", "fechaPublicacion": "2025-06-09", "cve": "BOC-A-2025-112-2086",
            "urlOficial": "https://sede.gobiernodecanarias.org/boc/boc-a-2025-112-2086.pdf",
            "urlVerificacion": "https://www.gobiernodecanarias.org/boc/2025/112/2086.html", "anexo": "2",
        })
        document["revision"]["notas"][-1] = "El Decreto 78/2025 entra en vigor el 10 de junio de 2025 y no fija un calendario de implantación por curso escolar; aplicableDesdeCurso queda en null."
    # Referencias que figuran en el BOC pero faltan en el ODT de apoyo.
    if meta["codigoInterno"] == "FIS":
        ce = next(c for c in document["competenciasEspecificas"] if c["codigoOficial"] == "6")
        ce["descripcion"]["es"] = [p.replace("Por último, la competencia específica pretende", "Por último, la competencia específica (C6) pretende") for p in ce["descripcion"]["es"]]
    if meta["codigoInterno"] == "PA":
        ce = next(c for c in document["competenciasEspecificas"] if c["codigoOficial"] == "5")
        ce["descripcion"]["es"] = [p.replace("Con la competencia específica se concreta", "Con la competencia específica (C5) se concreta") for p in ce["descripcion"]["es"]]
    if meta["codigoInterno"] == "PSI":
        for ce in document["competenciasEspecificas"]:
            ce["descripcion"]["es"] = [p.replace("perfsonas", "personas").replace("socieomocionales", "socioemocionales") for p in ce["descripcion"]["es"]]
        for development in document["desarrollos"]:
            for block in development["bloquesCompetenciales"]:
                block["explicacion"]["es"] = [p.replace("perfsonas", "personas").replace("socieomocionales", "socioemocionales") for p in block["explicacion"]["es"]]
                if block["competenciaEspecificaRef"] == "ce-5":
                    block["procedencia"]["paginas"] = [350]
    if meta["codigoInterno"] == "TL":
        document["introduccion"]["es"] = [p.replace("el consumo responsable y el medioambiente", "el consumo responsable, la gestión de residuos y el medioambiente") for p in document["introduccion"]["es"]]
        for development in document["desarrollos"]:
            for block in development["bloquesSaberes"]:
                for part in block.get("apartados", [block]):
                    for saber in part["saberes"]:
                        if saber["id"] == "TL.1.C.5":
                            # Restitución confirmada de la preposición omitida: CN-BACH-003.
                            saber["texto"]["es"] = saber["texto"]["es"].replace("proyectos divulgación científica", "proyectos de divulgación científica")
    if meta["codigoInterno"] == "GEO":
        replacements = {
            "2": ("En esta competencia específica ,", "En esta competencia específica (C2),"),
            "3": ("de la competencia específica abordan", "de la competencia específica (C3) abordan"),
            "4": ("de esta competencia específica están", "de esta competencia específica (C4) están"),
            "5": ("de esta competencia específica se centran", "de esta competencia específica (C5) se centran"),
            "6": ("de esta competencia específica se pretende", "de esta competencia específica (C6) se pretende"),
        }
        for ce in document["competenciasEspecificas"]:
            if ce["codigoOficial"] in replacements:
                old, new = replacements[ce["codigoOficial"]]
                ce["descripcion"]["es"] = [p.replace(old, new) for p in ce["descripcion"]["es"]]
        # Corrección confirmada de la redacción publicada: CN-BACH-002.
        criterion = next(c for d in document["desarrollos"] for c in d["criteriosEvaluacion"] if c["codigoOficial"] == "5.1")
        criterion["texto"]["es"] = criterion["texto"]["es"].replace("económicos, y planteando", "económicos y plantear")
    if meta["codigoInterno"] == "FIL":
        for development in document["desarrollos"]:
            for block in development["bloquesSaberes"]:
                for part in block.get("apartados", [block]):
                    for saber in part["saberes"]:
                        if saber["id"].startswith("FIL.1.C.1.8.4."):
                            saber["numeracionFuente"] = saber["id"].rsplit(".", 1)[1]
                        if saber["id"] == "FIL.1.C.1.8":
                            # Eliminación confirmada del punto sobrante: CN-BACH-001.
                            saber["texto"]["es"] = saber["texto"]["es"].removeprefix(".")
        document["revision"]["notas"].append("La sublista de 1.8.4 del bloque III reinicia sus etiquetas como 1, 2 y 3: numeracionFuente conserva esas etiquetas y los id internos mantienen la jerarquía completa.")
    return document


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--limit", type=int, default=67)
    args = parser.parse_args()
    assert 1 <= args.start <= args.limit <= 67
    manifest = json.loads((SUPPORT / "manifest.json").read_text(encoding="utf-8"))
    sources = {"30/2023": pdf_pages()} if args.start <= 43 else {}
    if args.limit > 43:
        sources["78/2025"] = pdf_pages(OPT_PDF, 421)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for meta in manifest[args.start - 1:args.limit]:
        pages, headings = sources[meta["decreto"]]
        document = parse_area(meta, pages, headings)
        (OUTPUT / f"{meta['slug']}.json").write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(meta["nombre"], len(document["competenciasEspecificas"]), sum(len(d["criteriosEvaluacion"]) for d in document["desarrollos"]), shared.saber_count(document))


if __name__ == "__main__":
    main()
