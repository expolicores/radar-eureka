import urllib.request, sys, json, re, gzip
sys.stdout.reconfigure(encoding="utf-8")
UA={"User-Agent":"Mozilla/5.0 (compatible; research-spike-d6)","Accept":"application/json,text/html,*/*"}
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
        b=r.read()
        if r.headers.get("Content-Encoding")=="gzip" or b[:2]==b"\x1f\x8b": b=gzip.decompress(b)
        return r.status, b
st,b=get("https://www.exito.com/api/catalog_system/pub/products/search?ft=televisor%2055%20pulgadas&_from=0&_to=9")
ps=json.loads(b); print("ÉXITO VTEX productos:",len(ps))
print("  claves producto:", list(ps[0].keys())[:40])
for p in ps[:10]:
    it=p["items"][0]; sel=it["sellers"]
    s0=sel[0]; co=s0["commertialOffer"]
    specs={k:p.get(k) for k in p.get("allSpecifications",[]) if re.search(r"(?i)modelo|referencia|tama|pulg|resoluci|tecnolog",k)}
    print(f"  - {p['brand']} | {p['productName'][:60]} | seller={s0['sellerName']} | Price={co.get('Price')} List={co.get('ListPrice')} Tax={co.get('Tax')} | ean={it.get('ean')} | specs={ {k:(v[0] if isinstance(v,list) else v) for k,v in list(specs.items())[:4]} }")
