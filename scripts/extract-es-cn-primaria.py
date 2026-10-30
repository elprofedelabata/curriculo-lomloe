"""Extrae el anexo 2 de Primaria de Canarias y coteja el texto con el PDF del BOC.

Los ODT enlazados por la Consejería se usan únicamente para leer la estructura de
las tablas. La publicación de referencia es el Decreto 211/2022 del BOC; cada
criterio se comprueba contra su texto y página en ese PDF.
"""

from __future__ import annotations

import json
import re
import subprocess
import unicodedata
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "sources/es-cn/normativa/primaria/2022-11-10-decreto-211-2022-curriculo-primaria.pdf"
ODT = ROOT / "sources/es-cn/apoyo/primaria"
OUTPUT = ROOT / "data/es-cn/primaria/materias"
SOURCE_ID = "boc-2022-231-decreto-211-2022"
OFFICE = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}"
TEXT = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"
TABLE = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"
AREA = [
    ("conocimiento-medio", "conocimiento-del-medio-natural-social-y-cultural", "Conocimiento del Medio Natural, Social y Cultural", "CM", 35, 87, [(1, 47, 59), (2, 60, 73), (3, 74, 87)]),
    ("artistica", "educacion-artistica", "Educación Artística", "EA", 87, 116, [(1, 97, 102), (2, 103, 109), (3, 110, 116)]),
    ("emocional", "educacion-emocional-y-para-la-creatividad", "Educación Emocional y para la Creatividad", "EEC", 116, 146, [(1, 124, 130), (2, 131, 138), (3, 139, 146)]),
    ("fisica", "educacion-fisica", "Educación Física", "EF", 146, 177, [(1, 156, 162), (2, 163, 169), (3, 170, 177)]),
    ("valores", "educacion-en-valores-civicos-y-eticos", "Educación en Valores Cívicos y Éticos", "EVCE", 177, 193, [(3, 187, 193)]),
    ("lengua", "lengua-castellana-y-literatura", "Lengua Castellana y Literatura", "LCL", 193, 241, [(1, 203, 215), (2, 216, 228), (3, 229, 241)]),
    ("extranjera", "lengua-extranjera", "Lengua Extranjera", "LE", 241, 278, [(1, 253, 260), (2, 261, 269), (3, 270, 278)]),
    ("matematicas", "matematicas", "Matemáticas", "MAT", 278, 323, [(1, 289, 298), (2, 299, 310), (3, 311, 323)]),
    ("segunda-lengua", "segunda-lengua-extranjera", "Segunda Lengua Extranjera", "SLE", 323, 343, [(3, 335, 343)]),
]
ROMAN = {"I": "A", "II": "B", "III": "C", "IV": "D", "V": "E", "VI": "F", "VII": "G"}
REF = re.compile(r"\b[A-Z]{2,6}\d+(?:\.\d+)?\b")
NUMBERED = re.compile(r"^(\d+)\.(\d+)\.?\s+(.*)$")
HEADING = re.compile(r"^([IVX]+)\.\s*(.*)$")
CYCLE_NAME = {1: "Primer", 2: "Segundo", 3: "Tercer"}
SABER_START = {
    "conocimiento-medio": {1: 56, 2: 69, 3: 83},
    "artistica": {1: 101, 2: 107, 3: 114},
    "emocional": {1: 128, 2: 135, 3: 143},
    "fisica": {1: 161, 2: 168, 3: 175},
    "valores": {3: 191},
    "lengua": {1: 213, 2: 226, 3: 239},
    "extranjera": {1: 259, 2: 267, 3: 276},
    "matematicas": {1: 294, 2: 304, 3: 316},
    "segunda-lengua": {3: 341},
}


def clean(value: str) -> str:
    return " ".join(value.split())


def plain(node: ET.Element) -> str:
    return clean("".join(node.itertext()))


def direct_paragraphs(node: ET.Element) -> list[str]:
    return [plain(child) for child in node if child.tag == TEXT + "p" and plain(child)]


def normal(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in value if char.isalnum() and not unicodedata.combining(char))


def pdf_pages() -> list[str]:
    process = subprocess.run(["pdftotext", "-raw", "-enc", "UTF-8", str(PDF), "-"], check=True, capture_output=True)
    pages = process.stdout.decode("utf-8").split("\f")
    assert len(pages) == 347, len(pages)
    return [normal(page) for page in pages]


