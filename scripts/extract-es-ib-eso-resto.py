"""Extrae los dieciséis currículos restantes del anexo 2 del Decret 42/2025.

Uso: python scripts/extract-es-ib-eso-resto.py [--write]

Los criterios se leen del texto Unicode; los saberes, de las filas del PDF,
para conservar la separación visual de cursos y variantes. El script falla
ante filas sin clasificar y no decide en silencio sobre marcas ausentes.
"""

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

import pdfplumber


sys.dont_write_bytecode = True
MODULE = Path(__file__).with_name("extract-es-ib-eso.py")
SPEC = importlib.util.spec_from_file_location("ib_eso_base", MODULE)
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)

COURSE_LABELS = {
    "Primer i tercer curs", "Primer i segon curs", "Segon i tercer curs",
    "Tercer i quart curs", "Primer curs", "Segon curs", "Tercer curs",
    "Quart curs", "De primer a tercer", "Cultura Clàssica I",
    "Cultura Clàssica II", "Matemàtiques A", "Matemàtiques B",
}
HEADER_COURSES = {
    "1r": 1, "2n": 2, "3r": 3, "4t": 4, "RDI": 2, "RDII": 3,
}


def config(slug, code, courses, assignments):
    return {"slug": slug, "code": code, "courses": courses, "assignments": assignments}


# Cada asignación es curso, índice de criterios, índice de tabla de saberes,
# variante (o None), código interno de saber. Las marcas de tabla se filtran
# por el curso real y se conservan asimismo como cursoOrientativo.
CONFIG = {
    "Biologia i Geologia": config(
        "biologia-i-geologia", "BG", {1: "obligatoria", 3: "obligatoria", 4: "optativa"},
        [(1, 0, 0, None, "BG"), (3, 0, 0, None, "BG"), (4, 1, 1, None, "BG")],
    ),
    "Cultura Clàssica": config(
        "cultura-classica", "CC", {1: "optativa", 2: "optativa", 3: "optativa"},
        [(1, 0, 0, "i", "CCI"), (2, 0, 0, "i", "CCI"),
         (2, 1, 1, "ii", "CCII"), (3, 1, 1, "ii", "CCII")],
    ),
    "Economia i Emprenedoria": config(
        "economia-i-emprenedoria", "EE", {4: "optativa"},
        [(4, 0, 0, None, "EE")],
    ),
    "Educació Física": config(
        "educacio-fisica", "EF", {1: "obligatoria", 2: "obligatoria", 3: "obligatoria", 4: "obligatoria"},
        [(1, 0, 0, None, "EF"), (2, 0, 0, None, "EF"),
         (3, 1, 1, None, "EF"), (4, 1, 1, None, "EF")],
    ),
    "Educació Plàstica, Visual i Audiovisual": config(
        "educacio-plastica-visual-i-audiovisual", "EPVA",
        {2: "obligatoria", 3: "optativa"},
        [(2, 0, 0, None, "EPVA"), (3, 0, 0, None, "EPVA")],
    ),
    "Física i Química": config(
        "fisica-i-quimica", "FQ", {2: "obligatoria", 3: "obligatoria", 4: "optativa"},
        [(2, 0, 0, None, "FQ"), (3, 0, 0, None, "FQ"), (4, 1, 1, None, "FQ")],
    ),
    "Geografia i Història": config(
        "geografia-i-historia", "GH",
        {1: "obligatoria", 2: "obligatoria", 3: "obligatoria", 4: "obligatoria"},
        [(1, 0, 0, None, "GH"), (2, 0, 0, None, "GH"),
         (3, 1, 1, None, "GH"), (4, 1, 1, None, "GH")],
    ),
    "Llengua Castellana i Literatura": config(
        "llengua-castellana-i-literatura", "LCL",
        {1: "obligatoria", 2: "obligatoria", 3: "obligatoria", 4: "obligatoria"},
        [(1, 0, 0, None, "LCL"), (2, 0, 0, None, "LCL"),
         (3, 1, 1, None, "LCL"), (4, 1, 1, None, "LCL")],
    ),
    "Llengua Catalana i Literatura": config(
        "llengua-catalana-i-literatura", "LCT",
        {1: "obligatoria", 2: "obligatoria", 3: "obligatoria", 4: "obligatoria"},
        [(1, 0, 0, None, "LCT"), (2, 0, 0, None, "LCT"),
         (3, 1, 1, None, "LCT"), (4, 1, 1, None, "LCT")],
    ),
    "Llengua Estrangera": config(
        "llengua-estrangera", "LE",
        {1: "obligatoria", 2: "obligatoria", 3: "obligatoria", 4: "obligatoria"},
        [(1, 0, 0, None, "LE"), (2, 1, 0, None, "LE"),
         (3, 2, 1, None, "LE"), (4, 3, 1, None, "LE")],
    ),
    "Matemàtiques": config(
        "matematiques", "MAT",
        {1: "obligatoria", 2: "obligatoria", 3: "obligatoria", 4: "obligatoria"},
        [(1, 0, 0, None, "MAT"), (2, 0, 0, None, "MAT"),
         (3, 0, 0, None, "MAT"), (4, 1, 1, "a", "MATA"),
         (4, 2, 2, "b", "MATB")],
    ),
    "Música": config(
        "musica", "MUS",
        {1: "obligatoria", 3: "optativa", 4: "optativa"},
        [(1, 0, 0, None, "MUS"), (3, 1, 0, None, "MUS"),
         (4, 2, 1, None, "MUS")],
    ),
    "Recursos Digitals": config(
        "recursos-digitals", "RD",
        {2: "optativa", 3: "optativa"},
        [(2, 0, 0, "i", "RDI"), (3, 0, 0, "ii", "RDII")],
    ),
    "Segona Llengua Estrangera": config(
        "segona-llengua-estrangera", "SLE",
        {1: "optativa", 2: "optativa", 3: "optativa", 4: "optativa"},
        [(1, 0, 0, None, "SLE"), (2, 1, 0, None, "SLE"),
         (3, 2, 1, None, "SLE"), (4, 3, 1, None, "SLE")],
    ),
    "Tecnologia": config(
        "tecnologia", "TEC", {4: "optativa"},
        [(4, 0, 0, None, "TEC")],
    ),
    "Tecnologia i Digitalització": config(
        "tecnologia-i-digitalitzacio", "TD",
        {2: "obligatoria", 3: "obligatoria"},
        [(2, 0, 0, None, "TD"), (3, 0, 0, None, "TD")],
    ),
}


