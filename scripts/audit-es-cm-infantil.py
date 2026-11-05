"""Coteja los JSON de Infantil de Castilla-La Mancha con Poppler y el esquema común."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NORMATIVE = ROOT / "sources/es-cm/normativa"
DATA = ROOT / "data/es-cm/infantil/materias"
SOURCE_ID = "es-cm-infantil-decreto-80-2022"
DESCRIPTOR_PREFIX = "Esta competencia específica se conecta con los siguientes descriptores:"
AREAS = (
    ("crecimiento-en-armonia", "Crecimiento en Armonía", 4, ((12, 27, 4), (15, 31, 4))),
    ("descubrimiento-y-exploracion-del-entorno", "Descubrimiento y Exploración del Entorno", 3, ((8, 15, 3), (16, 27, 3))),
    ("comunicacion-y-representacion-de-la-realidad", "Comunicación y Representación de la Realidad", 5, ((14, 31, 8), (25, 43, 9))),
)
TEXT_REVERSALS = (
    ("las sensaciones que experimentan,", "las sensaciones que experimenta,"),
    (
        "hábitos saludables y sostenibles, así como su progresiva integración en la vida cotidiana, contribuye al cuidado del propio cuerpo y al logro",
        "hábitos saludables y sostenibles y así como su progresiva integración en la vida cotidiana contribuye al cuidado del propio cuerpo, y al logro",
    ),
    ("la aceptación de la discapacidad", "la aceptación de la capacidad"),
    ("hábitos ecosaludables", "hábitos ecosaludabes"),
    ("Espacios protegidos de Castilla-La Mancha:", "Espacios protegidos de Castilla La Mancha:"),
    ("interpretación y comprensión.", "interpretación y compresión."),
)
CRITERION_REVERSALS = {
    ("CA", 2, "2.3"): ("sobre los logros conseguidos.", "sobre los logros conseguidos,"),
    ("DEE", 1, "2.3"): ("retos que se le planteen.", "retos a los que se le planteen"),
    ("DEE", 1, "3.1"): ("los animales que lo habitan.", "los animales que lo habitan"),
    ("CRR", 2, "3.1"): ("contextos formales e informales.", "contextos formales e informales"),
    ("CRR", 2, "4.2"): ("la interpretación de mensajes.", "la interpretación de mensajes"),
}


def raw_pages(pdf: Path, first: int, last: int) -> list[str]:
    data = subprocess.check_output(
        ["pdftotext", "-layout", "-enc", "UTF-8", "-f", str(first), "-l", str(last), str(pdf), "-"],
        text=True, encoding="utf-8",
    )
    pages = data.split("\f")
    assert not pages[-1].strip()
    assert len(pages[:-1]) == last - first + 1
    return pages[:-1]


def compact(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", value))


def source_body(page: str) -> str:
    rows = [line for line in page.splitlines()
            if not re.match(r"^\s*AÑO XLI\s+Núm\.\s+134\b", line)]
    return compact(re.sub(r"(?m)^\s*[-−–]\s+", "- ", "\n".join(rows)))


def published(value: str) -> str:
    for new, old in TEXT_REVERSALS:
        value = value.replace(new, old)
    return value


class Source:
    def __init__(self, pages: list[str]) -> None:
        self.text = "".join(pages)
        self.spans = []
        cursor = 0
        for number, page in enumerate(pages, 19):
            self.spans.append((number, cursor, cursor + len(page)))
            cursor += len(page)
        self.position = self.text.index(compact("Área 1. Crecimiento en Armonía."))

    def take(self, value: str) -> None:
        target = compact(value)
        actual = self.text[self.position:self.position + len(target)]
        if actual != target:
            index = next((i for i, (expected, got) in enumerate(zip(target, actual)) if expected != got), len(actual))
            left, right = max(0, index - 22), index + 72
            raise AssertionError((self.position + index, target[left:right],
                                  self.text[self.position + left:self.position + right]))
        self.position += len(target)

    def optional_period(self) -> None:
        if self.text[self.position:self.position + 1] == ".":
            self.position += 1

    def pages_since(self, start: int) -> list[int]:
        return [number for number, left, right in self.spans if left < self.position and right > start]


def verify(document: dict, source: Source, index: int, name: str, count: int, expected: tuple,
           valid_descriptors: set[str]) -> tuple[int, int, int]:
    area_start = source.position
    source.take(f"Área {index}. {name}.")
    for paragraph in document["introduccion"]["es"]:
        source.take(published(paragraph))
    source.take("Competencias específicas")
    source.optional_period()
    competencies = document["competenciasEspecificas"]
    assert len(competencies) == count
    assert [item["codigoOficial"] for item in competencies] == [str(n) for n in range(1, count + 1)]
    assert [item["id"] for item in competencies] == [f"ce-{n}" for n in range(1, count + 1)]
    ids = [item["id"] for item in competencies]
    provenance = 0

    def verify_origin(item: dict, start: int) -> None:
        nonlocal provenance
        assert item["procedencia"] == {"fuenteRef": SOURCE_ID, "paginas": source.pages_since(start)}, item["id"]
        provenance += 1

    descriptor_count = 0
    for ce in competencies:
        start = source.position
        source.take(f'{ce["codigoOficial"]}. {ce["enunciado"]["es"]}')
        for paragraph in ce["descripcion"]["es"]:
            source.take(published(paragraph))
        codes = ce["descriptoresOperativosRefs"]
        assert set(codes) <= valid_descriptors, (name, ce["id"], codes)
        source.take(f'{DESCRIPTOR_PREFIX} {", ".join(codes)}.')
        descriptor_count += len(codes)
        verify_origin(ce, start)
    total_criteria = total_sabers = 0
    assert [item["ciclo"] for item in document["desarrollos"]] == [1, 2]
    for development, label, (criterion_count, saber_count, block_count) in zip(
        document["desarrollos"], ("Primer", "Segundo"), expected,
    ):
        cycle = development["ciclo"]
        source.take(f"{label} ciclo. Criterios de evaluación.")
        criteria = development["criteriosEvaluacion"]
        assert len(criteria) == criterion_count
        current = None
        for criterion in criteria:
            code = criterion["codigoOficial"]
            ce_number = code.split(".")[0]
            assert criterion["competenciaEspecificaRef"] == f"ce-{ce_number}"
            assert criterion["saberesBasicosRefs"] == []
            if ce_number != current:
                source.take(f"Competencia específica {ce_number}.")
                current = ce_number
            start = source.position
            text = criterion["texto"]["es"]
            assert text.endswith("."), criterion["id"]
            reversal = CRITERION_REVERSALS.get((document["materia"]["codigo"], cycle, code))
            if reversal:
                new, old = reversal
                assert text.endswith(new)
                text = text.removesuffix(new) + old
            source.take(f"{code}. {text}")
            verify_origin(criterion, start)
            ids.append(criterion["id"])
        source.take("Saberes básicos.")
        blocks = development["bloquesSaberes"]
        assert len(blocks) == block_count and sum(len(block["saberes"]) for block in blocks) == saber_count
        for block in blocks:
            source.take(f'{block["codigo"]}. {block["nombre"]["es"]}')
            source.optional_period()
            for saber in block["saberes"]:
                assert saber["codigoOficial"] is None
                start = source.position
                source.take(f'- {published(saber["texto"]["es"])}')
                verify_origin(saber, start)
                ids.append(saber["id"])
        total_criteria += criterion_count
        total_sabers += saber_count
    assert len(ids) == len(set(ids))
    pages = source.pages_since(area_start)
    assert document["fuentes"][0]["paginasMateria"] == {"desde": pages[0], "hasta": pages[-1]}
    assert provenance == count + total_criteria + total_sabers
    return provenance, descriptor_count, total_criteria + total_sabers


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packages", type=Path)
    args = parser.parse_args()
    if args.packages:
        sys.path.insert(0, str(args.packages.resolve()))
    import jsonschema

    catalog = json.loads((NORMATIVE / "catalogo.json").read_text(encoding="utf-8"))
    entry = next(item for item in catalog["documentos"] if item["id"] == SOURCE_ID)
    pdf = NORMATIVE / entry["archivo"]
    schema = json.loads((ROOT / "schemas/materia.schema.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    valid = set(re.findall(r"\b(?:CCL|CP|STEM|CD|CPSAA|CCEC|CC|CE)\d+\.", "\n".join(raw_pages(pdf, 11, 18))))
    valid = {code.rstrip(".") for code in valid}
    source = Source([source_body(page) for page in raw_pages(pdf, 19, 39)])
    assert {path.stem for path in DATA.glob("*.json")} == {slug for slug, _, _, _ in AREAS}
    origins = descriptors = elements = 0
    for index, (slug, name, count, cycles) in enumerate(AREAS, 1):
        document = json.loads((DATA / f"{slug}.json").read_text(encoding="utf-8"))
        validator.validate(document)
        assert document["revision"]["fuenteComprobada"]
        assert document["materia"]["nombre"]["es"] == name
        assert document["fuentes"][0]["id"] == SOURCE_ID
        assert document["vigencia"]["entradaEnVigor"] == "2022-07-15"
        assert document["vigencia"]["aplicableDesdeCurso"] == "2022/2023"
        origin_count, descriptor_count, element_count = verify(document, source, index, name, count, cycles, valid)
        origins += origin_count
        descriptors += descriptor_count
        elements += element_count
    assert source.position == len(source.text), source.text[source.position:source.position + 200]
    assert (origins, descriptors, elements) == (276, 77, 264)
    print(json.dumps({"areas": len(AREAS), "referenciasDeDescriptor": descriptors, "procedencias": origins,
                      "elementosPorCiclo": elements, "erroresDeEsquema": 0, "diferenciasDeCobertura": 0}))


if __name__ == "__main__":
    main()
