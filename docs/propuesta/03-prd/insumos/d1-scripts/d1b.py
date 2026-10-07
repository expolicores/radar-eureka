import json, urllib.request, sys
sys.stdout.reconfigure(encoding="utf-8")
def get(u):
    with urllib.request.urlopen(u, timeout=120) as r: return json.load(r)
ids=["p6dx-8zbt","jbjy-vk9h","dmgg-8hin","nbae-kzan","rgxm-mmea","rpmr-utcd"]
out={}
for i in ids:
    v=get(f"https://www.datos.gov.co/api/views/{i}.json")
    cols=[(c["fieldName"],c["dataTypeName"]) for c in v["columns"] if not c["fieldName"].startswith(":")]
    try: n=get(f"https://www.datos.gov.co/resource/{i}.json?$select=count(*)")[0]
    except Exception as e: n=str(e)
    out[i]={"name":v["name"],"rows":n,"cols":cols,"desc":(v.get("description") or "")[:300]}
    print("==",i,v["name"],"| rows:",n)
    print("  ", ", ".join(f for f,_ in cols))
json.dump(out,open("d1_meta.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
