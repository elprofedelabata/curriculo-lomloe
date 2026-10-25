"""Extrae el anexo 2 (Infantil) del Decreto balear 40/2025.

Uso: python scripts/extract-es-ib-infantil.py [--write]
Sin --write solo muestra el inventario y verifica recuentos. La geometría de
las tablas se obtiene con pdfplumber; Poppler aporta el texto Unicode de cada
celda, pues la codificación de caracteres del PDF no se lee bien en pdfplumber.
"""

import argparse
import json
import re
import subprocess
import unicodedata
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

import pdfplumber


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "sources/es-ib/normativa/infantil/2025-08-01-decreto-40-2025-curriculo-infantil.pdf"
DEST = ROOT / "data/es-ib/infantil/materias"
SOURCE_ID = "boib-2025-102-decret-40-2025"
SOURCE_TITLE = (
    "Decret 40/2025, d’1 d’agost, pel qual s’estableixen l’ordenació "
    "i el currículum de l’educació infantil a les Illes Balears"
)
SOURCE_URL = "https://www.caib.es/eboibfront/eli/es-ib/d/2025/08/01/40/dof/cat/pdf"
VERIFY_URL = "https://www.caib.es/eboibfront/pdf/ca/2025/102/1197505"
AREAS = (
    ("creixement-en-harmonia", "Creixement en Harmonia", "CHA", 23, 37, 4),
    ("descobriment-i-exploracio-de-lentorn", "Descobriment i Exploració de l’Entorn", "DEE", 38, 50, 3),
    ("comunicacio-i-representacio-de-la-realitat", "Comunicació i Representació de la Realitat", "CRR", 51, 71, 5),
)
NS = {"x": "http://www.w3.org/1999/xhtml"}


def collapse(value):
    text = re.sub(r"\s+", " ", value).strip()
    # Dos acentos aparecen duplicados como glifos sueltos tras ó en la capa de texto.
    text = text.replace(" \u0301", "")
    # La separación entre líneas del PDF puede quedar tras un guion catalán.
    text = re.sub(r"(?<=\w)- (?=\w)", "-", text)
    return unicodedata.normalize("NFC", text)


def poppler_text(*options):
    return subprocess.check_output(
        ["pdftotext", *options, "-enc", "UTF-8", str(PDF), "-"], stderr=subprocess.DEVNULL
    ).decode("utf-8")


def raw_pages():
    pages = poppler_text("-raw").split("\f")
    assert len(pages) >= 86
    cleaned = []
    for page in pages:
        lines = []
        for raw_line in page.splitlines():
            line = raw_line.strip()
            if not line or line.startswith(
                ("Núm. 102", "2 d’agost de 2025", "Fascicle 210", "https://www.caib.es/")
            ):
                continue
            lines.append(line)
        cleaned.append(lines)
    return cleaned


def bbox_pages():
    xml = poppler_text("-bbox-layout")
    # El glifo de viñeta aparece como U+0010 en este PDF y no es XML válido.
    xml = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", xml)
    root = ET.fromstring(xml)
    pages = []
    for page in root.findall(".//x:page", NS):
        lines = []
        for line in page.findall(".//x:line", NS):
            words = []
            for word in line.findall("x:word", NS):
                words.append(
                    (
                        float(word.attrib["xMin"]),
                        float(word.attrib["xMax"]),
                        float(word.attrib["yMin"]),
                        float(word.attrib["yMax"]),
                        word.text or "",
                    )
                )
            if words:
                lines.append(words)
        pages.append(lines)
    assert len(pages) == 86
    return pages


def cell_text(lines, box):
    if box is None:
        return ""
    x1, y1, x2, y2 = box
    parts = []
    for line in lines:
        words = [
            word
            for word in line
            if x1 - 0.5 <= (word[0] + word[1]) / 2 <= x2 + 0.5
            and y1 - 0.5 <= (word[2] + word[3]) / 2 <= y2 + 0.5
        ]
        if words:
            parts.append(
                (min(word[2] for word in words), " ".join(word[4] for word in sorted(words, key=lambda word: word[0])))
            )
    return collapse(" ".join(text for _, text in sorted(parts, key=lambda entry: entry[0]))).lstrip("−–- ")


