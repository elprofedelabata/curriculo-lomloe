"""Extrae las siete áreas de Primaria del anexo II-A del Decreto 66/2022.

Uso: python scripts/extract-es-cb-primaria.py [--write]
Los identificadores de saberes y las abreviaturas de área son internos.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "sources/es-cb/normativa/infantil-primaria/2022-07-07-decreto-66-2022-curriculo-infantil-primaria.pdf"
DEST = ROOT / "data/es-cb/primaria/materias"
SOURCE_ID = "es-cb-infantil-primaria-decreto-66-2022"
URL = "https://boc.cantabria.es/boces/verAnuncioAction.do?idAnuBlob=374267"
AREAS = (
    ("conocimiento-del-medio-natural-social-y-cultural", "Conocimiento del Medio Natural, Social y Cultural", "CM", 9),
    ("educacion-artistica", "Educación Artística", "EA", 4),
    ("educacion-fisica", "Educación Física", "EF", 5),
    ("educacion-en-valores-civicos-y-eticos", "Educación en Valores Cívicos y Éticos", "EVCE", 4),
    ("lengua-castellana-y-literatura", "Lengua Castellana y Literatura", "LCL", 10),
    ("lengua-extranjera", "Lengua Extranjera", "LE", 6),
    ("matematicas", "Matemáticas", "MAT", 8),
)
DIAGNOSTICS: list[dict] = []


@dataclass(frozen=True)
class Line:
    page: int
    text: str
    indented: bool


def lines_from_pdf() -> list[Line]:
    catalog = json.loads((ROOT / "sources/es-cb/normativa/catalogo.json").read_text(encoding="utf-8"))
    source = next(d for d in catalog["documentos"] if d["id"] == SOURCE_ID)
    assert hashlib.sha256(PDF.read_bytes()).hexdigest() == source["sha256"]
    result = []
    with fitz.open(PDF) as pdf:
        for number in range(56, 176):
            rows = []
            for block in pdf[number - 1].get_text("dict", clip=fitz.Rect(95, 125, 525, 775))["blocks"]:
                for line in block.get("lines", []):
                    value = re.sub(r"\s+", " ", "".join(s["text"] for s in line["spans"])).strip()
                    if value:
                        rows.append((line["bbox"], value))
            rows.sort(key=lambda row: (round(row[0][1], 1), row[0][0]))
            # Algunos números y sus títulos son objetos PDF separados en una
            # misma línea visual; se reúnen antes de reconocer los apartados.
            merged = []
            for box, value in rows:
                if merged and abs(box[1] - merged[-1][0][1]) < 1:
                    old_box, old_value = merged[-1]
                    merged[-1] = ((old_box[0], old_box[1], max(old_box[2], box[2]), max(old_box[3], box[3])), old_value + " " + value)
                else:
                    merged.append((box, value))
            rows = merged
            margin = min(box[0] for box, _ in rows)
            result.extend(Line(number, value, margin + 8 < box[0] < margin + 40) for box, value in rows)
    return result


def text(lines: list[Line]) -> str:
    result = ""
    for line in lines:
        separator = "" if not result or result.endswith("-") else " "
        result += separator + line.text
    return result


def provenance(lines: list[Line]) -> dict:
    assert lines
    return {"fuenteRef": SOURCE_ID, "paginas": sorted({line.page for line in lines})}


def paragraphs(lines: list[Line]) -> list[str]:
    groups: list[list[Line]] = []
    for line in lines:
        if line.indented or not groups:
            groups.append([])
        groups[-1].append(line)
    return [text(group) for group in groups]


def find(lines: list[Line], label: str, *, case_sensitive: bool = False) -> int:
    positions = [i for i, line in enumerate(lines) if
                 (line.text.rstrip(".") == label if case_sensitive else line.text.rstrip(".").casefold() == label.casefold())]
    assert len(positions) == 1, (label, positions)
    return positions[0]


def competencies(lines: list[Line], count: int) -> list[dict]:
    starts = [(i, int(m.group(1))) for i, line in enumerate(lines) if (m := re.match(r"^(\d+)\.\s+", line.text))]
    assert [n for _, n in starts] == list(range(1, count + 1)), starts
    output = []
    for index, (start, number) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(lines)
        segment = lines[start:end]
        description_start = next(i for i, line in enumerate(segment) if line.indented)
        key_start = next(i for i, line in enumerate(segment) if line.text.startswith("Esta competencia específica se conecta"))
        raw_keys = text(segment[key_start:]).split("salida:", 1)[1]
        keys = re.findall(r"\b[A-Z]{2,6}\d+(?:\.\d+)?\b", raw_keys)
        extra = re.sub(r"\b[A-Z]{2,6}\d+(?:\.\d+)?\b|[,.;\s]", "", raw_keys)
        assert keys and not extra, (segment[0].page, raw_keys, extra)
        if len(keys) != len(set(keys)):
            DIAGNOSTICS.append({"tipo": "descriptor-repetido", "competencia": number, "paginas": provenance(segment)["paginas"], "texto": raw_keys})
        output.append({
            "id": f"ce-{number}", "codigoOficial": str(number),
            "enunciado": {"es": re.sub(r"^\d+\.\s+", "", text(segment[:description_start]))},
            "descripcion": {"es": paragraphs(segment[description_start:key_start])},
            "descriptoresOperativosRefs": list(dict.fromkeys(keys)), "procedencia": provenance(segment),
        })
    return output


def criteria(lines: list[Line], dimension: int, count: int) -> list[dict]:
    groups: list[tuple[str, list[Line]]] = []
    active = None
    requires_item = False
    seen = []
    for line in lines:
        heading = re.fullmatch(r"Competencia específica (\d+)\.?", line.text)
        item = re.match(r"^(\d+\.\d+)(\.)?\s+(.+)$", line.text)
        if heading:
            active = int(heading.group(1)); seen.append(active); requires_item = True
        elif item:
            code, separator, value = item.groups()
            assert int(code.split(".")[0]) == active, (line.page, line.text, active)
            if not separator:
                DIAGNOSTICS.append({"tipo": "separador-criterio-omitido", "dimension": dimension, "codigo": code, "pagina": line.page})
            groups.append((code, [Line(line.page, value, False)])); requires_item = False
        elif requires_item:
            assert active is not None
            code = f"{active}.1"
            DIAGNOSTICS.append({"tipo": "codigo-criterio-omitido", "dimension": dimension, "codigo": code, "pagina": line.page, "texto": line.text})
            groups.append((code, [line])); requires_item = False
        else:
            assert groups, (line.page, line.text)
            groups[-1][1].append(line)
    assert seen == list(range(1, count + 1)), seen
    result = [{"id": f"cri-{dimension}-{code.replace('.', '-')}", "codigoOficial": code,
               "competenciaEspecificaRef": "ce-" + code.split(".")[0], "texto": {"es": text(words)},
               "saberesBasicosRefs": [], "procedencia": provenance(words)} for code, words in groups]
    assert len(result) == len({item["id"] for item in result})
    return result


def knowledge(lines: list[Line], code: str, dimension: int) -> list[dict]:
    blocks = []
    for line in lines:
        heading = re.match(r"^([A-Z])\.\s+(.+)$", line.text)
        section = re.match(r"^(\d+)\.(\.)?\s*(.+)$", line.text)
        bullet = re.match(r"^-\s*(.+)$", line.text)
        if heading:
            letter, value = heading.groups()
            assert letter == chr(65 + len(blocks)), (code, dimension, line.page, line.text)
            blocks.append({"codigo": letter, "name": [Line(line.page, value, False)], "items": [], "parts": []})
        elif section:
            assert blocks and not blocks[-1]["items"], (code, dimension, line.text)
            number, extra_dot, value = section.groups()
            if extra_dot:
                DIAGNOSTICS.append({"tipo": "punto-apartado-duplicado", "area": code, "dimension": dimension, "codigo": number, "pagina": line.page})
            assert number not in {part["codigo"] for part in blocks[-1]["parts"]}
            blocks[-1]["parts"].append({"codigo": number, "name": [Line(line.page, value, False)], "items": []})
        elif bullet:
            assert blocks
            container = blocks[-1]["parts"][-1] if blocks[-1]["parts"] else blocks[-1]
            container["items"].append([Line(line.page, bullet.group(1), False)])
        else:
            assert blocks, (code, dimension, line.page, line.text)
            container = blocks[-1]["parts"][-1] if blocks[-1]["parts"] else blocks[-1]
            if container["items"]:
                container["items"][-1].append(line)
            else:
                container["name"].append(line)
    result = []
    for block in blocks:
        output = {"codigo": block["codigo"], "nombre": {"es": text(block["name"]).rstrip(".")}}
        number = 0
        def items(container: dict) -> list[dict]:
            nonlocal number
            values = []
            for words in container["items"]:
                number += 1
                values.append({"id": f"{code}.{dimension}.{block['codigo']}.{number:02d}", "codigoOficial": None,
                               "texto": {"es": text(words)}, "procedencia": provenance(words)})
            assert values, (code, dimension, block["codigo"], container)
            return values
        if block["parts"]:
            output["apartados"] = [{"codigo": part["codigo"], "nombre": {"es": text(part["name"]).rstrip(".")}, "saberes": items(part)} for part in block["parts"]]
        else:
            output["saberes"] = items(block)
        result.append(output)
    return result


def all_sabers(development: dict) -> list[dict]:
    return [item for block in development["bloquesSaberes"] for part in block.get("apartados", [block]) for item in part["saberes"]]


def normalize(document: dict) -> None:
    # Las decisiones editoriales se documentan solo en incidencias/es-cb.md.
    code = document["materia"]["codigo"]
    replacements = {
        "CM": [
            ("Materiales herramientas y objetos", "Materiales, herramientas y objetos"),
        ],
        "EA": [("Indagar en proceso de creación", "Indagar en el proceso de creación")],
        "EF": [("Tomar decisiones en contextos de practica motriz", "Tomar decisiones en contextos de práctica motriz")],
        "EVCE": [("los organismos internaciones", "los organismos internacionales")],
        "LCL": [
            ("contextos formales informales", "contextos formales e informales"),
            ("en el marco de propuestas la producción", "en el marco de propuestas de producción"),
            ("interacción oral y adecuada", "interacción oral adecuada"),
        ],
        "LE": [("estrategias básicas para entender y apreciar la diversidad lingüística, cultural y artística", "estrategias básicas para entender y apreciar la diversidad lingüística, cultural y artística.")],
        "MAT": [("figuras geométricas sencillas de una, dos dimensiones", "figuras geométricas sencillas de una y dos dimensiones")],
    }
    counts = {old: 0 for old, _ in replacements[code]}

    def replace(value):
        if isinstance(value, str):
            for old, new in replacements[code]:
                counts[old] += value.count(old)
                value = value.replace(old, new)
            return value
        if isinstance(value, list):
            return [replace(item) for item in value]
        if isinstance(value, dict):
            return {key: replace(item) for key, item in value.items()}
        return value

    corrected = replace(document)
    assert all(count == 1 for count in counts.values()), (code, counts)
    document.clear()
    document.update(corrected)
    if code == "CM":
        block = document["desarrollos"][2]["bloquesSaberes"][2]
        assert block["codigo"] == "C" and [part["codigo"] for part in block["apartados"]] == ["1", "2", "3"]
        civic = block["apartados"][-1]
        position = next(i for i, saber in enumerate(civic["saberes"]) if saber["texto"]["es"] == "Conciencia ecosocial.")
        assert position == 5 and len(civic["saberes"]) == 12
        block["apartados"].append({"codigo": "4", "nombre": {"es": "Conciencia ecosocial"}, "saberes": civic["saberes"][position + 1:]})
        civic["saberes"] = civic["saberes"][:position]
        for number, saber in enumerate((item for part in block["apartados"] for item in part["saberes"]), 1):
            saber["id"] = f"CM.3.C.{number:02d}"


def extract() -> list[dict]:
    lines = lines_from_pdf()
    starts = [find(lines, name, case_sensitive=True) for _, name, _, _ in AREAS]
    assert starts == sorted(starts)
    output = []
    for area_index, (slug, name, code, count) in enumerate(AREAS):
        end = starts[area_index + 1] if area_index + 1 < len(starts) else len(lines)
        area = lines[starts[area_index] + 1:end]
        narrative_start = find(area, "Competencias específicas")
        values = code == "EVCE"
        narrative_end = find(area, "Criterios de evaluación") if values else find(area, "Primer ciclo")
        ce = competencies(area[narrative_start + 1:narrative_end], count)
        if values:
            segments = [(5, area[narrative_end + 1:])]
        else:
            cycle_starts = [find(area, label + " ciclo") for label in ("Primer", "Segundo", "Tercer")]
            segments = []
            for cycle, position in enumerate(cycle_starts, 1):
                last = cycle_starts[cycle] if cycle < 3 else len(area)
                segment = area[position + 1:last]
                assert segment[0].text.rstrip(".") == "Criterios de evaluación"
                segments.append((cycle, segment[1:]))
        developments = []
        for dimension, segment in segments:
            saber_start = find(segment, "Saberes básicos")
            developments.append({"curso" if values else "ciclo": dimension,
                                 "criteriosEvaluacion": criteria(segment[:saber_start], dimension, count),
                                 "bloquesSaberes": knowledge(segment[saber_start + 1:], code, dimension)})
        notes = [
            "Las abreviaturas de área y los identificadores individuales de saberes son internos del proyecto, no códigos oficiales; los saberes se publican con viñetas y codigoOficial queda en null.",
            "Los números de los apartados de saberes se conservan en codigo; las letras de los bloques se conservan tal como se publican.",
            "Los descriptores operativos se publican por competencia específica. No se asignan descriptores a criterios ni asociaciones criterio-saber que la fuente no publica.",
            "Las disposiciones finales primera y tercera fijan la entrada en vigor para el curso 2022/2023 sin un día concreto. Se implanta en 1.º, 3.º y 5.º en 2022/2023 y en 2.º, 4.º y 6.º en 2023/2024; entradaEnVigor queda en null.",
        ]
        if values:
            notes.append("El artículo 17.2 sitúa Educación en Valores Cívicos y Éticos en 5.º de Primaria: se representa un único desarrollo de ese curso.")
        else:
            notes.append("Las competencias son comunes a la etapa y los desarrollos se conservan por ciclo, sin atribuir una secuenciación por curso que el anexo no publica.")
        document = {
            "$schema": "../../../../schemas/materia.schema.json", "schemaVersion": "0.3.0", "id": f"es-cb.primaria.{slug}",
            "territorio": "es-cb", "etapa": "primaria",
            "materia": {"codigo": code, "nombre": {"es": name},
                        "cursos" if values else "ciclos": [{"curso" if values else "ciclo": n, "caracter": "obligatoria"} for n in ([5] if values else [1, 2, 3])]},
            "vigencia": {"entradaEnVigor": None, "aplicableDesdeCurso": "2022/2023", "hasta": None, "estado": "vigente"},
            "fuentes": [{"id": SOURCE_ID, "tipo": "decreto", "titulo": "Decreto 66/2022, de 7 de julio, por el que se establece el currículo de la Educación Infantil y de la Educación Primaria en la Comunidad Autónoma de Cantabria",
                         "publicacion": "Boletín Oficial de Cantabria", "numero": "135", "fechaPublicacion": "2022-07-13", "cve": "CVE-2022-5545",
                         "urlOficial": URL, "urlVerificacion": URL, "anexo": "II-A", "paginasMateria": {"desde": lines[starts[area_index]].page, "hasta": area[-1].page}}],
            "introduccion": {"es": paragraphs(area[:narrative_start])}, "competenciasEspecificas": ce, "desarrollos": developments,
            "revision": {"estado": "revisado", "fuenteComprobada": True, "fechaUltimaRevision": "2026-11-04",
                         "metodo": "Extracción del texto y las coordenadas del PDF oficial, cotejo visual y contraste independiente con Poppler.", "notas": notes},
        }
        normalize(document)
        output.append(document)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--diagnostics", type=Path)
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for document in extract():
        stats = [(dev.get("ciclo", dev.get("curso")), len(dev["criteriosEvaluacion"]), len(all_sabers(dev))) for dev in document["desarrollos"]]
        print(document["materia"]["codigo"], "CE", len(document["competenciasEspecificas"]), "(ciclo/curso, criterios, saberes)", stats)
        if args.write:
            DEST.mkdir(parents=True, exist_ok=True)
            (DEST / (document["id"].split(".")[-1] + ".json")).write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.diagnostics:
        args.diagnostics.parent.mkdir(parents=True, exist_ok=True)
        args.diagnostics.write_text(json.dumps(DIAGNOSTICS, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("DIAGNOSTICOS", json.dumps(DIAGNOSTICS, ensure_ascii=False))


if __name__ == "__main__":
    main()
