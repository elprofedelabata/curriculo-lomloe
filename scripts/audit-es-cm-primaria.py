"""Coteja el anexo II de Primaria de Castilla-La Mancha con Poppler y valida los JSON."""

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
DATA = ROOT / "data/es-cm/primaria/materias"
SOURCE_ID = "es-cm-primaria-decreto-81-2022"
AREAS = (
    ("conocimiento-del-medio-natural-social-y-cultural", "Conocimiento del Medio Natural, Social y Cultural", "CM", 9,
     ((23, 39), (23, 47), (24, 49))),
    ("educacion-artistica", "Educación Artística", "EA", 4, ((9, 24), (9, 32), (10, 34))),
    ("educacion-fisica", "Educación Física", "EF", 5, ((14, 27), (14, 28), (14, 29))),
    ("educacion-en-valores-civicos-y-eticos", "Educación en Valores Cívicos y Éticos", "EVCE", 4, ((11, 24),)),
    ("lengua-castellana-y-literatura", "Lengua Castellana y Literatura", "LCL", 10, ((19, 28), (19, 30), (19, 32))),
    ("lengua-extranjera", "Lengua Extranjera", "LE", 6, ((13, 17), (15, 22), (15, 26))),
    ("matematicas", "Matemáticas", "MAT", 8, ((18, 35), (18, 55), (18, 56))),
)


def raw_pages(pdf: Path, first: int, last: int) -> list[str]:
    raw = subprocess.check_output(
        ["pdftotext", "-layout", "-enc", "UTF-8", "-f", str(first), "-l", str(last), str(pdf), "-"],
        text=True, encoding="utf-8",
    )
    pages = raw.split("\f")
    assert len(pages) == last - first + 2 and not pages[-1].strip()
    return pages[:-1]


