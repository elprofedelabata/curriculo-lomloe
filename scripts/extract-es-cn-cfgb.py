"""Extrae los dos ámbitos comunes del anexo 1 del Decreto 9/2023.

El ODT institucional aporta la estructura de las tablas; el PDF del BOC es
la referencia normativa. La secuenciación orientativa de saberes se conserva
en cursoOrientativo. Actividad Física y Bienestar Emocional solo es de 1.º.
"""
from __future__ import annotations

import copy
import json
import re
import sys
import unicodedata
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = ROOT / "sources/es-cn/apoyo/cfgb"
PDF = ROOT / "sources/es-cn/normativa/cfgb/2023-01-26-decreto-9-2023-curriculo-cfgb.pdf"
OUTPUT = ROOT / "data/es-cn/cfgb/materias"
SOURCE_ID = "boc-2023-025-decreto-9-2023"
OFFICE = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}"
TEXT = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"
TABLE = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"
REF = re.compile(r"\b(?:CCL|CPSAA|CCEC|STEM|CD|CP|CC|CE)\d(?:\.\d)?\b")
# Correcciones confirmadas y documentadas en incidencias/es-cn.md.
SABER_CORRECTIONS = {
    "CA.1.B.1.1": ("algunos número irracionales", "algunos números irracionales"),
    "CA.1.E.2.2": ("conmutativa y distributiva", "conmutativa y distributiva."),
    "CCS.2.A.3.12": ("LTGBQ+", "LGTBQ+"),
}
CRITERION_CORRECTIONS = {
    ("CCS", "2.2"): ("el cambio el climático", "el cambio climático"),
    ("CCS", "5.5"): ("exposiciones orales relacionados", "exposiciones orales relacionadas"),
}


def clean(value):
    return unicodedata.normalize("NFC", " ".join(value.split()))


def plain(node):
    """Lee también los espacios explícitos del formato OpenDocument."""
    def content(element):
        result = element.text or ""
        for child in element:
            if child.tag == TEXT + "s":
                result += " " * int(child.get(TEXT + "c", "1"))
            elif child.tag in (TEXT + "tab", TEXT + "line-break"):
                result += " "
            else:
                result += content(child)
            result += child.tail or ""
        return result
    return clean(content(node))


def normal(value):
    value = unicodedata.normalize("NFKD", value.casefold())
    return "".join(c for c in value if c.isalnum() and not unicodedata.combining(c))


def paragraphs(node):
    return [plain(p) for p in node.iter(TEXT + "p") if plain(p)]


def nodes():
    with ZipFile(SUPPORT / "anexo-1-ambitos-comunes.odt") as archive:
        root = ET.fromstring(archive.read("content.xml"))
    body = root.find(f".//{OFFICE}body/{OFFICE}text")
    assert body is not None
    def visible(parent):
        for node in parent:
            if node.tag == TEXT + "section":
                yield from visible(node)
            elif node.tag in (TEXT + "p", TEXT + "h", TEXT + "list", TABLE + "table"):
                yield node
    return list(visible(body))


def pdf_pages():
    import fitz
    # El BOC conserva partes de tablas fuera de la página visible. El recorte
    # evita atribuir al folio anterior textos que solo se ven en el siguiente.
    with fitz.open(PDF) as pdf:
        return [normal(p.get_text(clip=fitz.Rect(0, 90, p.rect.width, p.rect.height - 35)))
                for p in pdf[:99]]


def page_hits(value, pages, lo, hi):
    target = normal(value)
    exact = [p for p in range(lo, hi + 1) if target in pages[p - 1]]
    if exact:
        return [exact[0]]
    for length in (85, 65, 45, 25):
        hits = [p for p in range(lo, hi + 1) if target[:length] in pages[p - 1]]
        if hits:
            start = hits[0]
            if target in pages[start - 1]:
                return [start]
            for tail in (50, 35, 20):
                end = next((p for p in range(start, min(start + 3, hi) + 1)
                            if target[-min(tail, len(target)):] in pages[p - 1]), None)
                if end is not None:
                    return list(range(start, end + 1))
            raise ValueError(f"Final no localizado en el BOC ({lo}-{hi}): {value[:150]}")
    raise ValueError(f"No localizado en el BOC ({lo}-{hi}): {value[:150]}")


def provenance(value, pages, lo, hi):
    return {"fuenteRef": SOURCE_ID, "paginas": page_hits(value, pages, lo, hi)}


def cell_text(cell):
    return " ".join(paragraphs(cell))