def narrative(area, pages):
    slug, _name, _code, start, end, expected_ce = area
    lines = [(page_no, line) for page_no in range(start, end + 1) for line in pages[page_no - 1]]
    area_index = next(i for i, (_, line) in enumerate(lines) if line.startswith("Àrea "))
    ce_index = next(i for i, (_, line) in enumerate(lines) if line == "Competències específiques")
    criteria_index = next(i for i, (_, line) in enumerate(lines) if line == "Criteris d’avaluació")
    intro = collapse(" ".join(line for _, line in lines[area_index + 1 : ce_index]))
    groups = []
    for page_no, line in lines[ce_index + 1 : criteria_index]:
        if re.match(r"^CE [1-9]\s", line):
            groups.append([])
        if not groups:
            raise ValueError(f"Texto sin competencia en {slug}: {line}")
        groups[-1].append((page_no, line))
    if len(groups) != expected_ce:
        raise ValueError(f"{slug}: se esperaban {expected_ce} competencias, hay {len(groups)}")
    result = []
    for number, group in enumerate(groups, start=1):
        whole = collapse(" ".join(line for _, line in group))
        match = re.match(rf"^CE {number}\s+(.+?\.)\s+(.+)$", whole)
        if not match:
            raise ValueError(f"Competencia sin descripción: {slug} CE {number}")
        result.append(
            {
                "id": f"ce-{number}",
                "codigoOficial": str(number),
                "enunciado": {"ca": match.group(1)},
                "descripcion": {"ca": [match.group(2)]},
                "descriptoresOperativosRefs": [],
                "procedencia": {"fuenteRef": SOURCE_ID, "paginas": sorted({page for page, _ in group})},
            }
        )
    return intro, result


def append_guidance(item, field, text, page):
    if not text:
        return
    value = item.setdefault(field, {"ca": []})["ca"]
    # Un fragmento que continúa al cambiar de página no inicia otra viñeta.
    if text[0].islower() and value:
        value[-1] = collapse(value[-1] + " " + text)
    else:
        value.append(text)
    item["procedencia"]["paginas"].add(page)


