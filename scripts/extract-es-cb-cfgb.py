"""Extrae los dos ámbitos comunes de CFGB de Cantabria y sus variantes publicadas."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
import fitz
from cantabria_pdf_fonts import FontRecovery, normalize_unicode
ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data/es-cb/cfgb/materias"
CATALOG = json.loads((ROOT / "sources/es-cb/normativa/catalogo.json").read_text(encoding="utf-8"))
SOURCE_KEYS = {"D":"es-cb-eso-bachillerato-decreto-73-2022", "O":"es-cb-cfgb-orden-edu-47-2024", "M":"es-cb-cfgb-orden-edu-99-2025"}
SOURCE_RANGES = {"D":(320,352), "O":(586,626), "M":(35,71)}
SOURCES = {k: next(x for x in CATALOG["documentos"] if x["id"]==v) for k,v in SOURCE_KEYS.items()}
DIAGNOSTICS = []
COMPONENT_NAMES = {"CA":"Matemáticas aplicadas y Ciencias aplicadas", "CCS":"Comunicación y Ciencias Sociales", "EF":"Educación Físico-Deportiva - Actividad Física y Bienestar Emocional", "DEVAS":"Desarrollo de Estilo de Vida Activo y Saludable"}

@dataclass(frozen=True)
class Line:
    page: int
    text: str
    indented: bool
    x: float = 0.0


def source_lines(key: str) -> list[Line]:
    source = SOURCES[key]
    path = ROOT / "sources/es-cb/normativa" / source["archivo"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]
    output = []
    first, last = SOURCE_RANGES[key]
    with fitz.open(path) as pdf:
        recovery = FontRecovery(pdf)
        for number in range(first, last + 1):
            rows = []
            for block in recovery.page(pdf[number - 1])["blocks"]:
                for line in block.get("lines", []):
                    value = normalize_unicode(re.sub(r"\s+", " ", "".join(span["text"] for span in line["spans"]))).strip()
                    if value and not re.fullmatch(r"\d+|\d{4}/\d+", value):
                        rows.append((line["bbox"], value))
            rows.sort(key=lambda row: (round(row[0][1], 1), row[0][0]))
            merged = []
            for box, value in rows:
                if merged and abs(box[1] - merged[-1][0][1]) < 1:
                    previous, old = merged[-1]
                    merged[-1] = ((previous[0], previous[1], max(previous[2], box[2]), max(previous[3], box[3])), old + " " + value)
                else:
                    merged.append((box, value))
            margin = min(box[0] for box, _ in merged)
            for index, (box, value) in enumerate(merged):
                paragraph_gap = key in ("O", "M") and index > 0 and box[1] - merged[index - 1][0][1] > 14
                output.append(Line(number, value, box[0] > margin + 8 or paragraph_gap, box[0]))
    return output


def join(lines: list[Line]) -> str:
    result = ""
    for line in lines:
        result += ("" if not result or result.endswith("-") else " ") + line.text
    return result


def provenance(lines: list[Line], key: str) -> dict:
    return {"fuenteRef": SOURCE_KEYS[key], "paginas": sorted({line.page for line in lines})}


def paragraphs(lines: list[Line]) -> list[str]:
    groups = []
    for line in lines:
        if not groups or line.indented:
            groups.append([])
        groups[-1].append(line)
    return [join(group) for group in groups]


def label(value: str) -> str:
    return value.strip().rstrip(".").casefold()


def competencies(lines: list[Line], key: str) -> list[dict]:
    starts = [(i, int(match.group(1))) for i, line in enumerate(lines) if (match := re.match(r"^(\d+)\.\s*-?\s+", line.text))]
    assert [number for _, number in starts] == list(range(1, len(starts) + 1)), starts
    assert starts
    output = []
    for index, (start, number) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(lines)
        segment = lines[start:end]
        descriptor_start = next(i for i, line in enumerate(segment) if line.text.startswith("Esta competencia") and re.search(r"(?:se )?(?:conecta|relaciona) con los (?:siguientes )?(?:descriptores|prescriptores)", join(segment[i:i + 3])))
        body = segment[:descriptor_start]
        description_start = next((i for i, line in enumerate(body[1:], 1) if line.indented), len(body))
        raw_refs = join(segment[descriptor_start:]).split(":", 1)[1]
        raw_refs = re.sub(r"([A-Z]{2,6})\s+(\d)", r"\1\2", raw_refs)
        keys = re.findall(r"\b[A-Z]{2,6}\d+(?:\.\d+)?\b", raw_refs)
        extra = re.sub(r"\b[A-Z]{2,6}\d+(?:\.\d+)?\b|[,.;\s]", "", raw_refs)
        assert keys and extra in ("", "y"), (segment[0].page, raw_refs)
        if len(keys) != len(set(keys)):
            DIAGNOSTICS.append({"tipo": "descriptor-repetido", "fuente": key, "pagina": segment[0].page, "competencia": number, "texto": raw_refs})
        ce = {"id": f"ce-{number}", "codigoOficial": str(number), "enunciado": {"es": re.sub(r"^\d+\.\s*-?\s*", "", join(body[:description_start]))}, "descriptoresOperativosRefs": list(dict.fromkeys(keys)), "procedencia": provenance(segment, key)}
        if description_start < len(body):
            ce["descripcion"] = {"es": paragraphs(body[description_start:])}
        output.append(ce)
    return output


def criteria(lines: list[Line], key: str, code: str) -> list[dict]:
    groups = []
    active = None
    for line in lines:
        heading = re.fullmatch(r"Competencia[s]? espec[ií]fica[s]?\s+(\d+)\.?", line.text, re.I)
        item = re.match(r"^(\d+[.,]+\d+)(\.)?\s*(.+)$", line.text)
        if label(line.text) == "criterios de evaluación":
            DIAGNOSTICS.append({"tipo": "rotulo-criterios-repetido", "fuente": key, "pagina": line.page})
            continue
        if heading:
            active = int(heading.group(1))
        elif item:
            number, separator, value = item.groups()
            if ".." in number:
                DIAGNOSTICS.append({"tipo": "punto-duplicado-criterio", "area": code, "pagina": line.page, "codigo": number})
                number = re.sub(r"\.+", ".", number)
            if "," in number:
                DIAGNOSTICS.append({"tipo": "coma-en-codigo-criterio", "area": code, "pagina": line.page, "codigo": number})
                number = number.replace(",", ".")
            assert active is None or int(number.split(".")[0]) == active, (code, line.page, active, line.text)
            if not separator:
                DIAGNOSTICS.append({"tipo": "separador-criterio-omitido", "area": code, "pagina": line.page, "codigo": number})
            groups.append((number, [Line(line.page, value, False)]))
        else:
            assert groups, (code, line.page, line.text)
            groups[-1][1].append(line)
    codes = [number for number, _ in groups]
    assert groups, code
    if len(codes) != len(set(codes)):
        DIAGNOSTICS.append({"tipo": "codigo-criterio-repetido", "area": code, "codigos": codes})
    return [{"codigoOficial": number, "competenciaEspecificaRef": "ce-" + number.split(".")[0], "texto": {"es": join(words)}, "saberesBasicosRefs": [], "procedencia": provenance(words, key)} for number, words in groups]


def all_sabers(node: dict) -> list[dict]:
    if "saberes" in node:
        return node["saberes"]
    return [item for part in node.get("apartados", node.get("bloquesSaberes", [])) for item in all_sabers(part)]


def source_metadata(source: dict, *, first: int | None = None, last: int | None = None, annex: str | None = None) -> dict:
    source_type = source["tipo"] if source["tipo"] != "correccion-errores" else "otro"
    result = {"id": source["id"], "tipo": source_type, "titulo": source["titulo"], "publicacion": "Boletín Oficial de Cantabria", "numero": source["boc"], "fechaPublicacion": source["fechaPublicacion"], "cve": source["codigoBoc"], "urlOficial": source["urlOficial"], "urlVerificacion": source["urlOficial"]}
    if first is not None:
        result["paginasMateria"] = {"desde": first, "hasta": last}
    if annex:
        result["anexo"] = annex
    return result


def split_components(lines):
    starts=[]
    for i,line in enumerate(lines):
        if line.text in ("Ciencias Aplicadas", "Ámbito de Ciencias Aplicadas"):
            starts.append((i,1,"CA"))
        elif line.text in ("Comunicación y Ciencias Sociales", "Ámbito de Comunicación y Ciencias Sociales"):
            starts.append((i,1,"CCS"))
        elif line.text.startswith("Currículo de Educación Físico"):
            starts.append((i,2,"EF"))
        elif line.text.startswith("Currículo de Desarrollo de Estilo"):
            starts.append((i,2,"DEVAS"))
    return {code:lines[start+skip:starts[n+1][0] if n+1<len(starts) else len(lines)] for n,(start,skip,code) in enumerate(starts)}


def knowledge(lines, key, code):
    """Conserva la sangría de viñetas y los apartados numerados publicados."""
    blocks=[]
    container=None
    stack=[]
    for line in lines:
        heading=re.match(r"^([A-Z])[.)]\s+(.+)$",line.text)
        section=re.match(r"^(\d+)\.\s+(.+)$",line.text)
        bullet=re.match(r"^[-–—−‐‑•\x83]\s*(.+)$",line.text)
        if code=="CCS" and line.text.startswith("Lectura guiada de obras relevantes del patrimonio literario"):
            bullet=re.match(r"^(.+)$",line.text)
            DIAGNOSTICS.append({"tipo":"vineta-omitida","fuente":key,"pagina":line.page,"area":code})
        if heading:
            letter,value=heading.groups()
            assert letter not in [b['codigo'] for b in blocks],(code,line.page,line.text)
            container={"codigo":letter,"name":[Line(line.page,value,False)],"items":[],"parts":[]}
            blocks.append(container);stack=[]
        elif section:
            assert blocks and not blocks[-1]['items'],(code,line.page,line.text)
            number,value=section.groups()
            container={"codigo":number,"name":[Line(line.page,value,False)],"items":[],"parts":[]}
            blocks[-1]['parts'].append(container);stack=[]
        elif bullet:
            assert container,(code,line.page,line.text)
            node={"lines":[Line(line.page,bullet.group(1),False)],"x":line.x,"children":[]}
            while stack and line.x<=stack[-1]['x']+8:
                stack.pop()
            (stack[-1]['children'] if stack else container['items']).append(node)
            stack.append(node)
        else:
            assert container,(code,line.page,line.text)
            if stack:
                stack[-1]['lines'].append(line)
            else:
                container['name'].append(line)

    def leaf(node):
        return {"codigoOficial":None,"texto":{"es":join(node['lines'])},"procedencia":provenance(node['lines'],key)}

    def nodes(values):
        assert values,(code,"apartado vacío")
        if not any(node['children'] for node in values):
            return {"saberes":[leaf(node) for node in values]}
        parts=[]
        for number,node in enumerate(values,1):
            part={"codigo":str(number),"nombre":{"es":join(node['lines']).rstrip('.')}}
            part.update(nodes(node['children']) if node['children'] else {"saberes":[leaf(node)]})
            parts.append(part)
        return {"apartados":parts}

    output=[]
    for block in blocks:
        result={"codigo":block['codigo'],"nombre":{"es":join(block['name']).rstrip('.')}}
        if block['parts']:
            assert not block['items']
            result['apartados']=[{"codigo":part['codigo'],"nombre":{"es":join(part['name']).rstrip('.')},**nodes(part['items'])} for part in block['parts']]
        else:
            result.update(nodes(block['items']))
        output.append(result)
    assert output
    return output


def parse_component(lines,key,code):
    start=next(i for i,line in enumerate(lines) if label(line.text)=='competencias específicas')
    criterion_start=next(i for i,line in enumerate(lines) if label(line.text)=='criterios de evaluación')
    saber_start=next(i for i,line in enumerate(lines) if label(line.text)=='saberes básicos')
    end=next((i for i,line in enumerate(lines[:criterion_start]) if line.text=='Cursos tercero y cuarto'),criterion_start)
    ce_lines=[Line(line.page,re.sub(r'^Competencias específicas\s+(?=\d+\.)','',line.text),line.indented,line.x) for line in lines[start+1:end]]
    ce=competencies(ce_lines,key)
    # La edición de 2024 imprime estos enunciados y su explicación seguidos,
    # en el mismo párrafo. La primera oración coincide con los enunciados de
    # las materias de referencia; se conserva todo el resto como explicación.
    if key=='O':
        for item in ce:
            if code in ('EF','DEVAS') or code=='CCS' and item['codigoOficial']=='4':
                first,separator,rest=item['enunciado']['es'].partition('. ')
                assert separator,(code,item['codigoOficial'],'límite del enunciado')
                item['enunciado']['es']=first+'.'
                item['descripcion']={'es':[rest]+item.get('descripcion',{}).get('es',[])}
    return {"introduccion":{"es":paragraphs(lines[:start])},"competenciasEspecificas":ce,"criteriosEvaluacion":criteria(lines[criterion_start+1:saber_start],key,code),"bloquesSaberes":knowledge(lines[saber_start+1:],key,code)}


def normalize_component(component,code):
    def replace(value):
        if isinstance(value,str):
            if code=='CA':
                value=value.replace('artículo 19 de la orden XXXX','artículo 19 de la Orden EDU/47/2024')
                value=value.replace('irracionales relevantes: (','irracionales relevantes (').replace('ordenación de la recta numérica','ordenación en la recta numérica')
                value=value.replace('valor precio','valor-precio')
            if code=='CCS':
                value=value.replace('coherencia, y el registro adecuado adecuación, adecuado,','coherencia y el registro adecuado,')
                value=value.replace('Tema y resumen La intención','Tema y resumen. La intención')
            if code=='DEVAS':
                value=value.replace(', ya que los requerimientos y exigencias a nivel académico y de preparación del 2º curso de Bachillerato pondrán a prueba la fortaleza y la capacidad de superación de los estudiantes','')
                value=value.replace('incertidumbre en el medio Asimismo','incertidumbre en el medio. Asimismo')
            return value
        if isinstance(value,list):
            return [replace(x) for x in value]
        if isinstance(value,dict):
            return {key:replace(child) for key,child in value.items()}
        return value
    result=replace(component)
    if code=='CCS':
        for ce in result['competenciasEspecificas']:
            ce['descriptoresOperativosRefs']=['CCL3' if value=='CL3' else value for value in ce['descriptoresOperativosRefs']]
    for node in result['competenciasEspecificas']+result['criteriosEvaluacion']:
        field='enunciado' if 'enunciado' in node else 'texto'
        text=node[field]['es']
        if not text.endswith(('.', '…')):
            node[field]['es']=text.rstrip(',')+'.'
    return result


def application(variant):
    if variant=='ordinaria':
        return {"codigo":"ordinaria","nombre":{"es":"Oferta ordinaria: Educación Físico-Deportiva"},"requiereAutorizacion":False,"condicionesAplicacion":{"es":["Se aplica el componente de Educación Físico-Deportiva - Actividad Física y Bienestar Emocional en la oferta ordinaria, fuera de los supuestos de oferta para personas adultas o adaptación autorizada del artículo 19."]},"procedencia":{"fuenteRef":SOURCE_KEYS['O'],"paginas":[4,9,10]}}
    return {"codigo":"devas","nombre":{"es":"Oferta para personas adultas o adaptación autorizada: DEVAS"},"requiereAutorizacion":True,"condicionesAplicacion":{"es":[
        "Se aplica a las ofertas para personas adultas autorizadas conforme al artículo 19.1 y 19.3: mayores de diecisiete años cuando su historia escolar lo aconseje o personas que hayan superado una o varias formaciones de Grado C.",
        "También se aplica a los centros que obtengan autorización específica de la Dirección General competente en Formación Profesional conforme al artículo 19.5. La norma menciona no disponer de instalaciones propias o cercanas y/o de profesorado de la especialidad; añade que, si se dispone de las instalaciones necesarias o de colaboración con instalaciones cercanas, no podrá solicitarse esta autorización.",
        "Sustituye únicamente el componente de actividad física por Desarrollo de Estilo de Vida Activo y Saludable; se mantienen Matemáticas aplicadas y Ciencias aplicadas. No es una opción de libre elección entre dos currículos."
    ]},"procedencia":{"fuenteRef":SOURCE_KEYS['O'],"paginas":[9,10]}}


def extract(cache=None):
    if cache:
        lines=[Line(**row) for row in json.loads((cache/'canonical-lines.json').read_text(encoding='utf-8'))]
    else:
        lines=source_lines('O')
    groups=split_components(lines)
    assert set(groups)=={'CA','CCS','EF','DEVAS'}
    components={code:normalize_component(parse_component(rows,'O',code),code) for code,rows in groups.items()}
    assert {code:len(c['competenciasEspecificas']) for code,c in components.items()}=={'CA':8,'CCS':8,'EF':5,'DEVAS':8}
    output=[]
    for code,name,slug in [('CA','Ámbito de Ciencias Aplicadas','ciencias-aplicadas'),('CCS','Ámbito de Comunicación y Ciencias Sociales','comunicacion-y-ciencias-sociales')]:
        component_codes=['CA','EF','DEVAS'] if code=='CA' else ['CCS']
        all_ce=[];offsets={};offset=0
        for part in component_codes:
            offsets[part]=offset
            for item in copy.deepcopy(components[part]['competenciasEspecificas']):
                item['id']='ce-'+str(offset+int(item['codigoOficial']))
                item['componente']={'es':COMPONENT_NAMES[part]}
                all_ce.append(item)
            offset+=len(components[part]['competenciasEspecificas'])
        developments=[]
        for variant in (['ordinaria','devas'] if code=='CA' else [None]):
            for course in [1,2]:
                active=['CA','EF' if variant=='ordinaria' else 'DEVAS'] if code=='CA' else ['CCS']
                dev={'curso':course,'criteriosEvaluacion':[],'bloquesSaberes':[]}
                if variant:
                    dev['variante']=application(variant)
                prefix=('CAO' if variant=='ordinaria' else 'CAD') if code=='CA' else 'CCS'
                for part in active:
                    for item in copy.deepcopy(components[part]['criteriosEvaluacion']):
                        namespace=(('ord' if variant=='ordinaria' else 'dev')+part.lower()) if variant else part.lower()
                        item['id']=f"cri-{course}-{namespace}-{item['codigoOficial'].replace('.','-')}"
                        item['competenciaEspecificaRef']='ce-'+str(offsets[part]+int(item['codigoOficial'].split('.')[0]))
                        dev['criteriosEvaluacion'].append(item)
                    for block in copy.deepcopy(components[part]['bloquesSaberes']):
                        original=block['codigo']
                        if part in ('EF','DEVAS'):
                            block['codigo']=chr(ord(original)+11)
                            block['nombre']['es']=original+'. '+block['nombre']['es']
                        block['componente']={'es':COMPONENT_NAMES[part]}
                        for number,saber in enumerate(all_sabers(block),1):
                            saber['id']=f"{prefix}.{course}.{block['codigo']}.{number:02d}"
                        dev['bloquesSaberes'].append(block)
                developments.append(dev)
        official=['3163','3164'] if code=='CA' else ['3161','3162']
        doc={
            '$schema':'../../../../schemas/materia.schema.json','schemaVersion':'0.9.0','id':f'es-cb.cfgb.{slug}','territorio':'es-cb','etapa':'cfgb',
            'materia':{'codigo':code,'nombre':{'es':name},'cursos':[{'curso':course,'caracter':'ambito','codigoOficial':official[course-1]} for course in [1,2]]},
            'vigencia':{'entradaEnVigor':'2024-10-09','aplicableDesdeCurso':'2024/2025','hasta':None,'estado':'vigente'},
            'fuentes':[source_metadata(SOURCES['O'],first=586 if code=='CA' else 597,last=626 if code=='CA' else 609,annex='XXI'),source_metadata(SOURCES['D'],first=320 if code=='CA' else 334,last=334 if code=='CA' else 352,annex='I-C'),source_metadata(SOURCES['M'],first=7,last=71 if code=='CA' else 55,annex='VI')],
            'introduccion':components[code]['introduccion'],'competenciasEspecificas':all_ce,'desarrollos':developments,
            'revision':{'estado':'revisado','fuenteComprobada':True,'fechaUltimaRevision':'2026-11-05','metodo':'Extracción de texto y coordenadas, cotejo visual y contraste independiente con Poppler de los tres anexos publicados.','notas':[
                'Las abreviaturas y los identificadores son internos del proyecto. codigoOficial conserva la numeración publicada de cada competencia, criterio y ámbito por curso.',
                'Los códigos por curso son los vigentes desde el 1 de noviembre de 2025, por la disposición final primera, apartado cinco, de la Orden EDU/99/2025. Sustituyen 3009/3010 por 3163/3164 y 3011/3012 por 3161/3162.',
                'entradaEnVigor corresponde a la Orden EDU/47/2024. Su implantación es en primero en 2024/2025 y en segundo en 2025/2026. La fecha de la actualización de códigos no se proyecta sobre cursos anteriores.',
                'El anexo XXI de 2024 remite al Decreto 73/2022 y publica los desarrollos de los ámbitos. El anexo VI de 2025 se coteja como publicación complementaria del título de Fabricación de Elementos Metálicos; no sustituye de forma general el anexo XXI.',
                'La fuente no secuencia competencias, criterios y saberes por curso. Se reproducen como contenido compartido en primero y segundo, sin inventar un reparto o una programación cronológica.',
                'Los contenidos de los ámbitos son prescriptivos. No se inventan relaciones criterio-saber ni descriptores por criterio.',
                'La jerarquía de viñetas se conserva según su sangría. Cuando un nivel contiene a la vez encabezados con hijos y elementos sueltos, estos últimos se representan mediante un apartado interno con un único saber idéntico al título, conservando el orden publicado.'
            ]}
        }
        if code=='CA':
            doc['revision']['notas'] += [
                'Las competencias ce-1 a ce-8 pertenecen al componente científico-matemático; ce-9 a ce-13 a Educación Físico-Deportiva y ce-14 a ce-21 a DEVAS. Esta numeración de id es interna: codigoOficial mantiene los números 1 a 5 u 8 que la fuente repite en los componentes.',
                'Cada desarrollo identifica la variante y sus condiciones. La variante ordinaria incorpora Educación Físico-Deportiva; la variante devas conserva los supuestos de oferta para personas adultas o adaptación autorizada, sin mezclar ambos componentes en un mismo desarrollo.',
                'Los recuentos de las variantes son alternativas y no se suman como exigencias para un alumno. Debe seleccionarse el curso y la variante que corresponda a la oferta o adaptación autorizada.',
                'La cabecera Cursos tercero y cuarto dentro del componente físico-deportivo identifica la remisión a ESO; el anexo lo incorpora a Ciencias Aplicadas I y II, sin crear cursos tercero o cuarto de CFGB.',
                'Los bloques A-K conservan sus letras. Los bloques A-F de actividad física reciben letras internas L-Q, conservando la letra publicada en el nombre y su componente. Los prefijos CAO y CAD distinguen los identificadores de saberes de las dos variantes.',
                'Los descriptores de DEVAS se mantienen tal como se publican, incluidas referencias subdivididas de Bachillerato. No se convierten por inferencia a descriptores de la enseñanza básica.'
            ]
        output.append(doc)
    return output


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--write',action='store_true')
    parser.add_argument('--cache',type=Path)
    parser.add_argument('--diagnostics',type=Path)
    args=parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    documents=extract(args.cache)
    print(json.dumps({'materias':len(documents),'diagnosticos':DIAGNOSTICS},ensure_ascii=False))
    if args.diagnostics:
        args.diagnostics.parent.mkdir(parents=True,exist_ok=True)
        args.diagnostics.write_text(json.dumps(DIAGNOSTICS,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if args.write:
        DEST.mkdir(parents=True,exist_ok=True)
        for doc in documents:
            (DEST/(doc['id'].split('.')[-1]+'.json')).write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
