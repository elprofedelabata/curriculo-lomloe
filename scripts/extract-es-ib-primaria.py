"""Extrae las ocho áreas del anexo 2 del Decret balear 41/2025.

Uso: python scripts/extract-es-ib-primaria.py [--write]
El decreto publica criterios por ciclo y concreciones de saberes con marcas
orientativas por curso. Los desarrollos JSON se generan por curso para siete
áreas; Educación en Valores se mantiene completa en el tercer ciclo y conserva
las marcas en cursoOrientativo, sin duplicar ni filtrar saberes.
"""

import argparse
import json
import re
import subprocess
import unicodedata
from pathlib import Path
from xml.etree import ElementTree as ET

import pdfplumber


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "sources/es-ib/normativa/primaria/2025-08-01-decreto-41-2025-curriculo-primaria.pdf"
DEST = ROOT / "data/es-ib/primaria/materias"
SOURCE_ID = "boib-2025-103-decret-41-2025"
SOURCE_TITLE = (
    "Decret 41/2025, d’1 d’agost, pel qual s’estableixen l’ordenació "
    "i el currículum de l’educació primària de les Illes Balears"
)
SOURCE_URL = "https://www.caib.es/eboibfront/eli/es-ib/d/2025/08/01/41/dof/cat/pdf"
VERIFY_URL = "https://www.caib.es/eboibfront/pdf/ca/2025/103/1197477"
AREAS = (
    ("coneixement-del-medi-natural-social-i-cultural", "Coneixement del medi natural, social i cultural", "CMSC", 39, 90, (1, 2, 3)),
    ("educacio-artistica", "Educació Artística", "EA", 91, 108, (1, 2, 3)),
    ("educacio-en-valors-civics-i-etics", "Educació en Valors Cívics i Ètics", "EVCE", 109, 118, (3,)),
    ("educacio-fisica", "Educació Física", "EF", 119, 138, (1, 2, 3)),
    ("llengua-castellana-i-literatura", "Llengua Castellana i Literatura", "LCL", 139, 171, (1, 2, 3)),
    ("llengua-catalana-i-literatura", "Llengua Catalana i Literatura", "LCLCAT", 172, 205, (1, 2, 3)),
    ("llengua-estrangera", "Llengua Estrangera", "LE", 206, 231, (1, 2, 3)),
    ("matematiques", "Matemàtiques", "MAT", 232, 266, (1, 2, 3)),
)
NS = {"x": "http://www.w3.org/1999/xhtml"}


def collapse(value):
    value = re.sub(r"\s+", " ", value).strip().replace(" \u0301", "")
    value = re.sub(r"(?<=\w)- (?=\w)", "-", value)
    return unicodedata.normalize("NFC", value)


def clean_table_guidance(value):
    """Quita guiones de viñeta que la extracción intercala entre palabras."""
    return re.sub(r"(?<=[A-Za-zÀ-ÿ])\s+-\s+(?=[A-Za-zÀ-ÿ])", " ", value)


def poppler_text(*options):
    return subprocess.check_output(
        ["pdftotext", *options, "-enc", "UTF-8", str(PDF), "-"],
        stderr=subprocess.DEVNULL,
    ).decode("utf8")


def raw_pages():
    pages = poppler_text("-raw").split("\f")
    assert len(pages) >= 286
    result = []
    for page in pages:
        result.append([
            line.strip() for line in page.splitlines()
            if line.strip() and not line.startswith((
                "Núm. 103", "4 d’agost de 2025", "Fascicle 214",
                "https://www.caib.es/",
            ))
        ])
    return result


def bbox_pages():
    xml = poppler_text("-bbox-layout")
    xml = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", xml)
    root = ET.fromstring(xml)
    pages = []
    for page in root.findall(".//x:page", NS):
        lines = []
        for line in page.findall(".//x:line", NS):
            words = [
                (
                    float(word.attrib["xMin"]),
                    float(word.attrib["xMax"]),
                    float(word.attrib["yMin"]),
                    float(word.attrib["yMax"]),
                    word.text or "",
                )
                for word in line.findall("x:word", NS)
            ]
            if words:
                lines.append(words)
        pages.append(lines)
    assert len(pages) == 286
    return pages


