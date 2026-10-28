"""Extrae veinte materias más del anexo 1 del Bachillerato balear.

Uso: python scripts/extract-es-ib-bachillerato-20.py [--write]

Las materias I/II comparten competencias específicas pero conservan por
separado sus criterios y saberes. El script exige la secuencia de secciones
publicada y falla si encuentra texto fuera de esa estructura.
"""

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path


sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location(
    "ib_bach_first", Path(__file__).with_name("extract-es-ib-bachillerato.py")
)
first = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(first)
base = first.base

# Nombre, páginas PDF inclusivas, slug, código interno, cursos, carácter.
AREAS = (
    ("Anàlisi Musical", 40, 50, "analisi-musical", "AMU", (1, 2), "modalidad"),
    ("Arts Escèniques", 51, 59, "arts-esceniques", "AE", (1, 2), "modalidad"),
    ("Cor i Tècnica Vocal", 89, 99, "cor-i-tecnica-vocal", "CTV", (1, 2), "modalidad"),
    ("Cultura Audiovisual", 100, 108, "cultura-audiovisual", "CAU", (1,), "modalidad"),
    ("Dibuix Artístic", 109, 124, "dibuix-artistic", "DA", (1, 2), "modalidad"),
    ("Dibuix Tècnic", 125, 134, "dibuix-tecnic", "DT", (1, 2), "modalidad"),
    ("Dibuix Tècnic Aplicat a les Arts Plàstiques i al Disseny", 135, 145,
     "dibuix-tecnic-aplicat-a-les-arts-plastiques-i-al-disseny", "DTAPD",
     (1, 2), "modalidad"),
    ("Disseny", 146, 156, "disseny", "DIS", (2,), "modalidad"),
    ("Economia", 157, 165, "economia", "ECO", (1,), "modalidad"),
    ("Economia, Emprenedoria i Activitat Empresarial", 166, 172,
     "economia-emprenedoria-i-activitat-empresarial", "EEAE",
     (1,), "modalidad"),
    ("Educació Física", 173, 182, "educacio-fisica", "EF", (1,), "obligatoria"),
    ("Empresa i Disseny de Models de Negoci", 183, 190,
     "empresa-i-disseny-de-models-de-negoci", "EDMN",
     (2,), "modalidad"),
    ("Filosofia", 191, 201, "filosofia", "FIL", (1,), "obligatoria"),
    ("Física", 202, 209, "fisica", "FIS", (2,), "modalidad"),
    ("Física i Química", 210, 218, "fisica-i-quimica", "FQ", (1,), "modalidad"),
    ("Fonaments Artístics", 219, 230, "fonaments-artistics", "FA",
     (2,), "modalidad"),
    ("Geografia", 231, 243, "geografia", "GEO", (2,), "modalidad"),
    ("Geologia i Ciències Ambientals", 244, 253,
     "geologia-i-ciencies-ambientals", "GCA", (2,), "modalidad"),
    ("Grec", 254, 269, "grec", "GRE", (1, 2), "modalidad"),
    ("Història d’Espanya", 270, 283, "historia-despanya", "HE",
     (2,), "obligatoria"),
)


def check_knowledge_coverage(name, course, segment, blocks):
    parts = []
    for block in blocks:
        parts.append(block["nombre"]["ca"])
        for group in block.get("apartados") or [block]:
            if group is not block:
                parts.append(group["nombre"]["ca"])
            parts.extend(item["texto"]["ca"] for item in group["saberes"])
    corpus = re.sub(r"\s+", "", " ".join(parts)).casefold()
    missing = []
    for page, line in segment[1:]:
        if base.heading(line, "saberes") or line == name + " II":
            continue
        if line.startswith((
            "Es concreten", "Els sabers", "Les concrecions",
            "Es distribueixen en blocs les concrecions dels sabers",
            "per a cada curs.",
            "seqüenciació per a cada curs.",
        )):
            continue
        fragment = re.sub(r"^\s*(?:[-–]\s+|[A-Z]\.\s+)", "", line)
        fragment = re.sub(r"\s+", "", fragment).casefold()
        if fragment and fragment not in corpus:
            missing.append((page, line))
    if missing:
        raise ValueError(
            f"{name} {course}: saberes sin cobertura textual: {missing[:8]}"
        )


