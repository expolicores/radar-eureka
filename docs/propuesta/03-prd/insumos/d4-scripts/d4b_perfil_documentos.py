# D4b: perfil de documentos (texto vs escaneo), expansión de zip, paquetes de texto con marcas de página e imágenes de páginas escaneadas
import json, os, sys, io, zipfile, re, logging
logging.disable(logging.WARNING)
import pymupdf, openpyxl, docx
sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.join(os.path.dirname(__file__), "..", "d4")
M = json.load(open(os.path.join(BASE,"d4_muestra_inventario.json"), encoding="utf-8"))
MAXIMG_PAGES = 6       # páginas escaneadas a renderizar por documento
MAXTXT_PAGES = 25      # páginas de texto a volcar por documento
def pdf_profile(data, label, cdir, stem, bundle, imgs):
    d = pymupdf.open(stream=data, filetype="pdf"); n = len(d); txt_pages = scan_pages = 0; rendered = 0
    for i, pg in enumerate(d):
        t = pg.get_text().strip()
        if len(t) >= 50:
            txt_pages += 1
            if i < MAXTXT_PAGES: bundle.append(f"\n----- [{label} | página {i+1}] -----\n{t}")
        else:
            scan_pages += 1
            if rendered < MAXIMG_PAGES:
                fn = os.path.join(cdir, f"{stem}_p{i+1}.png"); pg.get_pixmap(dpi=110).save(fn); rendered += 1
                imgs.append(os.path.relpath(fn, BASE)); bundle.append(f"\n----- [{label} | página {i+1}] ----- (SIN CAPA DE TEXTO: ver imagen {os.path.basename(fn)})")
    return {"paginas": n, "paginas_texto": txt_pages, "paginas_escaneadas": scan_pages}
def handle(data, ext, label, cdir, stem, bundle, imgs):
    ext = ext.lower()
    if ext == "pdf": return pdf_profile(data, label, cdir, stem, bundle, imgs)
    if ext in ("xlsx","xlsm"):
        wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True); rows = 0
        for ws in wb.worksheets:
            for r_i, row in enumerate(ws.iter_rows(values_only=True), 1):
                vals = [str(v) for v in row if v not in (None, "")]
                if vals: rows += 1; bundle.append(f"[{label} | hoja {ws.title} | fila {r_i}] " + " | ".join(vals))
        return {"tipo": "xlsx", "filas": rows}
    if ext == "docx":
        dd = docx.Document(io.BytesIO(data)); paras = [p.text for p in dd.paragraphs if p.text.strip()]
        for t_i, tb in enumerate(dd.tables, 1):
            for r_i, row in enumerate(tb.rows, 1):
                paras.append(f"[tabla {t_i} fila {r_i}] " + " | ".join(c.text.strip() for c in row.cells))
        bundle.append(f"\n----- [{label}] -----\n" + "\n".join(paras)); return {"tipo": "docx", "parrafos": len(paras)}
    if ext in ("jpg","jpeg","png"):
        fn = os.path.join(cdir, f"{stem}.{ext}"); open(fn,"wb").write(data); imgs.append(os.path.relpath(fn, BASE))
        bundle.append(f"\n----- [{label}] ----- (IMAGEN: {os.path.basename(fn)})"); return {"tipo": "imagen", "paginas_escaneadas": 1, "paginas": 1}
    return {"tipo": ext, "no_soportado": True}
res = []
for c in M:
    cdir = os.path.join(BASE, "documentos", c["id_contrato"].replace(".","_")); bundle = [f"# Contrato {c['id_contrato']} | proceso {c['proceso']} | {c['entidad']} | {c['anio']}\n# Objeto: {c['objeto']}\n# Valor del contrato (datos abiertos): {c['valor']} | modalidad: {c['modalidad']}"]; imgs = []; perf = []
    for d in c["seleccionados"]:
        if "error" in d: perf.append({"doc": d["nombre"], "error": d["error"]}); continue
        data = open(os.path.join(BASE, d["archivo"]), "rb").read(); stem = d["id_documento"]
        try:
            if d["ext"] == "zip":
                z = zipfile.ZipFile(io.BytesIO(data)); inner = []
                for zi in z.infolist()[:15]:
                    e = zi.filename.rsplit(".",1)[-1].lower() if "." in zi.filename else ""
                    if e in ("pdf","xlsx","docx","jpg","jpeg","png"):
                        p = handle(z.read(zi), e, f"{d['nombre']} > {zi.filename}", cdir, f"{stem}_{len(inner)}", bundle, imgs); p["doc"] = f"{d['nombre']} > {zi.filename}"; inner.append(p)
                perf += inner or [{"doc": d["nombre"], "tipo": "zip", "vacio_o_no_soportado": True}]
            else:
                p = handle(data, d["ext"], d["nombre"], cdir, stem, bundle, imgs); p["doc"] = d["nombre"]; perf.append(p)
        except Exception as e:
            perf.append({"doc": d["nombre"], "error": str(e)[:120]})
    txt = "\n".join(bundle); open(os.path.join(cdir, "_texto_para_extraccion.md"), "w", encoding="utf-8").write(txt)
    multi = bool(re.search(r"(?is)evaluaci[oó]n.{0,40}econ|cuadro comparativo|consolidado.{0,20}ofert|precio.{0,30}oferentes|orden de elegibilidad", txt))
    res.append({"id_contrato": c["id_contrato"], "perfil": perf, "imagenes": imgs, "chars_texto": len(txt), "indicio_multi_oferentes": multi})
    print(c["id_contrato"], "docs", len(perf), "img", len(imgs), "chars", len(txt), "multi", multi, flush=True)
json.dump(res, open(os.path.join(BASE, "d4_perfil_documentos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
