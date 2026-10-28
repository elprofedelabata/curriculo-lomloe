"""Extrae los dos ámbitos comunes de CFGB publicados en el portal balear.

Uso: python scripts/extract-es-ib-cfgb.py [--write]
Los PDF no secuencian los criterios ni los saberes por curso. El desarrollo
común se replica para I y II como representación interna, no como atribución
de curso a la fuente.
"""

import argparse
import copy
import json
import re
import subprocess
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "sources/es-ib/normativa/cfgb"
DEST = ROOT / "data/es-ib/cfgb/materias"
SPEC = (
    ("ciències-aplicades", "ciencies-aplicades", "CA",
     "curriculo-ciencias-aplicadas.pdf", 16,
     "es-ib-cfgb-ciencies-aplicades-portal", "505705"),
    ("comunicació-i-ciències-socials", "comunicacio-i-ciencies-socials",
     "CCS", "curriculo-comunicacion-ciencias-sociales.pdf", 21,
     "es-ib-cfgb-comunicacio-ciencies-socials-portal", "505692"),
)
PORTAL = "https://www.caib.es/sites/comunitatdocent/ca/curraculums_transversals"
DECREE_URL = "https://www.caib.es/eboibfront/eli/es-ib/d/2025/08/01/39/dof/cat/pdf"
DESCRIPTOR_INTRO = (
    "Aquesta competència específica es connecta amb els descriptors del "
    "Perfil de sortida següents:"
)


def clean(text):
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"(?<=\w)- (?=\w)", "-", text)
    return unicodedata.normalize("NFC", text)


def pages(pdf):
    raw = subprocess.check_output(
        ["pdftotext", "-raw", "-enc", "UTF-8", str(pdf), "-"]
    ).decode("utf8")
    output = []
    for number, page in enumerate(raw.split("\f"), 1):
        if not page.strip():
            continue
        lines = []
        for original in page.splitlines():
            line = original.strip()
            if not line or line.startswith((
                "C. del Ter, 16", "07009 Palma", "Tel. 971", "educacio.caib.es"
            )) or re.fullmatch(r"\d{1,2}", line):
                continue
            lines.append((number, line))
        output.extend(lines)
    return output


def provenance(source_id, group):
    return {
        "fuenteRef": source_id,
        "paginas": sorted({page for page, _ in group}),
    }


def parse_competencies(group, source_id, slug):
    starts = [
        index for index, (_, line) in enumerate(group)
        if re.match(r"^[1-8]\.\s+\S", line)
    ]
    if len(starts) != 8:
        raise ValueError(f"{slug}: se esperaban ocho competencias, hay {len(starts)}")
    result = []
    anomalies = []
    for expected, start in enumerate(starts, 1):
        part = group[start:starts[expected] if expected < 8 else len(group)]
        first = re.match(r"^([1-8])\.\s+(.+)$", part[0][1])
        if int(first.group(1)) != expected:
            raise ValueError(f"{slug}: orden de competencias alterado: {first.group(1)}")
        body = clean(" ".join([first.group(2)] + [text for _, text in part[1:]]))
        if expected == 8 and slug == "comunicacio-i-ciencies-socials":
            bad = "9. " + DESCRIPTOR_INTRO
            if bad not in body:
                raise ValueError("CCS: no se encuentra la numeración 9 anómala")
            body = body.replace(bad, DESCRIPTOR_INTRO, 1)
            anomalies.append("La fuente numera como 9 la frase de descriptores de CE 8.")
        if body.count(DESCRIPTOR_INTRO) != 1:
            raise ValueError(f"{slug}: descriptores de CE {expected} no unívocos")
        narrative, descriptors = body.split(DESCRIPTOR_INTRO)
        match = re.match(r"^(.+?\.)\s+(.+)$", narrative.strip())
        if not match:
            raise ValueError(f"{slug}: CE {expected} sin enunciado y descripción")
        refs = re.findall(r"\b[A-Z]{2,6}[0-9]+(?:\.[0-9]+)?\b", descriptors)
        if not refs or len(refs) != len(set(refs)):
            raise ValueError(f"{slug}: descriptores de CE {expected} ilegibles")
        if expected == 4 and slug == "comunicacio-i-ciencies-socials":
            if "CL3" not in refs:
                raise ValueError("CCS: no se encuentra la errata CL3 de CE 4")
            refs = ["CCL3" if ref == "CL3" else ref for ref in refs]
            anomalies.append("Se normaliza CL3 a CCL3 en los descriptores de CE 4.")
        result.append({
            "id": f"ce-{expected}",
            "codigoOficial": str(expected),
            "enunciado": {"ca": match.group(1)},
            "descripcion": {"ca": [match.group(2)]},
            "descriptoresOperativosRefs": refs,
            "procedencia": provenance(source_id, part),
        })
    return result, anomalies