def sections(lines):
    markers = [
        (index, "saberes" if base.heading(text, "saberes") else "criterios")
        for index, (_, text) in enumerate(lines)
        if base.heading(text, "saberes") or base.heading(text, "criterios")
    ]
    return [
        (kind, lines[start:markers[position + 1][0] if position + 1 < len(markers) else len(lines)])
        for position, (start, kind) in enumerate(markers)
    ]


def parse_criteria(area, segment):
    trimmed = []
    for page, line in segment:
        if line in COURSE_LABELS:
            break
        trimmed.append((page, line))
    parsed, _ = base.criteria(
        area, trimmed + [(trimmed[-1][0], "Sabers bàsics")], 0
    )
    if area[0] == "Física i Química":
        for item in parsed:
            if item["codigoOficial"] == "3.1":
                item["texto"]["ca"] = item["texto"]["ca"].replace(
                    "interpretar. organitzar", "interpretar, organitzar"
                )
    return parsed


def heading_top(page, kind):
    pattern = (
        r"Sabers? [Bb]àsics"
        if kind == "saberes" else r"Criteris d.avaluació"
    )
    hits = page.search(pattern, regex=True)
    if not hits:
        raise ValueError(f"Cabecera {kind} no encontrada en PDF página {page.page_number}")
    return hits[0]["top"]


def area_title_top(page, name):
    hits = page.search(re.escape(name), regex=True)
    if not hits:
        raise ValueError(f"Cabecera de materia no encontrada: {name}, página {page.page_number}")
    return hits[0]["top"]


