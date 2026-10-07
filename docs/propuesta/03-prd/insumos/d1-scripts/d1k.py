import json, urllib.request, urllib.parse, sys, re, collections
sys.stdout.reconfigure(encoding="utf-8")
def q(ds, **p): return json.load(urllib.request.urlopen(f"https://www.datos.gov.co/resource/{ds}.json?"+urllib.parse.urlencode({"$"+k:v for k,v in p.items()}), timeout=300))
W="(upper(item) like '%TELEVISOR%' OR upper(item) like '% TV %' OR upper(item) like '%SMART TV%') AND upper(item) not like '%MANTENIMIENTO%' AND upper(item) not like '%SOPORTE%' AND upper(item) not like '%CABLE%' AND upper(item) not like '%CONTROL%' AND fecha >= '2023-01-01'"
rows=q("3hdv-smhz", select="orden_de_compra,fecha,item,price,qty", where=W, limit=10000)
print("Lineas TV TVEC 2023+:",len(rows))
by=collections.Counter(r['fecha'][:4] for r in rows); print(" por año:",sorted(by.items()))
print(" unidades:", sum(float(r['qty']) for r in rows), "| ordenes:", len({r['orden_de_compra'] for r in rows}))
model=re.compile(r"\b(?=[A-Z0-9]*\d)(?=[A-Z0-9]*[A-Z])[A-Z0-9]{6,}\b")
withm=[r for r in rows if model.search(r['item'].upper().replace("4K","").replace("UHD",""))]
print(" con codigo de modelo probable:",len(withm), f"({100*len(withm)//max(1,len(rows))}%)")
inch=[r for r in rows if re.search(r"\b(2[4-9]|[3-9]\d)\s*(\"|”|''|PULG|PULGADAS|IN\b)|\b(32|40|43|50|55|58|60|65|70|75|85)\b", r['item'].upper())]
print(" con tamaño identificable:",len(inch))
brands=collections.Counter()
for r in rows:
    for b in ["SAMSUNG","LG","TCL","HISENSE","KALLEY","CHALLENGER","SONY","XIAOMI","PANASONIC","PHILIPS","AIWA","JVC","CAIXUN"]:
        if b in r['item'].upper(): brands[b]+=1; break
print(" marcas:",brands.most_common(10))
for r in withm[:8]: print("   ",r['fecha'][:10],r['price'],r['qty'],"|",r['item'][:90])
json.dump(rows,open("d1_tvec_tv.json","w",encoding="utf-8"),ensure_ascii=False)
