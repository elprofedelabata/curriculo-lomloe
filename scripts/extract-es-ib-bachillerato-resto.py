"""Extrae las 28 materias restantes del anexo 1 de Bachillerato balear.

Uso: python scripts/extract-es-ib-bachillerato-resto.py [--write]

Reutiliza los controles de secciones, recuentos, procedencia y cobertura
textual de la tanda anterior. Los identificadores son internos.
"""

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path


sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location(
    "ib_bach_twenty", Path(__file__).with_name("extract-es-ib-bachillerato-20.py")
)
previous = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(previous)
raw_source_lines = previous.first.source_lines

# Nombre, páginas PDF inclusivas, slug, código interno, cursos, carácter.
AREAS = (
    ("Història de la Filosofia", 284, 293, "historia-de-la-filosofia",
     "HF", (2,), "obligatoria"),
    ("Història de la Música i de la Dansa", 294, 300,
     "historia-de-la-musica-i-de-la-dansa", "HMD", (2,), "modalidad"),
    ("Història de l’Art", 301, 311, "historia-de-l-art",
     "HA", (2,), "modalidad"),
    ("Història del Món Contemporani", 312, 326,
     "historia-del-mon-contemporani", "HMC", (1,), "modalidad"),
    ("Història i Cultura de les Illes Balears", 327, 331,
     "historia-i-cultura-de-les-illes-balears", "HCIB", (1,), "optativa"),
    ("Literatura Dramàtica", 332, 340, "literatura-dramatica",
     "LD", (2,), "modalidad"),
    ("Literatura Universal", 341, 349, "literatura-universal",
     "LU", (1,), "modalidad"),
    ("Llatí", 350, 366, "llati", "LL", (1, 2), "modalidad"),
    ("Llengua Castellana i Literatura", 367, 385,
     "llengua-castellana-i-literatura", "LCL", (1, 2), "obligatoria"),
    ("Llengua Catalana i Literatura", 386, 404,
     "llengua-catalana-i-literatura", "LCAT", (1, 2), "obligatoria"),
    ("Llengua Estrangera", 405, 435, "llengua-estrangera",
     "LE", (1, 2), "obligatoria"),
    ("Llenguatge i Pràctica Musical", 436, 441,
     "llenguatge-i-practica-musical", "LPM", (1,), "modalidad"),
    ("Matemàtiques", 442, 459, "matematiques", "MAT",
     (1, 2), "modalidad"),
    ("Matemàtiques Aplicades a les Ciències Socials", 460, 476,
     "matematiques-aplicades-a-les-ciencies-socials", "MACS",
     (1, 2), "modalidad"),
    ("Matemàtiques generals", 477, 487, "matematiques-generals",
     "MG", (1,), "modalidad"),
    ("Moviments Culturals i Artístics", 488, 498,
     "moviments-culturals-i-artistics", "MCA", (2,), "modalidad"),
    ("Programació i Tractament de Dades", 499, 506,
     "programacio-i-tractament-de-dades", "PTD", (1, 2), "optativa"),
    ("Projecte Empresarial", 507, 510,
     "projecte-empresarial", "PE", (2,), "optativa"),
    ("Projectes Artístics", 511, 517,
     "projectes-artistics", "PA", (1,), "modalidad"),
    ("Psicologia", 518, 526, "psicologia", "PSI",
     (2,), "optativa"),
    ("Química", 527, 535, "quimica", "QUI",
     (2,), "modalidad"),
    ("Segona Llengua Estrangera", 536, 570,
     "segona-llengua-estrangera", "SLE", (1, 2), "optativa"),
    ("Tècniques d’Expressió Gràficoplàstica", 571, 579,
     "tecniques-d-expressio-graficoplastica", "TEG",
     (2,), "modalidad"),
    ("Tècniques Experimentals", 579, 587,
     "tecniques-experimentals", "TE", (1,), "optativa"),
    ("Tecnologia i Enginyeria", 588, 602,
     "tecnologia-i-enginyeria", "TIE", (1, 2), "modalidad"),
    ("Treball d’Investigació, Anàlisi i Creativitat", 603, 605,
     "treball-d-investigacio-analisi-i-creativitat", "TIAC",
     (1,), "optativa"),
    ("Unió Europea", 606, 611,
     "unio-europea", "UE", (1,), "optativa"),
    ("Volum", 612, 619, "volum", "VOL", (1,), "modalidad"),
)


def source_lines(start, end):
    lines = raw_source_lines(start, end)
    if start == 571:
        end_index = next(
            index for index, (_, line) in enumerate(lines)
            if line == "Tècniques Experimentals"
        )
        lines = lines[:end_index]
        lines = [
            (page, "- " + line) if page == 578 and line.startswith(
                "Estratègies d’investigació, anàlisi, interpretació"
            ) else (page, line)
            for page, line in lines
        ]
    if start == 579:
        start_index = next(
            index for index, (_, line) in enumerate(lines)
            if line == "Tècniques Experimentals"
        )
        lines = lines[start_index:]
        joined = []
        for page, line in lines:
            if (
                joined and joined[-1][0] == page
                and joined[-1][1].endswith("-")
                and line and line[0].islower()
            ):
                previous_page, previous_line = joined[-1]
                joined[-1] = (previous_page, previous_line[:-1] + line)
            else:
                joined.append((page, line))
        lines = joined
        knowledge_index = next(
            index for index, (_, line) in enumerate(lines)
            if line == "Sabers bàsics"
        )
        # El texto anuncia bloques, pero la tabla solo enumera epígrafes
        # temáticos sin letras. Usamos un único bloque interno contenedor.
        lines.insert(knowledge_index + 2, (586, "A. Sabers bàsics"))
    # El decreto imprime esta única cabecera con punto final (p. 323).
    if start == 312:
        lines = [
            (page, "Sabers bàsics") if page == 323 and line == "Sabers bàsics."
            else (page, line)
            for page, line in lines
        ]
    # Fila de contenido independiente sin viñeta en la tabla (p. 310).
    if start == 301:
        lines = [
            (page, "- " + line) if page == 310 and line.startswith(
                "La dona com a artista. La lluita per la visibilitat"
            ) else (page, line)
            for page, line in lines
        ]
    return lines