def table_rows(pdf, area, segment, next_segment, next_area):
    start_page = segment[0][0]
    start_top = heading_top(pdf.pages[start_page - 1], "saberes")
    if next_segment is not None:
        end_page = next_segment[0][0]
        end_top = heading_top(pdf.pages[end_page - 1], "criterios")
    elif next_area is not None:
        end_page = next_area[1]
        end_top = area_title_top(pdf.pages[end_page - 1], next_area[0])
    else:
        end_page, end_top = 412, pdf.pages[411].height
    rows = []
    for number in range(start_page, end_page + 1):
        page = pdf.pages[number - 1]
        for table in page.find_tables():
            if number == start_page and table.bbox[1] <= start_top:
                continue
            if number == end_page and table.bbox[1] >= end_top:
                continue
            if number == end_page and table.bbox[3] > end_top + 1:
                raise ValueError(f"{area[0]}: tabla invade la sección siguiente en página {number}")
            for cells in table.extract():
                if any(cell and cell.strip() for cell in cells):
                    rows.append((number, cells))
    if not rows:
        raise ValueError(f"{area[0]}: ninguna fila de saberes")
    return rows


def cell_text(value):
    return base.clean(value or "")


def new_block(blocks, title):
    coded = re.match(r"^([A-Z])\.\s+(.+)$", title)
    if coded:
        code, name = coded.groups()
    else:
        code, name = chr(65 + len(blocks)), title
    block = {"codigo": code, "nombre": {"ca": name}, "directos": [], "apartados": []}
    blocks.append(block)
    return block


def parse_knowledge(area, rows):
    blocks = []
    block = None
    pending = ""
    previous = None
    marker_courses = []
    printed = 0
    for page, cells in rows:
        values = [cell_text(value) for value in cells]
        if len(values) >= 3:
            labels = values[-3:] if len(values) >= 4 and all(
                label in HEADER_COURSES for label in values[-3:]
            ) else values[-2:]
            if all(label in HEADER_COURSES for label in labels):
                marker_courses = [HEADER_COURSES[label] for label in labels]
                title = " ".join(value for value in values[:-len(labels)] if value)
                if block and not block["directos"] and not block["apartados"] and not pending:
                    # Una cabecera de bloque puede continuar en la fila siguiente;
                    # la presente, en cambio, inicia siempre un bloque nuevo.
                    pass
                block = new_block(blocks, title)
                pending = ""
                previous = None
                continue
        text_columns = len(values) - len(marker_courses) if len(values) > 1 else 1
        text_values = values[:text_columns]
        text = " ".join(value for value in text_values if value)
        text = re.sub(r"^-\s*", "- ", text)
        marks = values[text_columns:] if len(values) > 1 else []
        selected = [
            course for course, mark in zip(marker_courses, marks) if "x" in mark.lower()
        ]
        starts_continuation = (
            not text_values[0] or (
                text and text[0].islower() and not text.startswith("- ")
            )
        )
        if not text and selected and previous and previous["marcaPendiente"]:
            previous["cursos"] = selected
            previous["marcaPendiente"] = False
            previous["paginas"].add(page)
            continue
        if not text and selected and pending:
            text, pending = pending, ""
        if not text:
            continue
        if base.is_block(text) and not selected and not text.startswith("- "):
            if block and not block["directos"] and not block["apartados"] and not pending:
                block["nombre"]["ca"] = base.clean(block["nombre"]["ca"] + " " + text)
            else:
                if pending:
                    raise ValueError(f"{area[0]}: encabezado sin saber: {pending[:90]}")
                block = new_block(blocks, text)
            previous = None
            continue
        if block is None:
            raise ValueError(f"{area[0]}: fila antes del primer bloque: {text[:90]}")
        if selected and not text.startswith("- ") and previous and previous["marcaPendiente"]:
            previous["texto"]["ca"] = base.clean(previous["texto"]["ca"] + " " + text)
            previous["cursos"] = selected
            previous["marcaPendiente"] = False
            previous["paginas"].add(page)
            continue
        is_saber = text.startswith("- ") or bool(selected)
        if not is_saber and starts_continuation:
            if pending:
                pending = base.clean(pending + " " + text)
            elif previous:
                previous["texto"]["ca"] = base.clean(previous["texto"]["ca"] + " " + text)
                previous["paginas"].add(page)
            else:
                raise ValueError(f"{area[0]}: continuación sin antecedente: {text[:90]}")
            continue
        if not is_saber and previous and (
            previous["marcaPendiente"] or block["directos"]
        ):
            # En las tablas sin subapartados una viñeta larga puede continuar
            # en otra fila aunque la nueva frase empiece por mayúscula.
            previous["texto"]["ca"] = base.clean(previous["texto"]["ca"] + " " + text)
            previous["paginas"].add(page)
            continue
        if not is_saber:
            if pending and not block["directos"] and not block["apartados"]:
                pending = base.clean(pending + " " + text)
            else:
                pending = text
            previous = None
            continue
        if pending:
            if block["directos"]:
                raise ValueError(f"{area[0]}: bloque con saberes directos y apartados")
            part = {
                "codigo": str(len(block["apartados"]) + 1),
                "nombre": {"ca": pending},
                "saberes": [],
            }
            block["apartados"].append(part)
            pending = ""
        group = block["apartados"][-1]["saberes"] if block["apartados"] else block["directos"]
        previous = {
            "texto": {"ca": text[2:] if text.startswith("- ") else text},
            "cursos": selected or None,
            "marcaPendiente": bool(marker_courses and len(values) > 1 and not selected),
            "paginas": {page},
            "numero": len(group) + 1,
        }
        group.append(previous)
        printed += 1
    if pending:
        raise ValueError(f"{area[0]}: encabezado final sin saber: {pending[:90]}")
    if not blocks or not printed:
        raise ValueError(f"{area[0]}: no se extrajeron saberes")
    for item in blocks:
        if not item["directos"] and not item["apartados"]:
            raise ValueError(f"{area[0]}: bloque vacío: {item['nombre']['ca']}")
        groups = [item["directos"]] + [
            part["saberes"] for part in item["apartados"]
        ]
        for group in groups:
            for saber in group:
                if saber["marcaPendiente"]:
                    print(
                        f"SIN MARCA {area[0]} p.{min(saber['paginas'])}:"
                        f" {saber['texto']['ca'][:110]}"
                    )
    return blocks, printed


