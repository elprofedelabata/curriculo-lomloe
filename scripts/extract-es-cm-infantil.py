"""Extrae las tres áreas de Infantil del anexo II del Decreto 80/2022."""

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
DEST = ROOT / "data/es-cm/infantil/materias"
SOURCE_ID = "es-cm-infantil-decreto-80-2022"
AREAS = (
    ("crecimiento-en-armonia", "Crecimiento en Armonía", "CA"),
    ("descubrimiento-y-exploracion-del-entorno", "Descubrimiento y Exploración del Entorno", "DEE"),
    ("comunicacion-y-representacion-de-la-realidad", "Comunicación y Representación de la Realidad", "CRR"),
)
DESCRIPTOR_PREFIX = "Esta competencia específica se conecta con los siguientes descriptores:"
BULLET = re.compile(r"^[-−–]\s+(.+)$")
BLOCK = re.compile(r"^([A-I])\.\s+(.+)$")


@dataclass(frozen=True)
class Line:
    page: int
    text: str
    starts_paragraph: bool


def source_lines(path: Path) -> list[Line]:
    result = []
    with fitz.open(path) as pdf:
        for number in range(19, 40):
            rows = []
            for block in pdf[number - 1].get_text("dict")["blocks"]:
                block_lines = []
                for row in block.get("lines", []):
                    x, y = row["bbox"][:2]
                    value = " ".join("".join(span["text"] for span in row["spans"]).split())
                    if y >= 83 and value:
                        block_lines.append((y, x, value))
                rows.extend((y, x, value, i == 0) for i, (y, x, value) in enumerate(block_lines))
            for i, (_, _, value, new_paragraph) in enumerate(sorted(rows)):
                # At a page break the first block may continue the previous sentence.
                if i == 0 and result and value[0].islower():
                    new_paragraph = False
                result.append(Line(number, value, new_paragraph))
    return result


def joined(lines: list[Line]) -> str:
    assert lines
    result = lines[0].text
    for line in lines[1:]:
        # The annex wraps two hyphenated compounds across lines.
        space = "" if result.endswith("-") and line.text[0].islower() else " "
        result += space + line.text
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
        desc_start = references[0]
        statement, *description = paragraphs(segment[:desc_start])
        assert description, segment[0]
        reference_text = joined(segment[desc_start:]).removeprefix(DESCRIPTOR_PREFIX).strip()
        assert reference_text.endswith("."), reference_text
        descriptors = reference_text[:-1].replace("CPSAA 4", "CPSAA4").split(",")
        descriptors = [code.strip() for code in descriptors]
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


def criteria(lines: list[Line], cycle: int, ce_count: int) -> list[dict]:
    groups = []
    seen = []
    for line in lines:
        if match := re.fullmatch(r"Competencia específica (\d+)\.", line.text):
            seen.append(int(match[1]))
        elif match := re.fullmatch(r"(\d+\.\d+)\.\s+(.+)", line.text):
            code, value = match.groups()
            assert seen and int(code.split(".")[0]) == seen[-1], (line.page, line.text)
            groups.append((code, [replace(line, text=value)]))
        else:
            assert groups and not line.starts_paragraph, (line.page, line.text)
            groups[-1][1].append(line)
    assert seen == list(range(1, ce_count + 1))
    assert len({code for code, _ in groups}) == len(groups)
    return [{
        "id": f"cri-{cycle}-{code.replace('.', '-')}",
        "codigoOficial": code,
        "competenciaEspecificaRef": f"ce-{code.split('.')[0]}",
        "texto": {"es": joined(words)},
        "saberesBasicosRefs": [],
        "procedencia": provenance(words),
    } for code, words in groups]