def parse_criteria(group, source_id, slug):
    current_ce = None
    parts = []
    for page, line in group:
        heading = re.fullmatch(r"Competència específica ([1-8])", line)
        if heading:
            current_ce = int(heading.group(1))
            continue
        match = re.match(r"^([1-8])\.([0-9]+)\.\s+(.+)$", line)
        if match:
            if current_ce != int(match.group(1)):
                raise ValueError(f"{slug}: criterio fuera de CE {current_ce}: {line}")
            parts.append([(page, line)])
        elif parts:
            parts[-1].append((page, line))
        else:
            raise ValueError(f"{slug}: texto anterior al primer criterio: {line}")
    result = []
    for part in parts:
        match = re.match(r"^([1-8])\.([0-9]+)\.\s+(.+)$", part[0][1])
        ce, number, first = match.groups()
        text = clean(" ".join([first] + [line for _, line in part[1:]]))
        result.append({
            "id": f"cri-1-{ce}-{number}",
            "codigoOficial": f"{ce}.{number}",
            "competenciaEspecificaRef": f"ce-{ce}",
            "texto": {"ca": text},
            "saberesBasicosRefs": [],
            "procedencia": provenance(source_id, part),
        })
    if not result or len({item["codigoOficial"] for item in result}) != len(result):
        raise ValueError(f"{slug}: criterios vacíos o duplicados")
    return result


def parse_knowledge(group, source_id, code, slug):
    blocks = []
    current = None
    part = None
    current_saber = None
    count = 0
    for page, line in group:
        heading = re.match(r"^([A-K])\.\s+(.+)$", line)
        subheading = re.match(r"^([1-4])\.\s+(.+)$", line)
        if heading:
            letter, title = heading.groups()
            if letter != chr(65 + len(blocks)):
                raise ValueError(f"{slug}: orden de bloques: {letter}")
            current = {"codigo": letter, "nombre": {"ca": title}}
            if slug == "comunicacio-i-ciencies-socials" and letter in ("B", "C"):
                current["apartados"] = []
            else:
                current["saberes"] = []
            blocks.append(current)
            current_saber = None
            part = None
        elif subheading and current and "apartados" in current:
            number, title = subheading.groups()
            if int(number) != len(current["apartados"]) + 1:
                raise ValueError(f"{slug}: orden de apartados: {line}")
            part = {"codigo": number, "nombre": {"ca": title}, "saberes": []}
            current["apartados"].append(part)
            current_saber = None
        elif line.startswith(("— ", "– ", "- ")):
            if not current:
                raise ValueError(f"{slug}: saber sin bloque: {line}")
            target = part["saberes"] if part else current.get("saberes")
            if target is None:
                raise ValueError(f"{slug}: saber sin apartado: {line}")
            prefix = f"{part['codigo']}." if part else ""
            current_saber = {
                "id": f"{code}.1.{current['codigo']}.{prefix}{len(target)+1:02d}",
                "codigoOficial": None,
                "texto": {"ca": line[2:]},
                "procedencia": {"fuenteRef": source_id, "paginas": [page]},
            }
            target.append(current_saber)
            count += 1
        elif part and current_saber is None:
            part["nombre"]["ca"] = clean(part["nombre"]["ca"] + " " + line)
        elif current_saber:
            current_saber["texto"]["ca"] += " " + line
            if page not in current_saber["procedencia"]["paginas"]:
                current_saber["procedencia"]["paginas"].append(page)
        else:
            raise ValueError(f"{slug}: texto no clasificado en saberes: {line}")
    for block in blocks:
        groups = [part["saberes"] for part in block["apartados"]] if "apartados" in block else [block["saberes"]]
        if not groups or not all(groups):
            raise ValueError(f"{slug}: bloque o apartado vacío: {block['codigo']}")
        for items in groups:
            for saber in items:
                saber["texto"]["ca"] = clean(saber["texto"]["ca"])
    if not blocks or count < 20:
        raise ValueError(f"{slug}: faltan bloques o saberes")
    return blocks, count