def parse_competence(table, code, pages, lo, hi):
    rows = table.findall(TABLE + "table-row")
    cells = [row.findall(TABLE + "table-cell") for row in rows]
    heading = cell_text(cells[0][0])
    match = re.fullmatch(r"Competencia específica (\d+):\s*(.+)", heading)
    assert match, heading
    number, statement = match.groups()
    descriptors = list(dict.fromkeys(REF.findall(cell_text(cells[1][0]))))
    ce = {"id": f"ce-{number}", "codigoOficial": number, "enunciado": {"es": statement},
          "descriptoresOperativosRefs": descriptors,
          "procedencia": provenance(statement, pages, lo, hi)}
    criteria = []
    for row in cells[2:-1]:
        strings = paragraphs(row[0])
        current = []
        groups = []
        for value in strings:
            value = re.sub(r"^Criterios de evaluación:\s*", "", value)
            if not value:
                continue
            if re.match(r"^\d+\.\d+\.", value):
                if current:
                    groups.append(current)
                current = [value]
            else:
                assert current, value
                current.append(value)
        if current:
            groups.append(current)
        assert groups, strings
        refs = list(dict.fromkeys(REF.findall(cell_text(row[1]))))
        for group in groups:
            value = " ".join(group)
            match = re.fullmatch(r"(\d+)\.(\d+)\.\s*(.+)", value)
            assert match and match[1] == number, value
            major, minor, text = match.groups()
            criteria.append({"id": f"cri-1-{major}-{minor}", "codigoOficial": f"{major}.{minor}",
                             "competenciaEspecificaRef": ce["id"], "texto": {"es": text},
                             "descriptoresOperativosRefs": refs, "saberesBasicosRefs": [],
                             "procedencia": provenance(text, pages, lo, hi)})
    explanation = paragraphs(cells[-1][0])
    explanation[0] = re.sub(r"^Explicación del bloque competencial:\s*", "", explanation[0])
    explanation = [text for text in explanation if text]
    assert explanation
    block = {"competenciaEspecificaRef": ce["id"],
             "competenciasClaveRefs": list(dict.fromkeys(re.match(r"[A-Z]+", ref)[0] for ref in descriptors)),
             "descriptoresOperativosRefs": descriptors, "explicacion": {"es": explanation},
             "procedencia": {"fuenteRef": SOURCE_ID, "paginas": sorted({p for text in explanation for p in page_hits(text, pages, lo, hi)})}}
    return ce, criteria, block


def list_entries(cell):
    # Algunas entradas reales están almacenadas como list-header en el ODT.
    # En estas tablas cada entrada ocupa un párrafo, incluidos los epígrafes.
    return paragraphs(cell)


def saber(text, code, course, letter, number, pages, lo, hi, suggested=None):
    value = {"id": f"{code}.{course}.{letter}.{number}", "codigoOficial": None,
             "texto": {"es": text}, "procedencia": provenance(text, pages, lo, hi)}
    if suggested:
        value["cursoOrientativo"] = suggested
    return value


def science_sabers(table, pages):
    by_course = {1: [], 2: []}
    current, title, part_number, part_title = None, None, 0, None
    for row in table.findall(TABLE + "table-row"):
        cells = list(row)
        first = cell_text(cells[0])
        heading = re.fullmatch(r"([A-K])\.\s*(.+)", first)
        if heading:
            current, title = heading.groups()
            part_number = 0
            continue
        if "CURSO" in " ".join(cell_text(c) for c in cells):
            continue
        if first:
            part_title = first
            part_number += 1
        assert current and part_title
        shared = cells[1].get(TABLE + "number-columns-spanned") == "2"
        for course in (1, 2):
            cell = cells[1] if shared else cells[course]
            texts = list_entries(cell)
            if not texts:
                continue
            blocks = by_course[course]
            block = next((b for b in blocks if b["codigo"] == current), None)
            if block is None:
                block = {"codigo": current, "nombre": {"es": title}, "apartados": []}
                blocks.append(block)
            part = next((p for p in block["apartados"] if p["codigo"] == str(part_number)), None)
            if part is None:
                part = {"codigo": str(part_number), "nombre": {"es": part_title}, "saberes": []}
                block["apartados"].append(part)
            start = len(part["saberes"])
            for i, text in enumerate(texts, start + 1):
                part["saberes"].append(saber(text, "CA", course, current, f"{part_number}.{i}", pages, 48, 58,
                                               [1, 2] if shared else [course]))
    return by_course


