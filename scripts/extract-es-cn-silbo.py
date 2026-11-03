"""Extrae las dos concreciones de Lengua del Decreto 24/2026 (Silbo Gomero).

Son JSON complementarios vinculados al currículo base. Los saberes comunes
se representan en todos los ciclos/cursos, sin atribuirles una secuenciación.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = ROOT / "sources/es-cn/apoyo/silbo-gomero"
PDF = ROOT / "sources/es-cn/normativa/primaria-eso/2026-03-09-decreto-24-2026-lenguaje-silbado-gomera.pdf"
SOURCE_ID = "boc-2026-052-decreto-24-2026"
spec = importlib.util.spec_from_file_location("cn_primary", ROOT / "scripts/extract-es-cn-primaria.py")
primary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(primary)
spec = importlib.util.spec_from_file_location("cn_utils", ROOT / "scripts/extract-es-cn-cfgb.py")
utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils)
TEXT, TABLE, OFFICE = utils.TEXT, utils.TABLE, utils.OFFICE
primary.SOURCE_ID = SOURCE_ID
primary.plain = utils.plain
primary.direct_paragraphs = lambda node: [utils.plain(p) for p in node if p.tag == TEXT + "p" and utils.plain(p)]
primary.page_hits = lambda pages, value, lo, hi: utils.page_hits(value, pages, lo, hi)


def read_nodes(filename):
    with ZipFile(SUPPORT / filename) as archive:
        root = ET.fromstring(archive.read("content.xml"))
    body = root.find(f".//{OFFICE}body/{OFFICE}text")
    def visible(parent):
        for node in parent:
            if node.tag == TEXT + "section":
                yield from visible(node)
            elif node.tag in (TEXT + "p", TEXT + "h", TEXT + "list", TABLE + "table"):
                yield node
    return list(visible(body))


def pdf_pages():
    import fitz
    with fitz.open(PDF) as pdf:
        return [utils.normal(primary.REF.sub("", page.get_text(clip=fitz.Rect(0, 90, page.rect.width, page.rect.height - 40)))) for page in pdf]


def provenance(text, pages, lo, hi):
    return {"fuenteRef": SOURCE_ID, "paginas": utils.page_hits(text, pages, lo, hi)}


def saber_entry(text, number, letter, dimension, pages, lo, hi):
    return {"id": f"LCLSG.{dimension}.{letter}.{number}", "codigoOficial": None,
            "numeracionFuente": number, "texto": {"es": text},
            "procedencia": provenance(text, pages, lo, hi)}


def parse_sabers(nodes, dimension, pages, lo, hi):
    positions = [(i, re.fullmatch(r"([IVX]+)\.\s*(.+)", utils.plain(node)))
                 for i, node in enumerate(nodes) if node.tag == TEXT + "p"]
    positions = [(i, match) for i, match in positions if match]
    assert [match[1] for _, match in positions] == ["I", "II", "III"]
    blocks = []
    for index, (start, match) in enumerate(positions):
        end = positions[index + 1][0] if index + 1 < len(positions) else len(nodes)
        segment = nodes[start + 1:end]
        letter = chr(65 + index)
        block = {"codigo": letter, "nombre": {"es": match[2]}}
        if letter != "B":
            texts = [text for node in segment if node.tag == TEXT + "list" for text in utils.paragraphs(node)]
            block["saberes"] = [saber_entry(text, str(i), letter, dimension, pages, lo, hi) for i, text in enumerate(texts, 1)]
        else:
            block["apartados"] = []
            first_list = next(node for node in segment if node.tag == TEXT + "list")
            top_items = first_list.findall(TEXT + "list-item")
            assert len(top_items) == 3
            for number, item in enumerate(top_items[:2], 1):
                title = primary.direct_paragraphs(item)
                assert len(title) == 1
                texts = [text for node in item if node.tag == TEXT + "list" for text in utils.paragraphs(node)]
                block["apartados"].append({"codigo": str(number), "nombre": {"es": title[0]},
                                           "saberes": [saber_entry(text, f"{number}.{i}", letter, dimension, pages, lo, hi) for i, text in enumerate(texts, 1)]})
            assert primary.direct_paragraphs(top_items[2]) == ["Procesos"]
            counter = 0
            for subtitle in ("Comprensión", "Producción"):
                position = next(i for i, node in enumerate(segment) if node.tag == TEXT + "p" and utils.plain(node) == subtitle)
                listing = segment[position + 1]
                assert listing.tag == TEXT + "list"
                texts = utils.paragraphs(listing)
                part = {"codigo": "3.1" if subtitle == "Comprensión" else "3.2", "nombre": {"es": f"Procesos. {subtitle}"}, "saberes": []}
                for text in texts:
                    counter += 1
                    part["saberes"].append(saber_entry(text, f"3.{counter}", letter, dimension, pages, lo, hi))
                block["apartados"].append(part)
        blocks.append(block)
    assert sum(len(p["saberes"]) for b in blocks for p in b.get("apartados", [b])) == 20
    return blocks


def extract(stage, filename, lo, hi, starts, saber_lo, pages):
    nodes = read_nodes(filename)
    heading = (lambda text: {"Primer": 1, "Segundo": 2, "Tercer": 3}[text.split()[0]]
               if re.fullmatch(r"(Primer|Segundo|Tercer) ciclo de Educación Primaria", text) else None) if stage == "primaria" else (
               lambda text: int(text[0]) if re.fullmatch(r"[1-4]\.º ESO", text) else None)
    dimensions = [(i, heading(utils.plain(node))) for i, node in enumerate(nodes) if node.tag == TEXT + "p"]
    dimensions = [(i, value) for i, value in dimensions if value]
    assert [value for _, value in dimensions] == list(range(1, len(starts) + 1)), dimensions
    first = dimensions[0][0]
    desc_start = next(i for i in range(first) if re.match(r"^Competencia específica \d+ \(C\d+\)$", utils.plain(nodes[i])))
    desc_end = next(i for i in range(desc_start, first) if utils.plain(nodes[i]) == "Saberes básicos")
    intro_start = next(i for i in range(first) if utils.plain(nodes[i]) == "Introducción") + 1
    intro = []
    for node in nodes[intro_start:desc_start] + nodes[desc_end:first]:
        if node.tag in (TEXT + "p", TEXT + "h") and utils.plain(node):
            intro.append(utils.plain(node))
        elif node.tag == TEXT + "list":
            intro.extend(utils.paragraphs(node))
    descriptions = {}
    for i in range(desc_start, desc_end):
        match = re.fullmatch(r"Competencia específica (\d+) \(C\d+\)", utils.plain(nodes[i]))
        if not match:
            continue
        end = next((j for j in range(i + 1, desc_end) if re.fullmatch(r"Competencia específica \d+ \(C\d+\)", utils.plain(nodes[j]))), desc_end)
        descriptions[match[1]] = [utils.plain(n) for n in nodes[i + 1:end] if n.tag == TEXT + "p" and utils.plain(n)]
    saber_start = next(i for i in range(first, len(nodes)) if utils.plain(nodes[i]) == "Saberes básicos")
    competences, developments = [], []
    for index, (position, dimension) in enumerate(dimensions):
        end = dimensions[index + 1][0] if index + 1 < len(dimensions) else saber_start
        lower = starts[index]
        # La explicación de 3.º de ESO continúa en la página que inicia 4.º.
        upper = starts[index + 1] if index + 1 < len(starts) else saber_lo - 1
        criteria, blocks = [], []
        for table in [node for node in nodes[position:end] if node.tag == TABLE + "table"]:
            ces, cs, bs = primary.parse_table(table, dimension, lower, upper, pages)
            # Errata exclusiva del ODT de apoyo: el BOC dice «iniciándose».
            for block in bs:
                block["explicacion"]["es"] = [text.replace("iniciaciándose", "iniciándose") for text in block["explicacion"]["es"]]
            for ce in ces:
                old_id = ce["id"]
                match = next((existing for existing in competences if existing["codigoOficial"] == ce["codigoOficial"] and utils.normal(existing["enunciado"]["es"]) == utils.normal(ce["enunciado"]["es"])), None)
                if match:
                    target = match["id"]
                    match["procedencia"]["paginas"] = sorted(set(match["procedencia"]["paginas"] + ce["procedencia"]["paginas"]))
                    match["descriptoresOperativosRefs"] = list(dict.fromkeys(match["descriptoresOperativosRefs"] + ce["descriptoresOperativosRefs"]))
                else:
                    target = old_id if not any(c["id"] == old_id for c in competences) else f"ce-{max(int(c['id'][3:]) for c in competences) + 1}"
                    ce["id"] = target
                    ce["descripcion"] = {"es": descriptions[ce["codigoOficial"]]}
                    ce["procedencia"]["paginas"] = sorted(set(ce["procedencia"]["paginas"] + utils.page_hits(descriptions[ce["codigoOficial"]][0], pages, lo, starts[0] - 1)))
                    competences.append(ce)
                for obj in cs + bs:
                    if obj["competenciaEspecificaRef"] == old_id:
                        obj["competenciaEspecificaRef"] = target
            criteria.extend(cs)
            blocks.extend(bs)
        assert len(criteria) == 7 and len(blocks) == 5, (stage, dimension, len(criteria), len(blocks))
        developments.append({"ciclo" if stage == "primaria" else "curso": dimension,
                             "criteriosEvaluacion": criteria, "bloquesCompetenciales": blocks,
                             "bloquesSaberes": parse_sabers(nodes[saber_start + 1:], dimension, pages, saber_lo, hi)})
    slug = "lengua-castellana-y-literatura-silbo-gomero"
    return {"$schema": "../../../../schemas/materia.schema.json", "schemaVersion": "0.7.0",
            "id": f"es-cn.{stage}.{slug}", "territorio": "es-cn", "etapa": stage,
            "materia": {"codigo": "LCLSG", "nombre": {"es": "Lengua Castellana y Literatura · Silbo Gomero"},
                        "ciclos" if stage == "primaria" else "cursos": [{"ciclo" if stage == "primaria" else "curso": dimension, "caracter": "obligatoria"} for _, dimension in dimensions]},
            "concrecionCurricular": {"materiaBaseRef": f"es-cn.{stage}.lengua-castellana-y-literatura",
                                     "descripcion": {"es": "Concreción del currículo de Lengua Castellana y Literatura para la enseñanza del lenguaje silbado de la isla de La Gomera."},
                                     "aplicacion": {"preceptivaEn": ["La Gomera"], "facultativaEn": ["Resto de las islas de Canarias"], "facultativaRequiereAutorizacion": True},
                                     "procedencia": {"fuenteRef": SOURCE_ID, "paginas": [6, 7]}},
            "vigencia": {"entradaEnVigor": "2026-03-18", "aplicableDesdeCurso": None, "hasta": None, "estado": "vigente"},
            "fuentes": [{"id": SOURCE_ID, "tipo": "decreto", "titulo": "Decreto 24/2026, de 9 de marzo, por el que se regula la enseñanza del lenguaje silbado de la isla de La Gomera para su impartición en la Educación Primaria y en la Educación Secundaria Obligatoria en la Comunidad Autónoma de Canarias",
                         "publicacion": "Boletín Oficial de Canarias", "numero": "52", "fechaPublicacion": "2026-03-17", "cve": "BOC-A-2026-052-853",
                         "urlOficial": "https://sede.gobiernodecanarias.org/boc/boc-a-2026-052-853.pdf", "urlVerificacion": "https://www.gobiernodecanarias.org/boc/2026/052/853.html",
                         "anexo": "I" if stage == "primaria" else "II", "paginasMateria": {"desde": lo, "hasta": hi}}],
            "introduccion": {"es": intro}, "competenciasEspecificas": competences, "desarrollos": developments,
            "revision": {"estado": "revisado", "fuenteComprobada": True, "fechaUltimaRevision": "2026-11-03",
                         "metodo": "Extracción del ODT institucional y cotejo de textos, numeración y tablas con el PDF del BOC.",
                         "notas": ["Desarrollo complementario del currículo de Lengua; su aplicación territorial y autorización se indican en concrecionCurricular.",
                                   "El carácter de la materia se refiere a Lengua Castellana y Literatura. El desarrollo del silbo es preceptivo en La Gomera y facultativo en el resto de las islas.",
                                   "Los saberes publicados son comunes a los ciclos o cursos: se representan en todos ellos, sin inventar una secuenciación.",
                                   "Las siglas y los identificadores de saberes son internos; numeracionFuente conserva las etiquetas publicadas.",
                                   "Los códigos internos 3.1 y 3.2 de los apartados de Comunicación distinguen Procesos: Comprensión y Procesos: Producción.",
                                   "La norma fija la entrada en vigor, pero no un curso académico de implantación: aplicableDesdeCurso queda en null."]}}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    pages = pdf_pages()
    for spec in [("primaria", "anexo_I_ep_cec.odt", 8, 29, [16, 20, 24], 28),
                 ("eso", "anexo_II_eso_cec.odt", 30, 60, [38, 43, 48, 53], 59)]:
        d = extract(*spec, pages)
        output = ROOT / f"data/es-cn/{spec[0]}/materias/lengua-castellana-y-literatura-silbo-gomero.json"
        output.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(spec[0], len(d["competenciasEspecificas"]), sum(len(x["criteriosEvaluacion"]) for x in d["desarrollos"]))


if __name__ == "__main__":
    main()
