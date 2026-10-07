import json, urllib.request, urllib.parse, sys, os
sys.stdout.reconfigure(encoding="utf-8")
def q(ds, **p):
    u=f"https://www.datos.gov.co/resource/{ds}.json?"+urllib.parse.urlencode({"$"+k:v for k,v in p.items()})
    with urllib.request.urlopen(u, timeout=240) as r: return json.load(r)
targets={"CO1.BDOS.10732896":["Anexo No 2 oferta economica.xlsx","CO1_PCCNTR_9895282_Firmado"],
         "CO1.BDOS.10714848":["EVALUACION VALOR ECONOMICA","CONDICIONES TECNICAS"],
         "CO1.BDOS.10818522":["COTIZACIONES","CTO 168-2026"]}
for proc,names in targets.items():
    fs=q("dmgg-8hin", where=f"proceso='{proc}'", limit=100)
    for f in fs:
        if any(n in f["nombre_archivo"] for n in names):
            url=f["url_descarga_documento"]["url"]
            fn="docs/"+f["id_documento"]+"."+f["extensi_n"]
            req=urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (research spike)"})
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    data=r.read(); ct=r.headers.get("Content-Type")
                open(fn,"wb").write(data)
                print(proc,"|",f["nombre_archivo"][:60],"|",ct,"|",len(data),"bytes | head:",data[:8])
            except Exception as e:
                print(proc,"|",f["nombre_archivo"][:60],"| ERROR",e)