def knowledge(lines: list[Line], area_code: str, cycle: int) -> list[dict]:
    blocks = []
    for line in lines:
        if match := BLOCK.fullmatch(line.text):
            code, value = match.groups()
            assert code == chr(ord("A") + len(blocks)), (line.page, line.text)
            blocks.append((code, [replace(line, text=value)], []))
        elif match := BULLET.fullmatch(line.text):
            assert blocks, (line.page, line.text)
            blocks[-1][2].append([replace(line, text=match[1])])
        else:
            assert blocks, (line.page, line.text)
            _, title, items = blocks[-1]
            (items[-1] if items else title).append(line)
    assert all(items for _, _, items in blocks)
    return [{
        "codigo": code,
        "nombre": {"es": joined(title).rstrip(".")},
        "saberes": [{
            "id": f"{area_code}.{cycle}.{code}.{i:02d}",
            "codigoOficial": None,
            "texto": {"es": joined(words)},
            "procedencia": provenance(words),
        } for i, words in enumerate(items, 1)],
    } for code, title, items in blocks]


def apply_editorial_changes(document: dict) -> None:
    """Aplica las correcciones confirmadas en el registro de Castilla-La Mancha."""
    area = document["materia"]["codigo"]
    introduction = document["introduccion"]["es"]
    competencies_list = document["competenciasEspecificas"]
    developments = document["desarrollos"]

    def substitute(values: list[str], old: str, new: str) -> None:
        assert sum(value.count(old) for value in values) == 1, (area, old)
        values[:] = [value.replace(old, new) for value in values]

    def criterion(cycle: int, code: str) -> dict:
        return next(item["texto"] for item in developments[cycle - 1]["criteriosEvaluacion"]
                    if item["codigoOficial"] == code)

    if area == "CA":
        substitute(introduction, "las sensaciones que experimenta,", "las sensaciones que experimentan,")
        substitute(
            competencies_list[2]["descripcion"]["es"],
            "hábitos saludables y sostenibles y así como su progresiva integración en la vida cotidiana contribuye al cuidado del propio cuerpo, y al logro",
            "hábitos saludables y sostenibles, así como su progresiva integración en la vida cotidiana, contribuye al cuidado del propio cuerpo y al logro",
        )
        substitute(competencies_list[3]["descripcion"]["es"], "la aceptación de la capacidad", "la aceptación de la discapacidad")
        target = criterion(2, "2.3")
        assert target["es"].endswith("sobre los logros conseguidos,")
        target["es"] = target["es"][:-1] + "."
    elif area == "DEE":
        substitute(introduction, "hábitos ecosaludabes", "hábitos ecosaludables")
        target = criterion(1, "2.3")
        assert target["es"].endswith("retos a los que se le planteen")
        target["es"] = target["es"].removesuffix("retos a los que se le planteen") + "retos que se le planteen."
        target = criterion(1, "3.1")
        assert target["es"].endswith("los animales que lo habitan")
        target["es"] += "."
        knowledge_items = developments[1]["bloquesSaberes"][2]["saberes"]
        target = next(item["texto"] for item in knowledge_items if "Espacios protegidos de Castilla La Mancha" in item["texto"]["es"])
        target["es"] = target["es"].replace("Castilla La Mancha", "Castilla-La Mancha", 1)
    else:
        for code, ending in (("3.1", "contextos formales e informales"), ("4.2", "la interpretación de mensajes")):
            target = criterion(2, code)
            assert target["es"].endswith(ending)
            target["es"] += "."
        knowledge_items = developments[1]["bloquesSaberes"][3]["saberes"]
        target = next(item["texto"] for item in knowledge_items if "interpretación y compresión." in item["texto"]["es"])
        target["es"] = target["es"].replace("interpretación y compresión.", "interpretación y comprensión.", 1)