def cell_text(lines, box, y_slack=0.5):
    if box is None:
        return ""
    x1, y1, x2, y2 = box
    parts = []
    for line in lines:
        words = [
            word for word in line
            if x1 - 0.5 <= (word[0] + word[1]) / 2 <= x2 + 0.5
            and y1 - y_slack <= (word[2] + word[3]) / 2 < y2 + y_slack
        ]
        if words:
            parts.append((
                min(word[2] for word in words),
                " ".join(word[4] for word in sorted(words, key=lambda word: word[0])),
            ))
    return collapse(" ".join(text for _, text in sorted(parts))).lstrip("−–- ")


def source_pages(item):
    item["procedencia"]["paginas"] = sorted(item["procedencia"]["paginas"])


def narrative(area, pages):
    slug, name, _code, start, end, _cycles = area
    lines = [(page, line) for page in range(start, end + 1) for line in pages[page - 1]]
    area_index = next(i for i, (_, line) in enumerate(lines) if line == name)
    ce_index = next(i for i, (_, line) in enumerate(lines) if line == "Competències específiques")
    criteria_index = next(
        i for i, (_, line) in enumerate(lines)
        if re.match(r"^Criteris d.avaluació$", line)
    )
    intro = collapse(" ".join(line for _, line in lines[area_index + 1:ce_index]))
    groups = []
    for page, line in lines[ce_index + 1:criteria_index]:
        if re.match(r"^CE [1-9][0-9]*\s", line):
            groups.append([])
        if not groups:
            raise ValueError(f"{slug}: línea anterior a CE: {line}")
        groups[-1].append((page, line))
    competencies = []
    for expected, group in enumerate(groups, 1):
        text = collapse(" ".join(line for _, line in group))
        match = re.match(rf"^CE {expected}\s+(.+?\.)\s+(.+)", text)
        if not match:
            raise ValueError(f"{slug}: competencia {expected} sin descripción: {text[:180]}")
        enunciado, description = match.groups()
        descriptor_match = re.search(r"Descriptors que es lliguen a aquesta competència específica:\s*(.*)$", description)
        refs = []
        if descriptor_match:
            refs = re.findall(r"\b[A-Z]{2,}[0-9]+(?:\.[0-9]+)?\b", descriptor_match.group(1))
            description = description[:descriptor_match.start()].strip()
        competencies.append({
            "id": f"ce-{expected}",
            "codigoOficial": str(expected),
            "enunciado": {"ca": enunciado},
            "descripcion": {"ca": [description]},
            "descriptoresOperativosRefs": list(dict.fromkeys(refs)),
            "procedencia": {"fuenteRef": SOURCE_ID, "paginas": sorted({page for page, _ in group})},
        })
    return intro, competencies


def append_text(item, field, value, page):
    if not value:
        return
    value = clean_table_guidance(value)
    paragraphs = item.setdefault(field, {"ca": []})["ca"]
    if paragraphs and value[0].islower():
        paragraphs[-1] = clean_table_guidance(collapse(paragraphs[-1] + " " + value))
    else:
        paragraphs.append(value)
    item["procedencia"]["paginas"].add(page)


