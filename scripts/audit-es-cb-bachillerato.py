"""Cotejo independiente de Bachillerato de Cantabria con Poppler y JSON Schema.

No importa ni ejecuta el extractor. Comprueba todas las materias completas,
las decisiones editoriales, la procedencia por páginas y los PDF oficiales.
"""
from __future__ import annotations
import argparse
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
 "es-cb-eso-bachillerato-decreto-73-2022": ("eso-bachillerato/2022-07-27-decreto-73-2022-curriculo-eso-bachillerato.pdf",353,878),
 "es-cb-bachillerato-orden-edu-42-2022": ("bachillerato/2022-08-08-orden-edu-42-2022-implantacion-optativas.pdf",21,93),
 "es-cb-bachillerato-orden-edu-30-2024": ("bachillerato/2024-06-11-orden-edu-30-2024-modificacion-optativas.pdf",10,25),
 "es-cb-eso-bachillerato-orden-edu-21-2025": ("eso-bachillerato/2025-05-07-orden-edu-21-2025-espade.pdf",24,31),
}
def published_title(document):
    if document["materia"]["codigo"] == "DEVAS":
        return "Desarrollo de Estilo de Vida Activa y Saludable (DEVAS)"
    return document["materia"]["nombre"]["es"]


def audit_area(document, raw, counts):
    code = document["materia"]["codigo"]
    stream = Stream(raw, code, counts)
    for paragraph in document["introduccion"]["es"]:
        stream.text(paragraph, "introduccion")
    stream.heading("Competencias específicas")
    for ce in document["competenciasEspecificas"]:
        stream.regex(re.escape(ce["codigoOficial"]) + r"\.-?")
        stream.text(ce["enunciado"]["es"], "competencia", ce["id"])
        for paragraph in ce.get("descripcion", {}).get("es", []):
            stream.text(paragraph, "descripcion", ce["id"])
        stream.regex(r"Estacompetencia(?:espec[ií]fica)?(?:se)?(?:conecta|relaciona)conlos(?:siguientes)?(?:descriptores|prescriptores)(?:operativos)?(?:(?:del|de|delas)?(?:[Pp]erfildesalida|salida|competenciasclave(?:enBachillerato)?)?)?:")
        fixture = REF_VERSIONS.get(code + ":" + ce["codigoOficial"])
        if fixture:
            assert ce["descriptoresOperativosRefs"] == fixture[1], (code, ce["id"], "tratamiento editorial")
        for key in fixture[0] if fixture else ce["descriptoresOperativosRefs"]:
            stream.regex(r"[,ye.]", optional=True)
            stream.text(key, "descriptor", ce["id"])
        stream.regex(r"[.,]", optional=True)
    for dev in document["desarrollos"]:
        if len(document["desarrollos"]) == 2:
            stream.regex("(?i:" + re.escape(compact(document["materia"]["nombre"]["es"])) + ("I" if dev["curso"] == 1 else "II") + r"\.?)")
        stream.heading("Competencias específicas" if code in ("GEO", "MCA") else "Criterios de evaluación")
        for criterion in dev["criteriosEvaluacion"]:
            competence = criterion["competenciaEspecificaRef"].split("-")[-1]
            stream.regex(r"Competencias?espec[ií]ficas?" + competence + r"\.?", optional=True)
            published_number = "6..1" if code == "FAG" and criterion["codigoOficial"] == "6.1" else criterion["codigoOficial"]
            stream.regex(re.escape(published_number) + r"\.?")
            stream.text(criterion["texto"]["es"], "criterio", criterion["id"])
        stream.heading("Saberes básicos")

        def part(node):
            if "apartados" in node:
                for child in node["apartados"]:
                    stream.regex(re.escape(child["codigo"]) + r"\.?")
                    stream.heading(child["nombre"]["es"])
                    if "saberes" in child and len(child["saberes"]) == 1 and compact(child["saberes"][0]["texto"]["es"]).rstrip(".") == compact(child["nombre"]["es"]).rstrip("."):
                        counts["saber-sin-vineta"] += 1
                    else:
                        part(child)
            else:
                for saber in node["saberes"]:
                    stream.regex(BULLET, optional=code == "LD" and saber["texto"]["es"] == "Drama: libertad individual y convenciones sociales.")
                    stream.text(saber["texto"]["es"], "saber", saber["id"])
        for block in dev["bloquesSaberes"]:
            if code not in ("GR", "LAT"):
                stream.regex(re.escape(block["codigo"]) + r"[.)]")
            stream.heading(block["nombre"]["es"])
            part(block)
    stream.end()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--packages", type=Path)
    parser.add_argument("--cache-source-text", type=Path)
    parser.add_argument("--report", type=Path, default=ROOT / "tmp/pdfs/cantabria-bachillerato-audit.json")
    args = parser.parse_args()
    if args.packages:
        sys.path.insert(0, str(args.packages.resolve()))
    import jsonschema
    sys.stdout.reconfigure(encoding="utf-8")
    schema = json.loads((ROOT / "schemas/materia.schema.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    documents = [json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "data/es-cb/bachillerato/materias").glob("*.json")]
    assert len(documents) == 53
    report = {"schemaErrors": [], "coverageDifferences": [], "descriptorAnomalies": [], "descriptorGroups": [], "areas": [], "fragmentosProcedencia": 0, "fuentesRecuperadas": {}}
    counts = Counter()
    valid = {f"{key}{n}" for key,end in (("CCL",5),("CP",3),("STEM",5),("CD",5),("CC",4),("CE",3)) for n in range(1,end+1)} | {"CPSAA1.1", "CPSAA1.2", "CPSAA2", "CPSAA3.1", "CPSAA3.2", "CPSAA4", "CPSAA5", "CCEC1", "CCEC2", "CCEC3.1", "CCEC3.2", "CCEC4.1", "CCEC4.2"}
    broad = {"CPSAA1", "CPSAA3", "CCEC3", "CCEC4"}
    for source_id in SOURCES:
        cache_path = args.cache_source_text / (source_id + ".json") if args.cache_source_text else None
        if cache_path and cache_path.exists():
            raw, cached_pages, recovered = json.loads(cache_path.read_text(encoding="utf-8"))
            pages = {int(n): text for n,text in cached_pages.items()}
        else:
            raw, pages, recovered = source_text(source_id)
            if cache_path:
                cache_path.parent.mkdir(parents=True,exist_ok=True)
                cache_path.write_text(json.dumps([raw,pages,recovered],ensure_ascii=False),encoding="utf-8")
        report["fuentesRecuperadas"][source_id] = recovered
        selected = [x for x in documents if x["fuentes"][0]["id"] == source_id]
        positions = title_positions(raw, [published_title(x) for x in selected])
        boundaries = sorted((offset, title) for title,offset in positions.items())
        bodies = {}
        for index,(start,title) in enumerate(boundaries):
            end = boundaries[index+1][0] if index+1<len(boundaries) else len(raw)
            bodies[title] = raw[raw.index("\n",start)+1:end]
        for document in selected:
            code = document["materia"]["codigo"]
            report["schemaErrors"].extend([code,e.json_path,e.message] for e in validator.iter_errors(document))
            assert document["schemaVersion"] == "0.8.0" and document["revision"]["estado"] == "revisado" and document["revision"]["fuenteComprobada"]
            assert not re.search(r"CB-BACH-\d+|INCIDENCIAS\.md", json.dumps(document,ensure_ascii=False))
            ce_ids = {x["id"] for x in document["competenciasEspecificas"]}
            ids = [x["id"] for x in document["competenciasEspecificas"]]

            def provenance(node, texts):
                origin = node["procedencia"]
                assert origin["fuenteRef"] == source_id
                numbers = origin["paginas"]
                assert numbers and numbers == sorted(set(numbers)) and all(n in pages for n in numbers)
                published = compact(" ".join(pages[n] for n in numbers))
                for value,kind in texts:
                    if not any(compact(candidate) in published for candidate in original_candidates(value,code,kind)):
                        report["coverageDifferences"].append([code,node.get("id"),numbers,"procedencia"])
                    report["fragmentosProcedencia"] += 1

            for ce in document["competenciasEspecificas"]:
                provenance(ce, [(ce["enunciado"]["es"],"competencia")] + [(p,"descripcion") for p in ce.get("descripcion",{}).get("es",[])])
                for key in ce["descriptoresOperativosRefs"]:
                    if key in broad:
                        report["descriptorGroups"].append([code,ce["id"],key])
                    elif key not in valid:
                        report["descriptorAnomalies"].append([code,ce["id"],key])
            for dev in document["desarrollos"]:
                assert dev["curso"] in [x["curso"] for x in document["materia"]["cursos"]]
                for criterion in dev["criteriosEvaluacion"]:
                    provenance(criterion,[(criterion["texto"]["es"],"criterio")])
                    assert criterion["competenciaEspecificaRef"] in ce_ids and criterion["competenciaEspecificaRef"] == "ce-"+criterion["codigoOficial"].split(".")[0]
                    assert not criterion["saberesBasicosRefs"]
                    ids.append(criterion["id"])
                for saber in leaves(dev):
                    provenance(saber,[(saber["texto"]["es"],"saber")])
                    assert saber["codigoOficial"] is None
                    ids.append(saber["id"])
            assert len(ids)==len(set(ids)),code
            try:
                audit_area(document,bodies[published_title(document)],counts)
            except AssertionError as error:
                report["coverageDifferences"].append([code,str(error)])
            report["areas"].append({"materia": document["materia"]["nombre"]["es"], "competencias": len(ce_ids), "desarrollos": len(document["desarrollos"]), "criterios": sum(len(x["criteriosEvaluacion"]) for x in document["desarrollos"]), "saberes": sum(len(leaves(x)) for x in document["desarrollos"])})
    source_catalog = json.loads((ROOT / "sources/es-cb/normativa/catalogo.json").read_text(encoding="utf-8"))
    source_ids = {source["id"] for document in documents for source in document["fuentes"]}
    for source in source_catalog["documentos"]:
        if source["id"] in source_ids:
            assert hashlib.sha256((ROOT / "sources/es-cb/normativa" / source["archivo"]).read_bytes()).hexdigest() == source["sha256"]
    report["counts"] = dict(counts)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"materias":len(documents),"fragmentos":sum(counts.values()),"procedencia":report["fragmentosProcedencia"],**{key:len(report[key]) for key in ("schemaErrors","coverageDifferences","descriptorAnomalies","descriptorGroups")}},ensure_ascii=False))
    if report["schemaErrors"] or report["coverageDifferences"] or report["descriptorAnomalies"]:
        raise SystemExit(1)


