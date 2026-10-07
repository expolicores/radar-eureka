# D4a: muestra estratificada, inventario y priorización de documentos, descarga y perfil de capa de texto
import json, random, re, urllib.request, urllib.parse, sys, os, io, zipfile, hashlib, collections, logging
logging.disable(logging.WARNING)
sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.join(os.path.dirname(__file__), "..", "d4")
U = json.load(open(os.path.join(BASE, "universo_secop_tv.json"), encoding="utf-8"))
def q(ds, **p):
    u=f"https://www.datos.gov.co/resource/{ds}.json?"+urllib.parse.urlencode({"$"+k:v for k,v in p.items()})
    return json.load(urllib.request.urlopen(u, timeout=300))
DS={"2023":["3skv-9na7","dmgg-8hin"],"2024":["nbae-kzan","dmgg-8hin"],"2025":["dmgg-8hin"],"2026":["dmgg-8hin"]}
# 1) muestra estratificada por año (50), semilla fija
random.seed(2026)
by=collections.defaultdict(list)
for c in U: by[c["fecha_de_firma"][:4]].append(c)
cuota={"2023":13,"2024":13,"2025":13,"2026":11}
muestra=[]
for y,n in cuota.items(): muestra+=random.sample(by[y], n)
# 2) priorización de documentos
PRI=[(r"evaluaci[oó]n.*econ|econ[oó]mic.*evaluaci|informe.*evaluaci|evaluaci[oó]n", 9),
     (r"oferta.*econ|propuesta.*econ|econ[oó]mica|anexo.*econ|formato.*oferta", 8),
     (r"oferta|propuesta", 7),(r"aceptaci[oó]n", 6),(r"cotizaci", 5),
     (r"contrato|cto\b|clausulado|minuta|_firmado", 4),(r"estudio.*previo|estudios previos|an[aá]lisis.*sector", 3),
     (r"invitaci|pliego|condiciones t[eé]cnicas|ficha t[eé]cnica|especificaci", 2)]
EXC=r"(?i)cdp|disponibilidad presupuestal|p[oó]liza|garant[ií]a|rut\b|c[aá]mara de comercio|antecedente|cedula|c[eé]dula|registro presupuestal|\brp\b|acta de inicio|paz y salvo|seguridad social|parafiscal|certificado|aprobaci[oó]n|designaci|supervis|bpin|paa\b|plan anual|resoluci|estampilla|factura|acta de pago|liquidaci"
def score(f):
    t=(f.get("nombre_archivo","")+" "+f.get("descripci_n","")).lower()
    if re.search(EXC,t): return 0
    for pat,s in PRI:
        if re.search(pat,t): return s
    return 0
out=[]
for i,c in enumerate(muestra):
    y=c["fecha_de_firma"][:4]; fs=[]
    for ds in DS[y]:
        try: fs+=q(ds, where=f"proceso='{c['proceso_de_compra']}'", limit=500)
        except Exception as e: pass
    seen=set(); fs=[f for f in fs if not (f["id_documento"] in seen or seen.add(f["id_documento"]))]
    ranked=sorted([(score(f),f) for f in fs], key=lambda x:-x[0])
    sel=[f for s,f in ranked if s>0][:4]
    cdir=os.path.join(BASE,"documentos",c["id_contrato"].replace(".","_")); os.makedirs(cdir, exist_ok=True)
    docs=[]
    for f in sel:
        ext=(f.get("extensi_n") or "").lower(); url=f["url_descarga_documento"]["url"]
        fn=os.path.join(cdir, f"{f['id_documento']}.{ext}")
        try:
            if not os.path.exists(fn):
                data=urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"SeguimientoComprasPublicas-spike-D4"}),timeout=180).read()
                open(fn,"wb").write(data)
            data=open(fn,"rb").read()
            docs.append({"id_documento":f["id_documento"],"nombre":f["nombre_archivo"],"ext":ext,"prioridad":score(f),"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"url":url,"archivo":os.path.relpath(fn,BASE)})
        except Exception as e:
            docs.append({"id_documento":f["id_documento"],"nombre":f["nombre_archivo"],"ext":ext,"prioridad":score(f),"error":str(e)[:120]})
    out.append({"id_contrato":c["id_contrato"],"proceso":c["proceso_de_compra"],"anio":y,"entidad":c["nombre_entidad"],"objeto":c["objeto_del_contrato"][:300],
                "modalidad":c["modalidad_de_contratacion"],"valor":c.get("valor_del_contrato"),"unspsc":c.get("codigo_de_categoria_principal"),
                "docs_total":len(fs),"docs_priorizables":sum(1 for s,_ in ranked if s>0),"seleccionados":docs})
    print(f"{i+1:02d} {c['id_contrato']} {y} docs={len(fs)} prior={sum(1 for s,_ in ranked if s>0)} sel={len(docs)}", flush=True)
json.dump(out, open(os.path.join(BASE,"d4_muestra_inventario.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
