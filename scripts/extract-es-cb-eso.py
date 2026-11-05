"""Extrae ESO de Cantabria del decreto, las optativas y ESPADE.

Uso: python scripts/extract-es-cb-eso.py [--write] [--diagnostics RUTA]
Las abreviaturas de materia y los identificadores de saberes son internos.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import fitz
from cantabria_pdf_fonts import FontRecovery, normalize_unicode

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data/es-cb/eso/materias"
SOURCE_KEYS = {
    "D": "es-cb-eso-bachillerato-decreto-73-2022",
    "O": "es-cb-eso-correccion-orden-edu-40-2022",
    "E": "es-cb-eso-bachillerato-orden-edu-21-2025",
}
SOURCE_RANGES = {"D": (37, 317), "O": (1, 114), "E": (17, 23)}
# source, slug, nombre publicado, abreviatura interna, cursos obligatorios,
# cursos optativos. Las versiones con competencias diferentes se separan.
CURRICULA = (
    ("D", "biologia-y-geologia", "Biología y Geología", "BG", [1, 3], [4]),
    ("D", "digitalizacion", "Digitalización", "DIG", [], [4]),
    ("D", "economia-y-emprendimiento", "Economía y Emprendimiento", "EE", [], [4]),
    ("D", "educacion-fisica", "Educación Física", "EF", [1, 2, 3, 4], []),
    ("D", "educacion-plastica-visual-y-audiovisual", "Educación Plástica, Visual y Audiovisual", "EPVA", [1, 3], []),
    ("D", "educacion-en-valores-civicos-y-eticos", "Educación en Valores Cívicos y Éticos", "EVCE", [3], []),
    ("D", "expresion-artistica", "Expresión Artística", "EAR", [], [4]),
    ("D", "fisica-y-quimica", "Física y Química", "FQ", [2, 3], [4]),
    ("D", "formacion-y-orientacion-personal-y-profesional", "Formación y Orientación Personal y Profesional", "FOPP", [], [4]),
    ("D", "geografia-e-historia", "Geografía e Historia", "GH", [1, 2, 3, 4], []),
    ("D", "latin", "Latín", "LAT", [], [4]),
    ("D", "lengua-castellana-y-literatura", "Lengua Castellana y Literatura", "LCL", [1, 2, 3, 4], []),
    ("D", "lengua-extranjera", "Lengua Extranjera", "LE", [1, 2, 3, 4], []),
    ("D", "matematicas", "Matemáticas", "MAT", [1, 2, 3, 4], []),
    ("D", "musica", "Música", "MUS", [1, 2], [4]),
    ("D", "segunda-lengua-extranjera", "Segunda Lengua Extranjera", "SLE", [], [1, 2, 3, 4]),
    ("D", "tecnologia", "Tecnología", "TEC", [], [4]),
    ("D", "tecnologia-y-digitalizacion", "Tecnología y Digitalización", "TYD", [2, 3], []),
    ("O", "alimentacion-y-nutricion", "Alimentación y Nutrición", "AN", [], [3]),
    ("O", "artes-escenicas-y-danza", "Artes Escénicas y Danza", "AED", [], [4]),
    ("O", "conflictos-morales-de-nuestro-tiempo-i", "Conflictos Morales de Nuestro Tiempo I", "CMNTI", [], [1]),
    ("O", "conflictos-morales-de-nuestro-tiempo-ii", "Conflictos Morales de Nuestro Tiempo II", "CMNTII", [], [2]),
    ("O", "cultura-clasica-i", "Cultura Clásica I", "CCI", [], [3]),
    ("O", "cultura-clasica-ii", "Cultura Clásica II", "CCII", [], [4]),
    ("O", "economia-y-cultura-financiera", "Economía y Cultura Financiera", "ECF", [], [4]),
    ("O", "iniciacion-a-la-actividad-emprendedora-y-empresarial", "Iniciación a la Actividad Emprendedora y Empresarial", "IAEE", [], [3]),
    ("O", "iniciacion-a-las-ciencias-experimentales-biologia-y-geologia", "Iniciación a las Ciencias Experimentales Biología y Geología", "ICEBG", [], [4]),
    ("O", "introduccion-al-debate-filosofico", "Introducción al Debate Filosófico", "IDF", [], [4]),
    ("O", "patrimonio-historico-artistico-de-cantabria", "Patrimonio Histórico Artístico de Cantabria", "PHAC", [], [3]),
    ("O", "patrimonio-natural-de-cantabria", "Patrimonio Natural de Cantabria", "PNC", [], [2]),
    ("O", "sistemas-de-control-y-robotica", "Sistemas de Control y Robótica", "SCR", [], [3, 4]),
    ("O", "taller-de-creatividad-musical", "Taller de Creatividad Musical", "TCM", [], [3]),
    ("O", "taller-de-iniciacion-a-las-tecnologias-de-la-informacion-y-la-digitalizacion", "Taller de Iniciación a las Tecnologías de la Información y la Digitalización", "TITID", [], [1, 2]),
    ("O", "taller-de-lengua", "Taller de Lengua", "TL", [], [1, 2]),
    ("O", "taller-de-matematicas", "Taller de Matemáticas", "TM", [], [1, 2]),
    ("O", "union-europea", "Unión Europea", "UE", [], [4]),
    ("E", "tecnificacion-deportiva", "Tecnificación Deportiva", "TD", [], [1, 2, 3, 4]),
)
DIAGNOSTICS: list[dict] = []
CATALOG = json.loads((ROOT / "sources/es-cb/normativa/catalogo.json").read_text(encoding="utf-8"))
SOURCES = {key: next(item for item in CATALOG["documentos"] if item["id"] == source_id) for key, source_id in SOURCE_KEYS.items()}


@dataclass(frozen=True)
class Line:
    page: int
    text: str
    indented: bool


def source_lines(key: str) -> list[Line]:
    source = SOURCES[key]
    path = ROOT / "sources/es-cb/normativa" / source["archivo"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]
    output = []
    first, last = SOURCE_RANGES[key]
    with fitz.open(path) as pdf:
        recovery = FontRecovery(pdf)
        for number in range(first, last + 1):
            rows = []
            for block in recovery.page(pdf[number - 1])["blocks"]:
                for line in block.get("lines", []):
                    value = normalize_unicode(re.sub(r"\s+", " ", "".join(span["text"] for span in line["spans"]))).strip()
                    if value and not re.fullmatch(r"\d+|\d{4}/\d+", value):
                        rows.append((line["bbox"], value))
            rows.sort(key=lambda row: (round(row[0][1], 1), row[0][0]))
            merged = []
            for box, value in rows:
                if merged and abs(box[1] - merged[-1][0][1]) < 1:
                    previous, old = merged[-1]
                    merged[-1] = ((previous[0], previous[1], max(previous[2], box[2]), max(previous[3], box[3])), old + " " + value)
                else:
                    merged.append((box, value))
            margin = min(box[0] for box, _ in merged)
            for index, (box, value) in enumerate(merged):
                paragraph_gap = key == "E" and index > 0 and box[1] - merged[index - 1][0][1] > 14
                output.append(Line(number, value, box[0] > margin + 8 or paragraph_gap))
    return output


def join(lines: list[Line]) -> str:
    result = ""
    for line in lines:
        result += ("" if not result or result.endswith("-") else " ") + line.text
    return result


def provenance(lines: list[Line], key: str) -> dict:
    return {"fuenteRef": SOURCE_KEYS[key], "paginas": sorted({line.page for line in lines})}


def paragraphs(lines: list[Line]) -> list[str]:
    groups = []
    for line in lines:
        if not groups or line.indented:
            groups.append([])
        groups[-1].append(line)
    return [join(group) for group in groups]


def label(value: str) -> str:
    return value.strip().rstrip(".").casefold()


def title_position(lines: list[Line], name: str) -> int:
    positions = [i for i, line in enumerate(lines) if line.text == name]
    assert len(positions) == 1, (name, positions)
    return positions[0]


def competencies(lines: list[Line], key: str) -> list[dict]:
    starts = [(i, int(match.group(1))) for i, line in enumerate(lines) if (match := re.match(r"^(\d+)\.\s*-?\s+", line.text))]
    assert [number for _, number in starts] == list(range(1, len(starts) + 1)), starts
    assert starts
    output = []
    for index, (start, number) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(lines)
        segment = lines[start:end]
        descriptor_start = next(i for i, line in enumerate(segment) if line.text.startswith("Esta competencia") and re.search(r"se (?:conecta|relaciona) con los (?:siguientes )?(?:descriptores|prescriptores)", join(segment[i:i + 3])))
        body = segment[:descriptor_start]
        description_start = next((i for i, line in enumerate(body[1:], 1) if line.indented), len(body))
        raw_refs = join(segment[descriptor_start:]).split(":", 1)[1]
        raw_refs = re.sub(r"([A-Z]{2,6})\s+(\d)", r"\1\2", raw_refs)
        if key == "D" and segment[0].page == 110 and number == 4 and raw_refs.endswith(". 83"):
            DIAGNOSTICS.append({"tipo": "numero-ajeno-descriptores", "fuente": key, "pagina": 110, "competencia": 4, "texto": raw_refs})
            raw_refs = raw_refs[:-3]
        keys = re.findall(r"\b[A-Z]{2,6}\d+(?:\.\d+)?\b", raw_refs)
        extra = re.sub(r"\b[A-Z]{2,6}\d+(?:\.\d+)?\b|[,.;\s]", "", raw_refs)
        assert keys and extra in ("", "y"), (segment[0].page, raw_refs)
        if len(keys) != len(set(keys)):
            DIAGNOSTICS.append({"tipo": "descriptor-repetido", "fuente": key, "pagina": segment[0].page, "competencia": number, "texto": raw_refs})
        ce = {"id": f"ce-{number}", "codigoOficial": str(number), "enunciado": {"es": re.sub(r"^\d+\.\s*-?\s*", "", join(body[:description_start]))}, "descriptoresOperativosRefs": list(dict.fromkeys(keys)), "procedencia": provenance(segment, key)}
        if description_start < len(body):
            ce["descripcion"] = {"es": paragraphs(body[description_start:])}
        output.append(ce)
    return output


def criteria(lines: list[Line], key: str, code: str) -> list[dict]:
    groups = []
    active = None
    for line in lines:
        heading = re.fullmatch(r"Competencia[s]? espec[ií]fica[s]?\s+(\d+)\.?", line.text, re.I)
        item = re.match(r"^(\d+[.,]\d+)(\.)?\s*(.+)$", line.text)
        if label(line.text) == "criterios de evaluación":
            DIAGNOSTICS.append({"tipo": "rotulo-criterios-repetido", "fuente": key, "pagina": line.page})
            continue
        if heading:
            active = int(heading.group(1))
        elif item:
            number, separator, value = item.groups()
            if "," in number:
                DIAGNOSTICS.append({"tipo": "coma-en-codigo-criterio", "area": code, "pagina": line.page, "codigo": number})
                number = number.replace(",", ".")
            assert active is None or int(number.split(".")[0]) == active, (code, line.page, active, line.text)
            if not separator:
                DIAGNOSTICS.append({"tipo": "separador-criterio-omitido", "area": code, "pagina": line.page, "codigo": number})
            groups.append((number, [Line(line.page, value, False)]))
        else:
            assert groups, (code, line.page, line.text)
            groups[-1][1].append(line)
    codes = [number for number, _ in groups]
    assert groups, code
    if len(codes) != len(set(codes)):
        DIAGNOSTICS.append({"tipo": "codigo-criterio-repetido", "area": code, "codigos": codes})
    return [{"codigoOficial": number, "competenciaEspecificaRef": "ce-" + number.split(".")[0], "texto": {"es": join(words)}, "saberesBasicosRefs": [], "procedencia": provenance(words, key)} for number, words in groups]


def knowledge(lines: list[Line], key: str, code: str) -> list[dict]:
    blocks = []
    current = None
    numbered_leaves = code in ("CCI", "CCII")
    for line in lines:
        heading = re.match(r"^([A-Z])[.)]\s+(.+)$", line.text)
        numbered_block = re.match(r"^Bloque\s+(\d+)\.\s+(.+)$", line.text, re.I)
        numbered = re.match(r"^(\d{1,2}(?:\.\d+)*)\.?(?:\s+)(.+)$", line.text)
        bullet = re.match(r"^[-–—−‐‑•\x83]\s*(.+)$", line.text)
        if line.text in ("Se dividen en tres grandes bloques:", "BLOQUES"):
            continue
        if numbered_block:
            number, value = numbered_block.groups()
            heading = None
            blocks.append({"codigo": chr(64 + int(number)), "name": [Line(line.page, line.text, False)], "items": [], "parts": []})
            current = blocks[-1]
            continue
        if heading:
            letter, value = heading.groups()
            assert letter not in {b["codigo"] for b in blocks}, (code, line.page, line.text)
            blocks.append({"codigo": letter, "name": [Line(line.page, value, False)], "items": [], "parts": []})
            current = blocks[-1]
        elif numbered and not numbered_leaves:
            assert blocks and not blocks[-1]["items"], (code, line.page, line.text)
            number, value = numbered.groups()
            parent = blocks[-1]
            if "." in number:
                for ancestor in number.split(".")[:-1]:
                    parent = next(part for part in parent["parts"] if part["codigo"].split(".")[-1] == ancestor)
            current = {"codigo": number, "name": [Line(line.page, value, False)], "items": [], "parts": []}
            parent["parts"].append(current)
        elif bullet or (numbered and numbered_leaves):
            assert blocks, (code, line.page, line.text)
            container = current
            number = numbered.group(1) if numbered and numbered_leaves else None
            value = numbered.group(2) if number else bullet.group(1)
            container["items"].append({"number": number, "lines": [Line(line.page, value, False)]})
        else:
            assert blocks, (code, line.page, line.text)
            container = current
            if container["items"]:
                container["items"][-1]["lines"].append(line)
            else:
                container["name"].append(line)
    output = []
    for block in blocks:
        result = {"codigo": block["codigo"], "nombre": {"es": join(block["name"]).rstrip(".")}}
        def items(container):
            if not container["items"]:
                assert (code == "FOPP" and container["codigo"] == "2.2") or (code == "TITID" and container["codigo"] in ("7", "8", "9")), (code, block["codigo"], container["codigo"])
                container["items"] = [{"number": None, "lines": container["name"]}]
            values = []
            for item in container["items"]:
                value = {"codigoOficial": None, "texto": {"es": join(item["lines"])}, "procedencia": provenance(item["lines"], key)}
                if item["number"]:
                    value["numeracionFuente"] = item["number"]
                values.append(value)
            return values
        def part_value(part):
            output = {"codigo": part["codigo"], "nombre": {"es": join(part["name"]).rstrip(".")}}
            if part["parts"]:
                assert not part["items"], (code, part)
                output["apartados"] = [part_value(child) for child in part["parts"]]
            else:
                output["saberes"] = items(part)
            return output
        if block["parts"]:
            result["apartados"] = [part_value(part) for part in block["parts"]]
        else:
            result["saberes"] = items(block)
        output.append(result)
    assert output
    return output


def all_sabers(node: dict) -> list[dict]:
    if "saberes" in node:
        return node["saberes"]
    return [item for part in node.get("apartados", node.get("bloquesSaberes", [])) for item in all_sabers(part)]


def source_metadata(source: dict, *, first: int | None = None, last: int | None = None, annex: str | None = None) -> dict:
    source_type = source["tipo"] if source["tipo"] != "correccion-errores" else "otro"
    result = {"id": source["id"], "tipo": source_type, "titulo": source["titulo"], "publicacion": "Boletín Oficial de Cantabria", "numero": source["boc"], "fechaPublicacion": source["fechaPublicacion"], "cve": source["codigoBoc"], "urlOficial": source["urlOficial"], "urlVerificacion": source["urlOficial"]}
    if first is not None:
        result["paginasMateria"] = {"desde": first, "hasta": last}
    if annex:
        result["anexo"] = annex
    return result


def groups(area: list[Line], code: str, courses: list[int]) -> tuple[list[Line], list[tuple[list[int], str | None, list[Line]]]]:
    markers = {
        "Cursos de primero a tercero": ([1, 2, 3], None), "Cursos primero y segundo": ([1, 2], None),
        "Cursos de primero y segundo": ([1, 2], None), "Cursos tercero y cuarto": ([3, 4], None),
        "Cursos de tercero y cuarto": ([3, 4], None), "Tercer curso": ([3], None), "Cuarto curso": ([4], None),
        "Matemáticas A": ([4], "a"), "Matemáticas B": ([4], "b"),
        "Sistemas de Control y Robótica I": ([3], None), "Sistemas de Control y Robótica II": ([4], None),
        "Segundo curso": ([2], None),
        "Primer curso": ([1], None),
    }
    start = next(i for i, line in enumerate(area) if label(line.text) == "competencias específicas")
    criteria_start = next(i for i, line in enumerate(area) if label(line.text) == "criterios de evaluación")
    group_markers = [(i, markers[line.text.rstrip(".")]) for i, line in enumerate(area) if i > start and line.text.rstrip(".") in markers]
    narrative_end = group_markers[0][0] if group_markers and group_markers[0][0] < criteria_start else criteria_start
    parsed = []
    if narrative_end == criteria_start:
        implicit_courses = [1] if code == "TM" else courses
        parsed.append((criteria_start, (implicit_courses, None)))
    parsed.extend(group_markers)
    output = []
    for index, (position, (wanted, variant)) in enumerate(parsed):
        end = parsed[index + 1][0] if index + 1 < len(parsed) else len(area)
        selected = [course for course in wanted if course in courses]
        assert selected, (code, wanted, courses)
        output.append((selected, variant, area[position + (0 if position == criteria_start else 1):end]))
    return area[start + 1:narrative_end], output


def normalize(document: dict) -> None:
    # Las correcciones editoriales se documentan únicamente en el registro MD.
    code = document["materia"]["codigo"]
    replacements = {
        "EVCE": [("promover el autonocimiento", "promover el autoconocimiento")],
        "FOPP": [("Plan de autonocimiento", "Plan de autoconocimiento"), ("dentro los grupos", "dentro de los grupos")],
        "IDF": [("promover el autonocimiento", "promover el autoconocimiento")],
        "PNC": [("Patrimono natural", "Patrimonio natural")],
        "AED": [("patrimonio escénico y performativa", "patrimonio escénico y performativo")],
        "MAT": [("recta numérica.:", "recta numérica:")],
        "TITID": [("Conocer los compontes", "Conocer los componentes"), ("Manejo de una Suit ofimática:", "Manejo de una suite ofimática:"), ("el block de notas", "el bloc de notas"), ("Plataformas digital de aprendizaje", "Plataformas digitales de aprendizaje")],
        "TD": [("Comprender la incidencia del entrenamiento", "Comprender la incidencia que el entrenamiento")],
    }.get(code, [])
    def replace(value):
        if isinstance(value, str):
            for old, new in replacements:
                value = value.replace(old, new)
            return value
        if isinstance(value, list):
            return [replace(child) for child in value]
        if isinstance(value, dict):
            return {key: replace(child) for key, child in value.items()}
        return value
    corrected = replace(document)
    document.clear()
    document.update(corrected)
    key_replacements = {
        "ECF": {"CMCCT4": "STEM4"}, "IDF": {"ESTEM1": "STEM1", "ESTEM4": "STEM4"},
        "MUS": {"CCE3": "CCEC3"}, "PHAC": {"CCE1": "CCEC1"}, "SLE": {"CCCEC1": "CCEC1"},
        "SCR": {"STEAM1": "STEM1", "STEAM3": "STEM3"}, "TCM": {"CCPSAA1": "CPSAA1"},
        "TM": {"CCCEC1": "CCEC1"}, "TD": {"CPSSA2": "CPSAA2"},
    }.get(code, {})
    for ce in document["competenciasEspecificas"]:
        ce["descriptoresOperativosRefs"] = list(dict.fromkeys(key_replacements.get(key, key) for key in ce["descriptoresOperativosRefs"]))
        if code in ("AED", "TCM"):
            ce["descriptoresOperativosRefs"] = [key for key in ce["descriptoresOperativosRefs"] if key not in ("CCEC5", "CCEC6")]
    for node in list(document["competenciasEspecificas"]) + [item for dev in document["desarrollos"] for item in dev["criteriosEvaluacion"]]:
        field = "enunciado" if "enunciado" in node else "texto"
        text = node[field]["es"]
        if not text.endswith((".", "…")):
            node[field]["es"] = text.rstrip(",") + "."
    if code == "DIG":
        item = document["desarrollos"][0]["criteriosEvaluacion"][-1]
        assert item["codigoOficial"] == "4.4" and item["id"].endswith("-a")
        item["codigoOficial"] = "4.5"
        item["id"] = "cri-4-4-5"
    if code == "CCII":
        items = document["desarrollos"][0]["bloquesSaberes"][2]["saberes"]
        assert [item.get("numeracionFuente") for item in items] == ["1", "2", "3", "4", "5", "5", "6"]
        items[-2]["numeracionFuente"] = "6"
        items[-1]["numeracionFuente"] = "7"


def extract() -> list[dict]:
    sources = {key: source_lines(key) for key in SOURCES}
    # Las dos publicaciones de Segunda Lengua Extranjera se cotejan aparte.
    starts = {key: [(title_position(lines, name), config) for config in CURRICULA if config[0] == key for name in [config[2]]] for key, lines in sources.items()}
    starts["O"].append((title_position(sources["O"], "Segunda Lengua Extranjera"), None))
    for key in starts:
        starts[key].sort(key=lambda item: item[0])
    output, errors = [], []
    for key, ranges in starts.items():
        lines = sources[key]
        common_culture = lines[title_position(lines, "Cultura Clásica") + 1:title_position(lines, "Cultura Clásica I")] if key == "O" else []
        for index, (position, config) in enumerate(ranges):
            if config is None:
                continue
            _, slug, name, code, required, optional = config
            try:
                end = ranges[index + 1][0] if index + 1 < len(ranges) else len(lines)
                area = lines[position + 1:end]
                if code == "CMNTII":
                    common_start = next(i for i, line in enumerate(area) if line.text == "Cultura Clásica")
                    area = area[:common_start]
                courses = sorted(required + optional)
                ce_lines, developments = groups(area, code, courses)
                ce = competencies(ce_lines, key)
                first_ce = next(i for i, line in enumerate(area) if label(line.text) == "competencias específicas")
                intro = (common_culture if code in ("CCI", "CCII") else []) + area[:first_ce]
                final_developments = []
                for selected, variant, segment in developments:
                    assert label(segment[0].text) == "criterios de evaluación", (code, segment[0])
                    saber_start = next(i for i, line in enumerate(segment) if label(line.text) == "saberes básicos")
                    cri = criteria(segment[1:saber_start], key, code)
                    blocks = knowledge(segment[saber_start + 1:], key, code)
                    for course in selected:
                        dev = {"curso": course, "criteriosEvaluacion": copy.deepcopy(cri), "bloquesSaberes": copy.deepcopy(blocks)}
                        if variant:
                            dev["variante"] = {"codigo": variant, "nombre": {"es": "Matemáticas " + variant.upper()}}
                        seen_codes = set()
                        for criterion in dev["criteriosEvaluacion"]:
                            criterion["id"] = f"cri-{course}{'-' + variant if variant else ''}-{criterion['codigoOficial'].replace('.', '-')}"
                            if criterion["codigoOficial"] in seen_codes:
                                criterion["id"] += "-a"
                            seen_codes.add(criterion["codigoOficial"])
                        for block in dev["bloquesSaberes"]:
                            for number, saber in enumerate(all_sabers(block), 1):
                                saber["id"] = f"{code}{variant.upper() if variant else ''}.{course}.{block['codigo']}.{number:02d}"
                        final_developments.append(dev)
                assert {dev["curso"] for dev in final_developments} == set(courses), (code, courses)
                intro_first = common_culture[0].page if code in ("CCI", "CCII") else lines[position].page
                document = {
                    "$schema": "../../../../schemas/materia.schema.json", "schemaVersion": "0.8.0", "id": f"es-cb.eso.{slug}", "territorio": "es-cb", "etapa": "eso",
                    "materia": {"codigo": code, "nombre": {"es": name}, "cursos": [{"curso": course, "caracter": "obligatoria" if course in required else "optativa"} for course in courses]},
                    "vigencia": {"entradaEnVigor": {"D": None, "O": "2022-08-13", "E": "2025-05-15"}[key], "aplicableDesdeCurso": None if key == "E" else "2022/2023" if any(course in (1, 3) for course in courses) else "2023/2024", "hasta": None, "estado": "vigente"},
                    "fuentes": [source_metadata(SOURCES[key], first=intro_first, last=area[-1].page, annex="I-A" if key == "D" else "II" if key == "O" else "I")],
                    "introduccion": {"es": paragraphs(intro)}, "competenciasEspecificas": ce, "desarrollos": final_developments,
                    "revision": {"estado": "revisado", "fuenteComprobada": True, "fechaUltimaRevision": "2026-11-04", "metodo": "Extracción de texto y coordenadas del PDF oficial, cotejo visual y contraste independiente con Poppler.", "notas": [
                        "La abreviatura de materia y los identificadores individuales de saberes son internos del proyecto, no códigos oficiales. Los ordinales publicados en los saberes se conservan en numeracionFuente, cuando existen.",
                        "Los descriptores operativos se conservan por competencia específica. No se inventan asociaciones criterio-saber ni descriptores por criterio.",
                        "Los desarrollos publicados para un grupo de cursos se reproducen en los cursos en que se oferta la materia, conservando su carácter compartido: la repetición no atribuye una secuenciación por curso que la fuente no publica.",
                    ]},
                }
                if key != "E":
                    organization = next(item for item in CATALOG["documentos"] if item["id"] == "es-cb-eso-orden-edu-40-2022")
                    timetable = next(item for item in CATALOG["documentos"] if item["id"] == "es-cb-eso-bachillerato-orden-edu-36-2024")
                    document["fuentes"].extend([source_metadata(organization), source_metadata(timetable, first=17, last=18, annex="III")])
                    document["revision"]["notas"].append("La organización por cursos procede de los artículos 10 y 11 del Decreto 73/2022 y del anexo III de la Orden EDU/36/2024, que sustituye el anexo I de la Orden EDU/40/2022.")
                    document["revision"]["notas"].append("aplicableDesdeCurso indica el primer curso académico de implantación en los cursos de esta materia: 2022/2023 si incluye 1.º o 3.º, y 2023/2024 si solo se oferta en 2.º o 4.º, según el calendario normativo.")
                if code in ("CCI", "CCII"):
                    document["revision"]["notas"].append("Los bloques se publican como Bloque 1, Bloque 2, etc., sin letras. Se les asignan letras internas para los identificadores del esquema y se conserva la cabecera numerada completa en nombre.")
                if code == "FOPP":
                    document["revision"]["notas"].append("Se conservan los subapartados anidados del bloque A. El apartado 2.2, cuyo título contiene por sí solo un saber sin viñetas subordinadas, se representa con un único saber de texto idéntico, sin omitir su contenido.")
                if code == "TITID":
                    document["revision"]["notas"].append("El anexo III de la Orden EDU/36/2024 permite cursar este taller en uno de los dos primeros cursos. Los desarrollos de 1.º y 2.º representan las posibilidades de oferta, no la obligación ni la posibilidad de cursarlo dos veces.")
                if code == "SCR":
                    document["revision"]["notas"].append("Sistemas de Control y Robótica II se identifica como materia de continuidad en el anexo III de la Orden EDU/36/2024. Se conservan los desarrollos diferenciados de 3.º y 4.º.")
                if code == "SLE":
                    document["fuentes"].append(source_metadata(SOURCES["O"], first=65, last=78, annex="II"))
                if key == "D":
                    document["revision"]["notas"].append("La disposición final tercera del Decreto 73/2022 fija la entrada en vigor al inicio del curso 2022/2023, sin un día concreto; entradaEnVigor queda en null. Se implanta en 1.º y 3.º en 2022/2023 y en 2.º y 4.º en 2023/2024.")
                if code in ("CCI", "CCII", "CMNTI", "CMNTII"):
                    document["revision"]["notas"].append("Las versiones I y II tienen competencias específicas diferentes y se representan en JSON separados para conservar su numeración y sus vínculos sin mezclarlos. Cultura Clásica I y II comparten la introducción general publicada antes del primer nivel.")
                if code == "TD":
                    document["revision"]["fechaUltimaRevision"] = "2026-11-05"
                    document["revision"]["notas"].append("El artículo 4.c.1.º de la Orden EDU/21/2025 (página 3 del PDF) sitúa la materia en los cuatro cursos de ESO como optativa vinculada a ESPADE. Se dirige al alumnado del programa en Centros Educativos de Referencia autorizados, con federaciones deportivas participantes. La orden entra en vigor el 15 de mayo de 2025 y no fija el curso académico inicial.")
                normalize(document)
                output.append(document)
            except (AssertionError, StopIteration, IndexError, ValueError) as error:
                errors.append({"materia": name, "error": str(error) or type(error).__name__})
    if errors:
        raise ValueError(json.dumps(errors, ensure_ascii=False))
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--diagnostics", type=Path)
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    documents = extract()
    for doc in documents:
        stats = [(dev["curso"], dev.get("variante", {}).get("codigo"), len(dev["criteriosEvaluacion"]), len(all_sabers(dev))) for dev in doc["desarrollos"]]
        print(doc["materia"]["codigo"], len(doc["competenciasEspecificas"]), stats)
        if args.write:
            DEST.mkdir(parents=True, exist_ok=True)
            (DEST / (doc["id"].split(".")[-1] + ".json")).write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.diagnostics:
        args.diagnostics.parent.mkdir(parents=True, exist_ok=True)
        args.diagnostics.write_text(json.dumps(DIAGNOSTICS, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("DIAGNOSTICOS", json.dumps(DIAGNOSTICS, ensure_ascii=False))


if __name__ == "__main__":
    main()