def physical_sabers(table, pages):
    blocks, letter = [], None
    for row in table.findall(TABLE + "table-row")[1:]:
        cell = row.find(TABLE + "table-cell")
        text = cell_text(cell)
        heading = re.fullmatch(r"([A-D])\.\s*(.+)", text)
        if heading:
            source_letter, label = heading.groups()
            letter = chr(ord("L") + ord(source_letter) - ord("A"))
            blocks.append({"codigo": letter, "nombre": {"es": f"Actividad Física y Bienestar Emocional — {source_letter}. {label}"}, "saberes": []})
            continue
        assert letter
        # En el bloque A los cinco guiones son hijos del epígrafe Salud física.
        for i, text in enumerate(list_entries(cell), 1):
            if letter == "L":
                number = str(i) if i <= 2 else f"2.{i - 2}" if i <= 7 else str(i - 5)
            else:
                number = str(i)
            blocks[-1]["saberes"].append(saber(text, "CA", 1, letter, number, pages, 59, 60))
    assert len(blocks) == 4
    return blocks


def social_sabers(tables, pages):
    by_course = {1: [], 2: []}
    for index, table in enumerate(tables):
        letter = chr(65 + index)
        title = re.sub(r"^BLOQUE [ABC]:\s*", "", cell_text(table.find(TABLE + "table-row/" + TABLE + "table-cell")))
        courses = (1, 2)
        for row in table.findall(TABLE + "table-row")[1:]:
            cell = row.find(TABLE + "table-cell")
            value = cell_text(cell)
            if value in ("PRIMER CURSO", "SEGUNDO CURSO"):
                courses = (1,) if value == "PRIMER CURSO" else (2,)
                continue
            heading = re.fullmatch(r"([IVX]+)\.\s*(.+)", value)
            if heading:
                part_code, part_label = heading.groups()
                continue
            texts = list_entries(cell)
            for course in courses:
                blocks = by_course[course]
                block = next((b for b in blocks if b["codigo"] == letter), None)
                if block is None:
                    block = {"codigo": letter, "nombre": {"es": title}, "apartados": []}
                    blocks.append(block)
                part = {"codigo": part_code, "nombre": {"es": part_label}, "saberes": []}
                block["apartados"].append(part)
                part_number = {"I": 1, "II": 2, "III": 3, "IV": 4}[part_code]
                for i, text in enumerate(texts, 1):
                    part["saberes"].append(saber(text, "CCS", course, letter, f"{part_number}.{i}", pages, 91, 98,
                                                   list(courses) if letter == "A" else None))
    return by_course


