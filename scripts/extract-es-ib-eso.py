"""Extrae las materias de desarrollo único del anexo 2 del Decret 42/2025.

Uso: python scripts/extract-es-ib-eso.py [--write]

Las materias con tablas por varios cursos y las variantes se dejan para una
segunda fase: nunca se infiere un curso a partir de la posición de una viñeta.
"""

import argparse
import json
import re
import subprocess
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "sources/es-ib/normativa/eso/2025-08-01-decreto-42-2025-curriculo-eso.pdf"
DEST = ROOT / "data/es-ib/eso/materias"
SOURCE_ID = "boib-2025-103-decret-42-2025"
SOURCE_TITLE = (
    "Decret 42/2025, d’1 d’agost, pel qual s’estableixen l’ordenació i "
    "el currículum de l’educació secundària obligatòria a les Illes Balears"
)
SOURCE_URL = "https://www.caib.es/eboibfront/eli/es-ib/d/2025/08/01/42/dof/cat/pdf"
VERIFY_URL = "https://www.caib.es/eboibfront/pdf/ca/2025/103/1197479"

# Este inventario delimita las secciones; solo se escriben las entradas con curso.
# Nombre, página inicial, slug, abreviatura interna, curso(s), carácter.
AREAS = (
    ("Biologia i Geologia", 49, None, None, (), ""),
    ("Cooperació i Serveis a la Comunitat", 62, "cooperacio-i-serveis-a-la-comunitat", "CSC", (2,), "optativa"),
    ("Cultura Clàssica", 68, None, None, (), ""),
    ("Digitalització", 81, "digitalitzacio", "DIG", (4,), "optativa"),
    ("Economia i Emprenedoria", 87, None, None, (), ""),
    ("Educació en Valors Cívics i Ètics", 100, "educacio-en-valors-civics-i-etics", "EVCE", (4,), "obligatoria"),
    ("Educació Física", 108, None, None, (), ""),
    ("Educació Plàstica, Visual i Audiovisual", 122, None, None, (), ""),
    ("Entorns Digitals i Multimèdia", 133, "entorns-digitals-i-multimedia", "EDM", (1,), "optativa"),
    ("Expressió Artística", 137, "expressio-artistica", "EXP", (4,), "optativa"),
    ("Física i Química", 144, None, None, (), ""),
    ("Formació i Orientació Personal i Professional", 157, "formacio-i-orientacio-personal-i-professional", "FOPP", (4,), "optativa"),
    ("Geografia i Història", 165, None, None, (), ""),
    ("Igualtat de Gènere", 189, "igualtat-de-genere", "IG", (1, 2), "optativa"),
    ("Introducció a la Filosofia", 196, "introduccio-a-la-filosofia", "IF", (3,), "optativa"),
    ("Introducció a les tècniques experimentals", 204, "introduccio-a-les-tecniques-experimentals", "ITE", (3,), "optativa"),
    ("Llatí", 207, "llati", "LLAT", (4,), "optativa"),
    ("Llengua Castellana i Literatura", 215, None, None, (), ""),
    ("Llengua Catalana i Literatura", 237, None, None, (), ""),
    ("Llengua Estrangera", 258, None, None, (), ""),
    ("Matemàtiques", 294, None, None, (), ""),
    ("Música", 326, None, None, (), ""),
    ("Recursos Digitals", 337, None, None, (), ""),
    ("Segona Llengua Estrangera", 344, None, None, (), ""),
    ("Taller de Finances i Consum Responsable", 383, "taller-de-finances-i-consum-responsable", "TFCR", (3,), "optativa"),
    ("Tecnologia", 393, None, None, (), ""),
    ("Tecnologia i Digitalització", 403, None, None, (), ""),
)
SUBHEADING_PREFIXES = {
    "introduccio-a-la-filosofia": (
        "Filosofar.", "Antropologia.", "Realitat.", "Coneixement:",
        "Llenguatge:", "Ètica.", "Política.", "Feminisme.", "Estètica.",
    ),
}


def clean(value):
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"(?<=\w)- (?=\w)", "-", value)
    return unicodedata.normalize("NFC", value)