def page_hits(pages: list[str], value: str, lo: int, hi: int) -> list[int]:
    target = normal(value)
    assert len(target) >= 20, value
    for length in (85, 65, 45, 25):
        fragment = target[:length]
        matches = [p for p in range(lo, hi + 1) if fragment in pages[p - 1]]
        if matches:
            first = matches[0]
            if target not in pages[first - 1] and first < hi and target[-80:] in pages[first]:
                return [first, first + 1]
            return [first]
    raise ValueError(f"No consta en el PDF (páginas {lo}-{hi}): {value[:110]}")


def provenance(pages: list[int]) -> dict:
    return {"fuenteRef": SOURCE_ID, "paginas": sorted(set(pages))}


def odt_children(name: str) -> list[ET.Element]:
    with ZipFile(ODT / f"{name}.odt") as archive:
        root = ET.fromstring(archive.read("content.xml"))
    body = root.find(f".//{OFFICE}body/{OFFICE}text")
    assert body is not None
    section = next((child for child in body if child.tag == TEXT + "section"), body)
    return list(section)


def saber_tree(lists: list[ET.Element]) -> tuple[list[tuple[str | None, str]], bool]:
    """Devuelve (apartado, saber) y distingue listas simples de subapartados."""
    entries: list[tuple[str | None, str]] = []
    headings = False
    pending: str | None = None
    for listing in lists:
        items = [item for item in listing if item.tag == TEXT + "list-item"]
        for i, item in enumerate(items):
            if not plain(item):
                continue
            paragraphs = direct_paragraphs(item)
            nested = [child for child in item if child.tag == TEXT + "list"]
            if nested:
                headings = True
                label = paragraphs[0] if paragraphs else pending
                assert label, ("Sublista sin apartado", [plain(x)[:100] for x in item], pending)
                pending = None
                for subtree in nested:
                    for subitem in subtree.iter(TEXT + "list-item"):
                        if any(child.tag == TEXT + "list" for child in subitem):
                            continue
                        for value in direct_paragraphs(subitem):
                            entries.append((label, value))
            elif paragraphs:
                next_has_no_label = i + 1 < len(items) and any(child.tag == TEXT + "list" for child in items[i + 1]) and not direct_paragraphs(items[i + 1])
                if next_has_no_label or (i == len(items) - 1 and len(items) == 1 and not entries):
                    pending = paragraphs[0]
                else:
                    entries.extend((None, value) for value in paragraphs)
    if pending:
        # Un apartado aislado puede continuar en la lista siguiente; si no, es un saber.
        entries.append((None, pending))
    return entries, headings


def parse_sabers(nodes: list[ET.Element], code: str, cycle: int, lo: int, hi: int, pages: list[str]) -> list[dict]:
    blocks = []
    for index, node in enumerate(nodes):
        if node.tag != TEXT + "p":
            continue
        match = HEADING.match(plain(node))
        if not match or match.group(1) not in ROMAN:
            continue
        roman, name = match.groups()
        end = next((j for j in range(index + 1, len(nodes)) if nodes[j].tag == TEXT + "p" and HEADING.match(plain(nodes[j]))), len(nodes))
        listings = [n for n in nodes[index + 1:end] if n.tag == TEXT + "list"]
        entries, grouped = saber_tree(listings)
        assert entries, (code, cycle, roman)
        letter = ROMAN[roman]
        block = {"codigo": letter, "nombre": {"es": name.rstrip(".")}}
        if grouped:
            apartados: list[dict] = []
            by_name: dict[str, dict] = {}
            for number, (heading, value) in enumerate(entries, 1):
                heading = heading or "Otros saberes"
                if heading not in by_name:
                    section = {"codigo": str(len(apartados) + 1), "nombre": {"es": heading}, "saberes": []}
                    apartados.append(section)
                    by_name[heading] = section
                by_name[heading]["saberes"].append({
                    "id": f"{code}.{cycle}.{letter}.{number}", "codigoOficial": None,
                    "texto": {"es": value}, "procedencia": provenance(page_hits(pages, value, lo, hi)),
                })
            block["apartados"] = apartados
        else:
            block["saberes"] = [{
                "id": f"{code}.{cycle}.{letter}.{number}", "codigoOficial": None,
                "texto": {"es": value}, "procedencia": provenance(page_hits(pages, value, lo, hi)),
            } for number, (_, value) in enumerate(entries, 1)]
        blocks.append(block)
    assert blocks, (code, cycle)
    return blocks


