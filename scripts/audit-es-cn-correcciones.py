"""Audita las reparaciones de Primaria y las concreciones del silbo gomero.

Valida también el esquema y las referencias de los 109 JSON canarios.
Uso: python scripts/audit-es-cn-correcciones.py [--packages RUTA] [--report RUTA]
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = re.compile(r"\b[A-Z]{2,6}\d+(?:\.\d+)?\b")


def normal(text):
    text = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in text if c.isalnum() and not unicodedata.combining(c))


def clean(text):
    text = re.sub(r"(?m)^.*(?:Boletín Oficial de Canarias núm\.|sede.gobiernodecanarias.org/boc|boc-a-\d{4}-\d{3}-\d+).*$", "", text)
    text = normal(REF.sub("", text))
    return text.replace("descriptoresoperativosdelascompetenciasclaveperfildesalida", "").replace("descriptoresoperativosdelascompetenciasclave", "")


def contains(span, target):
    if target in span:
        return True
    for match in re.finditer(re.escape(target[:min(40, len(target))]), span):
        pos, i = match.start(), 0
        while pos < len(span) and i < len(target):
            if span[pos] == target[i]:
                pos, i = pos + 1, i + 1
            elif span[pos].isdigit() and not target[i].isdigit():
                while pos < len(span) and span[pos].isdigit():
                    pos += 1
            else:
                break
        if i == len(target):
            return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--packages", type=Path)
    parser.add_argument("--report", type=Path, default=ROOT / "tmp/pdfs/canarias-correcciones-audit.json")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.packages:
        sys.path.insert(0, str(args.packages.resolve()))
    import jsonschema
    spec = importlib.util.spec_from_file_location("silbo", ROOT / "scripts/extract-es-cn-silbo.py")
    silbo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(silbo)
    validator = jsonschema.Draft202012Validator(json.loads((ROOT / "schemas/materia.schema.json").read_text(encoding="utf-8")), format_checker=jsonschema.FormatChecker())
    documents = {d["id"]: d for p in sorted((ROOT / "data/es-cn").glob("*/materias/*.json")) if (d := json.loads(p.read_text(encoding="utf-8")))}
    assert len(documents) == 109
    report = {"counts": dict(Counter(d["etapa"] for d in documents.values())), "schemaErrors": [], "textDifferences": [], "numberingDifferences": [], "odtOmissions": []}
    for d in documents.values():
        report["schemaErrors"].extend([d["id"], e.json_path, e.message] for e in validator.iter_errors(d))
        ces = {c["id"]: c for c in d["competenciasEspecificas"]}
        assert len(ces) == len(d["competenciasEspecificas"])
        sources = {s["id"]: s for s in d["fuentes"]}
        ids, dimensions = [], []
        for dev in d["desarrollos"]:
            dimensions.append((dev.get("curso"), dev.get("ciclo"), dev.get("variante", {}).get("codigo")))
            sabers = [s for b in dev["bloquesSaberes"] for part in b.get("apartados", [b]) for s in part["saberes"]]
            refs = {s["id"] for s in sabers}
            assert len({b["codigo"] for b in dev["bloquesSaberes"]}) == len(dev["bloquesSaberes"])
            for c in dev["criteriosEvaluacion"]:
                assert ces[c["competenciaEspecificaRef"]]["codigoOficial"] == c["codigoOficial"].split(".")[0]
                assert not set(c["saberesBasicosRefs"]) - refs
            for obj in dev["criteriosEvaluacion"] + dev.get("bloquesCompetenciales", []) + sabers + list(ces.values()):
                if "competenciaEspecificaRef" in obj:
                    assert obj["competenciaEspecificaRef"] in ces
                provenance = obj["procedencia"]
                source = sources[provenance["fuenteRef"]]
                if "paginasMateria" in source:
                    assert all(source["paginasMateria"]["desde"] <= p <= source["paginasMateria"]["hasta"] for p in provenance["paginas"])
            ids += [s["id"] for s in sabers] + [c["id"] for c in dev["criteriosEvaluacion"]]
        assert len(ids) == len(set(ids)), d["id"]
        assert len(dimensions) == len(set(dimensions)), d["id"]
        declared = {x["curso"] for x in d["materia"].get("cursos", [])} or {x["ciclo"] for x in d["materia"].get("ciclos", [])}
        assert declared == {x[0] or x[1] for x in dimensions}, d["id"]
        if "concrecionCurricular" in d:
            assert d["concrecionCurricular"]["materiaBaseRef"] in documents
            assert d["concrecionCurricular"]["aplicacion"] == {"preceptivaEn": ["La Gomera"], "facultativaEn": ["Resto de las islas de Canarias"], "facultativaRequiereAutorizacion": True}
    support_manifest = json.loads((silbo.SUPPORT / "manifest.json").read_text(encoding="utf-8"))
    for source in support_manifest["documentos"]:
        assert hashlib.sha256((silbo.SUPPORT / source["archivo"]).read_bytes()).hexdigest() == source["sha256"]
    catalog = json.loads((ROOT / "sources/es-cn/normativa/catalogo.json").read_text(encoding="utf-8"))
    for source in catalog["documentos"]:
        assert hashlib.sha256((ROOT / "sources/es-cn/normativa" / source["archivo"]).read_bytes()).hexdigest() == source["sha256"]
    cache = {}
    for stage, filename in [("primaria", "primaria/2022-11-10-decreto-211-2022-curriculo-primaria.pdf"),
                            ("silbo", "primaria-eso/2026-03-09-decreto-24-2026-lenguaje-silbado-gomera.pdf")]:
        raw = subprocess.check_output(["pdftotext", "-raw", "-enc", "UTF-8", str(ROOT / "sources/es-cn/normativa" / filename), "-"]).decode("utf-8")
        cache[stage] = raw.split("\f")
    text_count = 0
    for d in documents.values():
        if d["etapa"] != "primaria" and "concrecionCurricular" not in d:
            continue
        limits = d["fuentes"][0]["paginasMateria"]
        pdf = cache["silbo" if "concrecionCurricular" in d else "primaria"]
        span = clean("\n".join(pdf[limits["desde"] - 1:limits["hasta"]]))
        entries = [("intro", str(i), text) for i, text in enumerate(d["introduccion"]["es"])]
        for c in d["competenciasEspecificas"]:
            entries += [("competencia", c["id"], c["enunciado"]["es"])] + [("descripcion", c["id"], text) for text in c.get("descripcion", {}).get("es", [])]
        for dev in d["desarrollos"]:
            dim = str(dev.get("curso", dev.get("ciclo")))
            entries += [("criterio", c["id"], c["texto"]["es"]) for c in dev["criteriosEvaluacion"]]
            entries += [("explicacion", dim + "-" + b["competenciaEspecificaRef"], text) for b in dev.get("bloquesCompetenciales", []) for text in b["explicacion"]["es"]]
            for b in dev["bloquesSaberes"]:
                for part in b.get("apartados", [b]):
                    for s in part["saberes"]:
                        entries.append(("saber", s["id"], s["texto"]["es"]))
                        if s.get("numeracionFuente"):
                            prefix = normal(s["numeracionFuente"] + s["texto"]["es"][:40])
                            if prefix not in span:
                                report["numberingDifferences"].append([d["id"], s["id"], s["numeracionFuente"]])
        for kind, identifier, text in entries:
            # CN-PRIM-005, confirmada: el BOC dice tres tras enumerar cinco.
            if d["id"] == "es-cn.primaria.lengua-extranjera":
                text = text.replace("Abordar estas cinco dimensiones", "Abordar estas tres dimensiones")
            text_count += 1
            if not contains(span, clean(text)):
                report["textDifferences"].append([d["id"], kind, identifier, text])
    # Cobertura por ciclo, para no enmascarar un enunciado ausente porque esté
    # repetido en otro ciclo (caso del epígrafe 2.10 de Matemáticas).
    primary = silbo.primary
    for area in primary.AREA:
        name, slug, _, _, _, _, _ = area
        d = documents["es-cn.primaria." + slug]
        nodes = primary.odt_children(name)
        cycle, in_sabers = None, False
        for node in nodes:
            text = silbo.utils.plain(node)
            match = re.fullmatch(r"(Primer|Segundo|Tercer) ciclo Educación Primaria", text)
            if match:
                cycle, in_sabers = {"Primer": 1, "Segundo": 2, "Tercer": 3}[match[1]], False
            if text == "Saberes básicos":
                in_sabers = True
            if cycle is None or not in_sabers or node.tag != silbo.TEXT + "list":
                continue
            dev = next(x for x in d["desarrollos"] if x["ciclo"] == cycle)
            values = []
            for b in dev["bloquesSaberes"]:
                values.append(b["nombre"]["es"])
                for part in b.get("apartados", [b]):
                    values.append(part["nombre"]["es"])
                    values += [s["texto"]["es"] for s in part["saberes"]]
            represented = normal(" ".join(values))
            for paragraph in silbo.utils.paragraphs(node):
                if normal(paragraph) not in represented:
                    report["odtOmissions"].append([slug, cycle, paragraph])
    math = documents["es-cn.primaria.matematicas"]
    sabers = {s["id"]: s for dev in math["desarrollos"] for b in dev["bloquesSaberes"] for part in b.get("apartados", [b]) for s in part["saberes"]}
    assert len(sabers) == 250
    for identifier, source_number in {"MAT.2.A.32": "2.2", "MAT.2.A.33": "2.3", "MAT.2.A.34": "2.10", "MAT.2.A.35": "2.12", "MAT.3.A.37": "2.2", "MAT.3.A.38": "2.3"}.items():
        assert sabers[identifier]["numeracionFuente"] == source_number
    report["fragmentosCotejados"] = text_count
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: len(value) if isinstance(value, list) else value for key, value in report.items()}, ensure_ascii=False))
    if any(report[k] for k in ["schemaErrors", "textDifferences", "numberingDifferences", "odtOmissions"]):
        for key in ["schemaErrors", "textDifferences", "numberingDifferences", "odtOmissions"]:
            for value in report[key][:10]:
                print(key, value)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
