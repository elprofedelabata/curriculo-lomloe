"""Cotejo independiente de CFGB de Cantabria con Poppler y JSON Schema.

Contrasta los componentes completos, su combinación por variantes y las tres
publicaciones. No importa ni ejecuta el extractor.
"""
from __future__ import annotations
import argparse
import copy
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
 "D": ("eso-bachillerato/2022-07-27-decreto-73-2022-curriculo-eso-bachillerato.pdf",320,352),
 "O": ("cfgb/2024-09-30-orden-edu-47-2024-cfgb.pdf",586,626),
 "M": ("cfgb/2025-10-24-orden-edu-99-2025-modificacion-cfgb.pdf",35,71),
}
SOURCE_IDS = {"D":"es-cb-eso-bachillerato-decreto-73-2022", "O":"es-cb-cfgb-orden-edu-47-2024", "M":"es-cb-cfgb-orden-edu-99-2025"}
COMPONENT_NAMES = {"CA":"Matemáticas aplicadas y Ciencias aplicadas", "CCS":"Comunicación y Ciencias Sociales", "EF":"Educación Físico-Deportiva - Actividad Física y Bienestar Emocional", "DEVAS":"Desarrollo de Estilo de Vida Activo y Saludable"}
BULLET = r"[-–—−‐‑•\x83]"
PUBLISHED = {
 "CA": [("artículo 19 de la Orden EDU/47/2024", "artículo 19 de la orden XXXX"), ("irracionales relevantes (", "irracionales relevantes: ("), ("ordenación en la recta numérica", "ordenación de la recta numérica"), ("valor-precio", "valor precio")],
 "CCS": [("coherencia y el registro adecuado,", "coherencia, y el registro adecuado adecuación, adecuado,"), ("Tema y resumen. La intención", "Tema y resumen La intención")],
 "DEVAS": [("gestionar los propios estados de ánimo.", "gestionar los propios estados de ánimo, ya que los requerimientos y exigencias a nivel académico y de preparación del 2º curso de Bachillerato pondrán a prueba la fortaleza y la capacidad de superación de los estudiantes."), ("incertidumbre en el medio. Asimismo", "incertidumbre en el medio Asimismo")]
}

def original_candidates(value,code,kind):
 values=[value]
 restored=value
 for corrected,published in PUBLISHED.get(code,[]):
  restored=restored.replace(corrected,published)
 if restored!=value:
  values.append(restored)
 for text in values:
  yield text
  if kind in ("competencia","criterio") and text.endswith("."):
   yield text[:-1]
   yield text[:-1]+","

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
                if re.match(r"^\s*(?:LUNES|MARTES|MIÉRCOLES|JUEVES|VIERNES|SÁBADO|DOMINGO), .+NÚM\.\s+\d+\s*$", line):
                    continue
                if any(marker in line for marker in ("BOC NÚM.", "CVE-", "boc.cantabria.es", "Boletín Oficial de Cantabria")):
                    continue
                if re.fullmatch(r"\s*(?:i|Pág\. \d+|\d+/(?:881|633|78)|\d{4}/\d+)\s*", line):
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


def leaves(node):
    return node['saberes'] if 'saberes' in node else [leaf for part in node.get('apartados',node.get('bloquesSaberes',[])) for leaf in leaves(part)]


def without_ids(value):
    if isinstance(value,dict):
        return {key:without_ids(child) for key,child in value.items() if key!='id'}
    if isinstance(value,list):
        return [without_ids(child) for child in value]
    return value