def extract() -> list[dict]:
    catalog = json.loads((NORMATIVE / "catalogo.json").read_text(encoding="utf-8"))
    source = next(item for item in catalog["documentos"] if item["id"] == SOURCE_ID)
    pdf = NORMATIVE / source["archivo"]
    assert hashlib.sha256(pdf.read_bytes()).hexdigest() == source["sha256"]
    lines = source_lines(pdf)
    starts = [heading(lines, f"Área {index}. {name}")
              for index, (_, name, _) in enumerate(AREAS, 1)]
    documents = []
    for index, (slug, name, code) in enumerate(AREAS):
        start = starts[index]
        end = starts[index + 1] if index + 1 < len(starts) else len(lines)
        area = lines[start + 1:end]
        first = heading(area, "Primer ciclo")
        second = heading(area, "Segundo ciclo")
        competence_start = heading(area[:first], "Competencias específicas")
        specific = competencies(area[competence_start + 1:first])
        developments = []
        for cycle, section in enumerate((area[first + 1:second], area[second + 1:]), 1):
            assert section[0].text == "Criterios de evaluación."
            saber_start = heading(section, "Saberes básicos")
            developments.append({
                "ciclo": cycle,
                "criteriosEvaluacion": criteria(section[1:saber_start], cycle, len(specific)),
                "bloquesSaberes": knowledge(section[saber_start + 1:], code, cycle),
            })
        document = {
            "$schema": "../../../../schemas/materia.schema.json",
            "schemaVersion": "0.3.0",
            "id": f"es-cm.infantil.{slug}",
            "territorio": "es-cm",
            "etapa": "infantil",
            "materia": {
                "codigo": code, "nombre": {"es": name},
                "ciclos": [{"ciclo": cycle, "caracter": "obligatoria"} for cycle in (1, 2)],
            },
            "vigencia": {"entradaEnVigor": "2022-07-15", "aplicableDesdeCurso": "2022/2023", "hasta": None, "estado": "vigente"},
            "fuentes": [{
                "id": SOURCE_ID, "tipo": "decreto", "titulo": source["titulo"],
                "publicacion": "Diario Oficial de Castilla-La Mancha", "numero": source["docm"],
                "fechaPublicacion": source["fechaPublicacion"], "cve": source["codigoDocm"],
                "urlOficial": source["urlOficial"], "urlVerificacion": source["urlOficial"],
                "anexo": "II", "paginasMateria": {"desde": lines[start].page, "hasta": area[-1].page},
            }],
            "introduccion": {"es": paragraphs(area[:competence_start])},
            "competenciasEspecificas": specific,
            "desarrollos": developments,
            "revision": {
                "estado": "revisado", "fuenteComprobada": True, "fechaUltimaRevision": "2026-11-05",
                "metodo": "Extracción del texto y las coordenadas del PDF, inspección visual y contraste independiente con Poppler.",
                "notas": [
                    "Las competencias específicas y sus descriptores publicados son comunes a ambos ciclos. Los criterios y saberes se organizan por ciclo.",
                    "El artículo 10.2 define el carácter orientativo de los descriptores operativos y el artículo 10.3 establece el carácter orientativo de los elementos curriculares del primer ciclo.",
                    "Las abreviaturas de área y los identificadores de saber son internos del proyecto. El decreto publica letras para los bloques y viñetas sin código individual para los saberes.",
                    "El decreto no publica correspondencias explícitas entre criterios y saberes.",
                    "La disposición final primera fija la implantación para 2022/2023. La disposición final tercera fija la entrada en vigor al día siguiente de la publicación.",
                ],
            },
        }
        apply_editorial_changes(document)
        documents.append(document)
    return documents


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    documents = extract()
    for document in documents:
        stats = [{
            "ciclo": dev["ciclo"],
            "criterios": len(dev["criteriosEvaluacion"]),
            "saberes": sum(len(block["saberes"]) for block in dev["bloquesSaberes"]),
        } for dev in document["desarrollos"]]
        print(json.dumps({
            "area": document["materia"]["nombre"]["es"],
            "competencias": len(document["competenciasEspecificas"]),
            "descriptores": sum(len(ce["descriptoresOperativosRefs"]) for ce in document["competenciasEspecificas"]),
            "ciclos": stats,
        }, ensure_ascii=False))
        if args.write:
            DEST.mkdir(parents=True, exist_ok=True)
            filename = document["id"].rsplit(".", 1)[-1] + ".json"
            (DEST / filename).write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
