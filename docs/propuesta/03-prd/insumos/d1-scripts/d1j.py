import json, urllib.request, urllib.parse, sys
sys.stdout.reconfigure(encoding="utf-8")
def get(u): return json.load(urllib.request.urlopen(u, timeout=300))
def q(ds, **p): return get(f"https://www.datos.gov.co/resource/{ds}.json?"+urllib.parse.urlencode({"$"+k:v for k,v in p.items()}))
for i in ["3hdv-smhz","usqp-5nsn"]:
    v=get(f"https://www.datos.gov.co/api/views/{i}.json")
    cols=[c["fieldName"] for c in v["columns"] if not c["fieldName"].startswith(":")]
    print("==",i,v["name"],"| actualizado:",v.get("rowsUpdatedAt"),"\n  cols:",cols)
    print("  rows:",q(i,select="count(*)"))
    tcol=[c for c in cols if "item" in c or "producto" in c or "nombre" in c or "descrip" in c]
    print("  text cols:",tcol)
    for t in tcol[:2]:
        try:
            r=q(i, where=f"upper({t}) like '%TELEVISOR%'", limit=4); print("  muestra TV via",t); [print("    ",x) for x in r]
            print("  count TV:", q(i, select="count(*)", where=f"upper({t}) like '%TELEVISOR%'"))
            break
        except Exception as e: print("  err",t,str(e)[:80])