def source_lines():
    data = subprocess.check_output(
        ["pdftotext", "-f", "49", "-l", "413", "-raw", "-enc", "UTF-8", str(PDF), "-"],
        stderr=subprocess.DEVNULL,
    ).decode("utf8")
    lines = []
    for page_no, page in enumerate(data.split("\f"), 49):
        for line in page.splitlines():
            line = line.strip()
            if line and not line.startswith((
                "Núm. 103", "4 d’agost de 2025", "Fascicle 216",
                "https://www.caib.es/",
            )):
                lines.append((page_no, line))
    return lines


def section_lines(lines):
    indices = []
    for area in AREAS:
        name, page = area[:2]
        found = [i for i, (p, text) in enumerate(lines) if p == page and text == name]
        if len(found) != 1:
            raise ValueError(f"Cabecera no unívoca: {name}, página {page}: {found}")
        indices.append(found[0])
    result = []
    for n, area in enumerate(AREAS):
        end = indices[n + 1] if n + 1 < len(indices) else len(lines)
        result.append((area, lines[indices[n]:end]))
    return result


def heading(text, kind):
    if kind == "saberes":
        return bool(re.match(r"^Sabers? [Bb]àsics$", text) or text == "Saber Bàsics")
    return bool(re.match(r"^Criteris d.avaluació$", text))


def introduction_and_competencies(area, lines):
    name = area[0]
    ce_heading = next(i for i, (_, line) in enumerate(lines) if line == "Competències específiques")
    criteria_heading = next(
        i for i in range(ce_heading + 1, len(lines))
        if heading(lines[i][1], "criterios")
    )
    intro = clean(" ".join(line for _, line in lines[1:ce_heading]))
    if len(intro) < 100:
        raise ValueError(f"{name}: introducción demasiado breve")
    groups = []
    for page, line in lines[ce_heading + 1:criteria_heading]:
        if line in {
            "Primer i tercer curs", "Primer i segon curs", "Segon i tercer curs",
            "Tercer i quart curs", "Primer curs", "Segon curs", "Tercer curs",
            "Quart curs", "De primer a tercer", "Cultura Clàssica I",
            "Matemàtiques A",
        }:
            continue
        if re.match(r"^CE\s+[0-9]+\b", line):
            groups.append([])
        if groups:
            groups[-1].append((page, line))
    competencies = []
    for expected, group in enumerate(groups, 1):
        text = clean(" ".join(line for _, line in group))
        match = re.match(r"^CE\s+([0-9]+)\s+(.+)$", text)
        if not match or int(match.group(1)) != expected:
            raise ValueError(f"{name}: secuencia de competencias: {text[:120]}")
        body = match.group(2)
        descriptor = None
        for candidate in re.finditer(
            r"(?:Descriptors que es lliguen a aquesta competència específica:"
            r"|Aquesta competència específica es connecta amb els següents descriptors"
            r"(?: del perfil de sortida)?:)",
            body,
            flags=re.IGNORECASE,
        ):
            # Una frase editorial de Taller de Finances anuncia descriptores,
            # pero le sigue texto narrativo. No debe truncarse ese desarrollo.
            tail = body[candidate.end():].lstrip(": ")
            if re.fullmatch(r"[\sA-Z0-9.,;i]+", tail) and re.search(
                r"\b[A-Z]{2,}\s*[0-9]+", tail
            ):
                descriptor = (candidate.start(), tail)
        refs = []
        if descriptor:
            refs = list(dict.fromkeys(
                re.findall(
                    r"\b[A-Z]{2,}\s*[0-9]+(?:\.[0-9]+)?\b",
                    descriptor[1],
                )
            ))
            refs = [re.sub(r"\s+", "", ref) for ref in refs]
            body = body[:descriptor[0]].strip()
        special_ending = (
            "llenguatge de les imatges."
            if area[2] == "introduccio-a-la-filosofia" and expected == 5 else None
        )
        if special_ending:
            boundary = body.find(special_ending)
            if boundary < 0:
                raise ValueError(f"{name}: no se encuentra el final de CE 5")
            boundary += len(special_ending)
            enunciado, description = body[:boundary], body[boundary:].strip()
        else:
            parts = re.match(r"^(.+?\.)\s+(.+)$", body)
            if not parts:
                raise ValueError(f"{name}: competencia sin descripción: {body[:150]}")
            enunciado, description = parts.groups()
        if area[2] == "taller-de-finances-i-consum-responsable" and expected == 6:
            editorial = (
                "Aquesta competència específica es connecta amb els següents descriptors:"
            )
            if not description.startswith(editorial + " La transició ecològica"):
                raise ValueError(f"{name}: ha cambiado la frase editorial de CE 6")
            description = description.removeprefix(editorial).strip()
        if not description:
            raise ValueError(f"{name}: competencia sin desarrollo narrativo: CE {expected}")
        competencies.append({
            "id": f"ce-{expected}",
            "codigoOficial": str(expected),
            "enunciado": {"ca": enunciado},
            "descripcion": {"ca": [description]},
            "descriptoresOperativosRefs": refs,
            "procedencia": {
                "fuenteRef": SOURCE_ID,
                "paginas": sorted({page for page, _ in group}),
            },
        })
    if not competencies:
        raise ValueError(f"{name}: no se detectaron competencias")
    return intro, competencies, criteria_heading