def parse_area_tables(area, pdf, word_pages):
    slug, _name, code, start, end, _expected_ce = area
    developments = {
        cycle: {"ciclo": cycle, "criteriosEvaluacion": [], "bloquesSaberes": []}
        for cycle in (1, 2)
    }
    blocks = {}
    mode = "criterios"
    cycle = None
    block_letter = None
    block_name = None
    current_criterion = None
    current_saber = None
    diagnostics = []

    for page_no in range(start, end + 1):
        page = pdf.pages[page_no - 1]
        tables = [table for table in page.find_tables() if len(table.columns) == 2]
        events = []
        for table in tables:
            for row in table.rows:
                events.append((row.bbox[1], "row", table, row))
        for line in word_pages[page_no - 1]:
            heading = collapse(" ".join(word[4] for word in line))
            if not re.match(r"^[A-I]\.\s+[A-ZÀ-Ü]", heading):
                continue
            x, y = line[0][0], line[0][2]
            if not any(
                table.bbox[0] <= x <= table.bbox[2]
                and table.bbox[1] <= y <= table.bbox[3]
                for table in tables
            ):
                events.append((y, "heading", heading, None))
        for _, kind, first, second in sorted(events, key=lambda event: event[0]):
            if kind == "heading":
                mode = "saberes"
                block_letter, block_name = first[0], collapse(first[3:])
                cycle = None
                current_saber = None
                continue
            table, row = first, second
            if len(table.columns) == 2:
                left = cell_text(word_pages[page_no - 1], row.cells[0])
                right = cell_text(word_pages[page_no - 1], row.cells[1])
                if not right and row.cells[0] and row.cells[1] is None:
                    x1, y1, x2, y2 = row.cells[0]
                    if x2 < table.bbox[2] - 10:
                        right = cell_text(
                            word_pages[page_no - 1], (x2, y1, table.bbox[2], y2)
                        )
                if not left and not right:
                    continue
                if re.match(r"^CE [1-9]\s", left) and not right:
                    continue
                block_match = re.match(r"^([A-I])\.\s+(.+)", left)
                if block_match and not right:
                    mode = "saberes"
                    block_letter = block_match.group(1)
                    block_name = block_match.group(2)
                    cycle = None
                    current_saber = None
                    continue
                if left in ("PRIMER CICLE", "SEGON CICLE"):
                    cycle = 1 if left.startswith("PRIMER") else 2
                    current_criterion = None
                    current_saber = None
                    continue
                if cycle is None:
                    if mode == "saberes" and left and not right and left.isupper():
                        block_name = collapse(block_name + " " + left)
                    continue

                if mode == "criterios":
                    match = re.match(r"^CA\s+([1-9])\.([1-9])\.?\s+(.+)", left)
                    if match:
                        ce_no, criterion_no, text = match.groups()
                        current_criterion = {
                            "id": f"cri-{cycle}-{ce_no}-{criterion_no}",
                            "codigoOficial": f"{ce_no}.{criterion_no}",
                            "competenciaEspecificaRef": f"ce-{ce_no}",
                            "texto": {"ca": text},
                            "saberesBasicosRefs": [],
                            "procedencia": {"fuenteRef": SOURCE_ID, "paginas": {page_no}},
                        }
                        developments[cycle]["criteriosEvaluacion"].append(current_criterion)
                    elif left and current_criterion:
                        current_criterion["texto"]["ca"] = collapse(
                            current_criterion["texto"]["ca"] + " " + left
                        )
                        current_criterion["procedencia"]["paginas"].add(page_no)
                    elif left:
                        diagnostics.append((page_no, "criterio suelto", left[:60], right[:60]))
                    if right and current_criterion:
                        append_guidance(current_criterion, "aclaraciones", right, page_no)
                    elif right:
                        diagnostics.append((page_no, "aclaración suelta", left[:60], right[:60]))
                else:
                    if block_letter is None:
                        raise ValueError(f"Bloque no localizado en {slug}, pág. {page_no}")
                    # El BOIB omite el punto final de esta entrada concreta.
                    if code == "CRR" and cycle == 2 and block_letter == "E" and left == "La biblioteca escolar":
                        left += "."
                    key = (cycle, block_letter)
                    if key not in blocks:
                        blocks[key] = {
                            "codigo": block_letter,
                            "nombre": {"ca": block_name},
                            "saberes": [],
                        }
                        developments[cycle]["bloquesSaberes"].append(blocks[key])
                    if left and left[0].islower() and current_saber:
                        current_saber["texto"]["ca"] = collapse(
                            current_saber["texto"]["ca"] + " " + left
                        )
                        current_saber["procedencia"]["paginas"].add(page_no)
                    elif left:
                        current_saber = {
                            "id": f"{code}.{cycle}.{block_letter}.{len(blocks[key]['saberes']) + 1:02d}",
                            "codigoOficial": None,
                            "texto": {"ca": left},
                            "procedencia": {"fuenteRef": SOURCE_ID, "paginas": {page_no}},
                        }
                        blocks[key]["saberes"].append(current_saber)
                    if right and current_saber:
                        append_guidance(current_saber, "concreciones", right, page_no)
                    elif right:
                        diagnostics.append((page_no, "concreción suelta", left[:60], right[:60]))

    for development in developments.values():
        for item in development["criteriosEvaluacion"]:
            if not item.get("aclaraciones"):
                diagnostics.append((item["procedencia"]["paginas"], "criterio sin aclaraciones", item["id"], ""))
        for block in development["bloquesSaberes"]:
            for item in block["saberes"]:
                if not item.get("concreciones"):
                    diagnostics.append((item["procedencia"]["paginas"], "saber sin concreciones", item["id"], ""))
    return list(developments.values()), diagnostics