def parse_table(table: ET.Element, cycle: int, lo: int, hi: int, pages: list[str]) -> tuple[list[dict], list[dict], list[dict]]:
    rows = table.findall(f"./{TABLE}table-row")
    first = rows[0].findall(f"./{TABLE}table-cell")
    enunciados = [p for p in direct_paragraphs(first[0]) if re.match(r"^\d+\.", p)]
    assert enunciados, plain(first[0])[:80]
    descriptors = REF.findall(" ".join(direct_paragraphs(first[1])))
    competencies = []
    for entry in enunciados:
        match = re.match(r"^(\d+)\.\s*(.*)$", entry)
        assert match, entry
        number, statement = match.groups()
        competencies.append({
            "id": f"ce-{number}", "codigoOficial": number,
            "enunciado": {"es": statement}, "descriptoresOperativosRefs": descriptors,
            "procedencia": provenance(page_hits(pages, statement, lo, hi)),
        })
    criteria = []
    for row in rows[2:-1]:
        cells = row.findall(f"./{TABLE}table-cell")
        if not cells or not plain(cells[0]):
            continue
        raw = plain(cells[0])
        if raw.startswith("7.1. Leer con progresiva autonomía"):
            raw = raw.replace("necesidadesm con", "necesidades con")
        match = NUMBERED.match(raw)
        assert match, raw[:100]
        major, minor, statement = match.groups()
        refs = REF.findall(" ".join(direct_paragraphs(cells[1]))) if len(cells) > 1 else []
        if major == "7" and minor == "2" and cycle == 1 and "CCE3" in refs:
            # Errata del BOC confirmada en CN-PRIM-004: la cabecera de CE7 indica CC3.
            refs = ["CC3" if ref == "CCE3" else ref for ref in refs]
        hit = page_hits(pages, raw, lo, hi)
        assert normal(raw) in "".join(pages[p - 1] for p in hit + [p + 1 for p in hit if p < hi]), raw[:90]
        criteria.append({
            "id": f"cri-{cycle}-{major}-{minor}", "codigoOficial": f"{major}.{minor}",
            "competenciaEspecificaRef": f"ce-{major}", "texto": {"es": statement},
            "descriptoresOperativosRefs": refs, "saberesBasicosRefs": [], "procedencia": provenance(hit),
        })
    explanation_cell = rows[-1].find(f"./{TABLE}table-cell")
    explanation = direct_paragraphs(explanation_cell)
    assert explanation and explanation[0].startswith("Explicación del bloque competencial"), explanation[:1]
    explanation = [p for p in explanation if p != "Explicación del bloque competencial"]
    explanation = [p.replace("se constarará que", "se constatará que").replace("demosttrando", "demostrando") for p in explanation]
    assert explanation
    blocks = []
    for ce in competencies:
        blocks.append({
            "competenciaEspecificaRef": ce["id"],
            "competenciasClaveRefs": list(dict.fromkeys(re.match(r"^[A-Z]+", ref).group() for ref in descriptors)),
            "descriptoresOperativosRefs": descriptors,
            "explicacion": {"es": explanation},
            "procedencia": provenance(page_hits(pages, explanation[0], lo, hi)),
        })
    return competencies, criteria, blocks


