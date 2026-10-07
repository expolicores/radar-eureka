import sys, glob, re, pypdf, openpyxl
sys.stdout.reconfigure(encoding="utf-8")
for fn in sorted(glob.glob("docs/*")):
    print("\n#####", fn)
    if fn.endswith(".xlsx"):
        wb=openpyxl.load_workbook(fn, data_only=True)
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                if any(v not in (None,"") for v in row): print("  ", [v for v in row if v not in (None,"")])
        continue
    r=pypdf.PdfReader(fn); n=len(r.pages)
    txt="\n".join((p.extract_text() or "") for p in r.pages[:6])
    chars=len(txt.strip())
    print(f"  pages={n} chars_first6={chars} -> {'TEXTO' if chars>200*min(n,6) else 'POSIBLE ESCANEADO/IMAGEN'}")
    lines=[l for l in txt.splitlines() if re.search(r"(?i)televisor|tv|pulgad|\$|precio|valor unit|cantidad|iva|samsung|lg|hisense|kalley|challenger", l)]
    for l in lines[:18]: print("   >", l.strip()[:160])
