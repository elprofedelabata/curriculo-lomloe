"""Extrae las tres áreas de Infantil del anexo I-A del Decreto 66/2022.

Uso: python scripts/extract-es-cb-infantil.py [--write]
Las abreviaturas y los identificadores individuales de saberes son internos.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "sources/es-cb/normativa/infantil-primaria/2022-07-07-decreto-66-2022-curriculo-infantil-primaria.pdf"
DEST = ROOT / "data/es-cb/infantil/materias"
SOURCE_ID = "boc-2022-135-decreto-66-2022"
SOURCE_URL = "https://boc.cantabria.es/boces/verAnuncioAction.do?idAnuBlob=374267"
AREAS = (
    ("crecimiento-en-armonia", "Crecimiento en Armonía", "CA", 4, (12, 14), (32, 35), (4, 4)),
    ("descubrimiento-y-exploracion-del-entorno", "Descubrimiento y Exploración del Entorno", "DEE", 3, (7, 14), (16, 27), (3, 3)),
    ("comunicacion-y-representacion-de-la-realidad", "Comunicación y Representación de la Realidad", "CRR", 5, (14, 21), (31, 43), (8, 9)),
)


@dataclass(frozen=True)
class Line:
    page: int
    text: str
    indented: bool


def source_lines() -> list[Line]:
    catalog = json.loads((ROOT / "sources/es-cb/normativa/catalogo.json").read_text(encoding="utf-8"))
    source = next(d for d in catalog["documentos"] if d["id"] == "es-cb-infantil-primaria-decreto-66-2022")
    assert hashlib.sha256(PDF.read_bytes()).hexdigest() == source["sha256"]
    result = []
    with fitz.open(PDF) as pdf:
        for page_number in range(24, 55):
            page = pdf[page_number - 1]
            rows = []
            for block in page.get_text("dict", clip=fitz.Rect(95, 125, 525, 775))["blocks"]:
                for line in block.get("lines", []):
                    text = re.sub(r"\s+", " ", "".join(span["text"] for span in line["spans"])).strip()
                    if text:
                        rows.append((line["bbox"], text))
            rows.sort(key=lambda row: (round(row[0][1], 1), row[0][0]))
            margin = min(box[0] for box, _ in rows)
            for box, text in rows:
                result.append(Line(page_number, text, margin + 8 < box[0] < margin + 40))
    return result


def text(lines: list[Line]) -> str:
    return " ".join(line.text for line in lines)


def provenance(lines: list[Line]) -> dict:
    assert lines
    return {"fuenteRef": SOURCE_ID, "paginas": sorted({line.page for line in lines})}


def paragraphs(lines: list[Line]) -> list[str]:
    result: list[list[Line]] = []
    for line in lines:
        if line.indented or not result:
            result.append([])
        result[-1].append(line)
    return [text(group) for group in result]


def find(lines: list[Line], label: str) -> int:
    matches = [i for i, line in enumerate(lines) if line.text.rstrip(".") == label]
    assert len(matches) == 1, (label, matches)
    return matches[0]


def competencies(lines: list[Line], expected: int) -> list[dict]:
    starts = [(i, int(match.group(1))) for i, line in enumerate(lines)
              if (match := re.match(r"^(\d+)\.\s+", line.text))]
    assert [number for _, number in starts] == list(range(1, expected + 1))
    result = []
    for index, (start, number) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(lines)
        segment = lines[start:end]
        description_start = next(i for i, line in enumerate(segment) if line.indented)
        statement = re.sub(r"^\d+\.\s+", "", text(segment[:description_start]))
        result.append({
            "id": f"ce-{number}", "codigoOficial": str(number),
            "enunciado": {"es": statement},
            "descripcion": {"es": paragraphs(segment[description_start:])},
            "descriptoresOperativosRefs": [], "procedencia": provenance(segment),
        })
    return result


def criteria(lines: list[Line], cycle: int, expected_competencies: int) -> list[dict]:
    groups: list[tuple[str, list[Line]]] = []
    active_competency = None
    seen_competencies = []
    for line in lines:
        heading = re.fullmatch(r"Competencia específica (\d+)\.", line.text)
        item = re.match(r"^(\d+\.\d+)\.?\s+(.+)$", line.text)
        if heading:
            active_competency = int(heading.group(1))
            seen_competencies.append(active_competency)
        elif item:
            code, value = item.groups()
            assert int(code.split(".")[0]) == active_competency, (line.page, line.text)
            groups.append((code, [Line(line.page, value, False)]))
        else:
            assert groups, (line.page, line.text)
            groups[-1][1].append(line)
    assert seen_competencies == list(range(1, expected_competencies + 1))
    result = [{
        "id": f"cri-{cycle}-{code.replace('.', '-')}", "codigoOficial": code,
        "competenciaEspecificaRef": f"ce-{code.split('.')[0]}",
        "texto": {"es": text(words)}, "saberesBasicosRefs": [],
        "procedencia": provenance(words),
    } for code, words in groups]
    assert len({item["id"] for item in result}) == len(result)
    return result


def knowledge(lines: list[Line], area_code: str, cycle: int) -> list[dict]:
    blocks: list[dict] = []
    for line in lines:
        heading = re.match(r"^([A-I])\.\s+(.+)$", line.text)
        bullet = re.match(r"^-\s*(.+)$", line.text)
        if heading:
            code, value = heading.groups()
            assert code == chr(65 + len(blocks))
            blocks.append({"codigo": code, "name": [Line(line.page, value, False)], "items": []})
        elif bullet:
            assert blocks
            blocks[-1]["items"].append([Line(line.page, bullet.group(1), False)])
        elif blocks and blocks[-1]["items"]:
            blocks[-1]["items"][-1].append(line)
        else:
            assert blocks, (line.page, line.text)
            blocks[-1]["name"].append(line)
    return [{
        "codigo": block["codigo"], "nombre": {"es": text(block["name"]).rstrip(".")},
        "saberes": [{
            "id": f"{area_code}.{cycle}.{block['codigo']}.{index:02d}",
            "codigoOficial": None, "texto": {"es": text(words)},
            "procedencia": provenance(words),
        } for index, words in enumerate(block["items"], 1)],
    } for block in blocks]


def normalize(document: dict) -> None:
    """Normalizaciones confirmadas; las decisiones se conservan en incidencias/es-cb.md."""
    def replace_once(values: list[str], old: str, new: str) -> list[str]:
        assert sum(value.count(old) for value in values) == 1, (document["id"], old)
        return [value.replace(old, new) for value in values]

    code = document["materia"]["codigo"]
    if code == "CA":
        document["introduccion"]["es"] = replace_once(document["introduccion"]["es"],
            "las sensaciones que experimenta,", "las sensaciones que experimentan,")
        description = document["competenciasEspecificas"][3]["descripcion"]
        description["es"] = replace_once(description["es"], "enriquecedora De esta manera", "enriquecedora. De esta manera")
    elif code == "DEE":
        document["introduccion"]["es"] = replace_once(document["introduccion"]["es"], "ecosaludabes", "ecosaludables")
        # El 2.1 del segundo ciclo no lleva punto separador en el PDF.
        # codigoOficial conserva 2.1; el enunciado queda separado igual que los demás.
    elif code == "CRR":
        description = document["competenciasEspecificas"][0]["descripcion"]
        description["es"] = replace_once(description["es"], ") facilitan la comprensión", ") facilita la comprensión")
        first = document["desarrollos"][0]["bloquesSaberes"][3]["saberes"][1]["texto"]
        first["es"] = replace_once([first["es"]], "Comunidad Autónomas", "Comunidad Autónoma")[0]
        second = document["desarrollos"][1]["bloquesSaberes"][3]["saberes"][2]["texto"]
        second["es"] = replace_once([second["es"]], "interpretación y compresión", "interpretación y comprensión")[0]


def extract() -> list[dict]:
    lines = source_lines()
    headings = [i for i, line in enumerate(lines) if re.match(r"^Área [123]\. ", line.text)]
    assert len(headings) == 3
    documents = []
    for area_index, (slug, name, code, ce_count, criterion_counts, saber_counts, block_counts) in enumerate(AREAS):
        end = headings[area_index + 1] if area_index + 1 < len(headings) else len(lines)
        area = lines[headings[area_index] + 1:end]
        narrative_end = find(area, "Primer ciclo")
        second_start = find(area, "Segundo ciclo")
        competency_start = find(area[:narrative_end], "Competencias específicas")
        developments = []
        for index, segment in enumerate((area[narrative_end + 1:second_start], area[second_start + 1:])):
            assert segment[0].text == "Criterios de evaluación."
            saber_start = find(segment, "Saberes básicos")
            development = {
                "ciclo": index + 1,
                "criteriosEvaluacion": criteria(segment[1:saber_start], index + 1, ce_count),
                "bloquesSaberes": knowledge(segment[saber_start + 1:], code, index + 1),
            }
            assert len(development["criteriosEvaluacion"]) == criterion_counts[index], (slug, index, "criterios")
            assert len(development["bloquesSaberes"]) == block_counts[index], (slug, index, "bloques")
            actual = sum(len(block["saberes"]) for block in development["bloquesSaberes"])
            assert actual == saber_counts[index], (slug, index, "saberes", actual)
            developments.append(development)
        document = {
            "$schema": "../../../../schemas/materia.schema.json", "schemaVersion": "0.3.0",
            "id": f"es-cb.infantil.{slug}", "territorio": "es-cb", "etapa": "infantil",
            "materia": {"codigo": code, "nombre": {"es": name},
                        "ciclos": [{"ciclo": cycle, "caracter": "obligatoria"} for cycle in (1, 2)]},
            "vigencia": {"entradaEnVigor": None, "aplicableDesdeCurso": "2022/2023", "hasta": None, "estado": "vigente"},
            "fuentes": [{
                "id": SOURCE_ID, "tipo": "decreto",
                "titulo": "Decreto 66/2022, de 7 de julio, por el que se establece el currículo de la Educación Infantil y de la Educación Primaria en la Comunidad Autónoma de Cantabria",
                "publicacion": "Boletín Oficial de Cantabria", "numero": "135", "fechaPublicacion": "2022-07-13",
                "cve": "CVE-2022-5545", "urlOficial": SOURCE_URL, "urlVerificacion": SOURCE_URL, "anexo": "I-A",
                "paginasMateria": {"desde": lines[headings[area_index]].page, "hasta": area[-1].page},
            }],
            "introduccion": {"es": paragraphs(area[:competency_start])},
            "competenciasEspecificas": competencies(area[competency_start + 1:narrative_end], ce_count),
            "desarrollos": developments,
            "revision": {"estado": "revisado", "fuenteComprobada": True, "fechaUltimaRevision": "2026-11-03",
                         "metodo": "Extracción del texto y las coordenadas del PDF oficial, cotejo visual y contraste independiente con Poppler.",
                         "notas": [
                             "Las competencias específicas son comunes a los dos ciclos; los criterios y los saberes se publican por ciclo.",
                             "Los elementos curriculares del primer ciclo tienen carácter orientativo según el artículo 8.2 del decreto.",
                             "Las abreviaturas de área y los identificadores de saberes son internos del proyecto, no códigos oficiales; codigoOficial se conserva como null para los saberes.",
                             "La fuente no publica asociaciones explícitas entre criterios y saberes ni descriptores operativos numerados; sus listas de referencias se conservan vacías.",
                             "Las disposiciones finales primera y tercera fijan la implantación y la entrada en vigor para el curso 2022/2023, sin un día concreto de entrada en vigor; entradaEnVigor queda en null.",
                         ]},
        }
        normalize(document)
        documents.append(document)
    return documents


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    for document in extract():
        stats = [(dev["ciclo"], len(dev["criteriosEvaluacion"]), sum(len(b["saberes"]) for b in dev["bloquesSaberes"]))
                 for dev in document["desarrollos"]]
        print(document["materia"]["codigo"], "CE", len(document["competenciasEspecificas"]), "(ciclo, criterios, saberes)", stats)
        if args.write:
            DEST.mkdir(parents=True, exist_ok=True)
            slug = document["id"].split(".")[-1]
            (DEST / f"{slug}.json").write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
