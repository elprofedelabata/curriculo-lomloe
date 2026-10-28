"""Extrae la primera tanda de materias de desarrollo único del Bachillerato balear.

Uso: python scripts/extract-es-ib-bachillerato.py [--write]

Los cursos y el carácter se toman de los artículos 14, 16 y 17 del decreto.
Las abreviaturas y los identificadores de saber son internos del proyecto.
"""

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "sources/es-ib/normativa/bachillerato/2025-08-01-decreto-43-2025-curriculo-bachillerato.pdf"
DEST = ROOT / "data/es-ib/bachillerato/materias"
SOURCE_ID = "boib-2025-103-decret-43-2025"
SOURCE_TITLE = (
    "Decret 43/2025, d’1 d’agost, pel qual s’estableixen l’ordenació "
    "i el currículum del batxillerat a les Illes Balears"
)
SOURCE_URL = "https://www.caib.es/eboibfront/eli/es-ib/d/2025/08/01/43/dof/cat/pdf"
VERIFY_URL = "https://www.caib.es/eboibfront/pdf/ca/2025/103/1197481"

SPEC = importlib.util.spec_from_file_location(
    "ib_eso_parser", Path(__file__).with_name("extract-es-ib-eso.py")
)
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)
base.SOURCE_ID = SOURCE_ID
base.SOURCE_TITLE = SOURCE_TITLE
base.SOURCE_URL = SOURCE_URL
base.VERIFY_URL = VERIFY_URL

# Nombre, páginas PDF inclusivas, slug, abreviatura, curso, carácter.
# Los títulos del anexo se cotejan antes de construir cada documento.
AREAS = (
    ("Activitat Física, Oci i Salut", 26, 31,
     "activitat-fisica-oci-i-salut", "AFOS", 2, "optativa"),
    ("Ampliació de Matemàtiques", 32, 39,
     "ampliacio-de-matematiques", "AM", 2, "optativa"),
    ("Biologia", 60, 68,
     "biologia", "BIO", 2, "modalidad"),
    ("Biologia, Geologia i Ciències Ambientals", 69, 78,
     "biologia-geologia-i-ciencies-ambientals", "BGCA", 1, "modalidad"),
    ("Ciències Generals", 79, 88,
     "ciencies-generals", "CG", 2, "modalidad"),
)


def source_lines(start, end):
    data = subprocess.check_output(
        ["pdftotext", "-f", str(start), "-l", str(end), "-raw",
         "-enc", "UTF-8", str(PDF), "-"],
        stderr=subprocess.DEVNULL,
    ).decode("utf8")
    result = []
    for page, text in enumerate(data.split("\f"), start):
        if page > end:
            break
        for line in text.splitlines():
            line = line.strip()
            if line and not line.startswith((
                "Núm. 103", "4 d’agost de 2025", "Fascicle 218",
                "https://www.caib.es/",
            )):
                result.append((page, line))
    return result


def build(area):
    name, start, end, slug, code, course, character = area
    lines = source_lines(start, end)
    if not lines or lines[0][1] != name:
        # La primera materia empieza por las dos cabeceras del anexo.
        if name != "Activitat Física, Oci i Salut" or [
            value for _, value in lines[:3]
        ] != ["ANNEX 1", "Matèries de batxillerat", name]:
            raise ValueError(f"{name}: cabecera inesperada en página {start}")
        lines = lines[2:]
    parser_area = (name, start, slug, code, (course,), character)
    intro, competencies, criterion_heading = base.introduction_and_competencies(
        parser_area, lines
    )
    if name == "Activitat Física, Oci i Salut":
        residual = "Les competències específiques de la matèria d’Educació Física"
        if intro.count(residual) != 1:
            raise ValueError(f"{name}: referencia residual inesperada")
        intro = intro.replace(
            residual,
            "Les competències específiques de la matèria d’Activitat Física, Oci i Salut",
        )
    criteria, knowledge_heading = base.criteria(
        parser_area, lines, criterion_heading
    )
    blocks, unclassified = base.knowledge(
        parser_area, lines, knowledge_heading
    )
    unexpected = [
        (page, kind, text) for page, kind, text in unclassified
        if kind != "texto sin saber"
        or not text.startswith(("Es concreten", "Els sabers", "Les concrecions"))
    ]
    if unexpected:
        raise ValueError(f"{name}: texto fuera de estructura: {unexpected[:5]}")
    for item in criteria:
        item["id"] = f"cri-{course}-{item['codigoOficial'].replace('.', '-')}"
    doc = {
        "$schema": "../../../../schemas/materia.schema.json",
        "schemaVersion": "0.4.0",
        "id": f"es-ib.bachillerato.{slug}",
        "territorio": "es-ib",
        "etapa": "bachillerato",
        "materia": {
            "codigo": code,
            "nombre": {"ca": name},
            "cursos": [{"curso": course, "caracter": character}],
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
            "cve": "1197481",
            "urlOficial": SOURCE_URL,
            "urlVerificacion": VERIFY_URL,
            "anexo": "1",
            "paginasMateria": {"desde": start, "hasta": end},
        }],
        "introduccion": {"ca": [intro]},
        "competenciasEspecificas": competencies,
        "desarrollos": [{
            "curso": course,
            "criteriosEvaluacion": criteria,
            "bloquesSaberes": blocks,
        }],
        "revision": {
            "estado": "borrador",
            "fuenteComprobada": True,
            "fechaUltimaRevision": "2026-10-28",
            "metodo": "Extracción del texto Unicode del PDF oficial y cotejo de estructura, recuentos y páginas.",
            "notas": [
                "Se conserva el texto publicado en catalán.",
                "La abreviatura, las letras de bloques sin código y los identificadores individuales de saber son internos, no oficiales.",
                "Las aclaraciones orientativas de los criterios se separan de su texto principal.",
                *(
                    ["Se corrige una referencia residual a Educació Física en la introducción de esta materia."]
                    if name == "Activitat Física, Oci i Salut" else []
                ),
            ],
        },
    }
    base.validate_document(doc)
    if len({item["codigoOficial"] for item in criteria}) != len(criteria):
        raise ValueError(f"{name}: códigos de criterio duplicados")
    return doc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    docs = []
    for area in AREAS:
        doc = build(area)
        saberes = sum(
            len(group["saberes"])
            for block in doc["desarrollos"][0]["bloquesSaberes"]
            for group in (block.get("apartados") or [block])
        )
        docs.append(doc)
        print(
            doc["materia"]["nombre"]["ca"],
            "CE", len(doc["competenciasEspecificas"]),
            "CA", len(doc["desarrollos"][0]["criteriosEvaluacion"]),
            "saberes", saberes,
        )
    if args.write:
        DEST.mkdir(parents=True, exist_ok=True)
        for doc in docs:
            slug = doc["id"].rsplit(".", 1)[-1]
            (DEST / f"{slug}.json").write_text(
                json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                encoding="utf8",
            )
        print("Escritos", len(docs), "JSON")


if __name__ == "__main__":
    main()