def extract_tables(area, pdf, words):
    slug, _name, code, start, end, allowed_cycles = area
    cycles = {
        cycle: {"criteria": [], "blocks": {}}
        for cycle in allowed_cycles
    }
    mode = "narrative"
    cycle = None
    block_letter = None
    block_name = None
    subsection_code = None
    subsection_name = None
    current_criterion = None
    current_saber = None
    criterion_split = 274.0
    pending_guidance = []
    last_right_span_end = 0
    last_right_span_page = None
    last_left_span_end = 0
    last_left_span_page = None
    diagnostics = []

    for page_no in range(start, end + 1):
        page = pdf.pages[page_no - 1]
        tables = page.find_tables()
        events = []
        for table in tables:
            for row in table.rows:
                events.append((row.bbox[1], "row", table, row))
        for line in words[page_no - 1]:
            heading = collapse(" ".join(word[4] for word in line))
            if re.match(r"^Criteris d.avaluació$", heading):
                events.append((line[0][2], "mode", "criteria", None))
            elif heading == "Sabers bàsics":
                events.append((line[0][2], "mode", "sabers", None))
        for _, kind, first, second in sorted(events, key=lambda event: event[0]):
            if kind == "mode":
                mode = first
                cycle = allowed_cycles[0] if mode == "criteria" else None
                current_criterion = None
                current_saber = None
                last_right_span_end = 0
                last_left_span_end = 0
                continue
            table, row = first, second
            if mode == "criteria":
                if len(table.columns) >= 2 and row.cells[1] is not None:
                    criterion_split = row.cells[1][0]
                elif table.bbox[0] > 250:
                    criterion_split = table.bbox[0]
                x1, y1, x2, y2 = row.bbox
                full = cell_text(words[page_no - 1], row.cells[0])
                left_cell = row.cells[0] if row.cells[0] is not None and row.cells[0][0] < criterion_split - 5 else None
                if left_cell is not None:
                    left = cell_text(words[page_no - 1], left_cell)
                    last_left_span_end = left_cell[3]
                    last_left_span_page = page_no
                elif last_left_span_page == page_no and last_left_span_end > y1 + 0.1:
                    left = ""
                else:
                    left = cell_text(words[page_no - 1], (150, y1, criterion_split, y2), y_slack=0)
                right_cells = [
                    box for box in row.cells if box is not None
                    and box[0] >= criterion_split - 2 and box[2] - box[0] > 100
                ]
                right = cell_text(words[page_no - 1], max(right_cells, key=lambda box: box[2] - box[0])) if right_cells else ""
                if not left and not right:
                    continue
                if re.match(r"^CE [0-9]+\s", full):
                    cycle = allowed_cycles[0]
                    current_criterion = None
                    last_right_span_end = 0
                    last_left_span_end = 0
                    continue
                cycle_match = re.match(r"^(PRIMER|SEGON|TERCER) CICLE\b", full)
                if cycle_match:
                    cycle = {"PRIMER": 1, "SEGON": 2, "TERCER": 3}[cycle_match.group(1)]
                    current_criterion = None
                    last_right_span_end = 0
                    last_left_span_end = 0
                    continue
                if cycle not in cycles:
                    if left or right:
                        diagnostics.append((page_no, "criterio sin ciclo", left[:50], right[:50]))
                    continue
                criterion_match = re.match(r"^CA\.?\s*([0-9]+)\.([0-9]+)\.?\s*(.+)", left)
                if criterion_match:
                    ce, number, text = criterion_match.groups()
                    previous_criterion = current_criterion
                    current_criterion = {
                        "codigoOficial": f"{ce}.{number}",
                        "competenciaEspecificaRef": f"ce-{ce}",
                        "texto": {"ca": text},
                        "saberesBasicosRefs": [],
                        "procedencia": {"fuenteRef": SOURCE_ID, "paginas": {page_no}},
                    }
                    if (not right and previous_criterion and previous_criterion.get("aclaraciones")
                            and last_right_span_page == page_no and last_right_span_end >= y2 - 0.5):
                        # Una única celda de aclaración puede abarcar dos criterios consecutivos.
                        current_criterion["aclaraciones"] = {
                            "ca": previous_criterion["aclaraciones"]["ca"].copy()
                        }
                    cycles[cycle]["criteria"].append(current_criterion)
                    for pending_text, pending_page in pending_guidance:
                        append_text(current_criterion, "aclaraciones", pending_text, pending_page)
                    pending_guidance.clear()
                elif left and current_criterion:
                    current_criterion["texto"]["ca"] = collapse(current_criterion["texto"]["ca"] + " " + left)
                    current_criterion["procedencia"]["paginas"].add(page_no)
                elif left:
                    # Las cabeceras CE que se parten en varias filas no son criterios.
                    pass
                if right and current_criterion:
                    append_text(current_criterion, "aclaraciones", right, page_no)
                    if right_cells:
                        last_right_span_end = max(box[3] for box in right_cells)
                        last_right_span_page = page_no
                elif right:
                    pending_guidance.append((right, page_no))

            elif mode == "sabers":
                if len(table.columns) < 4:
                    continue
                first_cell = row.cells[0]
                first_text = cell_text(words[page_no - 1], first_cell)
                if re.match(r"^(?:[A-Z]|[0-9]+)\.$", first_text) and len(row.cells) > 1:
                    first_text = collapse(first_text + " " + cell_text(words[page_no - 1], row.cells[1]))
                width = table.bbox[2] - table.bbox[0]
                heading = first_cell is not None and first_cell[2] - first_cell[0] > width * 0.52
                if re.match(r"^(?:[A-Z]\.|[0-9]+\.|PRIMER CICLE|SEGON CICLE|TERCER CICLE)(?:\s|$)", first_text):
                    heading = True
                if heading:
                    block_match = re.match(r"^([A-Z])\.\s+(.+)", first_text)
                    subsection_match = re.match(r"^([0-9]+)\.\s+(.+)", first_text)
                    cycle_match = re.match(r"^(PRIMER|SEGON|TERCER) CICLE\b", first_text)
                    if block_match:
                        block_letter, block_name = block_match.groups()
                        subsection_code = subsection_name = None
                        cycle = None
                        current_saber = None
                    elif subsection_match:
                        subsection_code, subsection_name = subsection_match.groups()
                        cycle = None
                        current_saber = None
                    elif cycle_match:
                        cycle = {"PRIMER": 1, "SEGON": 2, "TERCER": 3}[cycle_match.group(1)]
                        current_saber = None
                    continue
                if cycle not in cycles or block_letter is None:
                    continue
                left = cell_text(words[page_no - 1], first_cell)
                x1, y1, x2, y2 = row.bbox
                marker_start = x2 - 47.5
                right_cells = [
                    box for box in row.cells if box is not None
                    and box[0] >= x1 + 75 and box[2] <= marker_start + 5
                    and box[2] - box[0] > 100
                ]
                right = cell_text(words[page_no - 1], max(right_cells, key=lambda box: box[2] - box[0])) if right_cells else ""
                if not left and not right:
                    continue
                course_a, course_b = cycle * 2 - 1, cycle * 2
                right = clean_table_guidance(right)
                mid = x2 - 23.75
                mark_a = cell_text(words[page_no - 1], (marker_start, y1, mid, y2)).lower()
                mark_b = cell_text(words[page_no - 1], (mid, y1, x2, y2)).lower()
                courses = [course for course, mark in ((course_a, mark_a), (course_b, mark_b)) if "x" in mark]
                block = cycles[cycle]["blocks"].setdefault(block_letter, {
                    "codigo": block_letter,
                    "nombre": {"ca": block_name},
                    "apartados": {},
                    "saberes": [],
                })
                if subsection_code is not None:
                    group = block["apartados"].setdefault(subsection_code, {
                        "codigo": subsection_code,
                        "nombre": {"ca": subsection_name},
                        "saberes": [],
                    })["saberes"]
                else:
                    group = block["saberes"]
                continuation = bool(
                    current_saber and (
                        (right and not courses and right[0].islower())
                        or (left and (left[0].islower() or left.startswith("(")))
                    )
                )
                if left and continuation:
                    current_saber["texto"]["ca"] = collapse(current_saber["texto"]["ca"] + " " + left)
                    current_saber["procedencia"]["paginas"].add(page_no)
                elif left:
                    current_saber = {
                        "texto": {"ca": left},
                        "codigoOficial": None,
                        "concrecionesPorCurso": [],
                        "procedencia": {"fuenteRef": SOURCE_ID, "paginas": {page_no}},
                    }
                    group.append(current_saber)
                if right and current_saber:
                    items = current_saber["concrecionesPorCurso"]
                    if not courses and right[0].islower() and items:
                        items[-1]["texto"] = clean_table_guidance(collapse(items[-1]["texto"] + " " + right))
                    else:
                        if not courses:
                            diagnostics.append((page_no, "concreción sin marca de curso", left[:40], right[:70]))
                        items.append({"texto": right, "cursos": courses, "pagina": page_no})
                    current_saber["procedencia"]["paginas"].add(page_no)
                elif right:
                    diagnostics.append((page_no, "concreción sin saber", "", right[:70]))

    for cycle, content in cycles.items():
        for criterion in content["criteria"]:
            if not criterion.get("aclaraciones"):
                diagnostics.append((cycle, "criterio sin aclaración", criterion["codigoOficial"], ""))
        for block in content["blocks"].values():
            groups = [block["saberes"]] + [part["saberes"] for part in block["apartados"].values()]
            for group in groups:
                for saber in group:
                    if not saber["concrecionesPorCurso"]:
                        diagnostics.append((cycle, "saber sin concreción", saber["texto"]["ca"][:60], ""))
    if pending_guidance:
        diagnostics.append((end, "aclaraciones sin criterio posterior", len(pending_guidance), ""))
    return cycles, diagnostics


