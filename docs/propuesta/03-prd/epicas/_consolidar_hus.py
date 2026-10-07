# Consolidador de HUs generadas en paralelo (workflow generar-historias-usuario, modo automático)
# 1) verifica archivos, 2) renumera HU-T{E}{NN} -> HU-### secuencial, 3) consolida asunciones, 4) actualiza epicas.md
import os, re, json, glob, sys, shutil
sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))           # .../03-prd/epicas
PRD = os.path.dirname(BASE)
EPICAS_MD = os.path.join(PRD, "epicas.md")
ASUN = os.path.join(PRD, "asunciones.md")
TPL_ASUN = r"C:\Users\juan.sierra\Documents\ComercialPropuestasenProceso\COMPRAS PUBLICAS\.ceiba-metodo\metodo-ceiba-ventas\workflows\generar-historias-usuario\data\template-asunciones.md"
DATE = "2026-10-02"
REQ = ["historia.md", "index.md", "cambios.md", "qa.md", "especificacion.md"]

def epic_dirs(): return sorted(d for d in glob.glob(os.path.join(BASE, "epica-00*")) if os.path.isdir(d))

# ---------- 1. verificación ----------
problems = []; order = []
for ed in epic_dirs():
    res = json.load(open(os.path.join(ed, "_resumen.json"), encoding="utf-8"))
    for f in res["features"]:
        for h in f["hus"]:
            hd = os.path.join(ed, h["carpeta"])
            for r in REQ:
                if not os.path.isfile(os.path.join(hd, r)): problems.append(f"{h['id']}: falta {r}")
            hs = os.path.join(hd, "historia.md")
            if os.path.isfile(hs):
                t = open(hs, encoding="utf-8").read()
                if len(t.encode("utf-8")) < 2048: problems.append(f"{h['id']}: historia.md < 2KB")
                for sec in ["Historia de Usuario", "Criterios de Aceptación", "Información Recopilada"]:
                    if sec not in t: problems.append(f"{h['id']}: falta sección {sec}")
            q = os.path.join(hd, "qa.md")
            if os.path.isfile(q):
                qt = open(q, encoding="utf-8").read()
                if "Matriz de Cobertura" not in qt or "QA-" not in qt: problems.append(f"{h['id']}: qa.md incompleto")
            order.append((ed, f["nombre"], h))
    if not os.path.isfile(os.path.join(ed, "README.md")): problems.append(f"{os.path.basename(ed)}: falta README.md")
print("Verificación:", "OK" if not problems else f"{len(problems)} problemas"); [print("  -", p) for p in problems]
if problems and "--force" not in sys.argv: sys.exit(1)


# ---------- 1b. enlaces: historia.md vive en epicas/epica-00X/HU-xxx/ -> epicas.md está 3 niveles arriba ----------
for hs in glob.glob(os.path.join(BASE, "epica-00*", "HU-*", "*.md")):
    t = open(hs, encoding="utf-8").read()
    t2 = re.sub(r"\]\((?:\.\./){2}epicas\.md", "](../../../epicas.md", t)
    if t2 != t: open(hs, "w", encoding="utf-8").write(t2)

# ---------- 2. renumeración ----------
mapping = {}; n = 0
for ed, feat, h in order:
    n += 1; mapping[h["id"]] = f"HU-{n:03d}"
def tmp_num(tid): return tid.replace("HU-", "")             # T101
def remap_text(t):
    # IDs largos primero para no reemplazar prefijos (HU-T110 antes que HU-T11)
    for old in sorted(mapping, key=len, reverse=True):
        new = mapping[old]
        t = t.replace(old, new)
        t = t.replace("#" + tmp_num(old), "#" + new.replace("HU-", ""))
    return t
for ed in epic_dirs():
    for path in glob.glob(os.path.join(ed, "**", "*.*"), recursive=True):
        if path.endswith((".md", ".json")):
            t = open(path, encoding="utf-8").read(); t2 = remap_text(t)
            if t2 != t: open(path, "w", encoding="utf-8").write(t2)
    for d in sorted(glob.glob(os.path.join(ed, "HU-T*")), key=len, reverse=True):
        name = os.path.basename(d); tid = re.match(r"(HU-T\d+)", name).group(1)
        os.rename(d, os.path.join(ed, name.replace(tid, mapping[tid], 1)))