def parse_area(area: tuple, pages: list[str]) -> dict:
    name, slug, title, code, start, end, cycles = area
    children = odt_children(name)
    first_cycle = next(i for i, node in enumerate(children) if plain(node) == f"{CYCLE_NAME[cycles[0][0]]} ciclo Educación Primaria")
    intro_start = next(i for i, node in enumerate(children[:first_cycle]) if plain(node) == "Introducción") + 1
    ce_heading = next(i for i in range(intro_start, first_cycle) if plain(children[i]) == "Competencias específicas y criterios de evaluación")
    desc_start = next(i for i in range(ce_heading, first_cycle) if re.match(r"^Competencia específica \d+", plain(children[i])))
    desc_end = next(i for i in range(desc_start, first_cycle) if plain(children[i]) == "Saberes básicos")
    intro = [plain(node) for node in children[intro_start:desc_start] + children[desc_end:first_cycle] if node.tag == TEXT + "p" and plain(node)]
    descriptions = {}
    for i in range(desc_start, desc_end):
        heading = plain(children[i])
        if not heading.startswith("Competencia específica "):
            continue
        match = re.search(r"\(C(\d+)(?: y C(\d+))?\)", heading)
        assert match, (name, heading)
        next_heading = next((j for j in range(i + 1, desc_end) if plain(children[j]).startswith("Competencia específica ")), desc_end)
        paras = [plain(node) for node in children[i + 1:next_heading] if node.tag == TEXT + "p" and plain(node)]
        for number in match.groups():
            if number:
                if name == "matematicas" and number == "5":
                    paras = [p.replace("Con el desarrollo de esta competencia y", "Con el desarrollo de esta competencia (C5) y") for p in paras]
                descriptions[int(number)] = paras
    competencies: dict[int, dict] = {}
    developments = []
    for pos, (cycle, lo, hi) in enumerate(cycles):
        cstart = next(i for i, node in enumerate(children) if plain(node) == f"{CYCLE_NAME[cycle]} ciclo Educación Primaria")
        cend = next((i for i in range(cstart + 1, len(children)) if re.match(r"^(Primer|Segundo|Tercer) ciclo Educación Primaria$", plain(children[i]))), len(children))
        segment = children[cstart:cend]
        saber_start = next(i for i, node in enumerate(segment) if plain(node) == "Saberes básicos")
        tables = [node for node in segment[:saber_start] if node.tag == TABLE + "table"]
        assert tables, (name, cycle)
        criteria, blocks = [], []
        for table in tables:
            comp, crit, block = parse_table(table, cycle, lo, hi, pages)
            criteria.extend(crit)
            blocks.extend(block)
            for ce in comp:
                number = int(ce["codigoOficial"])
                if number in competencies:
                    assert normal(competencies[number]["enunciado"]["es"]) == normal(ce["enunciado"]["es"]), (name, number)
                    competencies[number]["descriptoresOperativosRefs"] = list(dict.fromkeys(competencies[number]["descriptoresOperativosRefs"] + ce["descriptoresOperativosRefs"]))
                    competencies[number]["procedencia"]["paginas"] = sorted(set(competencies[number]["procedencia"]["paginas"] + ce["procedencia"]["paginas"]))
                else:
                    competencies[number] = ce
        saberes = parse_sabers(segment[saber_start + 1:], code, cycle, SABER_START[name][cycle], hi, pages)
        assert len({c["id"] for c in criteria}) == len(criteria)
        developments.append({"ciclo": cycle, "criteriosEvaluacion": criteria, "bloquesCompetenciales": blocks, "bloquesSaberes": saberes})
    for number, ce in competencies.items():
        ce["descripcion"] = {"es": descriptions[number]}
        ce["procedencia"]["paginas"] = sorted(set(ce["procedencia"]["paginas"] + page_hits(pages, descriptions[number][0], start, cycles[0][1] - 1)))
    document = {
        "$schema": "../../../../schemas/materia.schema.json", "schemaVersion": "0.6.0",
        "id": f"es-cn.primaria.{slug}", "territorio": "es-cn", "etapa": "primaria",
        "materia": {"codigo": code, "nombre": {"es": title}, "ciclos": [{"ciclo": c, "caracter": "obligatoria"} for c, _, _ in cycles]},
        "vigencia": {"entradaEnVigor": "2022-11-24", "aplicableDesdeCurso": "2022/2023", "hasta": None, "estado": "vigente"},
        "fuentes": [{
            "id": SOURCE_ID, "tipo": "decreto",
            "titulo": "Decreto 211/2022, de 10 de noviembre, por el que se establece la ordenación y el currículo de la Educación Primaria en la Comunidad Autónoma de Canarias",
            "publicacion": "Boletín Oficial de Canarias", "numero": "231", "fechaPublicacion": "2022-11-23", "cve": "BOC-A-2022-231-3533",
            "urlOficial": "https://sede.gobiernodecanarias.org/boc/boc-a-2022-231-3533.pdf",
            "urlVerificacion": "https://www.gobiernodecanarias.org/boc/2022/231/001.html",
            "anexo": "2", "paginasMateria": {"desde": start, "hasta": end},
        }],
        "introduccion": {"es": intro},
        "competenciasEspecificas": [competencies[n] for n in sorted(competencies)],
        "desarrollos": developments,
        "revision": {"estado": "borrador", "fuenteComprobada": True, "fechaUltimaRevision": "2026-10-30",
                     "metodo": "Extracción estructurada de ODT oficial de apoyo; cotejo de los criterios con el PDF publicado en el BOC.",
                     "notas": ["Los códigos de saber son identificadores internos: la fuente publica listas sin códigos individuales.",
                               "Los descriptores se conservan por ciclo; la ficha de competencia reúne las referencias de sus tres ciclos.",
                               "Implantación progresiva: cursos 1.º, 3.º y 5.º en 2022/2023; 2.º, 4.º y 6.º en 2023/2024."]},
    }
    return document


def main() -> None:
    pages = pdf_pages()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for area in AREA:
        document = parse_area(area, pages)
        target = OUTPUT / f"{area[1]}.json"
        target.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(area[1], len(document["competenciasEspecificas"]),
              sum(len(d["criteriosEvaluacion"]) for d in document["desarrollos"]),
              sum(sum(len(b.get("saberes", [])) + sum(len(a["saberes"]) for a in b.get("apartados", [])) for b in d["bloquesSaberes"]) for d in document["desarrollos"]))


if __name__ == "__main__":
    main()