def build(spec):
    name, slug, code, filename, last_page, source_id, remote_id = spec
    lines = pages(SOURCE_DIR / filename)
    if max(page for page, _ in lines) != last_page:
        raise ValueError(f"{slug}: número de páginas distinto de {last_page}")
    # Los títulos originales usan capitalización editorial, no title case.
    title = lines[0][1]
    if not title.startswith("Currículum de l’àmbit de ") or name.split("-")[0].title() not in title:
        raise ValueError(f"{slug}: título inesperado: {title}")
    indices = {}
    for key, heading in (
        ("ce", "Competències específiques"),
        ("criteria", "Criteris d’avaluació"),
        ("sabers", "Sabers bàsics"),
    ):
        hits = [i for i, (_, line) in enumerate(lines) if line == heading]
        if len(hits) != 1:
            raise ValueError(f"{slug}: encabezado {heading}: {hits}")
        indices[key] = hits[0]
    if not (0 < indices["ce"] < indices["criteria"] < indices["sabers"]):
        raise ValueError(f"{slug}: secciones desordenadas")
    intro = clean(" ".join(line for _, line in lines[1:indices["ce"]]))
    competencies, anomalies = parse_competencies(
        lines[indices["ce"]+1:indices["criteria"]], source_id, slug
    )
    criteria = parse_criteria(
        lines[indices["criteria"]+1:indices["sabers"]], source_id, slug
    )
    blocks, saber_count = parse_knowledge(
        lines[indices["sabers"]+1:], source_id, code, slug
    )
    if len(intro) < 500:
        raise ValueError(f"{slug}: introducción demasiado breve")
    source_url = (
        "https://www.caib.es/sites/comunitatdocent/ca/archivopub.do"
        f"?ctrl=MCRST16306ZI{remote_id}&id={remote_id}"
    )
    document = {
        "$schema": "../../../../schemas/materia.schema.json",
        "schemaVersion": "0.4.0",
        "id": f"es-ib.cfgb.{slug}",
        "territorio": "es-ib",
        "etapa": "cfgb",
        "materia": {
            "codigo": code,
            "nombre": {"ca": title.removeprefix("Currículum de l’àmbit de ")},
            "cursos": [
                {"curso": 1, "caracter": "ambito"},
                {"curso": 2, "caracter": "ambito"},
            ],
        },
        "vigencia": {
            "entradaEnVigor": None,
            "aplicableDesdeCurso": None,
            "hasta": None,
            "estado": "vigente",
        },
        "fuentes": [
            {
                "id": source_id,
                "tipo": "otro",
                "titulo": title,
                "publicacion": "Portal institucional de la Direcció General de Formació Professional i Ordenació Educativa",
                "urlOficial": source_url,
                "urlVerificacion": PORTAL,
                "paginasMateria": {"desde": 1, "hasta": last_page},
            },
            {
                "id": "es-ib-cfgb-decret-39-2025",
                "tipo": "decreto",
                "titulo": "Decret 39/2025, d’1 d’agost, d’ordenació de la formació professional a les Illes Balears",
                "publicacion": "Butlletí Oficial de les Illes Balears",
                "numero": "104",
                "fechaPublicacion": "2025-08-05",
                "cve": "1197491",
                "urlOficial": DECREE_URL,
                "urlVerificacion": "https://www.caib.es/eboibfront/pdf/ca/2025/104/1197491",
            },
        ],
        "introduccion": {"ca": [intro]},
        "competenciasEspecificas": competencies,
        "desarrollos": [],
        "revision": {
            "estado": "borrador",
            "fuenteComprobada": True,
            "fechaUltimaRevision": "2026-10-28",
            "metodo": "Extracción estructurada de PDF oficial del portal institucional, con cotejo de encabezados, recuentos y páginas; pendiente de revisión humana.",
            "notas": [
                "El PDF del portal no es un decreto curricular publicado en el BOIB; el Decret 39/2025 regula la organización de los ámbitos, no el detalle de sus competencias, criterios y saberes.",
                "El propio portal indica que su información es orientativa y que, en caso de discrepancia, prevalece la normativa vigente.",
                "El documento no secuencia criterios ni saberes por 1.º y 2.º. Se replica el desarrollo común en ambos cursos como representación interna, sin atribuirles una división oficial.",
                "Las abreviaturas de ámbito y los identificadores individuales de saber son internos, no códigos oficiales.",
                "No se consigna fecha de entrada en vigor ni curso inicial de aplicación para este PDF institucional porque no aparecen en él.",
            ],
        },
    }
    for course in (1, 2):
        course_criteria = copy.deepcopy(criteria)
        course_blocks = copy.deepcopy(blocks)
        for item in course_criteria:
            item["id"] = item["id"].replace("cri-1-", f"cri-{course}-", 1)
        for block in course_blocks:
            for item in (
                [s for part in block["apartados"] for s in part["saberes"]]
                if "apartados" in block else block["saberes"]
            ):
                item["id"] = item["id"].replace(f"{code}.1.", f"{code}.{course}.", 1)
        document["desarrollos"].append({
            "curso": course,
            "criteriosEvaluacion": course_criteria,
            "bloquesSaberes": course_blocks,
        })
    return document, len(criteria), saber_count, anomalies


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    options = parser.parse_args()
    for spec in SPEC:
        document, criteria, sabers, anomalies = build(spec)
        print(f"{spec[1]}: 8 CE, {criteria} criterios, {sabers} saberes, "
              f"{len(document['desarrollos'][0]['bloquesSaberes'])} bloques")
        for anomaly in anomalies:
            print(f"  AVISO: {anomaly}")
        if options.write:
            DEST.mkdir(parents=True, exist_ok=True)
            (DEST / f"{spec[1]}.json").write_text(
                json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                encoding="utf8",
            )


if __name__ == "__main__":
    main()
