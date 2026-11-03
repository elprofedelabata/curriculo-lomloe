"""Coteja los JSON canarios con sus PDF y ODT institucionales.

Requiere jsonschema. --packages permite usar una instalación temporal.
El informe distingue diferencias textuales, numeración, referencias y omisiones.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--packages", type=Path)
    parser.add_argument("--report", type=Path, default=ROOT / "tmp/pdfs/canarias-bachillerato-audit.json")
    args = parser.parse_args()
    if args.packages:
        sys.path.insert(0, str(args.packages.resolve()))
    import jsonschema
    spec = importlib.util.spec_from_file_location("canarias_bach", ROOT / "scripts/extract-es-cn-bachillerato.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    validator = jsonschema.Draft202012Validator(json.loads((ROOT / "schemas/materia.schema.json").read_text(encoding="utf-8")))
    report = {"counts": {}, "schemaErrors": [], "textDifferences": [], "numberingDifferences": [], "structural": [], "omissions": [], "manualChecks": []}
    # Estos cinco textos se cotejaron en la página renderizada del BOC. La capa
    # de texto intercala restos de otras páginas; la huella exige revisar de nuevo
    # cualquier cambio posterior del texto que se comprobó visualmente.
    manual_checks = {
        ("anatomia-aplicada", "explicacion", "1-ce-3"): (28, "fed8e3fa5c4db4c17d77156fd58a591e40b18e13d555328f25791407d144cc1c"),
        ("cultura-cientifica", "explicacion", "1-ce-4"): (98, "51e12207d2131e60f70eeba5ad7c3d50ee3fab5be5975fa0183b4e72c81e955e"),
        ("taller-de-artes-integradas", "explicacion", "2-ce-2"): (366, "40eacab3b4cf9882334ecbed8ee8ea430bfcea923355dc8b0e1d81791bfaf919"),
        ("tecnicas-de-laboratorio", "saber", "TL.1.C.5"): (421, "76e44285930d4bdf1f2c109e76126d971a985f11c3655a2441d0194cb8627357"),
        ("psicologia", "explicacion", "2-ce-5"): (350, "27f549ec7d8ae72594b10736ec604c56b66a49230f00591d81baef10df5bd131"),
    }
    cache = {}
    for decree, pdf in [("30/2023", m.PDF), ("78/2025", m.OPT_PDF)]:
        raw = subprocess.run(["pdftotext", "-raw", "-enc", "UTF-8", str(pdf), "-"], capture_output=True, check=True).stdout.decode("utf-8").split("\f")
        signatures = {m.utils.normal(match.group(1)) for p in raw for match in re.finditer(r"documento\s+electrónico\s+siguiente:\s*([A-Za-z0-9_-]{25,})", p) if any(c.isdigit() for c in match.group(1))}
        def clean(value):
            value = re.sub(r"(?m)^Boletín Oficial de Canarias[^\n]*\n(?:\d{4,}\s*\n)?", "", value)
            value = m.utils.normal(m.shared.REF.sub("", value))
            fragments = ["enladireccionhttpssedegobiernodecanariasorgsedeverificadoccodigonde", "puedesercomprobadalaautenticidaddeestacopiamedianteelnumerode", "documentoelectronicosiguiente", "httpssedegobiernodecanariasorgboc", "boca2023058848", "boca20251122086", "descriptoresoperativosdelascompetenciasclaveperfildesalida", "descriptoresoperativosdelascompetenciasclave"] + list(signatures)
            for fragment in fragments:
                value = value.replace(fragment, "")
            return value
        cache[decree] = ([clean(p) for p in raw], [m.utils.normal(m.shared.REF.sub("", p)) for p in raw])
    valid_refs = {f"{p}{i}" for p, n in [("CCL", 5), ("CP", 3), ("STEM", 5), ("CD", 5), ("CC", 4), ("CE", 3)] for i in range(1, n + 1)} | {"CPSAA1.1", "CPSAA1.2", "CPSAA2", "CPSAA3.1", "CPSAA3.2", "CPSAA4", "CPSAA5", "CCEC1", "CCEC2", "CCEC3.1", "CCEC3.2", "CCEC4.1", "CCEC4.2"}
    manifest = json.loads((m.SUPPORT / "manifest.json").read_text(encoding="utf-8"))
    for meta in manifest:
        path = m.OUTPUT / (meta["slug"] + ".json")
        d = json.loads(path.read_text(encoding="utf-8"))
        report["schemaErrors"].extend([meta["slug"], e.json_path, e.message] for e in validator.iter_errors(d))
        source = d["fuentes"][0]
        expected_source = "boc-2025-112-decreto-78-2025" if meta["optativa"] else m.SOURCE_ID
        assert source["id"] == expected_source, path
        pages, literal_pages = cache[meta["decreto"]]
        lo, hi = meta["paginas"]["desde"], meta["paginas"]["hasta"]
        span, literal_span = "".join(pages[lo - 1:hi]), "".join(literal_pages[lo - 1:hi])
        entries = [("introduccion", str(i), text) for i, text in enumerate(d["introduccion"]["es"])]
        ces = {c["id"]: c for c in d["competenciasEspecificas"]}
        assert len(ces) == len(d["competenciasEspecificas"])
        referenced = list(ces.values())
        for ce in ces.values():
            entries.append(("competencia", ce["id"], ce["enunciado"]["es"]))
            entries.extend(("descripcion", ce["id"], text) for text in ce.get("descripcion", {}).get("es", []))
        for dev in d["desarrollos"]:
            for c in dev["criteriosEvaluacion"]:
                assert ces[c["competenciaEspecificaRef"]]["codigoOficial"] == c["codigoOficial"].split(".")[0]
                entries.append(("criterio", c["id"], c["texto"]["es"]))
            for b in dev["bloquesCompetenciales"]:
                assert b["competenciaEspecificaRef"] in ces
                entries.extend(("explicacion", f"{dev['curso']}-{b['competenciaEspecificaRef']}", text) for text in b["explicacion"]["es"])
            referenced += dev["criteriosEvaluacion"] + dev["bloquesCompetenciales"]
            for ce in ces.values():
                minors = [int(c["codigoOficial"].split(".")[1]) for c in dev["criteriosEvaluacion"] if c["competenciaEspecificaRef"] == ce["id"]]
                if minors and sorted(minors) != list(range(1, max(minors) + 1)):
                    report["structural"].append([meta["slug"], dev["curso"], ce["id"], "criterion sequence", minors])
            for block in dev["bloquesSaberes"]:
                entries.append(("bloque", f"{dev['curso']}-{block['codigo']}", block["nombre"]["es"]))
                for part in block.get("apartados", [block]):
                    if part is not block:
                        entries.append(("apartado", f"{dev['curso']}-{block['codigo']}", part["nombre"]["es"]))
                    for s in part["saberes"]:
                        entries.append(("saber", s["id"], s["texto"]["es"]))
                        if m.utils.normal(s["numeracionFuente"] + s["texto"]["es"][:35]) not in span:
                            report["numberingDifferences"].append([meta["slug"], s["id"], s["numeracionFuente"], s["texto"]["es"][:90]])
                        referenced.append(s)
        for obj in referenced:
            bad = set(obj.get("descriptoresOperativosRefs", [])) - valid_refs
            if bad:
                report["structural"].append([meta["slug"], obj.get("id", obj.get("competenciaEspecificaRef")), "descriptor", sorted(bad)])
            provenance = obj["procedencia"]
            assert provenance["fuenteRef"] == expected_source and all(lo <= p <= hi for p in provenance["paginas"]), (path, obj)
        nodes = m.read_odt_nodes(meta["odt"])
        course, in_sabers, original = None, False, []
        desc_start = next(i for i, n in enumerate(nodes) if re.match(r"^Competencias? específicas? \d+", m.utils.plain(n)))
        desc_end = next(i for i in range(desc_start, len(nodes)) if m.utils.plain(nodes[i]) == "Saberes básicos")
        for node in nodes[desc_start:desc_end]:
            if node.tag == m.TEXT + "list":
                report["omissions"].append([meta["slug"], "list in CE narrative", m.utils.plain(node)[:100]])
        for node in nodes:
            text = m.utils.plain(node)
            heading = m.course_heading(text)
            if heading:
                course, in_sabers = heading, False
            if not course:
                continue
            if text == "Saberes básicos":
                in_sabers = True
                continue
            if in_sabers and node.tag == m.TEXT + "list":
                for item in node.iter(m.TEXT + "list-item"):
                    if m.utils.direct_paragraphs(item):
                        original.append(m.utils.normal(" ".join(m.utils.direct_paragraphs(item))))
                    if item.attrib.get(m.TEXT + "start-value", "1") != "1":
                        report["structural"].append([meta["slug"], course, "manual numbering", item.attrib[m.TEXT + "start-value"]])
            if in_sabers and node.tag == m.TEXT + "p" and re.fullmatch(r"\d+\.\s+.+", text):
                original.append(m.utils.normal(re.sub(r"^\d+\.\s+", "", text)))
            if node.tag == m.TABLE + "table":
                rows = node.findall(f"./{m.TABLE}table-row")
                majors = {p.split(".")[0] for p in m.utils.direct_paragraphs(rows[0].find(f"./{m.TABLE}table-cell")) if re.match(r"^\d+\.", p)}
                for row in rows[2:-1]:
                    cell = row.find(f"./{m.TABLE}table-cell")
                    text = m.shared.cell_text(cell)
                    if text and text.split(".")[0] not in majors:
                        report["structural"].append([meta["slug"], course, "criterion in another CE", text[:100]])
                for row in rows:
                    cells = row.findall(f"./{m.TABLE}table-cell")
                    if len(cells) > 1:
                        text = m.shared.cell_text(cells[1])
                        if re.search(r"\d", m.shared.REF.sub("", text)):
                            report["structural"].append([meta["slug"], course, "unparsed descriptor", text])
        generated = [m.utils.normal(s["texto"]["es"].replace("proyectos de divulgación científica", "proyectos divulgación científica") if s["id"] == "TL.1.C.5" else s["texto"]["es"]) for dev in d["desarrollos"] for b in dev["bloquesSaberes"] for part in b.get("apartados", [b]) for s in part["saberes"]]
        if sorted(original) != sorted(generated):
            report["omissions"].append([meta["slug"], "saber completeness", len(original), len(generated)])
        for kind, identifier, text in entries:
            # Redacción original de las correcciones confirmadas en CN-BACH-001/002/003.
            if meta["codigoInterno"] == "GEO" and kind == "criterio" and identifier == "cri-2-5-1":
                assert "económicos y plantear soluciones razonables." in text
                text = text.replace("económicos y plantear", "económicos, y planteando")
            if kind == "saber" and identifier == "TL.1.C.5":
                assert "proyectos de divulgación científica" in text
                text = text.replace("proyectos de divulgación científica", "proyectos divulgación científica")
            report["counts"][kind] = report["counts"].get(kind, 0) + 1
            target = m.utils.normal(m.shared.REF.sub("", text))
            if target in span or target in literal_span:
                continue
            manual = manual_checks.get((meta["slug"], kind, identifier))
            if manual:
                page, expected_digest = manual
                assert hashlib.sha256(target.encode()).hexdigest() == expected_digest, (meta["slug"], kind, identifier, "Requiere nuevo cotejo visual")
                report["manualChecks"].append([meta["slug"], kind, identifier, page])
                continue
            positions, start = [], 0
            while True:
                pos = span.find(target[:min(45, len(target))], start)
                if pos < 0:
                    break
                positions.append(pos)
                start = pos + 1
            def prefix(pos):
                i = 0
                while i < len(target) and pos + i < len(span) and target[i] == span[pos + i]:
                    i += 1
                return i
            def skip_page_numbers(pos):
                i = 0
                while i < len(target) and pos < len(span):
                    if target[i] == span[pos]:
                        i += 1
                        pos += 1
                    elif span[pos].isdigit() and not target[i].isdigit():
                        while pos < len(span) and span[pos].isdigit():
                            pos += 1
                    else:
                        return False
                return i == len(target)
            if any(skip_page_numbers(pos) for pos in positions):
                continue
            if positions:
                pos = max(positions, key=prefix)
                common = prefix(pos)
                detail = {"common": common, "expected": target[max(0, common - 15):common + 100], "actual": span[pos + max(0, common - 15):pos + common + 100]}
            else:
                detail = {"prefixMissing": text[:120]}
            report["textDifferences"].append([meta["slug"], kind, identifier, detail])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for key, group in report.items():
        if key == "counts":
            print(key, group)
            continue
        print(key, len(group))
        for entry in group[:40]:
            print(json.dumps(entry, ensure_ascii=False))
    if any(report[key] for key in ("schemaErrors", "textDifferences", "numberingDifferences", "structural", "omissions")):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