def criteria(area, lines, first_heading):
    name = area[0]
    saber_heading = next(
        i for i in range(first_heading + 1, len(lines))
        if heading(lines[i][1], "saberes")
    )
    groups = []
    skipping_ce = False
    for page, line in lines[first_heading + 1:saber_heading]:
        if re.match(r"^CA\s*[0-9]+\.[0-9]+", line):
            groups.append([])
            skipping_ce = False
        elif re.match(r"^CE\s*[0-9]+\b", line):
            skipping_ce = True
            continue
        if groups and not skipping_ce and not heading(line, "criterios"):
            groups[-1].append((page, line))
    parsed = []
    for group in groups:
        first = group[0][1]
        match = re.match(r"^CA\s*([0-9]+)\.([0-9]+)\.?\s*(.*)$", first)
        if not match:
            raise ValueError(f"{name}: criterio ilegible: {first}")
        ce, number, start = match.groups()
        content = [(group[0][0], start)] + group[1:]
        main, guidance = [], []
        for page, line in content:
            if line.startswith(("- ", "– ")):
                guidance.append((page, line[2:]))
            elif guidance:
                old_page, old_text = guidance[-1]
                guidance[-1] = (old_page, clean(old_text + " " + line))
            else:
                main.append((page, line))
        if not main:
            raise ValueError(f"{name}: criterio sin texto: {ce}.{number}")
        item = {
            "codigoOficial": f"{ce}.{number}",
            "competenciaEspecificaRef": f"ce-{ce}",
            "texto": {"ca": clean(" ".join(text for _, text in main))},
            "saberesBasicosRefs": [],
            "procedencia": {
                "fuenteRef": SOURCE_ID,
                "paginas": sorted({page for page, _ in group}),
            },
        }
        if guidance:
            item["aclaraciones"] = {"ca": [clean(text) for _, text in guidance]}
        parsed.append(item)
    printed = sum(
        bool(re.match(r"^CA\s*[0-9]+\.[0-9]+", line))
        for _, line in lines[first_heading + 1:saber_heading]
    )
    if len(parsed) != printed or not parsed:
        raise ValueError(f"{name}: criterios extraídos {len(parsed)} != {printed}")
    return parsed, saber_heading


def is_block(line):
    if re.match(r"^[A-Z]\.\s+[A-ZÀ-Ü]", line):
        return True
    letters = [c for c in line if c.isalpha()]
    return (
        3 <= len(line) <= 105
        and len(letters) >= 3
        and all(c.isupper() for c in letters)
        and not re.search(r"\b(?:[1-4][rnt]|RDI|RDII)\b", line)
    )


