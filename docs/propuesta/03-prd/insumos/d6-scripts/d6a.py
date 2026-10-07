import urllib.request, json, sys, ssl
sys.stdout.reconfigure(encoding="utf-8")
UA={"User-Agent":"Mozilla/5.0 (compatible; research-spike-d6)","Accept":"application/json"}
def hit(u, n=400):
    try:
        req=urllib.request.Request(u, headers=UA)
        with urllib.request.urlopen(req, timeout=40) as r:
            b=r.read(); print(f"[{r.status}] {u}\n   ct={r.headers.get('Content-Type')} len={len(b)}\n   {b[:n]!r}")
            return b
    except urllib.error.HTTPError as e:
        print(f"[{e.code}] {u}\n   {e.read()[:n]!r}")
    except Exception as e: print(f"[ERR] {u} {e}")
print("### MERCADO LIBRE")
hit("https://api.mercadolibre.com/sites/MCO/search?q=televisor%2055%20pulgadas&limit=2")
hit("https://api.mercadolibre.com/sites/MCO/domain_discovery/search?q=televisor%2055")
hit("https://api.mercadolibre.com/products/search?status=active&site_id=MCO&q=Samsung%20UN55")
hit("https://api.mercadolibre.com/sites/MCO/categories", 300)