def complete_broken_page_tables(name, saber_index, blocks, segment):
    """Recupera tres filas cuyo borde superior abierto omite pdfplumber.

    Se cotejaron visualmente las páginas 156, 248 y 249. La aserción sobre
    el texto de pdftotext evita incorporar una fila que ya no esté en el PDF.
    """
    additions = {
        ("Física i Química", 1): [(
            "LA INTERACCIÓ", None, None, 156, None,
            "Forces i pressió en els fluids: efectes de les forces i la pressió sobre els líquids i els gasos estudiant els principis fonamentals com el principi d'Arquímedes, flotabilitat i principi de Pascal.",
        )],
        ("Llengua Catalana i Literatura", 0): [
            (
                "COMUNICACIÓ", "Gèneres discursius", "Anàlisi de la imatge",
                248, [1],
                "Riscs de desinformació, manipulació i vulneració de la privacitat en la xarxa.",
            ),
            (
                "COMUNICACIÓ", "Reconeixement i ús discursiu",
                "Recursos lingüístics per adequar", 249, [1, 2],
                "Ús coherent de les formes verbals en els texts. Els temps de passat en la narració. Correlació temporal en el discurs relatat.",
            ),
        ],
    }
    for block_prefix, part_prefix, before, page, courses, text in additions.get(
        (name, saber_index), []
    ):
        if not any(
            source_page == page and line.startswith("- " + text[:30])
            for source_page, line in segment
        ):
            raise ValueError(f"{name}: falta en la fuente la fila suplementaria: {text[:60]}")
        match = [block for block in blocks if block["nombre"]["ca"].startswith(block_prefix)]
        if len(match) != 1:
            raise ValueError(f"{name}: bloque suplementario ambiguo: {block_prefix}")
        block = match[0]
        if part_prefix:
            part = [
                item for item in block["apartados"]
                if item["nombre"]["ca"].startswith(part_prefix)
            ]
            if len(part) != 1:
                raise ValueError(f"{name}: apartado suplementario ambiguo: {part_prefix}")
            group = part[0]["saberes"]
        else:
            group = block["directos"]
        position = len(group)
        if before:
            matching = [
                index for index, item in enumerate(group)
                if item["texto"]["ca"].startswith(before)
            ]
            if len(matching) != 1:
                raise ValueError(f"{name}: ubicación suplementaria ambigua: {before}")
            position = matching[0]
        group.insert(position, {
            "texto": {"ca": text},
            "cursos": courses,
            "marcaPendiente": False,
            "paginas": {page},
            "numero": 0,
        })
        for index, item in enumerate(group, 1):
            item["numero"] = index
    return blocks