def parse_sections(area):
    name, start, end, slug, code, courses, character = area
    lines = first.source_lines(start, end)
    if not lines or lines[0][1] != name:
        raise ValueError(f"{name}: cabecera inesperada en página {start}")
    markers = [
        (index, "criterios" if base.heading(line, "criterios") else "saberes")
        for index, (_, line) in enumerate(lines)
        if base.heading(line, "criterios") or base.heading(line, "saberes")
    ]
    expected = ["criterios", "saberes"] * len(courses)
    if [kind for _, kind in markers] != expected:
        raise ValueError(f"{name}: secciones inesperadas: {markers}")
    intro_end = markers[0][0]
    if len(courses) == 2:
        if lines[intro_end - 1][1] != name + " I":
            raise ValueError(f"{name}: falta cabecera de primer curso")
        intro_end -= 1
    intro_lines = lines[:intro_end] + [(lines[intro_end - 1][0], "Criteris d’avaluació")]
    parser_area = (name, start, slug, code, courses, character)
    intro, competencies, _ = base.introduction_and_competencies(
        parser_area, intro_lines
    )
    developments = []
    for position, course in enumerate(courses):
        criterion_start = markers[position * 2][0]
        knowledge_start = markers[position * 2 + 1][0]
        next_start = (
            markers[(position + 1) * 2][0]
            if position + 1 < len(courses) else len(lines)
        )
        if position > 0 and lines[criterion_start - 1][1] != name + " II":
            raise ValueError(f"{name}: falta cabecera de segundo curso")
        criteria_segment = lines[criterion_start:knowledge_start + 1]
        criteria, _ = base.criteria(parser_area, criteria_segment, 0)
        for item in criteria:
            item["id"] = f"cri-{course}-{item['codigoOficial'].replace('.', '-')}"
        knowledge_end = next_start - 1 if position + 1 < len(courses) else next_start
        knowledge_area = (name, start, slug, code, (course,), character)
        knowledge_segment = lines[knowledge_start:knowledge_end]
        if name == "Cor i Tècnica Vocal" and course == 2:
            knowledge_segment = [
                (page, "- " + line) if page == 99 and line.startswith(
                    "Gestió de l'ansietat escènica."
                ) else (page, line)
                for page, line in knowledge_segment
            ]
        if name == "Dibuix Tècnic" and course == 2:
            knowledge_segment = [
                (page, "- " + line) if line.startswith((
                    "Projectes en col·laboració.",
                    "Plans de muntatge senzills.",
                    "Aplicacions CAD.",
                )) else (page, line)
                for page, line in knowledge_segment
            ]
        if name == "Física":
            for index, (page, line) in enumerate(knowledge_segment):
                if page == 208 and line.startswith("Valoració de les aportacions"):
                    previous_page, previous_line = knowledge_segment[index - 1]
                    knowledge_segment[index - 1] = (
                        previous_page, previous_line + " " + line
                    )
                    del knowledge_segment[index]
                    break
        blocks, unclassified = base.knowledge(knowledge_area, knowledge_segment, 0)
        check_knowledge_coverage(name, course, knowledge_segment, blocks)
        unexpected = [
            (page, kind, text) for page, kind, text in unclassified
            if kind != "texto sin saber"
            or not text.startswith((
                "Es concreten", "Els sabers", "Les concrecions",
                "Es distribueixen en blocs les concrecions dels sabers",
                "per a cada curs.",
                "seqüenciació per a cada curs.",
            ))
        ]
        if unexpected:
            raise ValueError(
                f"{name} {course}: texto fuera de estructura: {unexpected[:5]}"
            )
        developments.append({
            "curso": course,
            "criteriosEvaluacion": criteria,
            "bloquesSaberes": blocks,
        })
    return intro, competencies, developments


SINGLETON_ROWS = {
    "Cor i Tècnica Vocal": (
        (2, "C", "Gestió de l'ansietat escènica."),
    ),
    "Dibuix Tècnic": (
        (2, "C", "Projectes en col·laboració."),
        (2, "C", "Plans de muntatge senzills."),
        (2, "D", "Aplicacions CAD."),
    ),
    "Història de l’Art": (
        (2, "C", "La dona com a artista."),
    ),
    "Tècniques d’Expressió Gràficoplàstica": (
        (2, "A", "Estratègies d’investigació,"),
    ),
}


