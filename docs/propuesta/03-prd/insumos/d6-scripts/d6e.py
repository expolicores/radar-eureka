import json, re, sys, urllib.request, gzip, subprocess, collections
sys.stdout.reconfigure(encoding="utf-8")
rows=json.load(open("d1_tvec_tv.json",encoding="utf-8"))
pat=re.compile(r"\b(?=[A-Z0-9-]*\d)(?=[A-Z0-9-]*[A-Z])[A-Z0-9][A-Z0-9-]{5,}\b")
STOP={"4K-UHD","180006001","GSF01","GSF01-TV"}
models=collections.Counter()
for r in rows:
    if r['fecha']<'2025-01-01': continue
    for m in pat.findall(r['item'].upper()):
        if m in STOP or m.isdigit() or m.startswith("GSF") or re.fullmatch(r"\d+[A-Z]{0,2}",m) or len(m)<6: continue
        models[m.replace("-","")]+=1
top=[m for m,_ in models.most_common(25)]
print("Modelos TVEC 2025+ distintos:",len(models)," top:",top[:25])
A="Mozilla/5.0 (compatible; research-spike-d6)"
alk=subprocess.run(["curl","-s","-m","90","-A",A,"--compressed","https://www.alkosto.com/sitemap-productos.xml"],capture_output=True,text=True,encoding="utf-8").stdout.upper().replace("-","")
fa=open("fa0.xml",encoding="utf-8",errors="ignore").read().upper().replace("-","")
hits=[]
for m in top:
    core=m[:9]  # tolerar sufijos de región
    a= core in alk; f= core in fa
    hits.append((m,a,f))
for h in hits: print("  ",h)
print("Encontrados en Alkosto sitemap:",sum(h[1] for h in hits),"/",len(hits)," | Falabella (1 de N sitemaps):",sum(h[2] for h in hits))
