"""Guarda el inventario y los ODT institucionales de Bachillerato de Canarias."""
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen
import hashlib
import json
import re
import subprocess
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
PORTAL = "https://www.gobiernodecanarias.org/educacion/web/bachillerato/informacion/ordenacion_curriculo_competencias/curriculo_bach_lomce/index.html"
SUPPORT = ROOT / "sources/es-cn/apoyo/bachillerato"
CODES = "AM AE BIO BGCA CG CTV CA DA DTAPD DT DIS ECO EEAE EF EDMN FIL FIS FQ FA GEO GCA GRI HE HFI HMD HAR HMC LAT LCL LE LPM LD LU MACS MG MAT MCA PA QUI SLE TEGP TI VOL ANA AF AS BH BE CC ELE FOT FAG HC IS IA ID MA LC JDTC MNC TEG TA TL MEE MS PSI TAI".split()


class CurriculumTable(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.cells = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.cells = []
        elif tag in ("td", "th") and self.cells is not None:
            self.cell = {"text": "", "links": []}
        elif tag == "a" and self.cell is not None:
            self.cell["links"].extend(value for name, value in attrs if name == "href")

    def handle_data(self, value):
        if self.cell is not None:
            self.cell["text"] += value

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.cells.append(self.cell)
            self.cell = None
        elif tag == "tr" and self.cells is not None:
            self.rows.append(self.cells)
            self.cells = None


def download(url, path):
    if not path.exists():
        path.write_bytes(urlopen(url, timeout=90).read())


def normal(value):
    return "".join(c for c in unicodedata.normalize("NFKD", value.casefold()) if c.isalnum() and not unicodedata.combining(c))


def attach_pages(manifest, path, first_page, end_page):
    pages = subprocess.run(["pdftotext", "-raw", "-enc", "UTF-8", str(path), "-"], check=True, capture_output=True).stdout.decode("utf-8").split("\f")
    found = {}
    for page in range(first_page, end_page):
        lines = pages[page - 1].splitlines()
        for index, line in enumerate(lines):
            if normal(line) != "introduccion":
                continue
            title = normal(" ".join(lines[max(0, index - 5):index]))
            matches = [meta for meta in manifest if title.endswith(normal(meta["nombre"]))]
            if matches:
                meta = max(matches, key=lambda item: len(normal(item["nombre"])))
                found.setdefault(meta["slug"], page)
    assert len(found) == len(manifest), [meta["nombre"] for meta in manifest if meta["slug"] not in found]
    assert len(set(found.values())) == len(manifest), found
    boundaries = sorted(found.values()) + [end_page]
    for meta in manifest:
        start = found[meta["slug"]]
        meta["paginas"] = {"desde": start, "hasta": boundaries[boundaries.index(start) + 1] - 1}


def main():
    SUPPORT.mkdir(parents=True, exist_ok=True)
    parser = CurriculumTable()
    parser.feed(urlopen(PORTAL, timeout=60).read().decode("utf-8"))
    rows = [row for row in parser.rows if any(link.lower().endswith(".odt") for cell in row for link in cell["links"])]
    assert len(rows) == len(CODES) == 67, len(rows)
    manifest = []
    for index, (row, code) in enumerate(zip(rows, CODES), 1):
        name = " ".join(row[0]["text"].split()).replace("MusicaI", "Musical").replace("Hª", "Historia").replace("Fisica", "Física")
        name = re.sub(r" I y II$", "", name)
        name = name.replace("CCSS", "Ciencias Sociales").replace("Gráfico Plásticas", "Gráfico-Plásticas")
        name = name.replace("Técnicas de Expresión Gráfico-Plásticas", "Técnicas de Expresión Gráfico-Plástica")
        name = name.replace("Música, Expresión y Espectáculos", "Música, Expresión y Espectáculo")
        if name == "Talleres Artísticos":
            name = "Talleres Artísticos: Cerámica y Estampación"
        slug = re.sub(r"[^a-z0-9]+", "-", "".join(c for c in unicodedata.normalize("NFKD", name.lower()) if not unicodedata.combining(c))).strip("-")
        links = [urljoin(PORTAL, link) for cell in row for link in cell["links"]]
        courses = sorted({int(c) for c in re.findall(r"([12])\.?\s*[ºo]", row[1]["text"])})
        assert courses, row[1]
        meta = {"nombre": name, "slug": slug, "codigoInterno": code, "cursos": courses,
                "optativa": index > 43, "decreto": "78/2025" if index > 43 else "30/2023",
                "odt": f"{index:02d}-{slug}.odt", "urlOdt": next(link for link in links if link.lower().endswith(".odt")),
                "urlPdfApoyo": next(link for link in links if link.lower().endswith(".pdf"))}
        manifest.append(meta)
    assert len({meta["slug"] for meta in manifest}) == 67
    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(lambda meta: download(meta["urlOdt"], SUPPORT / meta["odt"]), manifest))
    directory = ROOT / "sources/es-cn/normativa/bachillerato"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "2025-06-02-decreto-78-2025-optativas-bachillerato.pdf"
    url = "https://sede.gobiernodecanarias.org/boc/boc-a-2025-112-2086.pdf"
    download(url, target)
    attach_pages(manifest[:43], ROOT / "sources/es-cn/normativa/eso-bachillerato/2023-03-16-decreto-30-2023-curriculo-eso-bachillerato.pdf", 901, 1942)
    attach_pages(manifest[43:], target, 1, 422)
    (SUPPORT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    expected = {meta["odt"] for meta in manifest}
    for cached in SUPPORT.glob("*.odt"):
        if cached.name not in expected:
            assert cached.parent.resolve() == SUPPORT.resolve()
            cached.unlink()
    print("Inventario:", len(manifest), "materias; ODT:", len(list(SUPPORT.glob('*.odt'))))
    print("Decreto 78/2025 SHA256:", hashlib.sha256(target.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
