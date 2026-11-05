"""Extrae las siete áreas del anexo II del Decreto 81/2022 de Castilla-La Mancha."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
NORMATIVE = ROOT / "sources/es-cm/normativa"
DEST = ROOT / "data/es-cm/primaria/materias"
SOURCE_ID = "es-cm-primaria-decreto-81-2022"
AREAS = (
    ("conocimiento-del-medio-natural-social-y-cultural", "Conocimiento del Medio Natural, Social y Cultural", "CM"),
    ("educacion-artistica", "Educación Artística", "EA"),
    ("educacion-fisica", "Educación Física", "EF"),
    ("educacion-en-valores-civicos-y-eticos", "Educación en Valores Cívicos y Éticos", "EVCE"),
    ("lengua-castellana-y-literatura", "Lengua Castellana y Literatura", "LCL"),
    ("lengua-extranjera", "Lengua Extranjera", "LE"),
    ("matematicas", "Matemáticas", "MAT"),
)
DESCRIPTOR_PREFIX = "Esta competencia específica se conecta con los siguientes descriptores del Perfil de salida:"
BLOCK = re.compile(r"^([A-Z])\.\s+(.+)$")
PART = re.compile(r"^(\d+)\.\s+([^\W\d_].*)$")
BULLET = re.compile(r"^[-–−]\s+(.+)$")
LEGADO = "El legado artístico, literario, patrimonial y natural propio de países de la lengua extranjera."
UNNUMBERED_CRITERIA = {
    ("LCL", 1, 2): (71, "Comprender el sentido de textos orales y multimodales sencillos"),
    ("LCL", 1, 5): (71, "Producir textos escritos y multimodales sencillos y coherentes"),
    ("LE", 1, 4): (84, "Interpretar y explicar, de forma guiada, información básica"),
}
EDITORIAL_CHANGES = {
    "EF": (
        ("de manera no especifica", "de manera no específica", 2),
        ("Valoración de la condición física orientadas a la salud", "Valoración de la condición física orientada a la salud", 2),
        ("Batería ALPHA-Fitness$", "Batería ALPHA-Fitness.", 1),
        ("propia cultura de Castilla la Mancha", "propia cultura de Castilla-La Mancha", 1),
    ),
    "EVCE": (("La transversalidad con las que se afrontan", "La transversalidad con la que se afrontan", 1),),
    "LCL": (("del metalenguaje necesario para la reflexionar", "del metalenguaje necesario para reflexionar", 1),),
    "LE": (
        ("del auditoria", "del auditorio", 1),
        ("Interpretar, explica o transmitir", "Interpretar, explicar o transmitir", 1),
        ("los conocimientos precios", "los conocimientos previos", 1),
    ),
}


@dataclass(frozen=True)
class Line:
    page: int
    text: str
    starts_paragraph: bool


def source_lines(path: Path) -> list[Line]:
    result = []
    with fitz.open(path) as pdf:
        for number in range(26, 105):
            rows = []
            for block in pdf[number - 1].get_text("dict")["blocks"]:
                for row in block.get("lines", []):
                    x, y = row["bbox"][:2]
                    value = " ".join("".join(span["text"] for span in row["spans"]).split())
                    if y >= 83 and value:
                        rows.append((y, x, value))
            previous_y = None
            for y, _, value in sorted(rows):
                if previous_y is None:
                    # At a page break a line may complete the preceding paragraph.
                    new_paragraph = not result or (not value[0].islower() and result[-1].text.endswith((".", "?", "!", "»")))
                else:
                    new_paragraph = y - previous_y > 16
                result.append(Line(number, value, new_paragraph))
                previous_y = y
    return result


def joined(lines: list[Line]) -> str:
    assert lines
    result = lines[0].text
    for line in lines[1:]:
        separator = "" if result.endswith("-") and line.text[0].isalpha() else " "
        result += separator + line.text
    return result


def provenance(lines: list[Line]) -> dict:
    assert lines
    return {"fuenteRef": SOURCE_ID, "paginas": sorted({line.page for line in lines})}


def paragraphs(lines: list[Line]) -> list[str]:
    groups = []
    for line in lines:
        if not groups or line.starts_paragraph:
            groups.append([])
        groups[-1].append(line)
    return [joined(group) for group in groups]


def heading(lines: list[Line], label: str) -> int:
    matches = [i for i, line in enumerate(lines) if line.text.rstrip(".") == label]
    assert len(matches) == 1, (label, matches)
    return matches[0]


def competencies(lines: list[Line]) -> list[dict]:
    starts = [(i, int(match[1])) for i, line in enumerate(lines)
              if (match := re.match(r"^(\d+)\.\s+", line.text))]
    assert starts and starts[0][0] == 0
    assert [number for _, number in starts] == list(range(1, len(starts) + 1))
    result = []
    for i, (start, number) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(lines)
        segment = lines[start:end]
        references = [j for j, line in enumerate(segment) if line.text.startswith(DESCRIPTOR_PREFIX)]
        assert len(references) == 1, (segment[0], references)
        reference_start = references[0]
        statement, *description = paragraphs(segment[:reference_start])
        assert description, segment[0]
        reference_text = joined(segment[reference_start:]).removeprefix(DESCRIPTOR_PREFIX).strip()
        assert reference_text.endswith("."), reference_text
        descriptors = [code.strip() for code in reference_text[:-1].split(",")]
        assert len(descriptors) == len(set(descriptors))
        assert all(re.fullmatch(r"(?:CCL|CP|STEM|CD|CPSAA|CCEC|CC|CE)[1-5]", code)
                   for code in descriptors), descriptors
        result.append({
            "id": f"ce-{number}",
            "codigoOficial": str(number),
            "enunciado": {"es": re.sub(r"^\d+\.\s+", "", statement)},
            "descripcion": {"es": description},
            "descriptoresOperativosRefs": descriptors,
            "procedencia": provenance(segment),
        })
    return result


def criteria(lines: list[Line], area_code: str, dimension: int, ce_count: int) -> list[dict]:
    groups = []
    seen = []
    awaiting_first = False
    for line in lines:
        if match := re.fullmatch(r"Competencia específica (\d+)\.?", line.text):
            seen.append(int(match[1]))
            awaiting_first = True
        elif match := re.fullmatch(r"(\d+\.\d+)\.?\s+(.+)", line.text):
            code, value = match.groups()
            assert seen and int(code.split(".")[0]) == seen[-1], (line.page, line.text)
            groups.append((code, [replace(line, text=value)]))
            awaiting_first = False
        elif awaiting_first:
            location = UNNUMBERED_CRITERIA.get((area_code, dimension, seen[-1]))
            assert location and line.page == location[0] and line.text.startswith(location[1]), (line.page, line.text)
            groups.append((f"{seen[-1]}.1", [line]))
            awaiting_first = False
        else:
            assert groups and not line.starts_paragraph, (line.page, line.text)
            groups[-1][1].append(line)
    assert seen == list(range(1, ce_count + 1)), seen
    assert len({code for code, _ in groups}) == len(groups)
    return [{
        "id": f"cri-{dimension}-{code.replace('.', '-')}",
        "codigoOficial": code,
        "competenciaEspecificaRef": f"ce-{code.split('.')[0]}",
        "texto": {"es": joined(words)},
        "saberesBasicosRefs": [],
        "procedencia": provenance(words),
    } for code, words in groups]


def knowledge(lines: list[Line], area_code: str, dimension: int) -> list[dict]:
    blocks = []
    for line in lines:
        if match := BLOCK.fullmatch(line.text):
            letter, title = match.groups()
            assert letter == chr(ord("A") + len(blocks)), (line.page, line.text)
            blocks.append({"code": letter, "title": title, "parts": [], "items": []})
            continue
        assert blocks, (line.page, line.text)
        block = blocks[-1]
        part = PART.fullmatch(line.text)
        unnumbered_part = area_code == "MAT" and dimension == 1 and line.text == "Organización y análisis de datos."
        if part or unnumbered_part:
            assert not block["items"], (line.page, line.text)
            code, title = part.groups() if part else ("organizacion-y-analisis-de-datos", line.text)
            assert code not in {item["code"] for item in block["parts"]}
            block["parts"].append({"code": code, "title": title, "items": []})
            continue
        container = block["parts"][-1] if block["parts"] else block
        bullet = BULLET.fullmatch(line.text)
        evce_point = area_code == "EVCE" and line.page == 65 and line.text.startswith(". ")
        if bullet:
            container["items"].append([replace(line, text=bullet[1])])
        elif evce_point:
            container["items"].append([replace(line, text=line.text[2:])])
        elif area_code == "LE" and line.page == 89 and line.text == LEGADO:
            container["items"].append([line])
        elif container["items"]:
            container["items"][-1].append(line)
        else:
            container["title"] += " " + line.text

    result = []
    for block in blocks:
        entry = {"codigo": block["code"], "nombre": {"es": block["title"].rstrip(".")}}
        number = 0

        def items(container: dict) -> list[dict]:
            nonlocal number
            values = []
            for words in container["items"]:
                number += 1
                values.append({
                    "id": f"{area_code}.{dimension}.{block['code']}.{number:02d}",
                    "codigoOficial": None, "texto": {"es": joined(words)}, "procedencia": provenance(words),
                })
            assert values, (area_code, dimension, container["title"])
            return values

        if block["parts"]:
            entry["apartados"] = [{
                "codigo": part["code"], "nombre": {"es": part["title"].rstrip(".")}, "saberes": items(part),
            } for part in block["parts"]]
        else:
            entry["saberes"] = items(block)
        result.append(entry)
    return result


def source_metadata(source: dict, *, annex: str | None = None, pages: tuple[int, int]) -> dict:
    result = {
        "id": source["id"],
        "tipo": "otro" if source["tipo"] == "correccion-errores" else source["tipo"],
        "titulo": source["titulo"],
        "publicacion": "Diario Oficial de Castilla-La Mancha",
        "numero": source["docm"],
        "fechaPublicacion": source["fechaPublicacion"],
        "cve": source["codigoDocm"],
        "urlOficial": source["urlOficial"],
        "urlVerificacion": source["urlOficial"],
        "paginasMateria": {"desde": pages[0], "hasta": pages[1]},
    }
    if annex:
        result["anexo"] = annex
    return result


def saber_items(development: dict):
    for block in development["bloquesSaberes"]:
        for container in block.get("apartados", [block]):
            yield from container["saberes"]


def apply_editorial_changes(document: dict, area_code: str) -> None:
    changes = EDITORIAL_CHANGES[area_code]
    counts = [0] * len(changes)

    def correct(text: str) -> str:
        for index, (published, proposed, _) in enumerate(changes):
            text, count = re.subn(published, proposed, text)
            counts[index] += count
        return text

    intro = document["introduccion"]["es"]
    document["introduccion"]["es"] = [correct(text) for text in intro]
    for development in document["desarrollos"]:
        for criterion in development["criteriosEvaluacion"]:
            criterion["texto"]["es"] = correct(criterion["texto"]["es"])
        for saber in saber_items(development):
            saber["texto"]["es"] = correct(saber["texto"]["es"])
    assert counts == [count for _, _, count in changes], (area_code, counts)


def extract() -> list[dict]:
    catalog = json.loads((NORMATIVE / "catalogo.json").read_text(encoding="utf-8"))
    sources = {item["id"]: item for item in catalog["documentos"]}
    source = sources[SOURCE_ID]
    pdf = NORMATIVE / source["archivo"]
    assert hashlib.sha256(pdf.read_bytes()).hexdigest() == source["sha256"]
    lines = source_lines(pdf)
    starts = [heading(lines, name) for _, name, _ in AREAS]
    documents = []
    for index, (slug, name, code) in enumerate(AREAS):
        start = starts[index]
        end = starts[index + 1] if index + 1 < len(starts) else len(lines)
        area = lines[start + 1:end]
        competence_start = heading(area, "Competencias específicas")
        if code == "EVCE":
            section_start = heading(area, "Criterios de evaluación")
            sections = [(5, area[section_start:])]
            dimension_key = "curso"
        else:
            cycle_starts = [heading(area, f"{label} ciclo") for label in ("Primer", "Segundo", "Tercer")]
            section_start = cycle_starts[0]
            cycle_bounds = zip(cycle_starts, cycle_starts[1:] + [len(area)])
            sections = [(cycle, area[lower + 1:upper]) for cycle, (lower, upper) in enumerate(cycle_bounds, 1)]
            dimension_key = "ciclo"
        specific = competencies(area[competence_start + 1:section_start])
        developments = []
        for dimension, section in sections:
            assert section[0].text.rstrip(".") == "Criterios de evaluación"
            saber_start = heading(section, "Saberes básicos")
            developments.append({
                dimension_key: dimension,
                "criteriosEvaluacion": criteria(section[1:saber_start], code, dimension, len(specific)),
                "bloquesSaberes": knowledge(section[saber_start + 1:], code, dimension),
            })

        notes = [
            "Las abreviaturas de área y los identificadores individuales de saber son internos. El decreto publica letras y, cuando procede, números de apartado.",
            "Las listas de descriptores corresponden a cada competencia específica. El decreto publica criterios y saberes por separado.",
            "La disposición final primera fija la implantación en primero, tercero y quinto en 2022/2023, y en segundo, cuarto y sexto en 2023/2024.",
        ]
        if code == "EVCE":
            notes.append("El artículo 9.2 y el horario del anexo IV sitúan esta área en quinto. Los criterios y saberes se representan con curso 5.")
        else:
            notes.append("Las competencias específicas son comunes a los tres ciclos. Los criterios y saberes se conservan por ciclo.")
        if code == "EA":
            notes.append("El artículo 9.1.b permite desdoblar Educación Artística en Educación Plástica y Visual y Música y Danza. El anexo II presenta su currículo en un único desarrollo de área.")
        if code == "MAT":
            notes.append("Organización y análisis de datos es un apartado sin número en el bloque E del primer ciclo. Su código textual es interno.")
        references = [source_metadata(source, annex="II", pages=(lines[start].page, area[-1].page))]
        if code == "LE":
            references.extend([
                source_metadata(sources["es-cm-infantil-primaria-orden-75-2023"], pages=(1, 3)),
                source_metadata(sources["es-cm-infantil-primaria-correccion-orden-75-2023"], pages=(1, 1)),
            ])
            notes.append("El anexo II publica un currículo común de Lengua Extranjera. El artículo 9.5 y el horario del anexo IV documentan la oferta autorizada de Segunda Lengua Extranjera. La Orden 75/2023 regula sus modalidades de implantación y su corrección rectifica el procedimiento de los centros.")
        document = {
            "$schema": "../../../../schemas/materia.schema.json",
            "schemaVersion": "0.3.0",
            "id": f"es-cm.primaria.{slug}", "territorio": "es-cm", "etapa": "primaria",
            "materia": {
                "codigo": code, "nombre": {"es": name},
                dimension_key + "s": [{dimension_key: dimension, "caracter": "obligatoria"} for dimension, _ in sections],
            },
            "vigencia": {"entradaEnVigor": "2022-07-15", "aplicableDesdeCurso": "2022/2023", "hasta": None, "estado": "vigente"},
            "fuentes": references,
            "introduccion": {"es": paragraphs(area[:competence_start])},
            "competenciasEspecificas": specific,
            "desarrollos": developments,
            "revision": {
                "estado": "revisado", "fuenteComprobada": True, "fechaUltimaRevision": "2026-11-05",
                "metodo": "Extracción del texto y las coordenadas del PDF, inspección visual y contraste independiente con Poppler.",
                "notas": notes,
            },
        }
        if code in EDITORIAL_CHANGES:
            apply_editorial_changes(document, code)
        documents.append(document)
    return documents


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    for document in extract():
        stats = []
        for dev in document["desarrollos"]:
            sabers = sum(1 for _ in saber_items(dev))
            stats.append([dev.get("ciclo", dev.get("curso")), len(dev["criteriosEvaluacion"]), sabers])
        print(json.dumps({
            "area": document["materia"]["nombre"]["es"],
            "competencias": len(document["competenciasEspecificas"]),
            "desarrollos": stats,
        }, ensure_ascii=False))
        if args.write:
            DEST.mkdir(parents=True, exist_ok=True)
            filename = document["id"].rsplit(".", 1)[-1] + ".json"
            (DEST / filename).write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
