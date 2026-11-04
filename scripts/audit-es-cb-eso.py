"""Cotejo independiente de ESO de Cantabria con Poppler y JSON Schema.

No importa ni ejecuta el extractor. Recorre cada área completa, en orden,
incluidos sus rótulos, descriptores, niveles y subapartados. El módulo compartido
de fuentes solo repara glifos sin Unicode a partir de los contornos incrustados.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import fitz

from cantabria_pdf_fonts import FontRecovery, normalize_unicode

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "es-cb-eso-bachillerato-decreto-73-2022": ("eso-bachillerato/2022-07-27-decreto-73-2022-curriculo-eso-bachillerato.pdf", 37, 317),
    "es-cb-eso-correccion-orden-edu-40-2022": ("eso/2022-08-23-correccion-orden-edu-40-2022-optativas.pdf", 1, 114),
    "es-cb-eso-bachillerato-orden-edu-21-2025": ("eso-bachillerato/2025-05-07-orden-edu-21-2025-espade.pdf", 17, 23),
}
GROUPS = {
    "BG": ["Cursos de primero a tercero", "Cuarto curso"],
    "EF": ["Cursos primero y segundo", "Cursos tercero y cuarto"],
    "FQ": ["Cursos de primero a tercero", "Cuarto curso"],
    "GH": ["Cursos primero y segundo", "Cursos tercero y cuarto"],
    "LCL": ["Cursos primero y segundo", "Cursos tercero y cuarto"],
    "LE": ["Cursos primero y segundo", "Cursos tercero y cuarto"],
    "MAT": ["Cursos de primero a tercero", "Matemáticas A", "Matemáticas B"],
    "MUS": ["Cursos de primero a tercero", "Cuarto curso"],
    "SLE": ["Cursos primero y segundo", "Tercer curso", "Cuarto curso"],
    "SCR": ["Sistemas de Control y Robótica I", "Sistemas de Control y Robótica II"],
    "TL": ["Cursos primero y segundo"],
    "TM": ["Primer curso", "Segundo curso"],
    "TD": ["Cursos de primero y segundo", "Cursos de tercero y cuarto"],
}
BULLET = r"[-–—−‐‑•\x83]"


def compact(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", normalize_unicode(value))).replace("\xad", "")


PUBLISHED = {
    "EVCE": [("promover el autoconocimiento", "promover el autonocimiento")],
    "FOPP": [("Plan de autoconocimiento", "Plan de autonocimiento"), ("dentro de los grupos", "dentro los grupos")],
    "IDF": [("promover el autoconocimiento", "promover el autonocimiento"), ("STEM1", "ESTEM1"), ("STEM4", "ESTEM4")],
    "PNC": [("Patrimonio natural", "Patrimono natural")],
    "AED": [("patrimonio escénico y performativo", "patrimonio escénico y performativa")],
    "MAT": [("recta numérica:", "recta numérica.:")],
    "TITID": [("Conocer los componentes", "Conocer los compontes"), ("Manejo de una suite ofimática:", "Manejo de una Suit ofimática:"), ("el bloc de notas", "el block de notas"), ("Plataformas digitales de aprendizaje", "Plataformas digital de aprendizaje")],
    "TD": [("Comprender la incidencia que el entrenamiento", "Comprender la incidencia del entrenamiento"), ("CPSAA2", "CPSSA2")],
    "ECF": [("STEM4", "CMCCT4")], "MUS": [("CCEC3", "CCE3")], "PHAC": [("CCEC1", "CCE1")],
    "SLE": [("CCEC1", "CCCEC1")], "SCR": [("STEM1", "STEAM1"), ("STEM3", "STEAM3")],
    "TCM": [("CPSAA1", "CCPSAA1")], "TM": [("CCEC1", "CCCEC1")],
}


def original_candidates(value: str, code: str, kind: str):
    values = [value]
    restored = value
    for corrected, published in PUBLISHED.get(code, []):
        restored = restored.replace(corrected, published)
    if restored != value:
        values.append(restored)
    for text in values:
        yield text
        if kind in ("competencia", "criterio") and text.endswith("."):
            yield text[:-1]
            yield text[:-1] + ","


def source_text(source_id: str) -> tuple[str, dict[int, str], list[int]]:
    filename, first, last = SOURCES[source_id]
    path = ROOT / "sources/es-cb/normativa" / filename
    raw = subprocess.check_output(["pdftotext", "-layout", "-enc", "UTF-8", "-f", str(first), "-l", str(last), str(path), "-"], text=True, encoding="utf-8")
    chunks = raw.split("\f")
    assert len(chunks) == last - first + 2 and not chunks[-1].strip()
    pages, repairs_count = {}, []
    with fitz.open(path) as pdf:
        recovery = FontRecovery(pdf)
        for number, raw_page in enumerate(chunks[:-1], first):
            lines = []
            for line in raw_page.splitlines():
                if any(marker in line for marker in ("BOC NÚM.", "CVE-", "boc.cantabria.es", "Boletín Oficial de Cantabria")):
                    continue
                if re.fullmatch(r"\s*(?:i|Pág\. \d+|\d+/(?:881|114|41)|\d{4}/\d+)\s*", line):
                    continue
                lines.append(line)
            page = "\n".join(lines)
            recovery.page(pdf[number - 1])
            repairs = recovery.repairs.get(number, [])
            if repairs:
                # Se sustituyen únicamente los tramos CID identificados, con
                # tolerancia a los espacios de presentación de Poppler.
                for encoded, decoded in sorted(repairs, key=lambda pair: len(pair[0]), reverse=True):
                    needle = re.sub(r"\s+", "", encoded)
                    if decoded.strip() == "–":
                        # Poppler puede resolver por sí solo la raya aislada;
                        # nunca se sustituye una «í» dentro de una palabra.
                        page = re.sub(r"(?m)^(\s*)" + re.escape(needle), lambda m: m.group(1) + decoded, page)
                        continue
                    expression = r"\s*".join(re.escape(char) for char in needle)
                    page, count = re.subn(expression, lambda _: decoded, page)
                    resolved = compact(decoded).lstrip("–-−•")
                    assert count or resolved in compact(page), (number, [ord(char) for char in needle])
                repairs_count.append(number)
            pages[number] = page
    return "\n".join(pages.values()), pages, repairs_count


def title_positions(raw: str, names: list[str]) -> dict[str, int]:
    positions = {}
    offset = 0
    for line in raw.splitlines(keepends=True):
        for name in names:
            if compact(line) == compact(name) and name not in positions:
                positions[name] = offset
        offset += len(line)
    assert set(positions) == set(names), set(names) - set(positions)
    return positions


def leaves(node: dict) -> list[dict]:
    return node["saberes"] if "saberes" in node else [item for part in node.get("apartados", node.get("bloquesSaberes", [])) for item in leaves(part)]


def signature(dev: dict) -> str:
    data = copy.deepcopy(dev)
    data.pop("curso")
    def erase(value):
        if isinstance(value, dict):
            value.pop("id", None)
            for child in value.values():
                erase(child)
        elif isinstance(value, list):
            for child in value:
                erase(child)
    erase(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


class Stream:
    def __init__(self, raw: str, code: str, counts: Counter):
        self.value = compact(raw)
        self.position = 0
        self.code = code
        self.counts = counts

    def regex(self, pattern: str, *, optional: bool = False):
        match = re.match(pattern, self.value[self.position:])
        if not match:
            assert optional, (self.position, "rotulo", pattern, self.value[self.position:self.position + 150])
            return
        self.position += len(match.group())

    def text(self, value: str, kind: str, context: str = ""):
        candidates = [compact(item) for item in original_candidates(value, self.code, kind)]
        matching = [candidate for candidate in candidates if self.value.startswith(candidate, self.position)]
        target = max(matching, key=len) if matching else candidates[0]
        if not self.value.startswith(target, self.position):
            actual = self.value[self.position:]
            offset = next((i for i, (left, right) in enumerate(zip(target, actual)) if left != right), min(len(target), len(actual)))
            raise AssertionError((self.position + offset, kind, context, target[max(0, offset - 60):offset + 130], actual[max(0, offset - 60):offset + 130]))
        self.position += len(target)
        self.counts[kind] += 1

    def heading(self, value: str):
        self.text(value, "rotulo")
        self.regex(r"\.", optional=True)

    def end(self):
        assert self.position == len(self.value), (self.position, "texto sobrante", self.value[self.position:self.position + 200])


def audit_area(document: dict, raw: str, counts: Counter, culture_intro: str | None = None) -> None:
    code = document["materia"]["codigo"]
    s = Stream(raw, code, counts)
    intro = document["introduccion"]["es"]
    if culture_intro is not None:
        assert compact(" ".join(intro)) == compact(culture_intro), (code, "introduccion compartida")
    else:
        for value in intro:
            s.text(value, "introduccion")
    s.regex(r"Competencias[Ee]specíficas\.?")
    for ce in document["competenciasEspecificas"]:
        number = ce["codigoOficial"]
        s.regex(re.escape(number) + r"\.-?")
        s.text(ce["enunciado"]["es"], "competencia", ce["id"])
        for value in ce.get("descripcion", {}).get("es", []):
            s.text(value, "descripcion", ce["id"])
        s.regex(r"Estacompetencia(?:espec[ií]fica)?se(?:conecta|relaciona)conlos(?:siguientes)?(?:descriptores|prescriptores)(?:(?:del|de)?[Pp]erfildesalida|desalida)?:")
        keys = list(ce["descriptoresOperativosRefs"])
        # Reconstruir solo para el cotejo las referencias inexistentes publicadas
        # y retiradas por decisión editorial; nunca añadirlas al JSON curricular.
        if (code, number) in {("AED", "4"), ("AED", "5"), ("AED", "6"), ("TCM", "4"), ("TCM", "6")}:
            keys.extend(["CCEC5", "CCEC6"])
        if code == "PHAC" and number == "7":
            keys.insert(keys.index("CPSAA1"), "CPSAA1")
        for key in keys:
            s.regex(r"[,ye]", optional=True)
            s.text(key, "descriptor", ce["id"])
        s.regex(r"[.,]", optional=True)
        if code == "EVCE" and number == "4":
            s.text("83", "rotulo-ajeno")
    distinct, seen = [], set()
    for dev in document["desarrollos"]:
        value = signature(dev)
        if value not in seen:
            distinct.append(dev)
            seen.add(value)
    headers = GROUPS.get(code, [""])
    assert len(headers) == len(distinct), (code, len(headers), len(distinct))
    for group_number, (header, dev) in enumerate(zip(headers, distinct), 1):
        if header:
            s.heading(header)
        s.heading("Criterios de evaluación")
        if code == "EVCE":
            s.heading("Criterios de evaluación")
        active = None
        for criterion in dev["criteriosEvaluacion"]:
            number = criterion["codigoOficial"].split(".")[0]
            if number != active:
                s.regex(r"Competencias?espec[ií]ficas?" + number + r"\.?", optional=True)
                active = number
            published_code = "3,1" if code == "IDF" and criterion["codigoOficial"] == "3.1" else criterion["codigoOficial"]
            if code == "DIG" and published_code == "4.5":
                published_code = "4.4"
            s.regex(re.escape(published_code) + r"\.?")
            s.text(criterion["texto"]["es"], "criterio", criterion["id"])
        s.heading("Saberes básicos")
        if code == "IDF":
            s.text("Se dividen en tres grandes bloques:", "rotulo")
        if code == "TITID":
            s.text("BLOQUES", "rotulo")
        def section(node: dict, *, block: bool = False):
            if not (block and code in ("CCI", "CCII")):
                s.regex(re.escape(node["codigo"]) + r"\.")
            s.text(node["nombre"]["es"], "bloque" if block else "apartado", str(group_number))
            s.regex(r"\.", optional=True)
            if "apartados" in node:
                for child in node["apartados"]:
                    section(child)
            else:
                alone = len(node["saberes"]) == 1 and node["saberes"][0]["texto"]["es"].rstrip(".") == node["nombre"]["es"]
                for saber in node["saberes"]:
                    if alone:
                        counts["saber-en-titulo"] += 1
                        continue
                    if "numeracionFuente" in saber:
                        published_number = {"CCII.4.C.06": "5", "CCII.4.C.07": "6"}.get(saber["id"], saber["numeracionFuente"])
                        s.regex(re.escape(published_number) + r"\.")
                    else:
                        s.regex(BULLET)
                    s.text(saber["texto"]["es"], "saber", saber["id"])
        for block in dev["bloquesSaberes"]:
            section(block, block=True)
    s.end()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--packages", type=Path)
    parser.add_argument("--report", type=Path, default=ROOT / "tmp/pdfs/cantabria-eso-audit.json")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.packages:
        sys.path.insert(0, str(args.packages.resolve()))
    import jsonschema

    validator = jsonschema.Draft202012Validator(json.loads((ROOT / "schemas/materia.schema.json").read_text(encoding="utf-8")), format_checker=jsonschema.FormatChecker())
    documents = [json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "data/es-cb/eso/materias").glob("*.json")]
    assert len(documents) == 37
    report = {"schemaErrors": [], "coverageDifferences": [], "descriptorAnomalies": [], "counts": {}, "areas": [], "fuentesRecuperadas": {}}
    provenance_count = 0
    for path in (ROOT / "data/es-cb/eso/materias").glob("*.json"):
        document = json.loads(path.read_text(encoding="utf-8"))
        report["schemaErrors"].extend([str(path.relative_to(ROOT)), error.json_path, error.message] for error in validator.iter_errors(document))
    counts = Counter()
    valid_keys = {f"{name}{n}" for name, end in (("CCL", 5), ("CP", 3), ("STEM", 5), ("CD", 5), ("CPSAA", 5), ("CC", 4), ("CE", 3), ("CCEC", 4)) for n in range(1, end + 1)}
    for source_id in SOURCES:
        raw, pages, repaired = source_text(source_id)
        report["fuentesRecuperadas"][source_id] = repaired
        selected = [d for d in documents if d["fuentes"][0]["id"] == source_id]
        names = [d["materia"]["nombre"]["es"] for d in selected]
        if source_id.endswith("correccion-orden-edu-40-2022"):
            names += ["Cultura Clásica", "Segunda Lengua Extranjera"]
        positions = title_positions(raw, names)
        boundaries = sorted((position, name) for name, position in positions.items())
        bodies = {}
        for i, (position, name) in enumerate(boundaries):
            line_end = raw.index("\n", position)
            end = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(raw)
            bodies[name] = raw[line_end + 1:end]
        for d in selected:
            code = d["materia"]["codigo"]
            assert d["schemaVersion"] == "0.8.0"
            assert d["revision"]["estado"] == "revisado" and d["revision"]["fuenteComprobada"]
            expected_year = None if code == "TD" else "2022/2023" if any(item["curso"] in (1, 3) for item in d["materia"]["cursos"]) else "2023/2024"
            assert d["vigencia"]["aplicableDesdeCurso"] == expected_year
            assert not re.search(r"CB-ESO-\d+|INCIDENCIAS\.md", json.dumps(d, ensure_ascii=False))
            ce_ids = {c["id"] for c in d["competenciasEspecificas"]}
            assert len(ce_ids) == len(d["competenciasEspecificas"])
            all_ids = list(ce_ids)
            def check_provenance(node, texts):
                nonlocal provenance_count
                origin = node["procedencia"]
                assert origin["fuenteRef"] == source_id
                numbers = origin["paginas"]
                assert numbers and numbers == sorted(set(numbers)) and all(page in pages for page in numbers)
                published = compact(" ".join(pages[page] for page in numbers))
                for value, kind in texts:
                    assert any(compact(candidate) in published for candidate in original_candidates(value, code, kind)), (code, node.get("id"), numbers, "procedencia")
                    provenance_count += 1
            for ce in d["competenciasEspecificas"]:
                check_provenance(ce, [(ce["enunciado"]["es"], "competencia")] + [(value, "descripcion") for value in ce.get("descripcion", {}).get("es", [])])
                extras = set(ce["descriptoresOperativosRefs"]) - valid_keys
                if extras:
                    report["descriptorAnomalies"].append([code, ce["id"], sorted(extras)])
            for dev in d["desarrollos"]:
                assert any(item["curso"] == dev["curso"] for item in d["materia"]["cursos"])
                for criterion in dev["criteriosEvaluacion"]:
                    check_provenance(criterion, [(criterion["texto"]["es"], "criterio")])
                    assert criterion["competenciaEspecificaRef"] in ce_ids and not criterion["saberesBasicosRefs"]
                    assert criterion["competenciaEspecificaRef"] == "ce-" + criterion["codigoOficial"].split(".")[0]
                    all_ids.append(criterion["id"])
                for saber in leaves(dev):
                    check_provenance(saber, [(saber["texto"]["es"], "saber")])
                    assert saber["codigoOficial"] is None
                    all_ids.append(saber["id"])
            assert len(all_ids) == len(set(all_ids)), code
            try:
                audit_area(d, bodies[d["materia"]["nombre"]["es"]], counts, bodies.get("Cultura Clásica") if code in ("CCI", "CCII") else None)
            except AssertionError as error:
                report["coverageDifferences"].append([code, str(error)])
            report["areas"].append({"materia": d["materia"]["nombre"]["es"], "competencias": len(ce_ids), "desarrollos": len(d["desarrollos"]), "criterios": sum(len(dev["criteriosEvaluacion"]) for dev in d["desarrollos"]), "saberes": sum(len(leaves(dev)) for dev in d["desarrollos"])})
    report["counts"] = dict(counts)
    report["fragmentosProcedencia"] = provenance_count
    assert not report["descriptorAnomalies"], report["descriptorAnomalies"]
    scope_path = ROOT / "data/es-cb/eso/ambitos-por-remision.json"
    scope_document = json.loads(scope_path.read_text(encoding="utf-8"))
    scope_schema = json.loads((ROOT / "schemas/ambitos-por-remision.schema.json").read_text(encoding="utf-8"))
    scope_errors = list(jsonschema.Draft202012Validator(scope_schema).iter_errors(scope_document))
    assert not scope_errors, [error.message for error in scope_errors]
    assert len(scope_document["ambitos"]) == 2 and scope_document["fuenteId"] == "es-cb-eso-orden-edu-41-2022"
    document_ids = {document["id"] for document in documents}
    for scope in scope_document["ambitos"]:
        assert set(scope["materiasBaseRefs"]) <= document_ids
        assert all(option["materiaRef"] in document_ids for option in scope["incorporacionesOpcionales"])
    source_catalog = json.loads((ROOT / "sources/es-cb/normativa/catalogo.json").read_text(encoding="utf-8"))
    source_ids = {source["id"] for document in documents for source in document["fuentes"]} | {scope_document["fuenteId"]}
    for source in source_catalog["documentos"]:
        if source["id"] in source_ids:
            path = ROOT / "sources/es-cb/normativa" / source["archivo"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"], source["id"]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"areas": len(documents), "fragmentos": sum(counts.values()), **{key: len(report[key]) for key in ("schemaErrors", "coverageDifferences", "descriptorAnomalies")}}, ensure_ascii=False))
    if report["schemaErrors"] or report["coverageDifferences"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
