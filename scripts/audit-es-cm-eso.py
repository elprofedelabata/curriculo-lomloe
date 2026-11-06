"""Coteja los currículos de ESO de Castilla-La Mancha con Poppler y el esquema."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from bisect import bisect_left, bisect_right
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NORMATIVE = ROOT / "sources/es-cm/normativa"
BASE = "es-cm-eso-cfgb-decreto-82-2022"
ERRATA = "es-cm-eso-cfgb-correccion-decreto-82-2022"
DATA = ROOT / "data/es-cm/eso/materias"
AREAS = (
    ("artes-escenicas-danza-y-folclore", "Artes Escénicas, Danza y Folclore", 5, ((4, "", 12, 19),)),
    ("biologia-y-geologia", "Biología y Geología", 6, ((1, "Cursos de primero a tercero", 19, 43),
                                                     (4, "Cuarto curso", 15, 30))),
    ("cultura-cientifica", "Cultura Científica", 5, ((4, "", 15, 21),)),
    ("cultura-clasica", "Cultura Clásica", 5, ((2, "2º de ESO", 11, 20), (4, "4º de ESO", 14, 23))),
)


def raw_pages(pdf: Path, first: int, last: int) -> list[str]:
    text = subprocess.check_output(
        ["pdftotext", "-layout", "-enc", "UTF-8", "-f", str(first), "-l", str(last), str(pdf), "-"],
        text=True, encoding="utf-8",
    )
    pages = text.split("\f")
    assert len(pages) == last - first + 2 and not pages[-1].strip()
    return pages[:-1]


def compact(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", text))


class Source:
    def __init__(self, pages: list[str], first: int) -> None:
        self.ends = []
        self.first = first
        parts = []
        end = 0
        for page in pages:
            body = re.sub(r"(?m)^\s*AÑO [IVXLCDM]+\s+Núm\.\s+\d+[^\n]*", "", page)
            body = compact(re.sub(r"(?m)^\s*[-−–]\s+", "- ", body))
            parts.append(body)
            end += len(body)
            self.ends.append(end)
        self.text = "".join(parts)
        self.position = 0

    def take(self, value: str) -> None:
        target = compact(value)
        actual = self.text[self.position:self.position + len(target)]
        if actual != target:
            mismatch = next((i for i, (a, b) in enumerate(zip(actual, target)) if a != b), len(actual))
            left, right = max(0, mismatch - 20), mismatch + 70
            raise AssertionError((self.first + bisect_right(self.ends, self.position + mismatch),
                                  target[left:right], self.text[self.position + left:self.position + right]))
        self.position += len(target)

    def heading(self, label: str) -> None:
        self.take(label)
        if self.text[self.position:self.position + 1] in (".", ":"):
            self.position += 1

    def prefix(self, pattern: str) -> str:
        match = re.match(pattern, self.text[self.position:], flags=re.I)
        assert match, (pattern, self.text[self.position:self.position + 130])
        self.position += len(match[0])
        return match[0]

    def pages_since(self, start: int) -> list[int]:
        return list(range(self.first + bisect_right(self.ends, start),
                          self.first + bisect_left(self.ends, self.position) + 1))

    def check_origin(self, item: dict, start: int, source_id: str = BASE) -> None:
        assert item["procedencia"] == {"fuenteRef": source_id, "paginas": self.pages_since(start)}, item["id"]


def verify_biology_shared(document: dict) -> None:
    first, third, fourth = document["desarrollos"]
    assert [first["curso"], third["curso"], fourth["curso"]] == [1, 3, 4]
    for key in ("criteriosEvaluacion", "bloquesSaberes"):
        source = json.dumps(first[key], ensure_ascii=False)
        source = source.replace('"cri-1-', '"cri-3-').replace('"BYG.1.', '"BYG.3.')
        assert json.loads(source) == third[key]


def verify(source: Source, document: dict, config: tuple, valid_codes: set[str], errata: str) -> tuple[int, int]:
    slug, name, ce_count, groups = config
    start_area = source.position
    source.heading(name)
    for paragraph in document["introduccion"]["es"]:
        if slug == "biologia-y-geologia" and "«Cuerpo Humano», «Hábitos saludables» y «Salud y enfermedad»" in paragraph:
            assert "«CuerpoHumano»,«Hábitossaludables»y«Saludyenfermedad»" in errata
            paragraph = paragraph.replace("«Cuerpo Humano», «Hábitos saludables» y «Salud y enfermedad»",
                                          "«Cuerpo Humano» y «Hábitos saludables»")
        source.take(paragraph)
    source.heading("Competencias específicas")
    assert [ce["codigoOficial"] for ce in document["competenciasEspecificas"]] == [str(i) for i in range(1, ce_count + 1)]
    corrections = {
        1: ("CCL1, CCL2, CC3, CPSAA4, CCEC1, CCEC2", "CCL1, CCL2, CC3, CCEC1, CCEC2"),
        2: ("CCL1, CC1, CE1, CCEC1, CCEC2, CCEC3", "CCL1, CC1, CCEC1, CCEC2, CCEC3"),
        4: ("CCEC3, CCEC4", "CCEC4, CCEC5"),
        5: ("CCL5, CD2, CD3, CE2, CPSAA4, CPSAA5, CCEC3, CCEC4", "CCL5, CD2, CD3, CCEC5, CCEC6"),
    }
    descriptors = 0
    for ce in document["competenciasEspecificas"]:
        start = source.position
        number = int(ce["codigoOficial"])
        source.take(f'{number}. {ce["enunciado"]["es"]}')
        for paragraph in ce["descripcion"]["es"]:
            source.take(paragraph)
        codes = ce["descriptoresOperativosRefs"]
        assert set(codes) <= valid_codes, codes
        descriptors += len(codes)
        refs = ", ".join(codes)
        if slug == "artes-escenicas-danza-y-folclore" and number in corrections:
            updated, original = corrections[number]
            assert refs.endswith(updated) and compact(updated) in errata
            refs = refs.removesuffix(updated) + original
        profile = "perfil" if slug == "artes-escenicas-danza-y-folclore" else "Perfil"
        source.take(f"Esta competencia específica se conecta con los siguientes descriptores del {profile} de salida: {refs}.")
        source.check_origin(ce, start)
    ids = [item["id"] for item in document["competenciasEspecificas"]]
    developments = {item["curso"]: item for item in document["desarrollos"]}
    if slug == "biologia-y-geologia":
        verify_biology_shared(document)
        del developments[3]
    assert list(developments) == [course for course, _, _, _ in groups]
    for course, label, expected_criteria, expected_sabers in groups:
        development = developments[course]
        if label:
            source.heading(label)
        source.heading("Criterios de evaluación")
        criteria = development["criteriosEvaluacion"]
        assert len(criteria) == expected_criteria
        active = None
        for criterion in criteria:
            code = criterion["codigoOficial"]
            ce_number = code.split(".")[0]
            if active != ce_number:
                active = ce_number
                source.heading(f"Competencia específica {active}")
            assert criterion["competenciaEspecificaRef"] == f"ce-{active}" and not criterion["saberesBasicosRefs"]
            start = source.position
            source.heading(code)
            text = criterion["texto"]["es"]
            if slug == "biologia-y-geologia" and course == 1 and code == "5.1":
                assert text.endswith("nuestro entorno de Castilla-La Mancha.")
                text = text.removesuffix(".")
            if slug == "biologia-y-geologia" and course == 1 and code == "2.3":
                assert "en Castilla-La Mancha" in text
                text = text.replace("en Castilla-La Mancha", "en Castila-La Mancha")
            source.take(text)
            source.check_origin(criterion, start)
            ids.append(criterion["id"])
        source.heading("Saberes básicos")
        count = 0
        for block in development["bloquesSaberes"]:
            source.heading(f'{block["codigo"]}. {block["nombre"]["es"]}')
            for saber in block["saberes"]:
                start = source.position
                assert saber["codigoOficial"] is None
                source.take("- " + saber["texto"]["es"])
                source.check_origin(saber, start)
                ids.append(saber["id"])
                count += 1
        assert count == expected_sabers
    assert len(ids) == len(set(ids))
    pages = source.pages_since(start_area)
    assert document["fuentes"][0]["paginasMateria"] == {"desde": pages[0], "hasta": pages[-1]}
    return len(ids), descriptors


def audit_remaining(source: Source, document: dict, valid_codes: set[str], amendment: str, errata: str) -> tuple[int, int]:
    name = document["materia"]["nombre"]["es"]
    code = document["materia"]["codigo"]
    source_id = document["fuentes"][0]["id"]
    title = {"ACT": "Ámbito Científico -Tecnológico", "UE": "«Unión Europea"}.get(code, name)
    if code in ("ALS", "ACT", "UE"):
        source.position = source.text.index(compact(title))
    source.heading(title)
    for paragraph in document["introduccion"]["es"]:
        source.take(paragraph)
    source.heading("Competencias específicas")
    descriptors = 0
    ids = []
    for ce in document["competenciasEspecificas"]:
        start = source.position
        n = int(ce["codigoOficial"])
        ids.append(ce["id"])
        source.take(f'{n}. {ce["enunciado"]["es"]}')
        for paragraph in ce["descripcion"]["es"]:
            if code == "DD" and paragraph.startswith(("Esta competencia pretende afianzar", "Esta materia proporciona conocimientos básicos")):
                assert compact(paragraph) in amendment
                source.prefix(r"EneltercercursodeEducaciónSecundariaObligatoria,esta.*?(?=Estacompetenciaespecíficaseconecta)")
            else:
                if code == "PAPV" and n == 2:
                    paragraph = paragraph.replace("eventos culturales cercanos", "eventos culturas cercanos")
                source.take(paragraph)
        source.prefix(r"E?stacompetencia(?:específica)?seconectaconlossiguientesdescriptores(?:delPerfildesalida)?:?")
        refs = ce["descriptoresOperativosRefs"]
        assert len(refs) == len(set(refs)) and set(refs) <= valid_codes, (code, refs)
        descriptors += len(refs)
        if code == "ESCR" and n in (1, 2):
            assert refs[-1] == "CE2" and compact(", ".join(refs[-4:])) in errata
            refs = refs[:-1]
        if code == "MAMF" and n == 5:
            assert compact(", ".join(refs)) in errata
            refs = "CCL5 CD5 CPSAA6 CPSAA7 CE3 CCEC5 CCEC6".split()
        typos = {("FYQ", 3): ("STEM5", "STEMS"), ("FYQ", 5): ("STEM5", "STEMS"),
                 ("MAMF", 1): ("CCEC2", "CCE2"), ("MUS", 3): ("CCEC3", "CCE3"),
                 ("ALS", 4): ("CCL3", "CL3")}
        if typo := typos.get((code, n)):
            assert typo[0] in refs
            refs = [typo[1] if ref == typo[0] else ref for ref in refs]
        for ref in refs:
            source.prefix(r"[,;]?y?")
            source.take(ref)
        source.prefix(r"[.]?")
        source.check_origin(ce, start, source_id)

    # Los desarrollos compartidos deben coincidir en texto, orden, estructura y páginas.
    previous = None
    origins = len(document["competenciasEspecificas"])
    for dev in document["desarrollos"]:
        ids.extend(item["id"] for item in dev["criteriosEvaluacion"])
        for block in dev["bloquesSaberes"]:
            for node in block.get("apartados", [block]):
                ids.extend(item["id"] for item in node["saberes"])
        if previous is not None and "variante" not in dev and "variante" not in previous:
            old, new = previous["curso"], dev["curso"]
            reference = json.dumps(previous, ensure_ascii=False).replace(f'"curso": {old}', f'"curso": {new}', 1)
            reference = reference.replace(f'"cri-{old}-', f'"cri-{new}-').replace(f'"{code}.{old}.', f'"{code}.{new}.')
            if json.loads(reference) == dev:
                continue
        source.prefix(r"(?:(?:Cursos(?:primero[y]segundo|tercero[y]cuarto|deprimeroatercero)|"
                      r"Tercercurso|Cuartocurso|Matemáticas[AB]deCuartocurso)[.]?)?")
        source.heading("Criterios de evaluación")
        active = None
        for criterion in dev["criteriosEvaluacion"]:
            number = criterion["codigoOficial"]
            ce_number = number.split(".")[0]
            if active != ce_number:
                active = ce_number
                source.heading(f"Competencia específica {ce_number}")
            assert criterion["competenciaEspecificaRef"] == f"ce-{active}" and not criterion["saberesBasicosRefs"]
            start = source.position
            source.heading(number)
            text = criterion["texto"]["es"]
            if code == "LCL" and dev["curso"] == 3 and number == "1.1":
                assert "Castilla-La Mancha" in text
                text = text.replace("Castilla-La Mancha", "Castilla- La Macha")
            if code == "SLE" and dev["curso"] == 3 and number in ("3.2", "4.2", "5.3"):
                assert text.endswith(".")
                text = text[:-1]
            source.take(text)
            source.check_origin(criterion, start, source_id)
            origins += 1
        source.heading("Saberes básicos")
        for block in dev["bloquesSaberes"]:
            marker = block["codigo"] if code == "ACT" and block["codigo"] == "G" else block["codigo"] + "."
            source.heading(marker + block["nombre"]["es"])
            for paragraph in block.get("descripcion", {}).get("es", []):
                source.take(paragraph)
            for node in block.get("apartados", [block]):
                if node is not block:
                    source.heading(node["codigo"] + "." + node["nombre"]["es"])
                    for paragraph in node.get("descripcion", {}).get("es", []):
                        source.take(paragraph)
                for saber in node["saberes"]:
                    start = source.position
                    text = saber["texto"]["es"]
                    if code == "UE":
                        text = text.replace("Parlamento, Comisión y Consejo", "Parlamento Comisión y Consejo")
                    source.take("- " + text)
                    source.check_origin(saber, start, source_id)
                    origins += 1
        previous = dev
    assert len(ids) == len(set(ids)), code
    if code == "UE":
        source.take("»")
        assert source.text.startswith("Veintiséis.", source.position)
    elif code == "ALS":
        assert source.text.startswith(compact("Ámbito Científico -Tecnológico"), source.position)
    else:
        assert source.position == len(source.text), (code, source.text[source.position:source.position + 140])
    return origins, descriptors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packages", type=Path)
    args = parser.parse_args()
    if args.packages:
        sys.path.insert(0, str(args.packages.resolve()))
    import jsonschema

    catalog = json.loads((NORMATIVE / "catalogo.json").read_text(encoding="utf-8"))
    files = {entry["id"]: NORMATIVE / entry["archivo"] for entry in catalog["documentos"]}
    schema = json.loads((ROOT / "schemas/materia.schema.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    profile = "\n".join(raw_pages(files[BASE], 25, 33))
    valid = set(re.findall(r"\b((?:CCL|CP|STEM|CD|CPSAA|CCEC|CC|CE)\d+)\.", profile))
    errata = compact(raw_pages(files[ERRATA], 1, 1)[0])
    source = Source(raw_pages(files[BASE], 34, 59), 34)
    source.take("Anexo II")
    source.heading("Materias de Educación Secundaria Obligatoria")
    elements = descriptors = 0
    for config in AREAS:
        document = json.loads((DATA / f"{config[0]}.json").read_text(encoding="utf-8"))
        validator.validate(document)
        assert document["materia"]["nombre"]["es"] == config[1] and document["fuentes"][0]["id"] == BASE
        origins, links = verify(source, document, config, valid, errata)
        elements += origins
        descriptors += links
    assert source.position == len(source.text) and elements == 263
    inventory = json.loads((NORMATIVE.parent / "inventario.json").read_text(encoding="utf-8"))
    eso = [entry for entry in inventory["curriculos"] if entry["etapa"] == "eso"]
    prior = {item[0] for item in AREAS}
    amendment = compact("\n".join(raw_pages(files["es-cm-eso-cfgb-decreto-31-2024"], 8, 9)))
    by_name = {entry["nombre"]: entry["localizadores"][0] for entry in eso}
    for path in sorted(DATA.glob("*.json")):
        if path.stem in prior:
            continue
        document = json.loads(path.read_text(encoding="utf-8"))
        validator.validate(document)
        loc = by_name[document["materia"]["nombre"]["es"]]
        first, last = loc["paginaInicio"], loc["paginaFin"]
        assert document["fuentes"][0]["id"] == loc["fuenteRef"]
        assert document["fuentes"][0]["paginasMateria"] == {"desde": first, "hasta": last}
        source = Source(raw_pages(files[loc["fuenteRef"]], first, last), first)
        try:
            origins, links = audit_remaining(source, document, valid, amendment, errata)
        except AssertionError as error:
            raise AssertionError(f"{path.stem}: {error}") from error
        elements += origins
        descriptors += links
    assert len(list(DATA.glob("*.json"))) == len(eso) == 31
    print(json.dumps({"curriculos": len(eso), "elementosCotejados": elements,
                      "referenciasDeDescriptor": descriptors, "erroresDeEsquema": 0}))


if __name__ == "__main__":
    main()