def parse_area(area_nodes, code, name, slug, lo, hi, pages):
    tables = [node for node in area_nodes if node.tag == TABLE + "table"]
    ce_tables = [t for t in tables if cell_text(t.find(TABLE + "table-row/" + TABLE + "table-cell")).startswith("Competencia específica")]
    ces, criteria, blocks = [], [], []
    for table in ce_tables:
        ce, cs, block = parse_competence(table, code, pages, 30 if code == "CA" else 75, hi)
        ces.append(ce)
        criteria.extend(cs)
        blocks.append(block)
    assert [int(c["codigoOficial"]) for c in ces] == list(range(1, (11 if code == "CA" else 8) + 1))
    assert len(criteria) == len({c["codigoOficial"] for c in criteria})
    saber_tables = [t for t in tables if t not in ce_tables]
    sabers = science_sabers(saber_tables[0], pages) if code == "CA" else social_sabers(saber_tables, pages)
    if code == "CA":
        sabers[1].extend(physical_sabers(saber_tables[1], pages))
    for course_blocks in sabers.values():
        for block in course_blocks:
            for part in block.get("apartados", [block]):
                for entry in part["saberes"]:
                    correction = SABER_CORRECTIONS.get(entry["id"])
                    if correction:
                        old, new = correction
                        assert entry["texto"]["es"].count(old) == 1, entry
                        entry["texto"]["es"] = entry["texto"]["es"].replace(old, new, 1)
                    # La lectura de columnas intercala celdas de la misma fila;
                    # estas entradas se cotejaron en las páginas renderizadas.
                    if entry["id"] == "CA.1.E.2.3":
                        entry["procedencia"]["paginas"] = [51]
                    if entry["id"] == "CA.2.J.3.1":
                        entry["procedencia"]["paginas"] = [58]
    for criterion in criteria:
        correction = CRITERION_CORRECTIONS.get((code, criterion["codigoOficial"]))
        if correction:
            old, new = correction
            assert criterion["texto"]["es"].count(old) == 1, criterion
            criterion["texto"]["es"] = criterion["texto"]["es"].replace(old, new, 1)
    intro, skip = [], False
    for node in area_nodes[1:]:
        if node.tag == TABLE + "table":
            continue
        value = plain(node)
        if re.match(r"^5\. Competencias específicas", value):
            skip = True
        if re.match(r"^6\. Orientaciones", value):
            skip = False
        if skip:
            continue
        intro.extend(paragraphs(node) if node.tag == TEXT + "list" else [value] if value else [])
    developments = []
    for course in (1, 2):
        ids = {ce["id"] for ce in ces if code != "CA" or course == 1 or int(ce["codigoOficial"]) <= 8}
        cs = copy.deepcopy([c for c in criteria if c["competenciaEspecificaRef"] in ids])
        for c in cs:
            c["id"] = c["id"].replace("cri-1-", f"cri-{course}-", 1)
        developments.append({"curso": course, "criteriosEvaluacion": cs,
                             "bloquesCompetenciales": copy.deepcopy([b for b in blocks if b["competenciaEspecificaRef"] in ids]),
                             "bloquesSaberes": sabers[course]})
    notes = ["Las siglas de ámbito y los identificadores de saberes son internos del proyecto; la fuente no asigna códigos individuales a los saberes.",
             "Los enunciados y descriptores se toman de las tablas de bloques competenciales.",
             "Los criterios y bloques competenciales comunes se representan en ambos cursos; la fuente no los secuencia por curso.",
             "La distribución de saberes se publica como propuesta orientativa y no cronológica; cursoOrientativo conserva las columnas o epígrafes de curso."]
    if code == "CA":
        notes.extend(["Actividad Física y Bienestar Emocional se imparte en primero: CE9, CE10, CE11 y sus saberes se incluyen únicamente en ese desarrollo.",
                      "Los bloques A-K conservan sus letras. Los bloques A-D de Actividad Física y Bienestar Emocional se identifican internamente como L-O; sus nombres conservan las letras publicadas.",
                      "Las subentradas de Salud física se representan con identificadores jerárquicos internos, sin atribuir numeración a la fuente."])
    notes.append("Implantación: primero en 2022/2023 y segundo en 2023/2024.")
    return {"$schema": "../../../../schemas/materia.schema.json", "schemaVersion": "0.6.0",
            "id": f"es-cn.cfgb.{slug}", "territorio": "es-cn", "etapa": "cfgb",
            "materia": {"codigo": code, "nombre": {"es": name}, "cursos": [{"curso": c, "caracter": "ambito"} for c in (1, 2)]},
            "vigencia": {"entradaEnVigor": "2023-02-07", "aplicableDesdeCurso": "2022/2023", "hasta": None, "estado": "vigente"},
            "fuentes": [{"id": SOURCE_ID, "tipo": "decreto", "titulo": "Decreto 9/2023, de 26 de enero, por el que se regula y establece el currículo de veintitrés Ciclos Formativos de Grado Básico en el ámbito de la Comunidad Autónoma de Canarias",
                         "publicacion": "Boletín Oficial de Canarias", "numero": "25", "fechaPublicacion": "2023-02-06", "cve": "BOC-A-2023-025-402",
                         "urlOficial": "https://sede.gobiernodecanarias.org/boc/boc-a-2023-025-402.pdf", "urlVerificacion": "https://www.gobiernodecanarias.org/boc/2023/025/001.html",
                         "anexo": "1", "paginasMateria": {"desde": lo, "hasta": hi}}],
            "introduccion": {"es": intro}, "competenciasEspecificas": ces, "desarrollos": developments,
            "revision": {"estado": "revisado", "fuenteComprobada": True, "fechaUltimaRevision": "2026-11-03",
                         "metodo": "Extracción estructurada del ODT institucional y cotejo con el PDF publicado en el BOC.", "notas": notes}}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    children, pages = nodes(), pdf_pages()
    starts = [i for i, node in enumerate(children) if plain(node) in ("ÁMBITO DE LAS CIENCIAS APLICADAS", "ÁMBITO DE COMUNICACIÓN Y CIENCIAS SOCIALES")]
    assert len(starts) == 2
    OUTPUT.mkdir(parents=True, exist_ok=True)
    specs = [("CA", "Ámbito de las Ciencias Aplicadas", "ciencias-aplicadas", 16, 60),
             ("CCS", "Ámbito de Comunicación y Ciencias Sociales", "comunicacion-y-ciencias-sociales", 61, 98)]
    for index, (code, name, slug, lo, hi) in enumerate(specs):
        end = starts[index + 1] if index == 0 else len(children)
        d = parse_area(children[starts[index]:end], code, name, slug, lo, hi, pages)
        (OUTPUT / f"{slug}.json").write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        counts = [(dev["curso"], len(dev["criteriosEvaluacion"]), sum(len(p["saberes"]) for b in dev["bloquesSaberes"] for p in b.get("apartados", [b]))) for dev in d["desarrollos"]]
        print(name, len(d["competenciasEspecificas"]), counts)


if __name__ == "__main__":
    main()