def separate_singleton_rows(name, developments, code):
    """Da apartado propio a cada fila sin viñeta que contiene un único saber."""
    for course, block_code, prefix in SINGLETON_ROWS.get(name, ()):
        development, = [
            item for item in developments if item["curso"] == course
        ]
        block, = [
            item for item in development["bloquesSaberes"]
            if item["codigo"] == block_code
        ]
        containers = block.get("apartados") or [block]
        matches = [
            (container, saber)
            for container in containers
            for saber in container["saberes"]
            if saber["texto"]["ca"].startswith(prefix)
        ]
        if len(matches) != 1:
            raise ValueError(f"{name}: fila única inesperada: {prefix}")
        container, saber = matches[0]
        container["saberes"].remove(saber)
        if container is block:
            del block["saberes"]
            block["apartados"] = []
        elif not container["saberes"]:
            raise ValueError(f"{name}: apartado anterior vacío: {prefix}")
        apartados = block.setdefault("apartados", [])
        apartado_code = str(len(apartados) + 1)
        saber["id"] = f"{code}.{course}.{block_code}.{apartado_code}.01"
        apartados.append({
            "codigo": apartado_code,
            "nombre": {"ca": saber["texto"]["ca"]},
            "saberes": [saber],
        })


def build(area):
    name, start, end, slug, code, courses, character = area
    intro, competencies, developments = parse_sections(area)
    separate_singleton_rows(name, developments, code)
    doc = {
        "$schema": "../../../../schemas/materia.schema.json",
        "schemaVersion": "0.4.0",
        "id": f"es-ib.bachillerato.{slug}",
        "territorio": "es-ib",
        "etapa": "bachillerato",
        "materia": {
            "codigo": code,
            "nombre": {"ca": name},
            "cursos": [
                {"curso": course, "caracter": character} for course in courses
            ],
        },
        "vigencia": {
            "entradaEnVigor": "2025-08-05",
            "aplicableDesdeCurso": "2025/2026",
            "hasta": None,
            "estado": "vigente",
        },
        "fuentes": [{
            "id": first.SOURCE_ID,
            "tipo": "decreto",
            "titulo": first.SOURCE_TITLE,
            "publicacion": "Butlletí Oficial de les Illes Balears",
            "numero": "103",
            "fechaPublicacion": "2025-08-04",
            "cve": "1197481",
            "urlOficial": first.SOURCE_URL,
            "urlVerificacion": first.VERIFY_URL,
            "anexo": "1",
            "paginasMateria": {"desde": start, "hasta": end},
        }],
        "introduccion": {"ca": [intro]},
        "competenciasEspecificas": competencies,
        "desarrollos": developments,
        "revision": {
            "estado": "borrador",
            "fuenteComprobada": True,
            "fechaUltimaRevision": "2026-10-28",
            "metodo": "Extracción Unicode del PDF oficial, con control de secciones, recuentos y procedencia.",
            "notas": [
                "Se conserva el texto publicado en catalán.",
                "La abreviatura y los identificadores individuales de saber son internos, no oficiales.",
                "Las aclaraciones orientativas de los criterios se separan de su texto principal.",
                *(
                    ["Las filas sin viñeta con un solo saber se representan como apartados independientes; su numeración es interna."]
                    if name in SINGLETON_ROWS else []
                ),
                *(
                    ["Las competencias comunes se comparten entre los dos cursos; los criterios y saberes se conservan en desarrollos diferenciados."]
                    if len(courses) == 2 else []
                ),
            ],
        },
    }
    base.validate_document(doc)
    for development in developments:
        codes = [
            item["codigoOficial"]
            for item in development["criteriosEvaluacion"]
        ]
        if len(set(codes)) != len(codes):
            raise ValueError(
                f"{name} {development['curso']}: códigos de criterio repetidos"
            )
    return doc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    docs = []
    for area in AREAS:
        doc = build(area)
        counts = [
            (
                len(dev["criteriosEvaluacion"]),
                sum(
                    len(group["saberes"])
                    for block in dev["bloquesSaberes"]
                    for group in (block.get("apartados") or [block])
                ),
            )
            for dev in doc["desarrollos"]
        ]
        docs.append(doc)
        print(area[0], "CE", len(doc["competenciasEspecificas"]), "CA/saberes", counts)
    if args.write:
        first.DEST.mkdir(parents=True, exist_ok=True)
        for doc in docs:
            slug = doc["id"].rsplit(".", 1)[-1]
            (first.DEST / f"{slug}.json").write_text(
                json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                encoding="utf8",
            )
        print("Escritos", len(docs), "JSON")


if __name__ == "__main__":
    main()