def knowledge(area, lines, heading_index):
    name = area[0]
    blocks = []
    current = None
    saber = None
    pending_heading = []
    unclassified = []
    printed = 0
    for page, line in lines[heading_index + 1:]:
        if heading(line, "saberes"):
            continue
        if saber and re.fullmatch(r"[A-ZÀ-Ü0-9+\-]+\.", line) and not saber["texto"]["ca"].endswith("."):
            saber["texto"]["ca"] = clean(saber["texto"]["ca"] + " " + line)
            pages = saber["procedencia"]["paginas"]
            if page not in pages:
                pages.append(page)
            continue
        if is_block(line):
            if current is not None and saber is None and not current.get("saberes") and not current.get("apartados") and not pending_heading and not re.match(r"^[A-Z]\.\s+", line):
                current["nombre"]["ca"] += " " + line
                continue
            if re.match(r"^([A-Z])\.\s+(.+)$", line):
                code, title = re.match(r"^([A-Z])\.\s+(.+)$", line).groups()
            else:
                code, title = chr(65 + len(blocks)), line
            if blocks and code == blocks[-1]["codigo"]:
                raise ValueError(f"{name}: bloque repetido {line}")
            current = {"codigo": code, "nombre": {"ca": title}, "saberes": []}
            blocks.append(current)
            saber = None
            pending_heading = []
            continue
        if line.startswith(("- ", "– ")):
            printed += 1
            if current is None:
                raise ValueError(f"{name}: saber antes del primer bloque en página {page}: {line}")
            if pending_heading:
                if "saberes" in current:
                    if current["saberes"]:
                        raise ValueError(f"{name}: mezcla de saberes y apartados en {current['codigo']}")
                    del current["saberes"]
                    current["apartados"] = []
                current["apartados"].append({
                    "codigo": str(len(current["apartados"]) + 1),
                    "nombre": {"ca": clean(" ".join(pending_heading))},
                    "saberes": [],
                })
                pending_heading = []
            group = (
                current["apartados"][-1]["saberes"]
                if "apartados" in current else current["saberes"]
            )
            suffix = (
                f"{current['apartados'][-1]['codigo']}."
                if "apartados" in current else ""
            )
            saber = {
                "id": f"{area[3]}.{area[4][0]}.{current['codigo']}.{suffix}{len(group) + 1:02d}",
                "codigoOficial": None,
                "texto": {"ca": line[2:]},
                "procedencia": {"fuenteRef": SOURCE_ID, "paginas": [page]},
            }
            group.append(saber)
            continue
        if line.lower() in ("x", "x x") or re.fullmatch(r"(?:[1-4][rnt]\s*)+", line):
            unclassified.append((page, "marca de curso", line))
            continue
        if current and saber is None:
            pending_heading.append(line)
        elif current and "apartados" in current and saber and (
            any(line.startswith(prefix) for prefix in SUBHEADING_PREFIXES.get(area[2], ()))
            or (
                area[2] not in SUBHEADING_PREFIXES
                and saber["texto"]["ca"].endswith(".")
            )
        ):
            pending_heading.append(line)
            saber = None
        elif saber:
            saber["texto"]["ca"] = clean(saber["texto"]["ca"] + " " + line)
            pages = saber["procedencia"]["paginas"]
            if page not in pages:
                pages.append(page)
        else:
            unclassified.append((page, "texto sin saber", line))
    for block in blocks:
        groups = (
            [part["saberes"] for part in block["apartados"]]
            if "apartados" in block else [block["saberes"]]
        )
        if not any(groups):
            raise ValueError(f"{name}: bloque vacío {block['nombre']['ca']}")
        for group in groups:
            for item in group:
                item["texto"]["ca"] = clean(item["texto"]["ca"])
    if printed != sum(
        len(part["saberes"])
        for block in blocks
        for part in (block.get("apartados") or [block])
    ):
        raise ValueError(f"{name}: recuento de saberes inconsistente")
    if pending_heading:
        unclassified.append((lines[-1][0], "encabezado sin viñetas", clean(" ".join(pending_heading))))
    return blocks, unclassified


