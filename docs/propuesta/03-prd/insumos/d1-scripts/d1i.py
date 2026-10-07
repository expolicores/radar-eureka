import json, urllib.request, urllib.parse, sys, random, re, io, pypdf, logging
logging.disable(logging.WARNING)
sys.stdout.reconfigure(encoding="utf-8")
def q(ds, **p):
    u=f"https://www.datos.gov.co/resource/{ds}.json?"+urllib.parse.urlencode({"$"+k:v for k,v in p.items()})
    with urllib.request.urlopen(u, timeout=300) as r: return json.load(r)
for s in ["Tienda Virtual detalle","TVEC items","Grandes Superficies","ordenes de compra TVEC"]:
    d=json.load(urllib.request.urlopen("https://api.us.socrata.com/api/catalog/v1?domains=www.datos.gov.co&limit=8&q="+urllib.parse.quote(s),timeout=60))
    print("==",s,[ (r['resource']['id'],r['resource']['name']) for r in d['results']][:8])
cs=json.load(open("d1_tv_contracts.json",encoding="utf-8"))
random.seed(7); smp=random.sample([c for c in cs if c['fecha_de_firma']>='2025'],18)
KEY=re.compile(r"(?i)oferta|econ|cotiz|propuesta|precio|contrato|cto|aceptaci|estudio|invitaci")
res=[]
for c in smp:
    fs=q("dmgg-8hin", where=f"proceso='{c['proceso_de_compra']}' AND extensi_n='pdf'", limit=200)
    fs=[f for f in fs if KEY.search(f['nombre_archivo'])][:2]
    for f in fs:
        try:
            req=urllib.request.Request(f["url_descarga_documento"]["url"], headers={"User-Agent":"Mozilla/5.0 (research spike)"})
            data=urllib.request.urlopen(req,timeout=120).read()
            r=pypdf.PdfReader(io.BytesIO(data)); n=len(r.pages); k=min(n,5)
            ch=sum(len((p.extract_text() or "").strip()) for p in r.pages[:k])/k
            txt=" ".join((p.extract_text() or "") for p in r.pages[:k])
            ocr_noise=len(re.findall(r"[a-z][0-9][a-z]|[a-z]6n\b", txt))
            res.append((f['nombre_archivo'][:45], n, int(ch), ocr_noise))
        except Exception as e: res.append((f['nombre_archivo'][:45],'ERR',str(e)[:40],0))
for r in res: print("  ",r)
ok=[r for r in res if r[1]!='ERR']
print("PDFs:",len(ok)," texto (>300 car/pag):",sum(r[2]>300 for r in ok)," sin texto (<50):",sum(r[2]<50 for r in ok)," con ruido OCR:",sum(r[3]>3 for r in ok))
