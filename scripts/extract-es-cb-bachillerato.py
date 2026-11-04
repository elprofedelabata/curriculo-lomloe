"""Extrae Bachillerato de Cantabria; los códigos asignados son internos."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
import fitz
from cantabria_pdf_fonts import FontRecovery, normalize_unicode

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data/es-cb/bachillerato/materias"
CATALOG = json.loads((ROOT / "sources/es-cb/normativa/catalogo.json").read_text(encoding="utf-8"))
SOURCE_KEYS = {"D": "es-cb-eso-bachillerato-decreto-73-2022", "O": "es-cb-bachillerato-orden-edu-42-2022", "V": "es-cb-bachillerato-orden-edu-30-2024", "E": "es-cb-eso-bachillerato-orden-edu-21-2025"}
SOURCE_RANGES = {"D": (353,878), "O": (21,93), "V": (10,25), "E": (24,31)}
SOURCES = {key: next(x for x in CATALOG["documentos"] if x["id"]==value) for key,value in SOURCE_KEYS.items()}
DIAGNOSTICS = []

# Curso y carácter según el decreto y el horario del anexo I de EDU/30/2024.
MAIN_CODES = {'Análisis Musical': 'AM',
 'Artes Escénicas': 'AE',
 'Biología': 'BIO',
 'Biología, Geología y Ciencias Ambientales': 'BGCA',
 'Ciencias Generales': 'CG',
 'Coro y Técnica Vocal': 'CTV',
 'Cultura Audiovisual': 'CAU',
 'Dibujo Artístico': 'DA',
 'Dibujo Técnico': 'DT',
 'Dibujo Técnico Aplicado a las Artes Plásticas y al Diseño': 'DTAAPD',
 'Diseño': 'DIS',
 'Economía': 'ECO',
 'Economía, Emprendimiento y Actividad Empresarial': 'EEAE',
 'Educación Física': 'EF',
 'Empresa y Diseño de Modelos de Negocio': 'EDMN',
 'Filosofía': 'FIL',
 'Física': 'FIS',
 'Física y Química': 'FQ',
 'Fundamentos Artísticos': 'FA',
 'Geología y Ciencias Ambientales': 'GCA',
 'Geografía': 'GEO',
 'Griego': 'GR',
 'Historia del Arte': 'HA',
 'Historia de España': 'HE',
 'Historia de la Filosofía': 'HF',
 'Historia del Mundo Contemporáneo': 'HMC',
 'Historia de la Música y de la Danza': 'HMD',
 'Latín': 'LAT',
 'Lengua Castellana y Literatura': 'LCL',
 'Lengua Extranjera': 'LE',
 'Lenguaje y Práctica Musical': 'LPM',
 'Literatura Dramática': 'LD',
 'Literatura Universal': 'LU',
 'Matemáticas': 'MAT',
 'Matemáticas Aplicadas a las Ciencias Sociales': 'MACS',
 'Matemáticas Generales': 'MG',
 'Movimientos Culturales y Artísticos': 'MCA',
 'Proyectos Artísticos': 'PA',
 'Química': 'QUI',
 'Técnicas de Expresión Gráfico-Plástica': 'TEGP',
 'Tecnología e Ingeniería': 'TI',
 'Volumen': 'VOL'}
FIRST_ONLY = {"BGCA", "CAU", "ECO", "EEAE", "EF", "FIL", "FQ", "HMC", "LPM", "LU", "MG", "PA", "VOL"}
SECOND_ONLY = {"BIO", "CG", "DIS", "EDMN", "FIS", "FA", "GCA", "GEO", "HA", "HE", "HF", "HMD", "LD", "MCA", "QUI", "TEGP"}
COMMON = {"EF", "FIL", "HE", "HF", "LCL", "LE"}
OPTIONAL = {"Anatomía Aplicada": ("AA", [1]), "Economía Financiera": ("EFIN", [1]), "Fundamentos de Administración y Gestión": ("FAG", [2]), "Imagen y Sonido": ("IS", [2]), "Segunda Lengua Extranjera I": ("SLEI", [1]), "Segunda Lengua Extranjera II": ("SLEII", [2]), "Programación y Gestión de Datos": ("PGD", [2]), "Psicología": ("PSI", [2]), "Tecnologías de la Información": ("TINF", [1])}

# Tratamientos editoriales confirmados por el usuario; su justificación se mantiene en MD.
REF_REPLACEMENTS = {
    "AE": {"CCE3": "CCEC3", "CPAAA6": None}, "BIO": {"CEC4": "CCEC3.2"},
    "CG": {"CEC1": "CCEC1"}, "CAU": {"CCE5": "CCEC4.1"},
    "DT": {"CEC1": "CCEC1", "CEC2": "CCEC2", "CEC4": "CCEC3.2"},
    "DTAAPD": {"CCE1": "CCEC1", "CCE2": "CCEC2", "CCE3": "CCEC3.1", "CCE4": "CCEC3.2", "CCE5": "CCEC4.1", "CCE6": "CCEC4.2"},
    "GEO": {"CEC1": "CCEC1"}, "HE": {"CEC1": "CCEC1", "CEC2": "CCEC2"},
    "HMD": {"CCEL3": "CCL3"}, "LAT": {"CPSAA3": "CPSAA3.1"},
    "TEGP": {"CCE3": "CCEC3.1"}, "TI": {"CPSAA1": "CPSAA1.1"},
    "AA": {"CEC4": "CCEC4"}, "IS": {"CCEC5": None}, "PGD": {"CPSAA7": None},
    "PSI": {"CPSAA6": None, "CPSAA7": None, "CC5": None},
}


def normalize_document(document):
    code = document["materia"]["codigo"]
    for ce in document["competenciasEspecificas"]:
        mapping = REF_REPLACEMENTS.get(code, {})
        ce["descriptoresOperativosRefs"] = list(dict.fromkeys(mapping.get(k,k) for k in ce["descriptoresOperativosRefs"] if mapping.get(k,k) is not None))
    for node in document["competenciasEspecificas"] + [item for dev in document["desarrollos"] for item in dev["criteriosEvaluacion"]]:
        field = "enunciado" if "enunciado" in node else "texto"
        text = node[field]["es"]
        if code == "EF":
            text = text.replace("forma d discriminación", "forma de discriminación")
        if code == "TINF":
            text = text.replace("las características tanto las suites", "las características tanto de las suites")
            text = text.replace("como las que están en la nube", "como de las que están en la nube")
        if not text.endswith((".", "…")):
            text = text.rstrip(",") + "."
        node[field]["es"] = text


def configurations():
    inventory = json.loads((ROOT / "sources/es-cb/inventario.json").read_text(encoding="utf-8"))
    items = [copy.deepcopy(x) for x in inventory["curriculos"] if x["etapa"] == "bachillerato"]
    output, main_number = [], 0
    for item in items:
        key = next(k for k, v in SOURCE_KEYS.items() if v == item["localizadores"][0]["fuenteRef"])
        name = item["nombre"]
        if key == "D":
            code = MAIN_CODES[name]
            main_number += 1
            courses = [1] if code in FIRST_ONLY else [2] if code in SECOND_ONLY else [1, 2]
            kind = "obligatoria" if code in COMMON else "modalidad"
        elif key == "O":
            if name == "Segunda Lengua Extranjera":
                for level, page in (("I", 48), ("II", 61)):
                    code, courses = OPTIONAL[name + " " + level]
                    output.append({"key": key, "nombre": name + " " + level, "code": code, "courses": courses, "kind": "optativa", "page": page})
                continue
            code, courses = OPTIONAL[name]
            kind = "optativa"
        else:
            code, courses, kind = ("DEVAS", [2], "optativa") if key == "V" else ("TDA", [1, 2], "optativa")
        output.append({"key": key, "nombre": name, "code": code, "courses": courses, "kind": kind, "page": item["localizadores"][0]["paginaInicio"]})
    assert main_number == 42 and len(output) == 53
    return output


def slug(value):
    value = "".join(c for c in unicodedata.normalize("NFD", value.lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def start_of(lines, config):
    wanted = label(config["nombre"])
    if config["code"] == "DEVAS":
        wanted = label("Desarrollo de Estilo de Vida Activa y Saludable (DEVAS)")
    options = [(i, i + 1) for i, line in enumerate(lines) if line.page == config["page"] and label(line.text) == wanted]
    options.extend((i, i + 2) for i, line in enumerate(lines[:-1]) if line.page == config["page"] and label(join(lines[i:i + 2])) == wanted)
    assert len(options) == 1, (config["nombre"], options)
    return options[0]


def extract(cache: Path | None = None):
    sources = {key: [Line(x["page"], normalize_unicode(x["text"]), x["indented"]) for x in json.loads((cache / (key + ".json")).read_text(encoding="utf-8"))] if cache else source_lines(key) for key in SOURCES}
    configs = configurations()
    output, errors = [], []
    for key, lines in sources.items():
        starts = sorted((start_of(lines, config), config) for config in configs if config["key"] == key)
        for index, ((position, first), config) in enumerate(starts):
            name, code, courses = config["nombre"], config["code"], config["courses"]
            area = lines[first:starts[index + 1][0][0] if index + 1 < len(starts) else len(lines)]
            try:
                ce_start = next(i for i, line in enumerate(area) if label(line.text) == "competencias específicas")
                criterion_headers = [i for i, line in enumerate(area) if label(line.text) == "criterios de evaluación" or (code in ("GEO", "MCA") and i > ce_start and label(line.text) == "competencias específicas")]
                assert criterion_headers, (code, "sin cabecera de criterios")
                criterion_start = criterion_headers[0]
                level_names = {label(name + " I"): 1, label(name + " II"): 2}
                markers = [(i, level_names[label(line.text)]) for i,line in enumerate(area) if i > ce_start and label(line.text) in level_names]
                narrative_end = markers[0][0] if markers and markers[0][0] < criterion_start else criterion_start
                ce = competencies(area[ce_start + 1:narrative_end], key)
                segments = [(i + 1, course) for i,course in markers] if markers else [(criterion_start, courses[0])]
                assert sorted(course for _,course in segments) == courses, (name, segments, courses)
                developments = []
                for j,(offset,course) in enumerate(segments):
                    end = markers[j + 1][0] if j + 1 < len(markers) else len(area)
                    segment = area[offset:end]
                    assert label(segment[0].text) in ("criterios de evaluación", "competencias específicas"), (code, segment[0])
                    saber_start = next(i for i, line in enumerate(segment) if label(line.text) == "saberes básicos")
                    cri = criteria(segment[1:saber_start], key, code)
                    blocks = knowledge(segment[saber_start + 1:], key, code)
                    dev = {"curso": course, "criteriosEvaluacion": cri, "bloquesSaberes": blocks}
                    seen = {}
                    for criterion in cri:
                        number = criterion["codigoOficial"]
                        seen[number] = seen.get(number, 0) + 1
                        criterion["id"] = f"cri-{course}-{number.replace('.', '-')}" + (f"-{seen[number]}" if seen[number] > 1 else "")
                    for block in blocks:
                        for number, saber in enumerate(all_sabers(block), 1):
                            saber["id"] = f"{code}.{course}.{block['codigo']}.{number:02d}"
                    developments.append(dev)
                document = {
                    "$schema": "../../../../schemas/materia.schema.json", "schemaVersion": "0.8.0", "id": "es-cb.bachillerato." + slug(name), "territorio": "es-cb", "etapa": "bachillerato",
                    "materia": {"codigo": code, "nombre": {"es": name}, "cursos": [{"curso": c, "caracter": config["kind"]} for c in courses]},
                    "vigencia": {"entradaEnVigor": {"D": None, "O": "2022-08-13", "V": "2024-06-20", "E": "2025-05-15"}[key], "aplicableDesdeCurso": ("2022/2023" if 1 in courses else "2023/2024") if key in ("D", "O") else None, "hasta": None, "estado": "vigente"},
                    "fuentes": [source_metadata(SOURCES[key], first=lines[position].page, last=area[-1].page, annex="II-A" if key=="D" else "II")],
                    "introduccion": {"es": paragraphs(area[:ce_start])}, "competenciasEspecificas": ce, "desarrollos": developments,
                    "revision": {"estado": "revisado", "fuenteComprobada": True, "fechaUltimaRevision": "2026-11-04", "metodo": "Extracción de texto y coordenadas del PDF oficial, cotejo visual y contraste independiente con Poppler.", "notas": [
                        "La abreviatura de materia y los identificadores de saberes son internos del proyecto, no códigos oficiales. Se conservan los ordinales publicados en numeracionFuente cuando existen.",
                        "Los descriptores se conservan por competencia específica. No se inventan asociaciones criterio-saber ni descriptores por criterio.",
                        "La asignación por cursos procede del Decreto 73/2022 y del horario del anexo I de la Orden EDU/30/2024. La oferta de materias depende de la modalidad o vía; el carácter modalidad no implica que todas sean obligatorias para todo el alumnado.",
                    ]},
                }
                if key != "O":
                    document["fuentes"].append(source_metadata(SOURCES["O"]))
                if key != "V":
                    document["fuentes"].append(source_metadata(SOURCES["V"], first=4, last=9, annex="I"))
                if key == "D":
                    document["revision"]["notas"].append("El decreto entra en vigor al inicio del curso 2022/2023, sin un día concreto; entradaEnVigor queda en null. Su implantación es en 1.º en 2022/2023 y en 2.º en 2023/2024.")
                if key == "E":
                    document["revision"]["notas"].append("Materia vinculada al Programa ESPADE en centros de referencia autorizados y para alumnado participante. Se conserva la entrada en vigor del 15 de mayo de 2025 sin atribuir un curso académico que la orden no fija.")
                if code in ("GR", "LAT"):
                    document["revision"]["notas"].append("Los bloques con números romanos reciben letras internas para sus identificadores. Su título conserva el número romano publicado; los apartados A y B del bloque I mantienen su jerarquía.")
                if code in ("LD", "LU"):
                    document["revision"]["notas"].append("Los subapartados cuyo título contiene por sí solo un contenido, sin viñetas subordinadas, se representan mediante un único saber de texto idéntico al título.")
                if code in ("SLEI", "SLEII"):
                    document["revision"]["notas"].append("La orden publica introducción, competencias y desarrollo completos para I y II. Los enunciados de la CE 3 difieren; se representan por separado para conservar el texto de cada nivel.")
                if code in ("AE", "AA", "EFIN", "FAG", "IS", "PSI"):
                    document["revision"]["notas"].append("Se conserva la granularidad de las referencias publicadas: CPSAA1, CPSAA3, CCEC3 y CCEC4, cuando aparecen sin subíndice, identifican el grupo y no atribuyen por sí solas una relación con cada descriptor subdividido.")
                normalize_document(document)
                output.append(document)
            except (AssertionError, StopIteration, IndexError, ValueError) as error:
                errors.append({"materia": name, "error": str(error) or type(error).__name__})
    return output, errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--diagnostics", type=Path)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    documents, errors = extract(args.cache)
    print(json.dumps({"materias": len(documents), "errores": errors, "diagnosticos": len(DIAGNOSTICS)}, ensure_ascii=False))
    if args.diagnostics:
        args.diagnostics.parent.mkdir(parents=True, exist_ok=True)
        args.diagnostics.write_text(json.dumps({"errores": errors, "diagnosticos": DIAGNOSTICS}, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    if errors:
        raise SystemExit(1)
    if args.write:
        DEST.mkdir(parents=True, exist_ok=True)
        for document in documents:
            (DEST / (document["id"].split(".")[-1] + ".json")).write_text(json.dumps(document,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")




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


def competencies(lines: list[Line], key: str) -> list[dict]:
    starts = [(i, int(match.group(1))) for i, line in enumerate(lines) if (match := re.match(r"^(\d+)\.\s*-?\s+", line.text))]
    assert [number for _, number in starts] == list(range(1, len(starts) + 1)), starts
    assert starts
    output = []
    for index, (start, number) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(lines)
        segment = lines[start:end]
        descriptor_start = next(i for i, line in enumerate(segment) if line.text.startswith("Esta competencia") and re.search(r"(?:se )?(?:conecta|relaciona) con los (?:siguientes )?(?:descriptores|prescriptores)", join(segment[i:i + 3])))
        body = segment[:descriptor_start]
        description_start = next((i for i, line in enumerate(body[1:], 1) if line.indented), len(body))
        raw_refs = join(segment[descriptor_start:]).split(":", 1)[1]
        raw_refs = re.sub(r"([A-Z]{2,6})\s+(\d)", r"\1\2", raw_refs)
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
        item = re.match(r"^(\d+[.,]+\d+)(\.)?\s*(.+)$", line.text)
        if label(line.text) == "criterios de evaluación":
            DIAGNOSTICS.append({"tipo": "rotulo-criterios-repetido", "fuente": key, "pagina": line.page})
            continue
        if heading:
            active = int(heading.group(1))
        elif item:
            number, separator, value = item.groups()
            if ".." in number:
                DIAGNOSTICS.append({"tipo": "punto-duplicado-criterio", "area": code, "pagina": line.page, "codigo": number})
                number = re.sub(r"\.+", ".", number)
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
    if code == "QUI":
        expanded = []
        for line in lines:
            if line.text == "A. Enlace químico y estructura de la materia. 1. Espectros atómicos.":
                expanded.extend([Line(line.page, "A. Enlace químico y estructura de la materia.", False), Line(line.page, "1. Espectros atómicos.", False)])
            else:
                expanded.append(line)
        lines = expanded
    blocks = []
    current = None
    numbered_leaves = code in ("CCI", "CCII")
    for line in lines:
        roman = re.match(r"^(I|II|III|IV|V)\.\s+(.+)$", line.text) if code in ("GR", "LAT") else None
        heading = re.match(r"^([A-Z])[.)]\s+(.+)$", line.text)
        numbered_block = re.match(r"^Bloque\s+(\d+)\.\s+(.+)$", line.text, re.I)
        numbered = re.match(r"^(\d{1,2}(?:\.\d+)*)\.?(?:\s+)(.+)$", line.text)
        bullet = re.match(r"^[-–—−‐‑•\x83]\s*(.+)$", line.text)
        if code == "LD" and line.text == "Drama: libertad individual y convenciones sociales.":
            bullet = re.match(r"^(.+)$", line.text)
            DIAGNOSTICS.append({"tipo": "vineta-omitida", "area": code, "pagina": line.page, "texto": line.text})
        if line.text in ("Se dividen en tres grandes bloques:", "BLOQUES"):
            continue
        if roman:
            blocks.append({"codigo": chr(65 + len(blocks)), "name": [line], "items": [], "parts": []})
            current = blocks[-1]
            continue
        if numbered_block:
            number, value = numbered_block.groups()
            heading = None
            blocks.append({"codigo": chr(64 + int(number)), "name": [Line(line.page, line.text, False)], "items": [], "parts": []})
            current = blocks[-1]
            continue
        if heading:
            letter, value = heading.groups()
            if code in ("GR", "LAT"):
                assert blocks, (code, line.page, line.text)
                current = {"codigo": letter, "name": [Line(line.page, value, False)], "items": [], "parts": []}
                blocks[-1]["parts"].append(current)
                continue
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
                assert code in ("LD", "LU") and container["codigo"] in ("1.4", "2.4"), (code, block["codigo"], container["codigo"])
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


if __name__ == "__main__":
    main()