def finish_provenance(document):
    for development in document["desarrollos"]:
        for item in development["criteriosEvaluacion"]:
            item["procedencia"]["paginas"] = sorted(item["procedencia"]["paginas"])
        for block in development["bloquesSaberes"]:
            for item in block["saberes"]:
                item["procedencia"]["paginas"] = sorted(item["procedencia"]["paginas"])


def make_document(area, intro, competencies, developments):
    slug, name, code, start, end, _expected_ce = area
    document = {
        "$schema": "../../../../schemas/materia.schema.json",
        "schemaVersion": "0.4.0",
        "id": f"es-ib.infantil.{slug}",
        "territorio": "es-ib",
        "etapa": "infantil",
        "materia": {
            "codigo": code,
            "nombre": {"ca": name},
            "ciclos": [{"ciclo": cycle, "caracter": "obligatoria"} for cycle in (1, 2)],
        },
        "vigencia": {
            "entradaEnVigor": "2025-08-03",
            "aplicableDesdeCurso": "2025/2026",
            "hasta": None,
            "estado": "vigente",
        },
        "fuentes": [
            {
                "id": SOURCE_ID,
                "tipo": "decreto",
                "titulo": SOURCE_TITLE,
                "publicacion": "Butlletí Oficial de les Illes Balears",
                "numero": "102",
                "fechaPublicacion": "2025-08-02",
                "cve": "1197505",
                "urlOficial": SOURCE_URL,
                "urlVerificacion": VERIFY_URL,
                "anexo": "2",
                "paginasMateria": {"desde": start, "hasta": end},
            }
        ],
        "introduccion": {"ca": [intro]},
        "competenciasEspecificas": competencies,
        "desarrollos": developments,
        "revision": {
            "estado": "revisado",
            "fuenteComprobada": True,
            "fechaUltimaRevision": "2026-10-23",
            "metodo": "Extracción de texto Unicode y geometría de tablas del PDF oficial, con cotejo visual de páginas del anexo.",
            "notas": [
                "La redacción se conserva en catalán, idioma de la publicación oficial consultada.",
                "Las aclaraciones y concreciones orientativas de las tablas se guardan separadas de los criterios y saberes.",
                "En el primer ciclo, los criterios de evaluación y los saberes básicos tienen carácter orientativo según el decreto.",
                "Los saberes carecen de código individual oficial; sus identificadores y las abreviaturas de área son internos del proyecto.",
                "No se publican asociaciones explícitas entre criterios y saberes ni descriptores operativos numerados.",
            ],
        },
    }
    finish_provenance(document)
    return document


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    plain_pages = raw_pages()
    words = bbox_pages()
    with pdfplumber.open(PDF) as pdf:
        documents = []
        all_diagnostics = []
        for area in AREAS:
            intro, competencies = narrative(area, plain_pages)
            developments, diagnostics = parse_area_tables(area, pdf, words)
            document = make_document(area, intro, competencies, developments)
            documents.append((area[0], document))
            all_diagnostics.extend((area[0], *entry) for entry in diagnostics)
            print(
                area[0],
                "CE", len(competencies),
                "CA", [len(dev["criteriosEvaluacion"]) for dev in developments],
                "bloques", [len(dev["bloquesSaberes"]) for dev in developments],
                "saberes", [sum(len(block["saberes"]) for block in dev["bloquesSaberes"]) for dev in developments],
            )
    if all_diagnostics:
        for entry in all_diagnostics[:60]:
            print("DIAGNÓSTICO", entry)
        raise SystemExit(f"{len(all_diagnostics)} anomalías de extracción")
    total_criteria = sum(
        len(dev["criteriosEvaluacion"])
        for _, doc in documents
        for dev in doc["desarrollos"]
    )
    if total_criteria != 84:
        raise SystemExit(f"Se esperaban 84 criterios y se obtuvieron {total_criteria}")
    if args.write:
        DEST.mkdir(parents=True, exist_ok=True)
        for slug, document in documents:
            (DEST / f"{slug}.json").write_text(
                json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        print("Escritos", len(documents), "JSON en", DEST)


if __name__ == "__main__":
    main()