previous.first.source_lines = source_lines
generic_parse_sections = previous.parse_sections


def parse_embedded_competencies(area):
    """CE publicadas solo dentro de la tabla de criterios, sin narración."""
    name, start, end, slug, code, courses, character = area
    lines = source_lines(start, end)
    criteria_index = next(
        index for index, (_, line) in enumerate(lines)
        if previous.base.heading(line, "criterios")
    )
    knowledge_index = next(
        index for index, (_, line) in enumerate(lines)
        if previous.base.heading(line, "saberes")
    )
    intro = previous.base.clean(" ".join(
        line for _, line in lines[1:criteria_index]
    ))
    competencies = []
    collecting = False
    descriptor_prefix = (
        "Aquesta competència específica es connecta amb els descriptors"
    )
    for page, line in lines[criteria_index + 1:knowledge_index]:
        match = re.match(r"^CE\s+([0-9]+)\s+(.+)$", line)
        if match:
            number, text = match.groups()
            if number != str(len(competencies) + 1):
                raise ValueError(f"{name}: secuencia CE inesperada: {number}")
            competencies.append({
                "id": f"ce-{number}",
                "codigoOficial": number,
                "enunciado": {"ca": text},
                "descriptoresOperativosRefs": [],
                "procedencia": {
                    "fuenteRef": previous.first.SOURCE_ID,
                    "paginas": [page],
                },
            })
            collecting = True
        elif line.startswith(descriptor_prefix):
            if not competencies:
                raise ValueError(f"{name}: descriptores sin competencia")
            refs = re.findall(r"\b[A-Z]{2,}[0-9]+(?:\.[0-9]+)?\b", line)
            competencies[-1]["descriptoresOperativosRefs"] = refs
            collecting = False
        elif re.match(r"^CA\s*[0-9]+\.[0-9]+", line):
            collecting = False
        elif collecting:
            item = competencies[-1]
            item["enunciado"]["ca"] += " " + line
            if page not in item["procedencia"]["paginas"]:
                item["procedencia"]["paginas"].append(page)
    for item in competencies:
        item["enunciado"]["ca"] = previous.base.clean(
            item["enunciado"]["ca"]
        )
        if not item["descriptoresOperativosRefs"]:
            raise ValueError(f"{name}: CE sin descriptores {item['id']}")
    criteria_segment = [
        entry for entry in lines[criteria_index:knowledge_index + 1]
        if not entry[1].startswith(descriptor_prefix)
    ]
    criteria, _ = previous.base.criteria(area, criteria_segment, 0)
    for item in criteria:
        item["id"] = (
            f"cri-{courses[0]}-{item['codigoOficial'].replace('.', '-')}"
        )
    knowledge_segment = lines[knowledge_index:]
    blocks, unclassified = previous.base.knowledge(
        area, knowledge_segment, 0
    )
    previous.check_knowledge_coverage(
        name, courses[0], knowledge_segment, blocks
    )
    unexpected = [
        (page, kind, text) for page, kind, text in unclassified
        if kind != "texto sin saber"
        or not text.startswith((
            "Es concreten", "Els sabers", "Les concrecions",
        ))
    ]
    if unexpected:
        raise ValueError(f"{name}: texto sin clasificar: {unexpected[:5]}")
    return intro, competencies, [{
        "curso": courses[0],
        "criteriosEvaluacion": criteria,
        "bloquesSaberes": blocks,
    }]


def parse_sections(area):
    if area[0] in (
        "Projecte Empresarial",
        "Treball d’Investigació, Anàlisi i Creativitat",
    ):
        return parse_embedded_competencies(area)
    return generic_parse_sections(area)


previous.parse_sections = parse_sections


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    docs = []
    errors = []
    for area in AREAS:
        try:
            doc = previous.build(area)
            if area[0] in (
                "Projecte Empresarial",
                "Treball d’Investigació, Anàlisi i Creativitat",
            ):
                doc["revision"]["notas"].append(
                    "El decreto publica las competencias dentro de Criteris d’avaluació, "
                    "sin un desarrollo narrativo separado; por eso se omite descripcion."
                )
            if area[0] == "Tècniques Experimentals":
                doc["revision"]["notas"].append(
                    "La letra A del bloque contenedor es interna: el decreto "
                    "presenta epígrafes temáticos sin letras de bloque."
                )
        except Exception as exc:
            errors.append((area[0], exc))
            print(area[0], "ERROR", repr(exc))
            continue
        counts = [
            (
                len(dev["criteriosEvaluacion"]),
                sum(
                    len(group["saberes"])
                    for block in dev["bloquesSaberes"]
                    for group in block.get("apartados") or [block]
                ),
            )
            for dev in doc["desarrollos"]
        ]
        docs.append(doc)
        print(area[0], "CE", len(doc["competenciasEspecificas"]),
              "CA/saberes", counts)
    if errors:
        raise ValueError(f"{len(errors)} materias requieren ajuste: {errors}")
    if args.write:
        previous.first.DEST.mkdir(parents=True, exist_ok=True)
        for doc in docs:
            slug = doc["id"].rsplit(".", 1)[-1]
            (previous.first.DEST / f"{slug}.json").write_text(
                json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                encoding="utf8",
            )
        print("Escritos", len(docs), "JSON")


if __name__ == "__main__":
    main()
