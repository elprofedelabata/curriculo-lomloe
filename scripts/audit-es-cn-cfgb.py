"""Valida los dos ámbitos canarios y coteja su contenido con el BOC y el ODT.

Uso: python scripts/audit-es-cn-cfgb.py [--packages RUTA] [--report RUTA]
Requiere PyMuPDF, Poppler y jsonschema. No modifica los JSON.
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
# Tablas partidas o columnas intercaladas: cotejo de las páginas renderizadas.
MANUAL = {
    "cri-1-10-1": "0f38ffe070e122baea7c7d81b24a19c8fcfc8ed4c414cc3cf83e680015c3fa40",
    "CA.1.A.2.1": "eb5ae6478a1b654338e3becc75f7cd9683f1a94876a33899f81f021cd7765707",
    "CA.2.A.2.1": "eb5ae6478a1b654338e3becc75f7cd9683f1a94876a33899f81f021cd7765707",
    "CA.1.E.2.3": "9f44af2787721b2a6600d0e491454eb53fb10d00729c90268cdc07a19031e8c0",
    "CA.1.I.2.1": "3b98ca65f83096be066779074103fa686e1e28a5eed7d55df899e46bcb1d169b",
    "CA.2.I.2.1": "df72a08698675c6f3a16badd7a68917ee16aacb52711ddc8cab9a7bb349561f8",
    "CA.2.J.3.1": "cf06351499692aae6c561a2cd7a4e3fa520badf571d7f8e1f9f73bf9712e205c",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--packages", type=Path)
    parser.add_argument("--report", type=Path, default=ROOT / "tmp/pdfs/canarias-cfgb-audit.json")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.packages:
        sys.path.insert(0, str(args.packages.resolve()))
    import fitz
    import jsonschema
    spec = importlib.util.spec_from_file_location("canarias_cfgb", ROOT / "scripts/extract-es-cn-cfgb.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    manifest = json.loads((m.SUPPORT / "manifest.json").read_text(encoding="utf-8"))
    for source in manifest["documentos"]:
        assert hashlib.sha256((m.SUPPORT / source["archivo"]).read_bytes()).hexdigest() == source["sha256"]
    sources = json.loads((ROOT / "sources/es-cn/normativa/catalogo.json").read_text(encoding="utf-8"))
    pdf_source = next(s for s in sources["documentos"] if s["id"] == "es-cn-cfgb-decreto-9-2023")
    assert hashlib.sha256(m.PDF.read_bytes()).hexdigest() == pdf_source["sha256"]
    validator = jsonschema.Draft202012Validator(json.loads((ROOT / "schemas/materia.schema.json").read_text(encoding="utf-8")))
    raw = subprocess.check_output(["pdftotext", "-f", "1", "-l", "99", "-raw", "-enc", "UTF-8", str(m.PDF), "-"]).decode("utf-8").split("\f")
    with fitz.open(m.PDF) as pdf:
        visible = [p.get_text(clip=fitz.Rect(0, 90, p.rect.width, p.rect.height - 35)) for p in pdf[:99]]
    def normalized(value):
        value = re.sub(r"(?m)^.*(?:Boletín Oficial de Canarias núm\.|sede.gobiernodecanarias.org/boc|boc-a-2023-025-402).*$", "", value)
        value = re.sub(r"(?m)^\s*\d+\s*$", "", value)
        return m.normal(m.REF.sub("", value))
    report = {"counts": {}, "schemaErrors": [], "textDifferences": [], "structural": [], "omissions": [], "manualChecks": []}
    expected = {"CA": [(34, 65), (20, 58)], "CCS": [(26, 88), (26, 90)]}
    all_text = []
    for path in sorted(m.OUTPUT.glob("*.json")):
        d = json.loads(path.read_text(encoding="utf-8"))
        code = d["materia"]["codigo"]
        report["schemaErrors"].extend([path.name, e.json_path, e.message] for e in validator.iter_errors(d))
        limits = d["fuentes"][0]["paginasMateria"]
        lo, hi = limits["desde"], limits["hasta"]
        spans = [normalized("\n".join(pages[lo - 1:hi])) for pages in (raw, visible)]
        entries = [("introduccion", str(i), text, None) for i, text in enumerate(d["introduccion"]["es"])]
        ces = {ce["id"]: ce for ce in d["competenciasEspecificas"]}
        assert len(ces) == (11 if code == "CA" else 8)
        entries += [("competencia", ce["id"], ce["enunciado"]["es"], ce) for ce in ces.values()]
        ids = set(ces)
        counts = []
        for dev in d["desarrollos"]:
            course = dev["curso"]
            saber_count = 0
            assert len(dev["bloquesSaberes"]) == len({b["codigo"] for b in dev["bloquesSaberes"]})
            for criterion in dev["criteriosEvaluacion"]:
                assert criterion["competenciaEspecificaRef"] in ces
                assert ces[criterion["competenciaEspecificaRef"]]["codigoOficial"] == criterion["codigoOficial"].split(".")[0]
                assert criterion["id"] not in ids
                ids.add(criterion["id"])
                entries.append(("criterio", criterion["id"], criterion["texto"]["es"], criterion))
            for block in dev["bloquesCompetenciales"]:
                assert block["competenciaEspecificaRef"] in ces
                entries.extend(("explicacion", f"{course}-{block['competenciaEspecificaRef']}-{i}", text, block)
                               for i, text in enumerate(block["explicacion"]["es"]))
            for block in dev["bloquesSaberes"]:
                for part in block.get("apartados", [block]):
                    for saber in part["saberes"]:
                        assert saber["id"] not in ids and saber["codigoOficial"] is None
                        ids.add(saber["id"])
                        assert "numeracionFuente" not in saber
                        assert not saber.get("cursoOrientativo") or course in saber["cursoOrientativo"]
                        entries.append(("saber", saber["id"], saber["texto"]["es"], saber))
                        saber_count += 1
            counts.append((len(dev["criteriosEvaluacion"]), saber_count))
        assert counts == expected[code], (code, counts)
        if code == "CA":
            assert all(int(c["codigoOficial"].split(".")[0]) <= 8 for c in d["desarrollos"][1]["criteriosEvaluacion"])
            assert all(b["codigo"] <= "K" for b in d["desarrollos"][1]["bloquesSaberes"])
        valid_refs = {f"{prefix}{n}" for prefix, stop in [("CCL", 5), ("CP", 3), ("STEM", 5), ("CD", 5), ("CPSAA", 5), ("CC", 4), ("CE", 3), ("CCEC", 4)] for n in range(1, stop + 1)}
        for kind, identifier, text, obj in entries:
            original = text
            correction = m.SABER_CORRECTIONS.get(identifier)
            if correction is None and kind == "criterio":
                correction = m.CRITERION_CORRECTIONS.get((code, obj["codigoOficial"]))
            if correction:
                old, new = correction
                assert text.count(new) == 1, identifier
                original = text.replace(new, old, 1)
            all_text.append(original)
            if obj:
                provenance = obj["procedencia"]
                assert provenance["fuenteRef"] == m.SOURCE_ID
                assert all(lo <= page <= hi for page in provenance["paginas"])
                assert not (set(obj.get("descriptoresOperativosRefs", [])) - valid_refs), identifier
            target = normalized(original)
            if not any(target in span for span in spans):
                if identifier in MANUAL and hashlib.sha256(text.encode("utf-8")).hexdigest() == MANUAL[identifier]:
                    report["manualChecks"].append([path.name, identifier, obj["procedencia"]["paginas"]])
                else:
                    report["textDifferences"].append([path.name, kind, identifier, text])
        report["counts"][path.stem] = {"competencias": len(ces), "cursos": [{"curso": i + 1, "criterios": c, "saberes": s} for i, (c, s) in enumerate(counts)]}
    # Comprobación independiente de cobertura: cada párrafo de las tablas de
    # saberes debe estar representado, también list-header y sublistas.
    joined = m.normal(" ".join(all_text))
    for node in m.nodes():
        if node.tag != m.TABLE + "table":
            continue
        title = m.cell_text(node.find(m.TABLE + "table-row/" + m.TABLE + "table-cell"))
        if title.startswith("Competencia específica"):
            continue
        for text in m.paragraphs(node):
            if "CURSO" in text or re.match(r"^(?:BLOQUE [ABC]:|[A-KIVX]+\.)\s", text) or text == "Actividad Física y Bienestar Emocional":
                continue
            # Las etiquetas de filas se conservan como nombres de apartados.
            if m.normal(text) not in joined:
                data = " ".join(path.read_text(encoding="utf-8") for path in m.OUTPUT.glob("*.json"))
                if m.normal(text) not in m.normal(data):
                    report["omissions"].append(text)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value if key == "counts" else len(value) for key, value in report.items()}, ensure_ascii=False))
    if any(report[key] for key in ("schemaErrors", "textDifferences", "structural", "omissions")):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
