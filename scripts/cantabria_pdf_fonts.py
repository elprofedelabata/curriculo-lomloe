"""Recupera glifos CID sin ToUnicode mediante sus contornos incrustados.

No modifica el PDF. Las correspondencias se obtienen comparando los contornos
con glifos con nombre de las fuentes Type1 del propio documento. Los registros
raw/decoded permiten reparar únicamente esos tramos en la salida de Poppler.
"""
from __future__ import annotations

import io
import re
import unicodedata

from fontTools.agl import toUnicode
from fontTools.cffLib import CFFFontSet
from fontTools.pens.recordingPen import RecordingPen


class FontRecovery:
    def __init__(self, pdf):
        self.pdf = pdf
        self.maps = {}
        self.references = {}
        self.repairs = {}

    def _cff(self, xref):
        data = self.pdf.extract_font(xref)[3]
        cff = CFFFontSet()
        cff.decompile(io.BytesIO(data), None)
        return cff[cff.fontNames[0]]

    @staticmethod
    def _outline(font, name):
        pen = RecordingPen()
        font.CharStrings[name].draw(pen)
        return repr(pen.value)

    def _map(self, page, xref):
        if xref in self.maps:
            return self.maps[xref]
        font = self._cff(xref)
        family = font.rawDict["BaseFontName"]
        if family not in self.references:
            named = {}
            for reference, extension, kind, name, *_ in page.get_fonts(full=True):
                if kind != "Type1" or name.split("+")[-1] != family:
                    continue
                other = self._cff(reference)
                for glyph in other.charset:
                    value = toUnicode(glyph)
                    if value:
                        named[self._outline(other, glyph)] = value
            self.references[family] = named
        named = self.references[family]
        mapping = {}
        for glyph in font.charset:
            if not glyph.startswith("cid"):
                continue
            value = named.get(self._outline(font, glyph))
            if value:
                mapping[int(glyph[3:])] = value
        # El CID 237 es la raya de viñeta, comprobada visualmente en Música.
        # Su contorno no está incluido en el subconjunto Type1 de referencia.
        if family == "ArialMT":
            mapping.setdefault(237, "–")
            mapping.setdefault(1171, "\u0301")
            # Beta en «β-oxidación», cotejada en la página 383 del decreto.
            mapping.setdefault(533, "β")
            # Ejemplos griegos cotejados en las páginas 591 y 594 del decreto.
            for cid, value in {652: "π", 540: "λ", 538: "ι", 546: "ς", 303: "δ", 531: "ί", 539: "κ", 536: "η", 2690: "ό", 541: "μ", 2581: "ἀ", 534: "γ", 555: "ώ", 545: "ρ", 548: "χ", 530: "ή", 2763: "ῆ", 2792: "ῦ", 537: "θ"}.items():
                mapping.setdefault(cid, value)
        if family == "SymbolMT":
            mapping.setdefault(16, "–")
        self.maps[xref] = mapping
        return mapping

    def page(self, page):
        cid_fonts = [xref for xref, _, kind, *_ in page.get_fonts(full=True)
                     if kind == "Type0" and self.pdf.xref_get_key(xref, "ToUnicode")[0] == "null"]
        if not cid_fonts:
            return page.get_text("dict", clip=(85, 120, 535, 776))
        maps = [self._map(page, xref) for xref in cid_fonts]
        fixes, repairs = {}, []
        for span in page.get_texttrace():
            body = [char for char in span["chars"] if 85 <= char[2][0] < 535 and 120 <= char[2][1] < 776]
            if not any(char[0] == 65533 for char in body):
                continue
            raw, decoded = [], []
            for unicode_value, glyph, origin, _ in body:
                if unicode_value == 65533:
                    candidates = {mapping[glyph] for mapping in maps if glyph in mapping}
                    assert len(candidates) == 1, (page.number + 1, glyph, candidates)
                    value = candidates.pop()
                    fixes[(round(origin[0], 2), round(origin[1], 2))] = value
                    raw.append(chr(glyph))
                    decoded.append(value)
                else:
                    raw.append(chr(unicode_value))
                    decoded.append(chr(unicode_value))
            repairs.append(("".join(raw), "".join(decoded)))
        self.repairs[page.number + 1] = repairs
        data = page.get_text("rawdict", clip=(85, 120, 535, 776))
        for block in data["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    span["text"] = "".join(fixes.get((round(char["origin"][0], 2), round(char["origin"][1], 2)), char["c"]) for char in span.pop("chars"))
        return data


def normalize_unicode(value):
    """Unifica acentos compuestos y marcas idénticas superpuestas del PDF."""
    decomposed = unicodedata.normalize("NFD", value)
    decomposed = re.sub(r"([\u0300-\u036f])\1+", r"\1", decomposed)
    value = unicodedata.normalize("NFC", decomposed)
    # Los contornos idénticos de letras latinas y griegas pueden recibir el
    # nombre latino. Restituir solo los ejemplos completos cotejados del PDF.
    for raw, greek in {"πóλις": "πόλις", "vόμoς": "νόμος", "ἀγώv": "ἀγών", "δῆμoς": "δῆμος", "μῦθoς": "μῦθος", "λóγoς": "λόγος"}.items():
        value = value.replace(raw, greek)
    return value
