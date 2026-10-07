import urllib.request, sys, json, re, gzip, html
sys.stdout.reconfigure(encoding="utf-8")
UA={"User-Agent":"Mozilla/5.0 (compatible; research-spike-d6)","Accept":"text/html,application/xml,*/*","Accept-Encoding":"gzip"}
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90) as r:
        b=r.read()
        if b[:2]==b"\x1f\x8b": b=gzip.decompress(b)
        return b.decode("utf-8","ignore")
def jsonld(page):
    out=[]
    for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', page, re.S):
        try:
            d=json.loads(html.unescape(m.group(1).strip()))
            for x in (d if isinstance(d,list) else [d]):
                if isinstance(x,dict) and "@graph" in x: out+=x["@graph"]
                else: out.append(x)
        except Exception: pass
    return [x for x in out if isinstance(x,dict) and x.get("@type") in ("Product",["Product"])]
# ALKOSTO
sm=get("https://www.alkosto.com/sitemap-productos.xml")
locs=re.findall(r"<loc>(https://www.alkosto.com/[^<]+/p/\d+)</loc>", sm)
tvs=[u for u in locs if re.search(r"(?i)/(televisor|tv-|smart-tv|led-|qled|oled)", u)]
print("ALKOSTO sitemap productos:",len(locs),"| URLs tipo TV:",len(tvs)); print("  ej:",tvs[:3])
if tvs:
    pg=get(tvs[0]); pr=jsonld(pg)
    print("  JSON-LD Product:", json.dumps(pr[:1],ensure_ascii=False)[:900] if pr else "NO")
# FALABELLA
idx=get("https://www.falabella.com.co/static/site/sitemaps/pdp/pdp_co_FA_COM-index.xml")
subs=re.findall(r"<loc>([^<]+)</loc>", idx); print("\nFALABELLA pdp sitemaps:",len(subs))
found=[]
for s in subs[:6]:
    t=get(s); us=re.findall(r"<loc>([^<]+)</loc>", t)
    found+= [u for u in us if re.search(r"(?i)televisor|smart-tv|-tv-", u)]
    if len(found)>3: break
print("  URLs TV en primeros sitemaps:",len(found),"ej:",found[:2])
if found:
    try:
        pg=get(found[0]); pr=jsonld(pg); print("  JSON-LD Product:", json.dumps(pr[:1],ensure_ascii=False)[:900] if pr else "NO")
    except Exception as e: print("  err",e)