BULLET = r"[-–—−‐‑•\x83]"
PUBLISHED = {"EF": [("forma de discriminación", "forma d discriminación")], "TINF": [("las características tanto de las suites", "las características tanto las suites"), ("como de las que están en la nube", "como las que están en la nube")]}

def original_candidates(value, code, kind):
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

def compact(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", normalize_unicode(value))).replace("\xad", "")

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
                if re.fullmatch(r"\s*(?:i|Pág\. \d+|\d+/(?:881|94|25|41)|\d{4}/\d+)\s*", line):
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
            if compact(line).casefold() == compact(name).casefold() and name not in positions:
                positions[name] = offset
        offset += len(line)
    assert set(positions) == set(names), set(names) - set(positions)
    return positions

def leaves(node: dict) -> list[dict]:
    return node["saberes"] if "saberes" in node else [item for part in node.get("apartados", node.get("bloquesSaberes", [])) for item in leaves(part)]

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

# Listas publicadas cotejadas visualmente y decisión editorial confirmada, por CE.
REF_VERSIONS = {'AA:1': [['CCL1', 'CCL2', 'CP1', 'STEM2', 'STEM4', 'CD3', 'CPSAA4', 'CC3', 'CEC4'],
          ['CCL1', 'CCL2', 'CP1', 'STEM2', 'STEM4', 'CD3', 'CPSAA4', 'CC3', 'CCEC4']],
 'AE:3': [['CCL1', 'CD2', 'CPSAA1.1', 'CPSAA2', 'CC1', 'CE1', 'CCE3'],
          ['CCL1', 'CD2', 'CPSAA1.1', 'CPSAA2', 'CC1', 'CE1', 'CCEC3']],
 'AE:4': [['CCL3', 'CD2', 'CPSAA3.1', 'CPAAA6', 'CC2', 'CC3', 'CE2', 'CE3', 'CCEC4.1', 'CCEC4.2'],
          ['CCL3', 'CD2', 'CPSAA3.1', 'CC2', 'CC3', 'CE2', 'CE3', 'CCEC4.1', 'CCEC4.2']],
 'BIO:1': [['CCL1', 'CCL2', 'CP1', 'STEM2', 'STEM4', 'CD3', 'CPSAA4', 'CC3', 'CEC4'],
           ['CCL1', 'CCL2', 'CP1', 'STEM2', 'STEM4', 'CD3', 'CPSAA4', 'CC3', 'CCEC3.2']],
 'CG:3': [['CCL1', 'CCL2', 'STEM2', 'STEM4', 'CD2', 'CPSAA2', 'CC4', 'CEC1'],
          ['CCL1', 'CCL2', 'STEM2', 'STEM4', 'CD2', 'CPSAA2', 'CC4', 'CCEC1']],
 'CG:5': [['CCL1', 'CCL2', 'STEM4', 'CD3', 'CPSAA4', 'CC1', 'CEC1'],
          ['CCL1', 'CCL2', 'STEM4', 'CD3', 'CPSAA4', 'CC1', 'CCEC1']],
 'CAU:4': [['STEM3', 'CD2', 'CD3', 'CPSAA5', 'CE3', 'CCE5', 'CCEC4.2'],
           ['STEM3', 'CD2', 'CD3', 'CPSAA5', 'CE3', 'CCEC4.1', 'CCEC4.2']],
 'DTAAPD:1': [['CCL1', 'CCL2', 'STEM2', 'CD1', 'CPSAA4', 'CC1', 'CCE1', 'CCE2'],
              ['CCL1', 'CCL2', 'STEM2', 'CD1', 'CPSAA4', 'CC1', 'CCEC1', 'CCEC2']],
 'DTAAPD:2': [['CCL1', 'STEM2', 'CPSAA1.1', 'CPSAA5', 'CCE3', 'CCE4', 'CCE5', 'CCE6'],
              ['CCL1', 'STEM2', 'CPSAA1.1', 'CPSAA5', 'CCEC3.1', 'CCEC3.2', 'CCEC4.1', 'CCEC4.2']],
 'DTAAPD:3': [['STEM4', 'CPSAA1.1', 'CPSAA5', 'CE3', 'CCE3', 'CCE4', 'CCE5', 'CCE6'],
              ['STEM4', 'CPSAA1.1', 'CPSAA5', 'CE3', 'CCEC3.1', 'CCEC3.2', 'CCEC4.1', 'CCEC4.2']],
 'DTAAPD:4': [['CCL2', 'STEM4', 'CD2', 'CPSAA5', 'CE3', 'CCE4', 'CCE5', 'CCE6'],
              ['CCL2', 'STEM4', 'CD2', 'CPSAA5', 'CE3', 'CCEC3.2', 'CCEC4.1', 'CCEC4.2']],
 'DTAAPD:5': [['STEM3', 'CD2', 'CD3', 'CPSAA5', 'CE3', 'CCE3', 'CCE5', 'CCE6'],
              ['STEM3', 'CD2', 'CD3', 'CPSAA5', 'CE3', 'CCEC3.1', 'CCEC4.1', 'CCEC4.2']],
 'DT:1': [['CCL1', 'CCL2', 'STEM4', 'CD1', 'CPSAA4', 'CC1', 'CEC1', 'CEC2'],
          ['CCL1', 'CCL2', 'STEM4', 'CD1', 'CPSAA4', 'CC1', 'CCEC1', 'CCEC2']],
 'DT:5': [['STEM2', 'STEM3', 'STEM4', 'CD1', 'CD2', 'CD3', 'CE3', 'CEC4'],
          ['STEM2', 'STEM3', 'STEM4', 'CD1', 'CD2', 'CD3', 'CE3', 'CCEC3.2']],
 'GEO:3': [['STEM1', 'STEM4', 'CPSAA3.1', 'CC1', 'CC3', 'CEC1'],
           ['STEM1', 'STEM4', 'CPSAA3.1', 'CC1', 'CC3', 'CCEC1']],
 'HE:6': [['STEM4', 'CPSAA1.1', 'CPSAA4', 'CC1', 'CC2', 'CC3', 'CEC1', 'CEC2'],
          ['STEM4', 'CPSAA1.1', 'CPSAA4', 'CC1', 'CC2', 'CC3', 'CCEC1', 'CCEC2']],
 'HE:7': [['CCL4', 'CPSAA1.1', 'CPSAA1.2', 'CPSAA3.1', 'CC2', 'CC3', 'CEC1', 'CEC2'],
          ['CCL4', 'CPSAA1.1', 'CPSAA1.2', 'CPSAA3.1', 'CC2', 'CC3', 'CCEC1', 'CCEC2']],
 'HMD:4': [['CCL2', 'CCEL3', 'STEM2', 'CD1', 'CD2', 'CPSAA4', 'CC1', 'CCEC1', 'CCEC2'],
           ['CCL2', 'CCL3', 'STEM2', 'CD1', 'CD2', 'CPSAA4', 'CC1', 'CCEC1', 'CCEC2']],
 'IS:1': [['CCL1', 'CP1', 'CD1', 'CD2', 'CPSAA1', 'CC1', 'CC3', 'CCEC1', 'CCEC5'],
          ['CCL1', 'CP1', 'CD1', 'CD2', 'CPSAA1', 'CC1', 'CC3', 'CCEC1']],
 'IS:2': [['CCL1', 'CP1', 'CD1', 'CD2', 'CPSAA1', 'CPSAA2', 'CC1', 'CC3', 'CCEC2', 'CCEC5'],
          ['CCL1', 'CP1', 'CD1', 'CD2', 'CPSAA1', 'CPSAA2', 'CC1', 'CC3', 'CCEC2']],
 'IS:3': [['CCL1', 'CP1', 'CD1', 'CD2', 'CPSAA1', 'CPSAA2', 'CC1', 'CC3', 'CCEC2', 'CCEC5'],
          ['CCL1', 'CP1', 'CD1', 'CD2', 'CPSAA1', 'CPSAA2', 'CC1', 'CC3', 'CCEC2']],
 'LAT:4': [['CCL3', 'CP3', 'CD1', 'CPSAA3', 'CC1'], ['CCL3', 'CP3', 'CD1', 'CPSAA3.1', 'CC1']],
 'PGD:3': [['CCL3', 'STEM3', 'CD1', 'CD5', 'CPSAA7', 'CE1'],
           ['CCL3', 'STEM3', 'CD1', 'CD5', 'CE1']],
 'PSI:1': [['CCL2', 'CCL3', 'STEM2', 'STEM4', 'CD1', 'CD2', 'CPSAA5', 'CPSAA6', 'CPSAA7'],
           ['CCL2', 'CCL3', 'STEM2', 'STEM4', 'CD1', 'CD2', 'CPSAA5']],
 'PSI:3': [['CCL1', 'STEM4', 'CD2', 'CPSAA6', 'CPSAA7', 'CE2', 'CE3'],
           ['CCL1', 'STEM4', 'CD2', 'CE2', 'CE3']],
 'PSI:4': [['CCL2', 'CPSAA1', 'CPSAA5', 'CPSAA6', 'CPSAA7', 'CC3', 'CC4'],
           ['CCL2', 'CPSAA1', 'CPSAA5', 'CC3', 'CC4']],
 'PSI:6': [['CCL5', 'CC1', 'CC3', 'CC5', 'CE1', 'CE3', 'CPSAA3', 'CPSAA4', 'CPSAA7'],
           ['CCL5', 'CC1', 'CC3', 'CE1', 'CE3', 'CPSAA3', 'CPSAA4']],
 'TEGP:4': [['STEM3', 'CPSAA1.1', 'CPSAA3.1', 'CPSAA3.2', 'CE3', 'CCE3', 'CCEC3.2', 'CCEC4.1'],
            ['STEM3', 'CPSAA1.1', 'CPSAA3.1', 'CPSAA3.2', 'CE3', 'CCEC3.1', 'CCEC3.2', 'CCEC4.1']],
 'TI:1': [['CCL1', 'STEM3', 'STEM4', 'CD1', 'CD2', 'CD5', 'CPSAA1', 'CE3'],
          ['CCL1', 'STEM3', 'STEM4', 'CD1', 'CD2', 'CD5', 'CPSAA1.1', 'CE3']]}


if __name__ == "__main__":
    main()
