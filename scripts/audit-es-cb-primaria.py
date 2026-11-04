"""Coteja Primaria de Cantabria con Poppler, sin importar el extractor.

Uso: python scripts/audit-es-cb-primaria.py [--packages RUTA] [--report RUTA]
Requiere jsonschema y pdftotext. Contrasta fragmentos, estructura y áreas íntegras.
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
NAMES = (
    "Conocimiento del Medio Natural, Social y Cultural", "Educación Artística",
    "Educación Física", "Educación en Valores Cívicos y Éticos",
    "Lengua Castellana y Literatura", "Lengua Extranjera", "Matemáticas",
)
# Se reconstruyen únicamente las catorce correcciones confirmadas.
# «Adaptados» se conserva tal como se publica, por decisión del usuario.
PUBLISHED = {
    "CM": (
        ("Materiales, herramientas y objetos", "Materiales herramientas y objetos"),
    ),
    "EA": (("Indagar en el proceso de creación", "Indagar en proceso de creación"),),
    "EF": (("Tomar decisiones en contextos de práctica motriz", "Tomar decisiones en contextos de practica motriz"),),
    "EVCE": (("los organismos internacionales", "los organismos internaciones"),),
    "LCL": (
        ("contextos formales e informales", "contextos formales informales"),
        ("en el marco de propuestas de producción", "en el marco de propuestas la producción"),
        ("Interacción oral: interacción oral adecuada", "Interacción oral: interacción oral y adecuada"),
    ),
    "LE": (("estrategias básicas para entender y apreciar la diversidad lingüística, cultural y artística.", "estrategias básicas para entender y apreciar la diversidad lingüística, cultural y artística"),),
    "MAT": (("figuras geométricas sencillas de una y dos dimensiones", "figuras geométricas sencillas de una, dos dimensiones"),),
}


def compact(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value)).replace("\xad", "")


def original(value: str, code: str, *, cycle: int | None = None) -> str:
    for corrected, published in PUBLISHED[code]:
        if code == "CM" and cycle != 1:
            continue
        if code == "LCL" and "contextos formales" in corrected and cycle != 1:
            continue
        if code == "LCL" and corrected.startswith("Interacción oral:") and cycle != 3:
            continue
        # Solo el título del primer ciclo presenta esta anomalía.
        if code == "LCL" and "propuestas" in corrected and cycle != 1:
            continue
        value = value.replace(corrected, published)
    return value


def pdf_pages() -> dict[int, str]:
    raw = subprocess.check_output(["pdftotext", "-layout", "-enc", "UTF-8", "-f", "56", "-l", "175", str(PDF), "-"], text=True, encoding="utf-8")
    pages = raw.split("\f")
    assert not pages[-1].strip() and len(pages) == 121
    result = {}
    for number, page in enumerate(pages[:-1], 56):
        body = []
        for line in page.splitlines():
            if any(marker in line for marker in ("BOC NÚM.", "CVE-2022-5545", "boc.cantabria.es")):
                continue
            if re.fullmatch(r"\s*(?:i|Pág\. \d+|\d+/176)\s*", line):
                continue
            body.append(line)
        result[number] = "\n".join(body)
    return result


def sabers(development: dict) -> list[dict]:
    return [saber for block in development["bloquesSaberes"] for part in block.get("apartados", [block]) for saber in part["saberes"]]


def fragments(document: dict):
    extent = document["fuentes"][0]["paginasMateria"]
    source_pages = list(range(extent["desde"], extent["hasta"] + 1))
    for index, value in enumerate(document["introduccion"]["es"]):
        yield "introduccion", str(index + 1), value, source_pages, None
    for ce in document["competenciasEspecificas"]:
        pages = ce["procedencia"]["paginas"]
        yield "competencia", ce["id"], ce["enunciado"]["es"], pages, None
        for index, value in enumerate(ce["descripcion"]["es"]):
            yield "descripcion", f"{ce['id']}:{index + 1}", value, pages, None
    for dev in document["desarrollos"]:
        dimension = dev.get("ciclo", dev.get("curso"))
        for criterion in dev["criteriosEvaluacion"]:
            yield "criterio", criterion["id"], criterion["texto"]["es"], criterion["procedencia"]["paginas"], dimension
        for block in dev["bloquesSaberes"]:
            items = [item for part in block.get("apartados", [block]) for item in part["saberes"]]
            pages = sorted({page for item in items for page in item["procedencia"]["paginas"]})
            heading_pages = sorted(set(pages) | {max(extent["desde"], pages[0] - 1)})
            yield "bloque", f"{dimension}-{block['codigo']}", block["nombre"]["es"], heading_pages, dimension
            for part in block.get("apartados", []):
                pages = sorted({page for item in part["saberes"] for page in item["procedencia"]["paginas"]})
                pages = sorted(set(pages) | {max(extent["desde"], pages[0] - 1)})
                yield "apartado", f"{dimension}-{block['codigo']}-{part['codigo']}", part["nombre"]["es"], pages, dimension
            for item in items:
                yield "saber", item["id"], item["texto"]["es"], item["procedencia"]["paginas"], dimension


def content_stream(document: dict, published: str) -> str:
    code = document["materia"]["codigo"]

    def heading(label: str, span: str = published) -> str:
        # Los puntos finales de los rótulos son variables en el anexo.
        needle = compact(label)
        pos = span.find(needle)
        assert pos >= 0, (code, label)
        return label + ("." if span[pos + len(needle):].startswith(".") else "")

    words = list(document["introduccion"]["es"])
    words.append("Competencias Específicas." if code == "EF" else "Competencias específicas.")
    for ce in document["competenciasEspecificas"]:
        words.extend([f"{ce['codigoOficial']}. {ce['enunciado']['es']}", *ce["descripcion"]["es"]])
        words.append(heading("Esta competencia específica se conecta con los siguientes descriptores del Perfil de salida: " + ", ".join(ce["descriptoresOperativosRefs"])))
    # Las normalizaciones textuales fuera de los títulos se revierten una sola vez.
    words = [original(value, code) for value in words]
    for dev in document["desarrollos"]:
        dimension = dev.get("ciclo", dev.get("curso"))
        dev_source = published
        if "ciclo" in dev:
            labels = {1: "Primer ciclo", 2: "Segundo ciclo", 3: "Tercer ciclo"}
            dev_source = published[published.index(compact(labels[dimension])):]
            if dimension < 3:
                dev_source = dev_source[:dev_source.index(compact(labels[dimension + 1]))]
            words.append(heading(labels[dimension], dev_source))
        words.append(heading("Criterios de evaluación", dev_source))
        previous = None
        for criterion in dev["criteriosEvaluacion"]:
            number = criterion["codigoOficial"].split(".")[0]
            if number != previous:
                words.append("Competencia específica " + number + ("" if code == "EF" else "."))
                previous = number
            omitted = (code == "EF" and criterion["codigoOficial"] == "5.1") or (code == "LCL" and (
                criterion["codigoOficial"] == "2.1" or (criterion["codigoOficial"] == "5.1" and dimension in (1, 2))))
            label = "" if omitted else criterion["codigoOficial"] + ". "
            words.append(label + original(criterion["texto"]["es"], code, cycle=dimension))
        words.append(heading("Saberes básicos", dev_source))
        for block in dev["bloquesSaberes"]:
            title = original(block["nombre"]["es"], code, cycle=dimension)
            words.append(heading(f"{block['codigo']}. {title}", dev_source))
            for part in block.get("apartados", [block]):
                if "apartados" in block:
                    title = original(part["nombre"]["es"], code, cycle=dimension)
                    if code == "CM" and dimension == 3 and block["codigo"] == "C" and part["codigo"] == "4":
                        words.append("- Conciencia ecosocial.")
                    else:
                        label = part["codigo"] + (".. " if code == "MAT" and dimension == 1 and block["codigo"] == "A" and part["codigo"] == "2" else ". ")
                        words.append(heading(label + title, dev_source))
                words.extend("- " + original(item["texto"]["es"], code, cycle=dimension) for item in part["saberes"])
    return " ".join(words)


def first_difference(left: str, right: str) -> dict:
    position = next((i for i, (a, b) in enumerate(zip(left, right)) if a != b), min(len(left), len(right)))
    return {"posicion": position, "json": left[max(0, position - 70):position + 160], "pdf": right[max(0, position - 70):position + 160]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packages", type=Path)
    parser.add_argument("--report", type=Path, default=ROOT / "tmp/pdfs/cantabria-primaria-audit.json")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.packages:
        sys.path.insert(0, str(args.packages.resolve()))
    import jsonschema

    validator = jsonschema.Draft202012Validator(json.loads((ROOT / "schemas/materia.schema.json").read_text(encoding="utf-8")), format_checker=jsonschema.FormatChecker())
    pages = pdf_pages()
    source = compact(" ".join(pages.values()))
    markers = [compact(name) for name in NAMES]
    documents = {d["materia"]["nombre"]["es"]: d for path in (ROOT / "data/es-cb/primaria/materias").glob("*.json") if (d := json.loads(path.read_text(encoding="utf-8")))}
    assert set(documents) == set(NAMES)
    valid_keys = {f"{key}{n}" for key, count in (("CCL", 5), ("CP", 3), ("STEM", 5), ("CD", 5), ("CPSAA", 5), ("CC", 4), ("CE", 3), ("CCEC", 4)) for n in range(1, count + 1)}
    report = {"schemaErrors": [], "textDifferences": [], "coverageDifferences": [], "structureDifferences": [], "counts": {}, "areas": []}
    totals = Counter()
    for index, name in enumerate(NAMES):
        d = documents[name]
        code = d["materia"]["codigo"]
        report["schemaErrors"].extend([d["id"], e.json_path, e.message] for e in validator.iter_errors(d))
        assert not re.search(r"CB-(?:INF|PRIM|ESO|BACH|CFGB)-\d+|INCIDENCIAS\.md", json.dumps(d, ensure_ascii=False), re.I)
        assert "incidencia" not in json.dumps(d["revision"], ensure_ascii=False).casefold()
        assert d["fuentes"][0]["id"] == SOURCE_ID and d["fuentes"][0]["anexo"] == "II-A"
        assert d["vigencia"]["entradaEnVigor"] is None and d["vigencia"]["aplicableDesdeCurso"] == "2022/2023"
        assert d["revision"]["fuenteComprobada"] and d["revision"]["estado"] == "revisado"
        if code == "EVCE":
            assert d["materia"]["cursos"] == [{"curso": 5, "caracter": "obligatoria"}]
            assert len(d["desarrollos"]) == 1 and d["desarrollos"][0]["curso"] == 5 and "ciclo" not in d["desarrollos"][0]
        else:
            assert [item["ciclo"] for item in d["materia"]["ciclos"]] == [1, 2, 3]
            assert [item["ciclo"] for item in d["desarrollos"]] == [1, 2, 3]
        ces = {ce["id"] for ce in d["competenciasEspecificas"]}
        assert len(ces) == len(d["competenciasEspecificas"])
        identifiers = list(ces)
        for ce in d["competenciasEspecificas"]:
            assert ce["id"] == "ce-" + ce["codigoOficial"] and ce["enunciado"]["es"].endswith(".")
            keys = ce["descriptoresOperativosRefs"]
            assert keys and len(keys) == len(set(keys)) and set(keys) <= valid_keys
            assert ce["procedencia"]["fuenteRef"] == SOURCE_ID
        for dev in d["desarrollos"]:
            for criterion in dev["criteriosEvaluacion"]:
                assert criterion["competenciaEspecificaRef"] in ces
                assert criterion["competenciaEspecificaRef"] == "ce-" + criterion["codigoOficial"].split(".")[0]
                assert criterion["saberesBasicosRefs"] == [] and not criterion.get("descriptoresOperativosRefs")
                assert criterion["procedencia"]["fuenteRef"] == SOURCE_ID and criterion["texto"]["es"].endswith(".")
                identifiers.append(criterion["id"])
            assert {item["competenciaEspecificaRef"] for item in dev["criteriosEvaluacion"]} == ces
            for block in dev["bloquesSaberes"]:
                if "apartados" in block:
                    assert [part["codigo"] for part in block["apartados"]] == [str(n) for n in range(1, len(block["apartados"]) + 1)]
                block_sabers = [saber for part in block.get("apartados", [block]) for saber in part["saberes"]]
                dimension = dev.get("ciclo", dev.get("curso"))
                assert [item["id"] for item in block_sabers] == [f"{code}.{dimension}.{block['codigo']}.{n:02d}" for n in range(1, len(block_sabers) + 1)]
            for item in sabers(dev):
                assert item["codigoOficial"] is None and "numeracionFuente" not in item
                assert item["procedencia"]["fuenteRef"] == SOURCE_ID
                identifiers.append(item["id"])
        assert len(identifiers) == len(set(identifiers))
        for kind, item_id, value, page_numbers, dimension in fragments(d):
            totals[kind] += 1
            assert page_numbers and page_numbers == sorted(set(page_numbers)) and all(56 <= page <= 175 for page in page_numbers)
            span = compact(" ".join(pages[page] for page in page_numbers))
            if compact(original(value, code, cycle=dimension)) not in span:
                report["textDifferences"].append([d["id"], kind, item_id, page_numbers, value])
        start = source.index(markers[index]) + len(markers[index])
        end = source.index(markers[index + 1], start) if index + 1 < len(markers) else len(source)
        published = source[start:end]
        reconstructed = compact(content_stream(d, published))
        if reconstructed != published:
            report["coverageDifferences"].append([d["id"], first_difference(reconstructed, published)])
        # Cotejo adicional de los rótulos de saberes y de sus viñetas.
        first = d["fuentes"][0]["paginasMateria"]["desde"]
        last = d["fuentes"][0]["paginasMateria"]["hasta"]
        raw = "\n".join(pages[page] for page in range(first, last + 1))
        # Delimitar por líneas completas evita menciones al nombre del área en prosa.
        raw = re.split(r"(?m)^\s*" + re.escape(name) + r"\s*$", raw, maxsplit=1)[1]
        if index + 1 < len(NAMES):
            raw = re.split(r"(?m)^\s*" + re.escape(NAMES[index + 1]) + r"\s*$", raw, maxsplit=1)[0]
        segments = re.split(r"(?m)^\s*Saberes básicos\.\s*$", raw)[1:]
        assert len(segments) == len(d["desarrollos"]), code
        for dev_index, (segment, dev) in enumerate(zip(segments, d["desarrollos"]), 1):
            segment = re.split(r"(?m)^\s*(?:Primer|Segundo|Tercer) ciclo\.?\s*$", segment, maxsplit=1)[0]
            bullets = len(re.findall(r"(?m)^\s*-\s*\S", segment))
            sections = len(re.findall(r"(?m)^\s*\d+\.\.?\s*\D", segment))
            expected_bullets = len(sabers(dev)) + (1 if code == "CM" and dev_index == 3 else 0)
            expected_sections = sum(len(block.get("apartados", [])) for block in dev["bloquesSaberes"]) - (1 if code == "CM" and dev_index == 3 else 0)
            if (bullets, sections) != (expected_bullets, expected_sections):
                report["structureDifferences"].append([code, dev_index, [bullets, sections], [expected_bullets, expected_sections]])
        report["areas"].append({"area": name, "competencias": len(ces), "desarrollos": [
            {"curso" if "curso" in dev else "ciclo": dev.get("curso", dev.get("ciclo")), "criterios": len(dev["criteriosEvaluacion"]), "saberes": len(sabers(dev))} for dev in d["desarrollos"]]})
    report["counts"] = dict(totals)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checks = ("schemaErrors", "textDifferences", "coverageDifferences", "structureDifferences")
    print(json.dumps({"fragmentos": sum(totals.values()), **{key: len(report[key]) for key in checks}, "counts": dict(totals)}, ensure_ascii=False))
    if any(report[key] for key in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
