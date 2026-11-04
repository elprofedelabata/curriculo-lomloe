"""Cotejo independiente de Infantil de Cantabria con Poppler y JSON Schema.

Uso: python scripts/audit-es-cb-infantil.py [--packages RUTA] [--report RUTA]
Requiere jsonschema y pdftotext. No importa ni ejecuta el extractor.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "sources/es-cb/normativa/infantil-primaria/2022-07-07-decreto-66-2022-curriculo-infantil-primaria.pdf"
SOURCE_ID = "boc-2022-135-decreto-66-2022"
# Se reconstruye la redacción publicada para cotejar las normalizaciones
# confirmadas en CB-INF-001 a 007, sin admitir diferencias adicionales.
PUBLISHED = (
    ("las sensaciones que experimentan,", "las sensaciones que experimenta,"),
    ("enriquecedora. De esta manera", "enriquecedora De esta manera"),
    ("ecosaludables", "ecosaludabes"),
    (") facilita la comprensión", ") facilitan la comprensión"),
    ("Comunidad Autónoma y de otras culturas", "Comunidad Autónomas y de otras culturas"),
    ("interpretación y comprensión", "interpretación y compresión"),
)


def original(value: str) -> str:
    for corrected, published in PUBLISHED:
        value = value.replace(corrected, published)
    return value


def normalize(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value)).replace("\xad", "")


def pdf_pages() -> dict[int, str]:
    raw = subprocess.check_output(["pdftotext", "-layout", "-enc", "UTF-8", "-f", "24", "-l", "54", str(PDF), "-"], text=True, encoding="utf-8")
    pages = raw.split("\f")
    assert not pages[-1].strip()
    assert len(pages) == 32
    result = {}
    for number, page in enumerate(pages[:-1], 24):
        body = []
        for line in page.splitlines():
            if any(marker in line for marker in ("BOC NÚM.", "CVE-2022-5545", "boc.cantabria.es")):
                continue
            if re.fullmatch(r"\s*(?:i|Pág\. \d+|\d+/176)\s*", line):
                continue
            body.append(line)
        result[number] = "\n".join(body)
    return result


def fragments(document: dict):
    source_range = document["fuentes"][0]["paginasMateria"]
    source_pages = list(range(source_range["desde"], source_range["hasta"] + 1))
    for index, value in enumerate(document["introduccion"]["es"]):
        yield "introduccion", str(index + 1), value, source_pages
    for ce in document["competenciasEspecificas"]:
        pages = ce["procedencia"]["paginas"]
        yield "competencia", ce["id"], ce["enunciado"]["es"], pages
        for index, value in enumerate(ce["descripcion"]["es"]):
            yield "descripcion", f"{ce['id']}:{index + 1}", value, pages
    for development in document["desarrollos"]:
        for criterion in development["criteriosEvaluacion"]:
            yield "criterio", criterion["id"], criterion["texto"]["es"], criterion["procedencia"]["paginas"]
        for block in development["bloquesSaberes"]:
            pages = sorted({page for item in block["saberes"] for page in item["procedencia"]["paginas"]})
            # El título puede quedar en la página inmediatamente anterior.
            block_pages = sorted(set(pages) | ({pages[0] - 1} if pages[0] > source_range["desde"] else set()))
            yield "bloque", f"{development['ciclo']}-{block['codigo']}", block["nombre"]["es"], block_pages
            for saber in block["saberes"]:
                yield "saber", saber["id"], saber["texto"]["es"], saber["procedencia"]["paginas"]


def content_stream(document: dict) -> str:
    words = list(document["introduccion"]["es"]) + ["Competencias específicas."]
    for ce in document["competenciasEspecificas"]:
        words.extend([f"{ce['codigoOficial']}. {ce['enunciado']['es']}", *ce["descripcion"]["es"]])
    for dev in document["desarrollos"]:
        words.extend(["Primer ciclo" if dev["ciclo"] == 1 else "Segundo ciclo", "Criterios de evaluación."])
        current_ce = None
        for criterion in dev["criteriosEvaluacion"]:
            number = criterion["codigoOficial"].split(".")[0]
            if number != current_ce:
                words.append(f"Competencia específica {number}.")
                current_ce = number
            # CB-INF-004: el separador está omitido en el criterio publicado.
            missing_separator = document["materia"]["codigo"] == "DEE" and dev["ciclo"] == 2 and criterion["codigoOficial"] == "2.1"
            separator = "" if missing_separator else "."
            words.append(f"{criterion['codigoOficial']}{separator} {criterion['texto']['es']}")
        words.append("Saberes básicos.")
        for block in dev["bloquesSaberes"]:
            words.append(f"{block['codigo']}. {block['nombre']['es']}.")
            words.extend("- " + saber["texto"]["es"] for saber in block["saberes"])
    return original(" ".join(words))


def first_difference(left: str, right: str) -> dict:
    position = next((i for i, (a, b) in enumerate(zip(left, right)) if a != b), min(len(left), len(right)))
    return {"posicion": position, "json": left[max(0, position - 55):position + 110], "pdf": right[max(0, position - 55):position + 110]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packages", type=Path)
    parser.add_argument("--report", type=Path, default=ROOT / "tmp/pdfs/cantabria-infantil-audit.json")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.packages:
        sys.path.insert(0, str(args.packages.resolve()))
    import jsonschema

    validator = jsonschema.Draft202012Validator(json.loads((ROOT / "schemas/materia.schema.json").read_text(encoding="utf-8")), format_checker=jsonschema.FormatChecker())
    pages = pdf_pages()
    entire_source = normalize(" ".join(pages.values()))
    names = ["Crecimiento en Armonía", "Descubrimiento y Exploración del Entorno", "Comunicación y Representación de la Realidad"]
    markers = [normalize(f"Área {index}. {name}") for index, name in enumerate(names, 1)]
    documents = {d["materia"]["nombre"]["es"]: d for p in (ROOT / "data/es-cb/infantil/materias").glob("*.json")
                 if (d := json.loads(p.read_text(encoding="utf-8")))}
    assert set(documents) == set(names)
    report = {"schemaErrors": [], "textDifferences": [], "coverageDifferences": [], "counts": {}, "areas": []}
    totals = Counter()
    for index, name in enumerate(names):
        d = documents[name]
        report["schemaErrors"].extend([d["id"], e.json_path, e.message] for e in validator.iter_errors(d))
        assert [item["ciclo"] for item in d["materia"]["ciclos"]] == [1, 2]
        assert [item["ciclo"] for item in d["desarrollos"]] == [1, 2]
        assert d["vigencia"]["entradaEnVigor"] is None and d["vigencia"]["aplicableDesdeCurso"] == "2022/2023"
        ces = {ce["id"] for ce in d["competenciasEspecificas"]}
        identifiers = []
        for ce in d["competenciasEspecificas"]:
            assert ce["descriptoresOperativosRefs"] == []
            assert ce["id"] == "ce-" + ce["codigoOficial"]
        for dev in d["desarrollos"]:
            for item in dev["criteriosEvaluacion"]:
                assert item["competenciaEspecificaRef"] in ces
                assert item["competenciaEspecificaRef"] == "ce-" + item["codigoOficial"].split(".")[0]
                assert item["saberesBasicosRefs"] == []
                identifiers.append(item["id"])
            for block in dev["bloquesSaberes"]:
                for item in block["saberes"]:
                    assert item["codigoOficial"] is None and "numeracionFuente" not in item
                    identifiers.append(item["id"])
        assert len(ces) == len(d["competenciasEspecificas"])
        assert len(identifiers) == len(set(identifiers))
        for kind, item_id, value, page_numbers in fragments(d):
            totals[kind] += 1
            assert page_numbers and page_numbers == sorted(set(page_numbers))
            assert all(24 <= page <= 54 for page in page_numbers)
            span = normalize(" ".join(pages[page] for page in page_numbers))
            if normalize(original(value)) not in span:
                report["textDifferences"].append([d["id"], kind, item_id, page_numbers, value])
        start = entire_source.index(markers[index]) + len(markers[index])
        end = entire_source.index(markers[index + 1]) if index + 1 < len(markers) else len(entire_source)
        reconstructed = normalize(content_stream(d))
        published = entire_source[start:end]
        if reconstructed != published:
            report["coverageDifferences"].append([d["id"], first_difference(reconstructed, published)])
        report["areas"].append({"area": name, "competencias": len(ces), "ciclos": [
            {"ciclo": dev["ciclo"], "criterios": len(dev["criteriosEvaluacion"]), "saberes": sum(len(b["saberes"]) for b in dev["bloquesSaberes"])}
            for dev in d["desarrollos"]]})
    report["counts"] = dict(totals)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"fragmentos": sum(totals.values()), **{key: len(report[key]) for key in ("schemaErrors", "textDifferences", "coverageDifferences")}, "counts": dict(totals)}, ensure_ascii=False))
    if any(report[key] for key in ("schemaErrors", "textDifferences", "coverageDifferences")):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