def saber_document(raw, prefix, course, block, part=None):
    code = f"{prefix}.{course}.{block['codigo']}."
    if part is not None:
        code += f"{part['codigo']}."
    code += f"{raw['numero']:02d}"
    result = {
        "id": code,
        "codigoOficial": None,
        "texto": raw["texto"],
        "procedencia": {
            "fuenteRef": base.SOURCE_ID,
            "paginas": sorted(raw["paginas"]),
        },
    }
    if raw["cursos"]:
        result["cursoOrientativo"] = raw["cursos"]
    return result


def selected_blocks(raw_blocks, prefix, course):
    result = []
    for source in raw_blocks:
        block = {"codigo": source["codigo"], "nombre": source["nombre"]}
        if source["apartados"]:
            block["apartados"] = []
            for part in source["apartados"]:
                sabers = [
                    saber_document(item, prefix, course, source, part)
                    for item in part["saberes"]
                    if item["cursos"] is None or course in item["cursos"]
                ]
                if sabers:
                    block["apartados"].append({
                        "codigo": part["codigo"],
                        "nombre": part["nombre"],
                        "saberes": sabers,
                    })
            if not block["apartados"]:
                continue
        else:
            block["saberes"] = [
                saber_document(item, prefix, course, source)
                for item in source["directos"]
                if item["cursos"] is None or course in item["cursos"]
            ]
            if not block["saberes"]:
                continue
        result.append(block)
    if not result:
        raise ValueError(f"{prefix}.{course}: ningún saber tras filtrar las marcas")
    return result