def document(area, lines):
    name, start, slug, code, courses, character = area
    intro, competencies, first_heading = introduction_and_competencies(area, lines)
    source_criteria, saber_heading = criteria(area, lines, first_heading)
    blocks, unclassified = knowledge(area, lines, saber_heading)
    unexpected = [
        (page, kind, text) for page, kind, text in unclassified
        if kind != "texto sin saber"
        or not text.startswith(("Es concreten", "Els sabers", "Les concrecions"))
    ]
    if unexpected:
        raise ValueError(f"{name}: texto fuera de la estructura: {unexpected[:5]}")
    developments = []
    for course in courses:
        developed_criteria = [{
            **item,
            "id": f"cri-{course}-{item['codigoOficial'].replace('.', '-')}",
        } for item in source_criteria]
        developed_blocks = json.loads(json.dumps(blocks, ensure_ascii=False))
        for block in developed_blocks:
            for part in block.get("apartados") or [block]:
                for item in part["saberes"]:
                    item["id"] = item["id"].replace(f".{courses[0]}.", f".{course}.", 1)
        developments.append({
            "curso": course,
            "criteriosEvaluacion": developed_criteria,
            "bloquesSaberes": developed_blocks,
        })
    return {
        "$schema": "../../../../schemas/materia.schema.json",
        "schemaVersion": "0.4.0",
        "id": f"es-ib.eso.{slug}",
        "territorio": "es-ib",
        "etapa": "eso",
        "materia": {
            "codigo": code,
            "nombre": {"ca": name},
            "cursos": [{"curso": course, "caracter": character} for course in courses],
        },
        "vigencia": {
            "entradaEnVigor": "2025-08-05",
            "aplicableDesdeCurso": "2025/2026",
            "hasta": None,
            "estado": "vigente",
        },
        "fuentes": [{
            "id": SOURCE_ID,
            "tipo": "decreto",
            "titulo": SOURCE_TITLE,
            "publicacion": "Butlletí Oficial de les Illes Balears",
            "numero": "103",
            "fechaPublicacion": "2025-08-04",
            "cve": "1197479",
            "urlOficial": SOURCE_URL,
            "urlVerificacion": VERIFY_URL,
            "anexo": "2",
            "paginasMateria": {"desde": start, "hasta": lines[-1][0]},
        }],
        "introduccion": {"ca": [intro]},
        "competenciasEspecificas": competencies,
        "desarrollos": developments,
        "revision": {
            "estado": "borrador",
            "fuenteComprobada": True,
            "fechaUltimaRevision": "2026-10-27",
            "metodo": "Extracción del texto Unicode del PDF oficial, con controles de recuento y cotejo selectivo.",
            "notas": [
                "Se conserva el texto publicado en catalán.",
                "La abreviatura de materia, las letras asignadas a bloques sin código y los identificadores de saber son internos del proyecto, no códigos oficiales.",
                "Las aclaraciones orientativas se separan del criterio de evaluación.",
                *(
                    ["El desarrollo común de esta optativa se replica en primero y segundo para facilitar la consulta; el decreto no establece una secuenciación distinta."]
                    if len(courses) > 1 else []
                ),
            ],
        },
    }, unclassified


def validate_document(doc):
    """Comprueba referencias e identificadores antes de publicar cada borrador."""
    competencies = {item["id"] for item in doc["competenciasEspecificas"]}
    if len(competencies) != len(doc["competenciasEspecificas"]):
        raise ValueError(f"{doc['id']}: competencias duplicadas")
    source = doc["fuentes"][0]
    first = source["paginasMateria"]["desde"]
    last = source["paginasMateria"]["hasta"]
    all_items = list(doc["competenciasEspecificas"])
    for development in doc["desarrollos"]:
        criteria = development["criteriosEvaluacion"]
        if len({item["id"] for item in criteria}) != len(criteria):
            raise ValueError(f"{doc['id']}: criterios duplicados")
        for criterion in criteria:
            if criterion["competenciaEspecificaRef"] not in competencies:
                raise ValueError(f"{doc['id']}: CE inexistente en {criterion['id']}")
        knowledge = [
            item
            for block in development["bloquesSaberes"]
            for group in (block.get("apartados") or [block])
            for item in group["saberes"]
        ]
        if len({item["id"] for item in knowledge}) != len(knowledge):
            raise ValueError(f"{doc['id']}: saberes duplicados")
        all_items.extend(criteria)
        all_items.extend(knowledge)
    for item in all_items:
        origin = item["procedencia"]
        if origin["fuenteRef"] != SOURCE_ID or not origin["paginas"]:
            raise ValueError(f"{doc['id']}: procedencia incompleta")
        if any(not first <= page <= last for page in origin["paginas"]):
            raise ValueError(f"{doc['id']}: página fuera de la materia")
    if "\ufffd" in json.dumps(doc, ensure_ascii=False):
        raise ValueError(f"{doc['id']}: carácter Unicode de sustitución")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    lines = source_lines()
    results = []
    for area, section in section_lines(lines):
        if not area[2]:
            continue
        doc, unclassified = document(area, section)
        validate_document(doc)
        results.append((area[2], doc))
        print(
            area[2], "CE", len(doc["competenciasEspecificas"]),
            "CA", len(doc["desarrollos"][0]["criteriosEvaluacion"]),
            "saberes", sum(
                len(part["saberes"])
                for block in doc["desarrollos"][0]["bloquesSaberes"]
                for part in block.get("apartados") or [block]
            ),
            "texto no clasificado", len(unclassified),
        )
    if args.write:
        DEST.mkdir(parents=True, exist_ok=True)
        for slug, item in results:
            (DEST / f"{slug}.json").write_text(
                json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
            )
        print("Escritos", len(results), "JSON en", DEST)


if __name__ == "__main__":
    main()