def developments_from_cycles(cycles, code):
    developments = []
    for cycle, content in cycles.items():
        # Valores se imparte en alguno de los cursos del tercer ciclo: las marcas
        # de la tabla orientan la secuenciación, no determinan dos currículos.
        for course in ((None,) if code == "EVCE" else (cycle * 2 - 1, cycle * 2)):
            number = cycle if course is None else course
            criteria = []
            for source in content["criteria"]:
                criterion = {
                    **source,
                    "id": f"cri-{number}-{source['codigoOficial'].replace('.', '-')}",
                    "procedencia": {**source["procedencia"]},
                }
                source_pages(criterion)
                criteria.append(criterion)
            blocks = []
            for source_block in content["blocks"].values():
                block = {
                    "codigo": source_block["codigo"],
                    "nombre": source_block["nombre"],
                }
                def filtered(source_saberes, part_code=None):
                    result = []
                    for index, source_saber in enumerate(source_saberes, 1):
                        items = [
                            item for item in source_saber["concrecionesPorCurso"]
                            if course is None or course in item["cursos"]
                        ]
                        if not items:
                            continue
                        identifier = f"{code}.{number}.{block['codigo']}."
                        if part_code is not None:
                            identifier += f"{part_code}."
                        identifier += f"{index:02d}"
                        saber = {
                            "id": identifier,
                            "codigoOficial": None,
                            "texto": source_saber["texto"],
                            "concreciones": {"ca": [item["texto"] for item in items]},
                            "procedencia": {
                                "fuenteRef": SOURCE_ID,
                                "paginas": sorted(source_saber["procedencia"]["paginas"]),
                            },
                        }
                        if course is None:
                            suggested_courses = {tuple(item["cursos"]) for item in items}
                            if len(suggested_courses) != 1:
                                raise ValueError(
                                    f"{code}: concreciones de un saber con marcas de curso distintas: {identifier}"
                                )
                            saber["cursoOrientativo"] = list(next(iter(suggested_courses)))
                        result.append(saber)
                    return result
                if source_block["apartados"]:
                    block["apartados"] = []
                    for part in source_block["apartados"].values():
                        sabers = filtered(part["saberes"], part["codigo"])
                        if sabers:
                            block["apartados"].append({
                                "codigo": part["codigo"],
                                "nombre": part["nombre"],
                                "saberes": sabers,
                            })
                    if not block["apartados"]:
                        continue
                else:
                    block["saberes"] = filtered(source_block["saberes"])
                    if not block["saberes"]:
                        continue
                blocks.append(block)
            developments.append({
                "ciclo" if course is None else "curso": number,
                "criteriosEvaluacion": criteria,
                "bloquesSaberes": blocks,
            })
    return developments