def canonical_components(documents):
    output={}
    for doc in documents:
        code=doc['materia']['codigo']
        ce_by_id={item['id']:item for item in doc['competenciasEspecificas']}
        assert len(ce_by_id)==len(doc['competenciasEspecificas'])
        for dev in doc['desarrollos']:
            variant=dev.get('variante',{}).get('codigo')
            expected=['CA','EF' if variant=='ordinaria' else 'DEVAS'] if code=='CA' else ['CCS']
            assert dev['curso'] in (1,2)
            if code=='CA':
                assert variant in ('ordinaria','devas') and dev['variante']['requiereAutorizacion']==(variant=='devas')
                assert dev['variante']['condicionesAplicacion']['es'] and dev['variante']['procedencia']['fuenteRef']==SOURCE_IDS['O']
                assert dev['variante']['procedencia']['paginas']==([4,9,10] if variant=='ordinaria' else [9,10])
            actual={ce_by_id[item['competenciaEspecificaRef']]['componente']['es'] for item in dev['criteriosEvaluacion']}
            assert actual=={COMPONENT_NAMES[x] for x in expected},(code,dev['curso'],variant)
            for part in expected:
                name=COMPONENT_NAMES[part]
                ce=[item for item in doc['competenciasEspecificas'] if item['componente']['es']==name]
                criteria=[item for item in dev['criteriosEvaluacion'] if ce_by_id[item['competenciaEspecificaRef']]['componente']['es']==name]
                blocks=[item for item in dev['bloquesSaberes'] if item['componente']['es']==name]
                comp={'competenciasEspecificas':ce,'criteriosEvaluacion':criteria,'bloquesSaberes':blocks,'introduccion':doc['introduccion'] if part==code else {'es':[]}}
                if part in output:
                    assert without_ids(comp)==without_ids(output[part]),(part,'contenido compartido alterado')
                else:
                    output[part]=comp
    assert {key:len(value['competenciasEspecificas']) for key,value in output.items()}=={'CA':8,'CCS':8,'EF':5,'DEVAS':8}
    return output


def heading(stream,text):
    stream.regex('(?i:'+re.escape(compact(text))+')')
    stream.regex(r'\.',optional=True)


def emit_knowledge(stream,code,blocks):
    def contents(node,published_numbers=False):
        if 'apartados' in node:
            for part in node['apartados']:
                if published_numbers:
                    stream.regex(re.escape(part['codigo'])+r'\.?')
                    heading(stream,part['nombre']['es'])
                    contents(part)
                else:
                    stream.regex(BULLET)
                    if 'saberes' in part and len(part['saberes'])==1 and compact(part['nombre']['es']).rstrip('.')==compact(part['saberes'][0]['texto']['es']).rstrip('.'):
                        stream.text(part['saberes'][0]['texto']['es'],'saber',part['saberes'][0]['id'])
                    else:
                        heading(stream,part['nombre']['es'])
                        contents(part)
        else:
            for saber in node['saberes']:
                stream.regex(BULLET,optional=code=='CCS' and saber['texto']['es'].startswith('Lectura guiada de obras relevantes del patrimonio literario'))
                stream.text(saber['texto']['es'],'saber',saber['id'])
    for block in blocks:
        if code not in ('EF','DEVAS'):
            stream.regex(re.escape(block['codigo'])+r'[.)]')
        heading(stream,block['nombre']['es'])
        contents(block,published_numbers=code=='CCS' and block['codigo']=='B')


