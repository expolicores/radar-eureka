import json, os, sys, collections, statistics as st
sys.stdout.reconfigure(encoding="utf-8")
B=os.path.join(os.path.dirname(__file__),"..","d4")
M=json.load(open(os.path.join(B,"d4_muestra_inventario.json"),encoding="utf-8")); P={p["id_contrato"]:p for p in json.load(open(os.path.join(B,"d4_perfil_documentos.json"),encoding="utf-8"))}
n=len(M); docs_tot=[c["docs_total"] for c in M]; pri=[c["docs_priorizables"] for c in M]
sel=sum(len(c["seleccionados"]) for c in M); err=sum(1 for c in M for d in c["seleccionados"] if "error" in d)
ext=collections.Counter(d["ext"] for c in M for d in c["seleccionados"])
pages=txt=scan=0; docs_pdf=docs_scan_any=docs_full_scan=0; noimpl=0; perdoc_pages=[]
for c in M:
    for p in P[c["id_contrato"]]["perfil"]:
        if p.get("no_soportado") or p.get("vacio_o_no_soportado"): noimpl+=1
        if "paginas" in p:
            docs_pdf+=1; pages+=p["paginas"]; txt+=p.get("paginas_texto",0); scan+=p.get("paginas_escaneadas",0); perdoc_pages.append(p["paginas"])
            if p.get("paginas_escaneadas",0)>0: docs_scan_any+=1
            if p.get("paginas_escaneadas",0)==p["paginas"]: docs_full_scan+=1
contr_scan=sum(1 for c in M if P[c["id_contrato"]]["imagenes"]); multi=sum(1 for c in M if P[c["id_contrato"]]["indicio_multi_oferentes"])
chars=[P[c["id_contrato"]]["chars_texto"] for c in M]; imgs=sum(len(P[c["id_contrato"]]["imagenes"]) for c in M)
R={"contratos":n,"docs_por_proceso_mediana":st.median(docs_tot),"docs_por_proceso_rango":[min(docs_tot),max(docs_tot)],
 "docs_priorizables_mediana":st.median(pri),"contratos_con_<2_priorizables":sum(1 for x in pri if x<2),
 "docs_seleccionados":sel,"descargas_fallidas":err,"extensiones_seleccionadas":dict(ext),
 "documentos_paginados_perfilados":docs_pdf,"paginas_totales":pages,"paginas_con_texto":txt,"paginas_escaneadas":scan,
 "pct_paginas_escaneadas":round(100*scan/max(1,pages),1),"docs_con_alguna_pagina_escaneada":docs_scan_any,"docs_100pct_escaneados":docs_full_scan,
 "paginas_por_doc_mediana":st.median(perdoc_pages),"contratos_que_requieren_imagen":contr_scan,"imagenes_renderizadas":imgs,
 "archivos_no_soportados":noimpl,"contratos_con_indicio_multi_oferentes(heuristica)":multi,
 "chars_texto_por_contrato_mediana":st.median(chars),"chars_texto_por_contrato_p90":sorted(chars)[int(.9*n)]}
json.dump(R,open(os.path.join(B,"d4_metricas_documentales.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
for k,v in R.items(): print(f"{k}: {v}")
