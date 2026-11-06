"""Extrae los currículos de ESO de Castilla-La Mancha."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from contextlib import ExitStack
from dataclasses import dataclass, replace
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
NORMATIVE = ROOT / "sources/es-cm/normativa"
DEST = ROOT / "data/es-cm/eso/materias"
BASE = "es-cm-eso-cfgb-decreto-82-2022"
ERRATA = "es-cm-eso-cfgb-correccion-decreto-82-2022"
AMENDMENT = "es-cm-eso-cfgb-decreto-31-2024"
DIV = "es-cm-eso-orden-166-2022"
DESCRIPTOR_PREFIX = re.compile(
    r"^[Ee]?sta competencia(?: específica)? se conecta con los siguientes descriptores"
    r"(?: del [Pp]erfil de salida)?:?\s+"
)
DESCRIPTOR = re.compile(r"\b(?:CCL|CP|STEM|CD|CPSAA|CCEC|CC|CE)\d+\b")
AREAS = (
    ("artes-escenicas-danza-y-folclore", "Artes Escénicas, Danza y Folclore", "AEDF", 34, 38,
     ((None, (4,)),)),
    ("biologia-y-geologia", "Biología y Geología", "BYG", 39, 47,
     (("Cursos de primero a tercero", (1, 3)), ("Cuarto curso", (4,)))),
    ("cultura-cientifica", "Cultura Científica", "CCI", 48, 52,
     ((None, (4,)),)),
    ("cultura-clasica", "Cultura Clásica", "CCL", 53, 59,
     (("2º de ESO", (2,)), ("4º de ESO", (4,)))),
)
COMMON_TWO = (("Cursos primero y segundo", (1, 2)), ("Cursos tercero y cuarto", (3, 4)))
REST = (
    ("desarrollo-digital", "DD", ((None, (2,)),), ()),
    ("digitalizacion", "DIG", ((None, (4,)),), ()),
    ("economia-y-emprendimiento", "EE", ((None, (4,)),), ()),
    ("educacion-fisica", "EF", COMMON_TWO, (1, 2, 3, 4)),
    ("educacion-en-valores-civicos-y-eticos", "EVCE", ((None, (2,)),), (2,)),
    ("educacion-plastica-visual-y-audiovisual", "EPVA", ((None, (2, 3)),), (2, 3)),
    ("emprendimiento-sostenibilidad-y-consumo-responsable", "ESCR", ((None, (3,)),), ()),
    ("expresion-artistica", "EA", ((None, (4,)),), ()),
    ("filosofia", "FIL", ((None, (4,)),), ()),
    ("fisica-y-quimica", "FYQ", (("Cursos de primero a tercero", (2, 3)), ("Cuarto curso", (4,))), (2, 3)),
    ("formacion-y-orientacion-personal-y-profesional", "FOPP", ((None, (4,)),), ()),
    ("geografia-e-historia", "GH", COMMON_TWO, (1, 2, 3, 4)),
    ("latin", "LAT", ((None, (4,)),), ()),
    ("lengua-castellana-y-literatura", "LCL", COMMON_TWO, (1, 2, 3, 4)),
    ("lengua-extranjera", "LE", COMMON_TWO, (1, 2, 3, 4)),
    ("matematicas", "MAT", (("Cursos primero y segundo", (1, 2)), ("Tercer curso", (3,)),
                           ("Matemáticas A de Cuarto curso", (4,)), ("Matemáticas B de Cuarto curso", (4,))), (1, 2, 3, 4)),
    ("musica-activa-movimiento-y-folclore", "MAMF", ((None, (3,)),), ()),
    ("musica", "MUS", (("Cursos de primero a tercero", (1, 2)), ("Cuarto curso", (4,))), (1, 2)),
    ("proyectos-de-robotica", "PR", ((None, (4,)),), ()),
    ("proyectos-de-artes-plasticas-y-visuales", "PAPV", ((None, (1,)),), ()),
    ("segunda-lengua-extranjera", "SLE", COMMON_TWO, ()),
    ("taller-de-emprendimiento-y-finanzas-personales", "TEFP", ((None, (1,)),), ()),
    ("tecnologia", "TEC", ((None, (4,)),), ()),
    ("tecnologia-y-digitalizacion", "TYD", ((None, (1, 3)),), (1, 3)),
    ("union-europea", "UE", ((None, (4,)),), ()),
    ("ambito-linguistico-y-social-diversificacion", "ALS", ((None, (3, 4)),), ()),
    ("ambito-cientifico-tecnologico-diversificacion", "ACT", ((None, (3, 4)),), ()),
)
ARTS_DESCRIPTOR_CORRECTIONS = {
    1: ("CCL1 CCL2 CC3 CCEC1 CCEC2", "CCL1 CCL2 CC3 CPSAA4 CCEC1 CCEC2"),
    2: ("CCL1 CC1 CCEC1 CCEC2 CCEC3", "CCL1 CC1 CE1 CCEC1 CCEC2 CCEC3"),
    4: ("CCL5 CC3 CE2 CCEC4 CCEC5", "CCL5 CC3 CE2 CCEC3 CCEC4"),
    5: ("CCL5 CD2 CD3 CCEC5 CCEC6", "CCL5 CD2 CD3 CE2 CPSAA4 CPSAA5 CCEC3 CCEC4"),
}
DESCRIPTOR_CORRECTIONS = {
    **{("AEDF", number): correction for number, correction in ARTS_DESCRIPTOR_CORRECTIONS.items()},
    ("MAMF", 5): ("CCL5 CD5 CPSAA6 CPSAA7 CE3 CCEC5 CCEC6", "CCL5 CD5 CPSAA3 CPSAA4 CPSAA5 CE3 CCEC3 CCEC4"),
}
DESCRIPTOR_TYPOS = {
    ("FYQ", 3): ("STEMS", "STEM5"),
    ("FYQ", 5): ("STEMS", "STEM5"),
    ("MAMF", 1): ("CCE2", "CCEC2"),
    ("MUS", 3): ("CCE3", "CCEC3"),
    ("ALS", 4): ("CL3", "CCL3"),
}
CRITERION_TYPOS = {
    ("BYG", "2.3"): ("Castila-La Mancha", "Castilla-La Mancha"),
    ("LCL", "1.1"): ("Castilla- La Macha", "Castilla-La Mancha"),
}


@dataclass(frozen=True)
class Line:
    page: int
    text: str
    paragraph_start: bool
    source: str = BASE


def read_lines(pdf: fitz.Document, first: int, last: int) -> list[Line]:
    lines = []
    for page in range(first, last + 1):
        rows = []
        for block in pdf[page - 1].get_text("dict")["blocks"]:
            for row in block.get("lines", []):
                x, y = row["bbox"][:2]
                text = " ".join("".join(span["text"] for span in row["spans"]).split())
                if y >= 78 and text:
                    rows.append((y, x, text))
        previous_y = None
        for y, _, text in sorted(rows):
            if previous_y is None:
                start = not lines or (text[0].isupper() and lines[-1].text.endswith((".", "?", "!")))
            else:
                start = y - previous_y > 16
            lines.append(Line(page, text, start))
            previous_y = y
    return lines


def joined(lines: list[Line]) -> str:
    assert lines
    text = lines[0].text
    for line in lines[1:]:
        sep = "" if text.endswith("-") and line.text[0].isalpha() else " "
        text += sep + line.text
    return text


def paragraphs(lines: list[Line]) -> list[str]:
    groups = []
    for line in lines:
        if not groups or line.paragraph_start:
            groups.append([])
        groups[-1].append(line)
    return [joined(group) for group in groups]


def origin(lines: list[Line]) -> dict:
    return {"fuenteRef": lines[0].source, "paginas": sorted({line.page for line in lines})}


def heading(lines: list[Line], title: str) -> int:
    positions = [index for index, line in enumerate(lines) if line.text.rstrip(".:") == title]
    assert len(positions) == 1, (title, positions)
    return positions[0]


def competencies(lines: list[Line], area_code: str) -> list[dict]:
    starts = [i for i, line in enumerate(lines) if re.match(r"^\d+\.(?!\d)\s*", line.text)]
    assert starts and starts[0] == 0
    result = []
    for number, (start, end) in enumerate(zip(starts, starts[1:] + [len(lines)]), 1):
        segment = lines[start:end]
        assert segment[0].text.startswith(f"{number}."), segment[0]
        descriptor_start, = (i for i, line in enumerate(segment) if DESCRIPTOR_PREFIX.match(line.text))
        statement, *description = paragraphs(segment[:descriptor_start])
        assert description, segment[0]
        if area_code == "PAPV" and number == 2:
            assert sum(text.count("eventos culturas cercanos") for text in description) == 1
            description = [text.replace("eventos culturas cercanos", "eventos culturales cercanos") for text in description]
        raw_refs = DESCRIPTOR_PREFIX.sub("", joined(segment[descriptor_start:]), count=1)
        if typo := DESCRIPTOR_TYPOS.get((area_code, number)):
            assert re.search(rf"\b{typo[0]}\b", raw_refs), raw_refs
            raw_refs = re.sub(rf"\b{typo[0]}\b", typo[1], raw_refs)
        codes = DESCRIPTOR.findall(raw_refs)
        assert codes and not re.sub(r"\by\b", "", DESCRIPTOR.sub("", raw_refs)).strip(" ,.;\t"), raw_refs
        if correction := DESCRIPTOR_CORRECTIONS.get((area_code, number)):
            original, amended = correction
            assert codes == original.split(), (number, codes)
            codes = amended.split()
        if area_code == "ESCR" and number in (1, 2):
            codes.append("CE2")
        assert len(codes) == len(set(codes)), codes
        result.append({
            "id": f"ce-{number}", "codigoOficial": str(number),
            "enunciado": {"es": statement.removeprefix(f"{number}.").lstrip()},
            "descripcion": {"es": description}, "descriptoresOperativosRefs": codes,
            "procedencia": origin(segment),
        })
    return result


def criteria(lines: list[Line], area_code: str, course: int, ce_count: int, variant: str = "") -> list[dict]:
    groups = []
    active = []
    for line in lines:
        if match := re.fullmatch(r"Competencia específica (\d+)\.?", line.text):
            active.append(int(match[1]))
        elif match := re.fullmatch(r"(\d+\.\d+)\.?\s+(.+)", line.text):
            code, text = match.groups()
            assert active and int(code.split(".")[0]) == active[-1], (line.page, line.text, active)
            groups.append((code, [replace(line, text=text)]))
        else:
            assert groups and not line.paragraph_start, line
            groups[-1][1].append(line)
    assert active == list(range(1, ce_count + 1)), active
    assert len({code for code, _ in groups}) == len(groups)
    result = []
    for code, words in groups:
        text = joined(words)
        if typo := CRITERION_TYPOS.get((area_code, code)):
            text = text.replace(*typo)
        if area_code == "BYG" and course in (1, 3) and code == "5.1":
            assert words[-1].page == 43 and text.endswith("nuestro entorno de Castilla-La Mancha")
            text += "."
        if area_code == "SLE" and course in (3, 4) and code in ("3.2", "4.2", "5.3"):
            assert words[0].page == 225 and not text.endswith(".")
            text += "."
        result.append({
            "id": f"cri-{course}{'-' + variant.lower() if variant else ''}-{code.replace('.', '-')}", "codigoOficial": code,
            "competenciaEspecificaRef": f"ce-{code.split('.')[0]}", "texto": {"es": text},
            "saberesBasicosRefs": [], "procedencia": origin(words),
        })
    return result


def knowledge(lines: list[Line], area_code: str, course: int, variant: str = "") -> list[dict]:
    blocks = []
    for line in lines:
        text = line.text
        if area_code == "ACT" and text == "G La materia y sus cambios.":
            text = "G. La materia y sus cambios."
        if match := re.fullmatch(r"([A-Z])\.\s+(.+)", text):
            code, title = match.groups()
            assert code == chr(ord("A") + len(blocks)), line
            blocks.append({"code": code, "title": title, "parts": [], "items": [], "intro": []})
            continue
        assert blocks, line
        block = blocks[-1]
        if match := re.fullmatch(r"(\d+)\.\s+([^\W\d_].*)", text):
            assert not block["items"], line
            number, title = match.groups()
            block["parts"].append({"code": number, "title": title, "items": [], "intro": []})
            continue
        node = block["parts"][-1] if block["parts"] else block
        if match := re.fullmatch(r"[-–−]\s+(.+)", text):
            node["items"].append([replace(line, text=match[1])])
        elif node["items"]:
            node["items"][-1].append(line)
        else:
            assert area_code == "LCL", line
            node["intro"].append(line)
    result = []
    for block in blocks:
        number = 0

        def value(node: dict) -> dict:
            nonlocal number
            entry = {"codigo": node["code"], "nombre": {"es": node["title"].rstrip(".")}}
            if node["intro"]:
                entry["descripcion"] = {"es": paragraphs(node["intro"])}
            if node.get("parts"):
                entry["apartados"] = [value(part) for part in node["parts"]]
            else:
                assert node["items"], (area_code, node)
                items = []
                for words in node["items"]:
                    number += 1
                    text = joined(words)
                    if area_code == "UE" and text.startswith("Órganos e instituciones principales"):
                        assert "Parlamento Comisión y Consejo" in text
                        text = text.replace("Parlamento Comisión y Consejo", "Parlamento, Comisión y Consejo")
                    items.append({
                        "id": f"{area_code}{variant}.{course}.{block['code']}.{number:02d}",
                        "codigoOficial": None, "texto": {"es": text}, "procedencia": origin(words),
                    })
                entry["saberes"] = items
            return entry

        result.append(value(block))
    assert result
    return result


def source_metadata(source: dict, first: int, last: int, annex: str | None = None) -> dict:
    item = {
        "id": source["id"], "tipo": "otro" if source["tipo"] == "correccion-errores" else source["tipo"],
        "titulo": source["titulo"], "publicacion": "Diario Oficial de Castilla-La Mancha",
        "numero": source["docm"], "fechaPublicacion": source["fechaPublicacion"], "cve": source["codigoDocm"],
        "urlOficial": source["urlOficial"], "urlVerificacion": source["urlOficial"],
        "paginasMateria": {"desde": first, "hasta": last},
    }
    if annex:
        item["anexo"] = annex
    return item


def extract(*, selected: str | None = None) -> list[dict]:
    catalog = json.loads((NORMATIVE / "catalogo.json").read_text(encoding="utf-8"))
    sources = {item["id"]: item for item in catalog["documentos"]}
    inventory = json.loads((NORMATIVE.parent / "inventario.json").read_text(encoding="utf-8"))
    entries = [entry for entry in inventory["curriculos"] if entry["etapa"] == "eso"]
    assert len(entries) == len(AREAS) + len(REST)
    config = {slug: (code, groups, (1, 3) if code == "BYG" else ()) for slug, _, code, _, _, groups in AREAS}
    config.update({slug: (code, groups, required) for slug, code, groups, required in REST})
    entries_by_slug = {}
    for entry in entries:
        normalized = unicodedata.normalize("NFKD", entry["nombre"]).encode("ascii", "ignore").decode().lower()
        slug = re.sub(r"[^a-z]+", "-", normalized).strip("-")
        if entry["localizadores"][0]["fuenteRef"] == DIV:
            slug += "-diversificacion"
        entries_by_slug[slug] = entry
    assert config.keys() == entries_by_slug.keys()
    for source_id in (BASE, ERRATA, AMENDMENT, DIV):
        source = sources[source_id]
        assert hashlib.sha256((NORMATIVE / source["archivo"]).read_bytes()).hexdigest() == source["sha256"]
    result = []
    with ExitStack() as stack:
        pdfs = {key: stack.enter_context(fitz.open(NORMATIVE / sources[key]["archivo"])) for key in (BASE, AMENDMENT, DIV)}
        for slug, entry in entries_by_slug.items():
            code, groups, required = config[slug]
            if selected and code != selected:
                continue
            name = entry["nombre"]
            location = entry["localizadores"][0]
            source_id, first, last = location["fuenteRef"], location["paginaInicio"], location["paginaFin"]
            pdf_title = {"ACT": "Ámbito Científico -Tecnológico", "UE": "«Unión Europea"}.get(code, name)
            lines = [replace(line, source=source_id) for line in read_lines(pdfs[source_id], first, last)]
            area = lines[heading(lines, pdf_title) + 1:]
            if code == "ALS":
                area = area[:heading(area, "Ámbito Científico -Tecnológico")]
            if code == "UE":
                end = next(index for index, line in enumerate(area) if line.text.startswith("Veintiséis."))
                area = area[:end]
                assert area[-1].text.endswith("»"), area[-1]
                area[-1] = replace(area[-1], text=area[-1].text.removesuffix("»"))
            try:
                intro_end = heading(area, "Competencias específicas")
                if groups[0][0] is None:
                    starts = [heading(area, "Criterios de evaluación")]
                else:
                    starts = [heading(area, label) for label, _ in groups]
                ce = competencies(area[intro_end + 1:starts[0]], code)
                intro = paragraphs(area[:intro_end])
            except (AssertionError, ValueError) as error:
                raise ValueError(f"{code}: {error}") from error
            references = [source_metadata(sources[source_id], first, last, location["anexo"])]
            notes = [
                "La abreviatura de materia y los identificadores de saberes son internos. Las letras de bloque proceden del decreto.",
                "Los descriptores operativos se conservan por competencia específica. El anexo presenta por separado los criterios y los saberes.",
            ]
            notes.append("El anexo II de la Orden 166/2022 sitúa el ámbito en 3.º y 4.º."
                         if source_id == DIV else
                         "La oferta por cursos se contrasta con el horario del anexo IV en la redacción del Decreto 31/2024.")
            if code in ("ESCR", "MAMF", "PAPV"):
                references.append(source_metadata(sources[ERRATA], 1, 1))
                notes.append("Se incorpora la corrección de errores de febrero de 2024.")
            if code == "DD":
                amended = read_lines(pdfs[AMENDMENT], 8, 9)
                for number, start in ((3, "Esta competencia pretende afianzar"), (4, "Esta materia proporciona conocimientos")):
                    start_at = next(i for i, line in enumerate(amended) if line.text.startswith("«" + start))
                    end_at = next(i for i in range(start_at, len(amended)) if amended[i].text.endswith("»"))
                    text = joined(amended[start_at:end_at + 1]).strip("«»")
                    description = ce[number - 1]["descripcion"]["es"]
                    old, = [i for i, paragraph in enumerate(description) if paragraph.startswith("En el tercer curso de Educación Secundaria Obligatoria")]
                    description[old] = text
                references.append(source_metadata(sources[AMENDMENT], 8, 9))
                notes.append("Se incorporan los párrafos de las competencias específicas 3 y 4 sustituidos por el Decreto 31/2024.")
            if code == "AEDF":
                references.append(source_metadata(sources[ERRATA], 1, 1))
                notes.append("Los descriptores de las competencias 1, 2, 4 y 5 incorporan la corrección de errores de febrero de 2024.")
            if code == "BYG":
                original = "«Cuerpo Humano» y «Hábitos saludables»"
                corrected = "«Cuerpo Humano», «Hábitos saludables» y «Salud y enfermedad»"
                assert sum(text.count(original) for text in intro) == 1
                intro = [text.replace(original, corrected) for text in intro]
                references.append(source_metadata(sources[ERRATA], 1, 1))
                notes.extend([
                    "La introducción incorpora la mención de «Salud y enfermedad» de la corrección de errores de febrero de 2024.",
                    "El desarrollo común de primero a tercero se reproduce en 1.º y 3.º, los cursos en que se imparte. 4.º es de opción y tiene un desarrollo propio.",
                ])
            if source_id == DIV:
                notes.append("Los criterios y saberes del ámbito se publican conjuntamente para ambos cursos.")
            elif source_id != AMENDMENT and code != "DD":
                references.append(source_metadata(sources[AMENDMENT], 13, 14, "IV"))
            elif code == "DD":
                references[-1]["paginasMateria"]["hasta"] = 14
            developments = []
            for (label, courses), start, end in zip(groups, starts, starts[1:] + [len(area)], strict=True):
                section = area[start + (label is not None):end]
                assert heading(section, "Criterios de evaluación") == 0
                saber_start = heading(section, "Saberes básicos")
                variant = label.split()[1] if label and label.startswith("Matemáticas ") else ""
                for course in courses:
                    try:
                        development = {
                            "curso": course, "criteriosEvaluacion": criteria(section[1:saber_start], code, course, len(ce), variant),
                            "bloquesSaberes": knowledge(section[saber_start + 1:], code, course, variant),
                        }
                    except (AssertionError, ValueError) as error:
                        raise ValueError(f"{code}/{course}{variant}: {error}") from error
                    if variant:
                        development["variante"] = {"codigo": variant.lower(), "nombre": {"es": f"Matemáticas {variant}"}}
                    developments.append(development)
            all_courses = sorted({item["curso"] for item in developments})
            starts_in_2022 = any(course in (1, 3) for course in all_courses)
            result.append({
                "$schema": "../../../../schemas/materia.schema.json", "schemaVersion": "0.8.0",
                "id": f"es-cm.eso.{slug}", "territorio": "es-cm", "etapa": "eso",
                "materia": {"codigo": code, "nombre": {"es": name}, "cursos": [{
                    "curso": course,
                    "caracter": "ambito" if source_id == DIV else "obligatoria" if course in required else "optativa",
                } for course in all_courses]},
                "vigencia": {"entradaEnVigor": {BASE: "2022-07-15", AMENDMENT: "2024-07-03", DIV: "2022-09-08"}[source_id],
                             "aplicableDesdeCurso": "2024/2025" if source_id == AMENDMENT else "2022/2023" if starts_in_2022 else "2023/2024",
                             "hasta": None, "estado": "vigente"},
                "fuentes": references, "introduccion": {"es": intro}, "competenciasEspecificas": ce,
                "desarrollos": developments, "revision": {"estado": "revisado", "fuenteComprobada": True,
                    "fechaUltimaRevision": "2026-11-06",
                    "metodo": "Extracción de texto y coordenadas del PDF y contraste con Poppler.",
                    "notas": notes},
            })
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--materia", help="Abreviatura de la materia")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    for doc in extract(selected=args.materia):
        courses = [[dev["curso"], len(dev["criteriosEvaluacion"]),
                    sum(len(node["saberes"]) for block in dev["bloquesSaberes"]
                        for node in block.get("apartados", [block]))] for dev in doc["desarrollos"]]
        print(json.dumps({"materia": doc["materia"]["nombre"]["es"],
                          "competencias": len(doc["competenciasEspecificas"]), "cursos": courses}, ensure_ascii=False))
        if args.write:
            DEST.mkdir(parents=True, exist_ok=True)
            path = DEST / (doc["id"].rsplit(".", 1)[-1] + ".json")
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