def emit_component(stream,code,component):
    stream.code=code
    titles={'CA':'Ámbito de Ciencias Aplicadas','CCS':'Ámbito de Comunicación y Ciencias Sociales','EF':'Currículo de Educación Físico-Deportiva - Actividad física y bienestar emocional dentro del ámbito de Ciencias Aplicadas I y II','DEVAS':'Currículo de Desarrollo de Estilo de Vida Activo y Saludable dentro del ámbito de Ciencias Aplicadas I y II'}
    heading(stream,titles[code])
    for paragraph in component['introduccion']['es']:
        stream.text(paragraph,'introduccion')
    heading(stream,'Competencias específicas')
    for ce in component['competenciasEspecificas']:
        if code=='EF' and ce['codigoOficial']=='1':
            heading(stream,'Competencias específicas')
        stream.regex(re.escape(ce['codigoOficial'])+r'\.')
        stream.text(ce['enunciado']['es'],'competencia',ce['id'])
        for paragraph in ce.get('descripcion',{}).get('es',[]):
            stream.text(paragraph,'descripcion',ce['id'])
        stream.regex(r'Estacompetencia(?:espec[ií]fica)?(?:se)?(?:conecta|relaciona)conlos(?:siguientes)?(?:descriptores|prescriptores)(?:operativos)?(?:(?:del|de|delas)?(?:[Pp]erfildesalida|salida|competenciasclave(?:enBachillerato)?)?)?:')
        for key in ce['descriptoresOperativosRefs']:
            stream.regex(r'[,ye.]',optional=True)
            stream.text('CL3' if code=='CCS' and ce['codigoOficial']=='4' and key=='CCL3' else key,'descriptor',ce['id'])
        stream.regex(r'[.,]',optional=True)
    if code=='EF':
        heading(stream,'Cursos tercero y cuarto')
    heading(stream,'Criterios de evaluación')
    for criterion in component['criteriosEvaluacion']:
        number=criterion['codigoOficial'].split('.')[0]
        stream.regex(r'Competencias?espec[ií]ficas?'+number+r'\.?',optional=True)
        stream.regex(re.escape(criterion['codigoOficial'])+r'\.?')
        stream.text(criterion['texto']['es'],'criterio',criterion['id'])
    heading(stream,'Saberes básicos')
    emit_knowledge(stream,code,component['bloquesSaberes'])


def source_bodies(raw,source):
    lines=raw.splitlines(keepends=True);starts=[];offset=0
    for line in lines:
        value=compact(line).casefold()
        if value==('cienciasaplicadas' if source=='D' else 'ámbitodecienciasaplicadas'):
            starts.append((offset,'CA'))
        elif value==('comunicaciónycienciassociales' if source=='D' else 'ámbitodecomunicaciónycienciassociales'):
            starts.append((offset,'CCS'))
        elif value.startswith('currículodeeducaciónfísico-deportiva'):
            starts.append((offset,'EF'))
        elif value.startswith('currículodedesarrollodeestilo'):
            starts.append((offset,'DEVAS'))
        offset+=len(line)
    bodies={}
    for i,(start,code) in enumerate(starts):
        end=starts[i+1][0] if i+1<len(starts) else len(raw)
        body=raw[start:end]
        label=re.search(r'(?m)^\s*Competencias específicas\.?\s*$',body)
        assert label,(source,code,'cabecera')
        bodies[code]=compact(body[label.end():])
    assert set(bodies)==({'CA','CCS'} if source=='D' else {'CA','CCS','EF','DEVAS'}),(source,list(bodies))
    return bodies