print(f"Renumeradas {n} HU: HU-001 a HU-{n:03d}")

# ---------- 3. asunciones ----------
rows = []
for ed in epic_dirs():
    p = os.path.join(ed, "_asunciones_parciales.md")
    if not os.path.isfile(p): continue
    for line in open(p, encoding="utf-8"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 5 and not re.match(r"^-+$", cells[0]) and cells[0].lower() not in ("asunción", "asuncion"):
            rows.append((os.path.basename(ed), cells[:5]))
def norm(s): return re.sub(r"[^a-z0-9áéíóúñ ]", "", s.lower())[:90]
merged = []; seen = {}
for ep, (a, cat, hus, imp, est) in rows:
    k = norm(a)
    links = []
    for hid in re.findall(r"HU-\d{3}", hus):
        hd = glob.glob(os.path.join(BASE, ep, hid + "-*"))
        links.append(f"[{hid}](./epicas/{ep}/{os.path.basename(hd[0])}/historia.md)" if hd else hid)
    if k in seen: merged[seen[k]][2].extend(l for l in links if l not in merged[seen[k]][2]); continue
    seen[k] = len(merged); merged.append([a, cat, links, imp, est or "Resuelta"])
tpl = open(TPL_ASUN, encoding="utf-8").read().replace("{{project_name}}", "Seguimiento Compras Públicas").replace("{{date}}", DATE)
table = "\n".join(f"| A-{i:03d} | {a} | {cat} | {', '.join(l)} | {imp} | {est} |" for i, (a, cat, l, imp, est) in enumerate(merged, 1))
tpl = tpl.replace("|----|----------|-----------|-----------------|---------|--------|", "|----|----------|-----------|-----------------|---------|--------|\n" + table)
tpl = tpl.replace("**Total de asunciones:** 0", f"**Total de asunciones:** {len(merged)}")
open(ASUN, "w", encoding="utf-8").write(tpl)
print(f"asunciones.md: {len(merged)} asunciones (de {len(rows)} filas parciales)")

# ---------- 4. epicas.md ----------
em = open(EPICAS_MD, encoding="utf-8").read()
for ed in epic_dirs():
    res = json.load(open(os.path.join(ed, "_resumen.json"), encoding="utf-8"))
    eid = res["epica"]; ep = os.path.basename(ed)
    total = sum(len(f["hus"]) for f in res["features"])
    lines = []
    for f in res["features"]:
        for h in f["hus"]:
            hd = glob.glob(os.path.join(ed, h["id"] + "-*"))[0]
            lines.append(f"| {f['nombre']} | [{h['id']}](./epicas/{ep}/{os.path.basename(hd)}/historia.md) | {h['titulo']} | {h['prioridad']} |")
    block = f"""

---

## 📋 Historias de Usuario Generadas

**Estado:** ✅ Generadas (modo automático, autorizado por el PO)
**Total HU:** {total} historias
**Última actualización:** {DATE}

### Descomposición en Features:

| Feature | HU | Título | Prioridad |
|---|---|---|---|
""" + "\n".join(lines) + f"""

📁 [Ver todas las HU de esta épica](./epicas/{ep}/)
"""
    # ubicar la épica y su bloque de criterios; insertar antes del separador que cierra la épica
    m = re.search(r"(### " + re.escape(eid) + r":.*?\*\*Criterios de Aceptación de Épica\*\*.*?)(\n---\n)", em, re.S)
    assert m, eid
    seg = m.group(1)
    if "📋 Historias de Usuario Generadas" in seg: continue
    em = em[:m.end(1)] + block + em[m.end(1):]
open(EPICAS_MD, "w", encoding="utf-8").write(em)
print("epicas.md actualizado")
json.dump(mapping, open(os.path.join(BASE, "_mapa_renumeracion.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
