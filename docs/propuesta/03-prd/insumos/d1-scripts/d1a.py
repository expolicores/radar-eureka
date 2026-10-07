import json, urllib.request, urllib.parse
def get(u):
    with urllib.request.urlopen(u, timeout=90) as r: return json.load(r)
for q in ["SECOP II items","Tienda Virtual del Estado","Archivos Descarga","SECOP II ofertas"]:
    d=get("https://api.us.socrata.com/api/catalog/v1?domains=www.datos.gov.co&limit=15&q="+urllib.parse.quote(q))
    print("==",q)
    for r in d["results"]:
        x=r["resource"]; print(" ",x["id"],"|",x["name"],"|",(x.get("data_updated_at") or "")[:10])