def compare_publications(streams):
    bodies={key:source_bodies(value,key) for key,value in streams.items()}
    rules={
        ('D','CA'):[('irracionalesrelevantes:(','irracionalesrelevantes('),('ordenacióndelarectanumérica','ordenaciónenlarectanumérica'),('calidad-precioyvalorprecio','calidad-precioyvalor-precio')],
        ('D','CCS'):[('desdeunalecturapuramente','desdeunlecturapuramente'),('desinformación,buscandotransformaresainformación','desinformación.buscandotransformaresainformación'),('ámbitocultural,socialyterritorialdelalumnado.Competenciaespecífica5','ámbitocultural,socialyterritorialdelalumnadoCompetenciaespecífica5'),('confluidez,coherencia,yelregistro','confluidez,coherenciayelregistro'),('motivacionesdelosinterlocutores.7.4','motivacionesdelosinterlocutores7.4')],
        ('M','CA'):[],
        ('M','CCS'):[('elregistroadecuadoadecuación,adecuado,','elregistroadecuado,'),('TemayresumenLaintención','Temayresumen.Laintención'),('3.Educaciónliteraria.Lecturaguiadadeobras','3.Educaciónliteraria.-Lecturaguiadadeobras')],
        ('M','EF'):[('Competenciasespecíficas1.','1.'),('Cursosterceroycuarto','')],
        ('M','DEVAS'):[(compact(', ya que los requerimientos y exigencias a nivel académico y de preparación del 2º curso de Bachillerato pondrán a prueba la fortaleza y la capacidad de superación de los estudiantes'),''),('incertidumbreenelmedioAsimismo','incertidumbreenelmedio.Asimismo')],
    }
    report=[]
    for (target,code),replacements in rules.items():
        expected=bodies['O'][code]
        for old,new in replacements:
            assert old in expected,(target,code,old,'diferencia documentada no encontrada')
            expected=expected.replace(old,new)
        actual=bodies[target][code]
        # Las publicaciones alternan grafías de estos compuestos, incluso
        # dentro de una misma materia. No se cambian los textos del JSON.
        orthographic=[]
        if target=='M' and code=='DEVAS':
            for dashed,closed in [('enseñanza-aprendizaje','enseñanzaaprendizaje'),('perceptivo-motrices','perceptivomotrices'),('artístico-expresiva','artísticoexpresiva'),('afectivo-sexual','afectivosexual')]:
                assert dashed in actual or dashed in expected,(code,dashed)
                expected=expected.replace(dashed,closed);actual=actual.replace(dashed,closed)
                orthographic.append([dashed,closed])
        if expected!=actual:
            i=next((i for i,(a,b) in enumerate(zip(expected,actual)) if a!=b),min(len(expected),len(actual)))
            raise AssertionError((target,code,i,expected[max(0,i-70):i+160],actual[max(0,i-70):i+160]))
        report.append({'fuente':target,'componente':code,'caracteres':len(actual),'ajustesDocumentados':len(replacements),'variacionesOrtograficas':orthographic})
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--packages',type=Path);parser.add_argument('--report',type=Path,default=ROOT/'tmp/pdfs/cantabria-cfgb-audit.json');args=parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    if args.packages:
        sys.path.insert(0,str(args.packages.resolve()))
    import jsonschema
    paths=sorted((ROOT/'data/es-cb/cfgb/materias').glob('*.json'));assert len(paths)==2
    documents=[json.loads(path.read_text(encoding='utf-8')) for path in paths]
    schema=json.loads((ROOT/'schemas/materia.schema.json').read_text(encoding='utf-8'))
    validator=jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker())
    report={'schemaErrors':[],'coverageDifferences':[],'descriptorAnomalies':[],'comparacionPublicaciones':[],'fragmentosProcedencia':0,'fuentesRecuperadas':{}}
    streams={};pages={}
    for key in SOURCES:
        raw,body_pages,recovered=source_text(key);streams[key]=raw;pages[key]=body_pages;report['fuentesRecuperadas'][key]=recovered
    components=canonical_components(documents)
    counts=Counter();stream=Stream(streams['O'],'CA',counts)
    heading(stream,'ANEXO XXI');heading(stream,'Ámbitos de Ciencias aplicadas y Comunicación y Ciencias Sociales de Grados básicos')
    try:
        for code in ('CA','CCS','EF','DEVAS'):
            emit_component(stream,code,components[code])
        stream.end()
    except AssertionError as error:
        report['coverageDifferences'].append(['canonico',str(error)])
    try:
        report['comparacionPublicaciones']=compare_publications(streams)
    except AssertionError as error:
        report['coverageDifferences'].append(['publicaciones',str(error)])
    valid_base={f'{name}{n}' for name,end in [('CCL',5),('CP',3),('STEM',5),('CD',5),('CPSAA',5),('CC',4),('CE',3),('CCEC',4)] for n in range(1,end+1)}
    valid_devas=valid_base|{'CPSAA1.1','CPSAA1.2','CPSAA3.1','CPSAA3.2','CCEC3.1','CCEC3.2','CCEC4.1','CCEC4.2'}
    for path,doc in zip(paths,documents):
        report['schemaErrors'] += [[path.name,error.json_path,error.message] for error in validator.iter_errors(doc)]
        assert doc['schemaVersion']=='0.9.0' and doc['revision']['estado']=='revisado' and doc['revision']['fuenteComprobada']
        assert not re.search(r'CB-CFGB-\d+|INCIDENCIAS\.md',json.dumps(doc,ensure_ascii=False))
        assert doc['vigencia']['entradaEnVigor']=='2024-10-09' and doc['vigencia']['aplicableDesdeCurso']=='2024/2025'
        assert [x['codigoOficial'] for x in doc['materia']['cursos']]==(['3163','3164'] if doc['materia']['codigo']=='CA' else ['3161','3162'])
        assert len(doc['desarrollos'])==(4 if doc['materia']['codigo']=='CA' else 2)
        ce_map={x['id']:x for x in doc['competenciasEspecificas']};ids=list(ce_map)
        def provenance(node,texts,code):
            origin=node['procedencia'];assert origin['fuenteRef']==SOURCE_IDS['O']
            numbers=origin['paginas'];assert numbers and numbers==sorted(set(numbers)) and all(n in pages['O'] for n in numbers)
            published=compact(' '.join(pages['O'][n] for n in numbers))
            for text,kind in texts:
                assert any(compact(candidate) in published for candidate in original_candidates(text,code,kind)),(code,node.get('id'),numbers,'procedencia')
                report['fragmentosProcedencia']+=1
        for ce in doc['competenciasEspecificas']:
            code=next(k for k,v in COMPONENT_NAMES.items() if v==ce['componente']['es'])
            provenance(ce,[(ce['enunciado']['es'],'competencia')]+[(x,'descripcion') for x in ce.get('descripcion',{}).get('es',[])],code)
            invalid=set(ce['descriptoresOperativosRefs'])-(valid_devas if code=='DEVAS' else valid_base)
            report['descriptorAnomalies'] += [[code,ce['id'],x] for x in invalid]
        for dev in doc['desarrollos']:
            for criterion in dev['criteriosEvaluacion']:
                ce=ce_map[criterion['competenciaEspecificaRef']]
                assert ce['codigoOficial']==criterion['codigoOficial'].split('.')[0] and not criterion['saberesBasicosRefs']
                code=next(k for k,v in COMPONENT_NAMES.items() if v==ce['componente']['es'])
                provenance(criterion,[(criterion['texto']['es'],'criterio')],code);ids.append(criterion['id'])
            for block in dev['bloquesSaberes']:
                code=next(k for k,v in COMPONENT_NAMES.items() if v==block['componente']['es'])
                for saber in leaves(block):
                    assert saber['codigoOficial'] is None
                    provenance(saber,[(saber['texto']['es'],'saber')],code);ids.append(saber['id'])
        assert len(ids)==len(set(ids)),doc['id']
    catalog=json.loads((ROOT/'sources/es-cb/normativa/catalogo.json').read_text(encoding='utf-8'))
    for source in catalog['documentos']:
        if source['id'] in SOURCE_IDS.values():
            assert hashlib.sha256((ROOT/'sources/es-cb/normativa'/source['archivo']).read_bytes()).hexdigest()==source['sha256']
    # Contraste de los códigos vigentes y de los dos supuestos de aplicación.
    def legal_text(key,first,last):
        path=ROOT/'sources/es-cb/normativa'/SOURCES[key][0]
        return compact(subprocess.check_output(['pdftotext','-layout','-enc','UTF-8','-f',str(first),'-l',str(last),str(path),'-'],text=True,encoding='utf-8'))
    code_update=legal_text('M',8,8)
    for old,new in [('3009','3163'),('3010','3164'),('3011','3161'),('3012','3162')]:
        assert 'Elcódigo'+old+'porelcódigo'+new in code_update
    application=legal_text('O',9,10)
    assert 'personasadultas,mayoresdediecisieteaños' in application
    assert 'autorizaciónparaadaptarlamateriadeCienciasAplicadas' in application
    assert 'nopodrásolicitarseestaautorización' in application
    report['counts']=dict(counts)
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'materias':2,'fragmentos':sum(counts.values()),'procedencia':report['fragmentosProcedencia'],**{key:len(report[key]) for key in ['schemaErrors','coverageDifferences','descriptorAnomalies','comparacionPublicaciones']}},ensure_ascii=False))
    if report['schemaErrors'] or report['coverageDifferences'] or report['descriptorAnomalies']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
