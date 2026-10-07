import urllib.request, sys, re
sys.stdout.reconfigure(encoding="utf-8")
UA={"User-Agent":"Mozilla/5.0 (compatible; research-spike-d6)","Accept":"application/json,text/plain,*/*"}
def hit(u, n=350, show=True):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40) as r:
            b=r.read(); print(f"[{r.status}] {u} ct={r.headers.get('Content-Type')} len={len(b)}")
            if show: print("   ",b[:n])
            return b
    except urllib.error.HTTPError as e: print(f"[{e.code}] {u}", e.read()[:200])
    except Exception as e: print(f"[ERR] {u} {e}")
for site in ["https://www.exito.com","https://www.alkosto.com","https://www.falabella.com.co"]:
    print("\n####",site)
    b=hit(site+"/robots.txt", show=False)
    if b:
        t=b.decode("utf-8","ignore")
        lines=[l for l in t.splitlines() if re.match(r"(?i)(user-agent|disallow|allow|sitemap)",l.strip())]
        print("   robots (primeras líneas relevantes):"); [print("     ",l) for l in lines[:25]]
        print("    ... total líneas:",len(lines), "| menciona /api:", "/api" in t)
print("\n#### VTEX público Éxito")
hit("https://www.exito.com/api/catalog_system/pub/products/search?ft=televisor%2055&_from=0&_to=1", 600)
hit("https://www.exito.com/api/io/_v/api/intelligent-search/product_search/?query=televisor&count=1", 300)