def document(area, intro, competencies, developments):
    slug, name, code, start, end, cycles = area
    return {
        "$schema": "../../../../schemas/materia.schema.json",
        "schemaVersion": "0.4.0",
        "id": f"es-ib.primaria.{slug}",
        "territorio": "es-ib",
        "etapa": "primaria",
        "materia": {
            "codigo": code,
            "nombre": {"ca": name},
            **(
                {"ciclos": [{"ciclo": 3, "caracter": "obligatoria"}]}
                if code == "EVCE" else
                {"cursos": [
                    {"curso": course, "caracter": "obligatoria"}
                    for cycle in cycles for course in (cycle * 2 - 1, cycle * 2)
                ]}
            ),
        },
        "vigencia": {
            "entradaEnVigor": "2025-08-05",
            "aplicableDesdeCurso": "2025/2026",
            "hasta": None,
            "estado": "vigente",
        },
        "fuentes": [{
            "id": SOURCE_ID,
            "tipo": "decreto",
            "titulo": SOURCE_TITLE,
            "publicacion": "Butlletí Oficial de les Illes Balears",
            "numero": "103",
            "fechaPublicacion": "2025-08-04",
            "cve": "1197477",
            "urlOficial": SOURCE_URL,
            "urlVerificacion": VERIFY_URL,
            "anexo": "2",
            "paginasMateria": {"desde": start, "hasta": end},
        }],
        "introduccion": {"ca": [intro]},
        "competenciasEspecificas": competencies,
        "desarrollos": developments,
        "revision": {
            "estado": "borrador",
            "fuenteComprobada": True,
            "fechaUltimaRevision": "2026-10-25" if code == "EVCE" else "2026-10-23",
            "metodo": "Extracción del texto Unicode y de la geometría de las tablas del PDF oficial, con cotejo visual.",
            "notas": [
                "Se conserva el texto oficial en catalán.",
                (
                    "Los criterios se mantienen una sola vez en el tercer ciclo."
                    if code == "EVCE" else
                    "Los criterios se publican por ciclo y se replican en los dos cursos del ciclo para facilitar su consulta; esta duplicación no es una secuenciación oficial."
                ),
                (
                    "Se conservan todos los saberes del tercer ciclo; cursoOrientativo recoge las marcas de 5.º y 6.º de la tabla sin restringir su aplicación."
                    if code == "EVCE" else
                    "Los saberes se asignan a cursos conforme a las marcas de las concreciones de la tabla oficial."
                ),
                "Las abreviaturas de área y los identificadores de saber son internos del proyecto, no códigos oficiales.",
                "Las aclaraciones y concreciones se guardan separadas del texto principal.",
                *(
                    ["El artículo 10.2 declara orientativa la secuenciación por cursos de los saberes. El artículo 11.2 sitúa esta área en alguno de los cursos del tercer ciclo. El desarrollo único por ciclo no presupone que se imparta obligatoriamente en ambos años."]
                    if code == "EVCE" else []
                ),
            ],
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    pages = raw_pages()
    words = bbox_pages()
    results = []
    diagnostics = []
    with pdfplumber.open(PDF) as pdf:
        for area in AREAS:
            intro, competencies = narrative(area, pages)
            cycles, issues = extract_tables(area, pdf, words)
            printed_criteria = sum(
                bool(re.match(r"^CA\.?\s*[0-9]+\.[0-9]+", line))
                for page in range(area[3], area[4] + 1)
                for line in pages[page - 1]
            )
            parsed_criteria = sum(len(content["criteria"]) for content in cycles.values())
            if parsed_criteria != printed_criteria:
                issues.append((area[3], "recuento CA distinto del texto oficial", parsed_criteria, printed_criteria))
            developments = developments_from_cycles(cycles, area[2])
            results.append((area[0], document(area, intro, competencies, developments)))
            diagnostics.extend((area[0], *entry) for entry in issues)
            print(area[0], "CE", len(competencies), "CA/ciclo",
                  [len(content["criteria"]) for content in cycles.values()],
                  "saberes/ciclo", [
                      sum(len(block["saberes"]) + sum(len(part["saberes"]) for part in block["apartados"].values())
                          for block in content["blocks"].values())
                      for content in cycles.values()
                  ])
    if diagnostics:
        for issue in diagnostics[:100]:
            print("DIAGNÓSTICO", issue)
        raise SystemExit(f"{len(diagnostics)} anomalías de extracción")
    if args.write:
        DEST.mkdir(parents=True, exist_ok=True)
        for slug, item in results:
            (DEST / f"{slug}.json").write_text(
                json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
            )
        print("Escritos", len(results), "JSON en", DEST)


if __name__ == "__main__":
    main()