def make_document(area, info, intro, competencies, criteria_sets, saber_sets):
    name, start = area[:2]
    developments = []
    for course, criterion_index, saber_index, variant, prefix in info["assignments"]:
        criteria = []
        for source in criteria_sets[criterion_index]:
            item = json.loads(json.dumps(source, ensure_ascii=False))
            suffix = f"-{variant}" if variant else ""
            item["id"] = (
                f"cri-{course}{suffix}-"
                f"{item['codigoOficial'].replace('.', '-')}"
            )
            criteria.append(item)
        development = {
            "curso": course,
            "criteriosEvaluacion": criteria,
            "bloquesSaberes": selected_blocks(saber_sets[saber_index], prefix, course),
        }
        if variant:
            title = (
                ("Matemàtiques " + variant.upper()) if name == "Matemàtiques"
                else (("Cultura Clàssica " if name == "Cultura Clàssica" else "Recursos Digitals ")
                      + variant.upper())
            )
            development["variante"] = {
                "codigo": variant,
                "nombre": {"ca": title},
            }
        developments.append(development)
    return {
        "$schema": "../../../../schemas/materia.schema.json",
        "schemaVersion": "0.4.0",
        "id": f"es-ib.eso.{info['slug']}",
        "territorio": "es-ib",
        "etapa": "eso",
        "materia": {
            "codigo": info["code"],
            "nombre": {"ca": name},
            "cursos": [
                {"curso": course, "caracter": character}
                for course, character in info["courses"].items()
            ],
        },
        "vigencia": {
            "entradaEnVigor": "2025-08-05",
            "aplicableDesdeCurso": "2025/2026",
            "hasta": None,
            "estado": "vigente",
        },
        "fuentes": [{
            "id": base.SOURCE_ID,
            "tipo": "decreto",
            "titulo": base.SOURCE_TITLE,
            "publicacion": "Butlletí Oficial de les Illes Balears",
            "numero": "103",
            "fechaPublicacion": "2025-08-04",
            "cve": "1197479",
            "urlOficial": base.SOURCE_URL,
            "urlVerificacion": base.VERIFY_URL,
            "anexo": "2",
            "paginasMateria": {"desde": start, "hasta": area[-1]},
        }],
        "introduccion": {"ca": [intro]},
        "competenciasEspecificas": competencies,
        "desarrollos": developments,
        "revision": {
            "estado": "borrador",
            "fuenteComprobada": True,
            "fechaUltimaRevision": "2026-10-25",
            "metodo": "Extracción Unicode de criterios y lectura geométrica de filas y marcas de las tablas del PDF oficial.",
            "notas": [
                "Se conserva el texto publicado en catalán.",
                "Las abreviaturas, identificadores de saber y letras de bloques sin código son internos del proyecto.",
                "Las aclaraciones orientativas se separan del texto de los criterios.",
                "Las marcas de curso de las tablas son orientativas; se conservan en cursoOrientativo.",
                "Los criterios comunes se replican por curso para facilitar la consulta, sin presentarlo como secuenciación oficial.",
            ],
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    all_sections = base.section_lines(base.source_lines())
    found = []
    with pdfplumber.open(base.PDF) as pdf:
        for index, (area, content) in enumerate(all_sections):
            if area[0] not in CONFIG:
                continue
            info = CONFIG[area[0]]
            # Las funciones de la primera tanda son compartidas para CE y CA.
            intro, competencies, _ = base.introduction_and_competencies(
                (area[0], area[1], info["slug"], info["code"],
                 tuple(info["courses"]), ""), content
            )
            groups = sections(content)
            criteria_sets = []
            saber_sets = []
            next_area = (
                all_sections[index + 1][0] if index + 1 < len(all_sections) else None
            )
            for position, (kind, segment) in enumerate(groups):
                if kind == "criterios":
                    criteria_sets.append(parse_criteria(area, segment))
                else:
                    following = (
                        groups[position + 1][1] if position + 1 < len(groups) else None
                    )
                    rows = table_rows(pdf, area, segment, following, next_area)
                    raw, count = parse_knowledge(area, rows)
                    raw = complete_broken_page_tables(
                        area[0], len(saber_sets), raw, segment
                    )
                    saber_sets.append(raw)
                    print(area[0], "tabla", len(saber_sets), "filas de saber", count)
            expected_criteria = 1 + max(item[1] for item in info["assignments"])
            expected_sabers = 1 + max(item[2] for item in info["assignments"])
            if (len(criteria_sets), len(saber_sets)) != (expected_criteria, expected_sabers):
                raise ValueError(
                    f"{area[0]}: secciones CE/CA/saber inesperadas:"
                    f" {len(criteria_sets)}/{len(saber_sets)}"
                )
            source_end = min(content[-1][0], 412) if area[0] == "Tecnologia i Digitalització" else content[-1][0]
            doc = make_document(
                (*area[:2], source_end), info, intro, competencies,
                criteria_sets, saber_sets
            )
            base.validate_document(doc)
            found.append((info["slug"], doc))
            print(
                "OK", info["slug"], "CE", len(competencies),
                "CA", [len(items) for items in criteria_sets],
                "desarrollos", len(doc["desarrollos"]),
            )
    if len(found) != len(CONFIG):
        raise ValueError(f"Faltan materias: {set(CONFIG) - {doc['materia']['nombre']['ca'] for _, doc in found}}")
    if args.write:
        base.DEST.mkdir(parents=True, exist_ok=True)
        for slug, document in found:
            (base.DEST / f"{slug}.json").write_text(
                json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                encoding="utf8",
            )
        print("Escritos", len(found), "JSON")


if __name__ == "__main__":
    main()