def compact(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", value))


class Source:
    def __init__(self, pages: list[str]) -> None:
        self.ends = []
        chunks = []
        end = 0
        for page in pages:
            body = re.sub(r"(?m)^\s*AÑO XLI\s+Núm\.\s+134[^\n]*", "", page)
            body = compact(re.sub(r"(?m)^\s*[-−–]\s+", "- ", body))
            chunks.append(body)
            end += len(body)
            self.ends.append(end)
        self.text = "".join(chunks)
        self.position = 0
        self.take("Anexo II")
        self.take("Áreas de educación primaria")

    def take(self, value: str) -> None:
        target = compact(value)
        actual = self.text[self.position:self.position + len(target)]
        if actual != target:
            mismatch = next((i for i, (a, b) in enumerate(zip(actual, target)) if a != b), len(actual))
            left, right = max(0, mismatch - 20), mismatch + 65
            raise AssertionError((self.pages_since(self.position), target[left:right],
                                  self.text[self.position + left:self.position + right]))
        self.position += len(target)

    def heading(self, value: str) -> None:
        self.take(value)
        if self.text.startswith(".", self.position):
            self.position += 1

    def pages_since(self, start: int) -> list[int]:
        boundaries = zip([0, *self.ends], self.ends)
        return [page for page, (left, right) in enumerate(boundaries, 26) if left < self.position and start < right]

    def check_origin(self, item: dict, start: int) -> None:
        assert item["procedencia"] == {"fuenteRef": SOURCE_ID, "paginas": self.pages_since(start)}, item["id"]


def verify_sabers(source: Source, development: dict, code: str, dimension: int) -> list[str]:
    ids = []
    for block in development["bloquesSaberes"]:
        letter = block["codigo"]
        source.heading(f'{letter}. {block["nombre"]["es"]}')
        for part in block.get("apartados", [block]):
            if part is not block:
                prefix = f'{part["codigo"]}. ' if part["codigo"].isdigit() else ""
                assert prefix or (code, dimension, letter, part["codigo"]) == (
                    "MAT", 1, "E", "organizacion-y-analisis-de-datos",
                )
                source.heading(f'{prefix}{part["nombre"]["es"]}')
            for saber in part["saberes"]:
                start = source.position
                text = saber["texto"]["es"]
                assert saber["codigoOficial"] is None
                marker = "-"
                if code == "EF" and dimension in (2, 3):
                    text = text.replace("de manera no específica", "de manera no especifica")
                    text = text.replace("Valoración de la condición física orientada a la salud",
                                        "Valoración de la condición física orientadas a la salud")
                    text = text.replace("propia cultura de Castilla-La Mancha", "propia cultura de Castilla la Mancha")
                    if dimension == 2:
                        text = re.sub(r"Batería ALPHA-Fitness\.$", "Batería ALPHA-Fitness", text)
                elif code == "EVCE" and text in ("Identidad de género y orientación sexual", "Diferencia entre sexo y género."):
                    marker = "."
                elif code == "LE" and dimension == 3 and text.startswith("El legado artístico, literario, patrimonial"):
                    marker = ""
                source.take(marker + text)
                source.check_origin(saber, start)
                ids.append(saber["id"])
    return ids


def verify(source: Source, document: dict, name: str, code: str, ce_count: int, counts: tuple,
           valid_descriptors: set[str]) -> tuple[int, int]:
    start_area = source.position
    source.heading(name)
    for paragraph in document["introduccion"]["es"]:
        if code == "EVCE":
            paragraph = paragraph.replace("La transversalidad con la que se afrontan",
                                          "La transversalidad con las que se afrontan")
        elif code == "LCL":
            paragraph = paragraph.replace("del metalenguaje necesario para reflexionar",
                                          "del metalenguaje necesario para la reflexionar")
        source.take(paragraph)
    source.heading("Competencias específicas")
    competencies = document["competenciasEspecificas"]
    assert [item["codigoOficial"] for item in competencies] == [str(i) for i in range(1, ce_count + 1)]
    ids = []
    descriptors = 0
    for ce in competencies:
        start = source.position
        source.take(f'{ce["codigoOficial"]}. {ce["enunciado"]["es"]}')
        for paragraph in ce["descripcion"]["es"]:
            source.take(paragraph)
        refs = ce["descriptoresOperativosRefs"]
        assert set(refs) <= valid_descriptors, refs
        descriptors += len(refs)
        source.take("Esta competencia específica se conecta con los siguientes descriptores del Perfil de salida: "
                    + ", ".join(refs) + ".")
        source.check_origin(ce, start)
        assert ce["id"] == f'ce-{ce["codigoOficial"]}'
        ids.append(ce["id"])
    dimensions, key = ([5], "curso") if code == "EVCE" else ([1, 2, 3], "ciclo")
    assert [item[key] for item in document["materia"][key + "s"]] == dimensions
    assert [item[key] for item in document["desarrollos"]] == dimensions
    missing_codes = {("LCL", 1, "2.1"), ("LCL", 1, "5.1"), ("LE", 1, "4.1")}
    le_reversals = {
        "2.1": ("del auditorio", "del auditoria"),
        "4.1": ("Interpretar, explicar o transmitir", "Interpretar, explica o transmitir"),
        "4.2": ("los conocimientos previos", "los conocimientos precios"),
    }
    cycle_labels = {1: "Primer ciclo", 2: "Segundo ciclo", 3: "Tercer ciclo"}
    for development, (criterion_count, saber_count) in zip(document["desarrollos"], counts, strict=True):
        dimension = development[key]
        if key == "ciclo":
            source.heading(cycle_labels[dimension])
        source.heading("Criterios de evaluación")
        criteria = development["criteriosEvaluacion"]
        assert len(criteria) == criterion_count
        current = None
        for criterion in criteria:
            number = criterion["codigoOficial"]
            ce_number = number.split(".")[0]
            assert criterion["competenciaEspecificaRef"] == f"ce-{ce_number}"
            assert criterion["saberesBasicosRefs"] == []
            if ce_number != current:
                source.heading(f"Competencia específica {ce_number}")
                current = ce_number
            start = source.position
            prefix = "" if (code, dimension, number) in missing_codes else f"{number} "
            text = criterion["texto"]["es"]
            if code == "LE" and dimension == 2 and number in le_reversals:
                corrected, original = le_reversals[number]
                assert corrected in text
                text = text.replace(corrected, original)
            source.take(prefix + text)
            source.check_origin(criterion, start)
            ids.append(criterion["id"])
        source.heading("Saberes básicos")
        saber_ids = verify_sabers(source, development, code, dimension)
        assert len(saber_ids) == saber_count
        ids.extend(saber_ids)
    assert len(ids) == len(set(ids))
    pages = source.pages_since(start_area)
    assert document["fuentes"][0]["paginasMateria"] == {"desde": pages[0], "hasta": pages[-1]}
    return len(ids), descriptors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packages", type=Path)
    args = parser.parse_args()
    if args.packages:
        sys.path.insert(0, str(args.packages.resolve()))
    import jsonschema

    catalog = json.loads((NORMATIVE / "catalogo.json").read_text(encoding="utf-8"))
    pdf = NORMATIVE / next(item["archivo"] for item in catalog["documentos"] if item["id"] == SOURCE_ID)
    schema = json.loads((ROOT / "schemas/materia.schema.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    profile = "\n".join(raw_pages(pdf, 17, 25))
    valid = set(re.findall(r"\b((?:CCL|CP|STEM|CD|CPSAA|CCEC|CC|CE)\d+)\.", profile))
    source = Source(raw_pages(pdf, 26, 104))
    assert {path.stem for path in DATA.glob("*.json")} == {area[0] for area in AREAS}
    origins = descriptors = 0
    for slug, name, code, ce_count, counts in AREAS:
        document = json.loads((DATA / f"{slug}.json").read_text(encoding="utf-8"))
        validator.validate(document)
        assert document["materia"]["codigo"] == code and document["materia"]["nombre"]["es"] == name
        assert document["fuentes"][0]["id"] == SOURCE_ID
        assert document["revision"]["estado"] == "revisado" and document["revision"]["fuenteComprobada"]
        origin_count, descriptor_count = verify(source, document, name, code, ce_count, counts, valid)
        origins += origin_count
        descriptors += descriptor_count
    assert source.position == len(source.text), source.text[source.position:source.position + 200]
    assert origins == 985
    print(json.dumps({"areas": len(AREAS), "procedencias": origins, "referenciasDeDescriptor": descriptors,
                      "erroresDeEsquema": 0, "diferenciasDeCobertura": 0}))


if __name__ == "__main__":
    main()
