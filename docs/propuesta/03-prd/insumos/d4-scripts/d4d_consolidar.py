# D4d: consolida las extracciones de los 50 contratos en métricas de disponibilidad y cobertura
import json, os, glob, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
B=os.path.join(os.path.dirname(__file__),"..","d4")
M={c["id_contrato"]:c for c in json.load(open(os.path.join(B,"d4_muestra_inventario.json"),encoding="utf-8"))}
P={p["id_contrato"]:p for p in json.load(open(os.path.join(B,"d4_perfil_documentos.json"),encoding="utf-8"))}
CAMPOS=["marca","modelo","tamano_pulgadas","cantidad","precio_unitario"]
def nn(v): return v not in (None,"",[],{})
rows=[]; C=collections.Counter(); campo=collections.Counter(); conf=collections.Counter(); iva=collections.Counter(); tp=collections.Counter()
ofer_unit=ofer_tot=0; imgs=0; ev_ok=ev_tot=0; incons=0
for f in sorted(glob.glob(os.path.join(B,"extraccion","*.json"))):
    d=json.load(open(f,encoding="utf-8")); cid=d.get("id_contrato") or os.path.basename(f)[:-5]
    items=[i for i in d.get("items",[]) if isinstance(i,dict)]
    real=[i for i in items if any(nn(i.get(k)) for k in ["precio_unitario","cantidad","tamano_pulgadas","marca","modelo","descripcion"])]
    if not items: cat="fuera_de_categoria_o_sin_tv"
    elif not any(nn(i.get("precio_unitario")) for i in items): cat="tv_sin_precio_unitario"
    else:
        tps={(i.get("tipo_precio") or "").lower() for i in items if nn(i.get("precio_unitario"))}
        cat="tv_precio_adjudicado" if tps & {"adjudicado","contratado"} else "tv_solo_presupuesto_o_cotizacion"
    C[cat]+=1
    for i in items:
        if not nn(i.get("precio_unitario")) and not nn(i.get("cantidad")) and not nn(i.get("tamano_pulgadas")): continue
        C["items_tv_con_datos"]+=1
        for k in CAMPOS:
            if nn(i.get(k)):
                campo[k]+=1; conf[(k,(i.get("confianza") or {}).get(k,"s/d"))]+=1
                ev_tot+=1; ev_ok+= 1 if nn((i.get("evidencia") or {}).get(k)) else 0
        if nn(i.get("precio_unitario")): iva[i.get("iva") or "s/d"]+=1; tp[i.get("tipo_precio") or "s/d"]+=1
    ofs=d.get("oferentes") or []
    if len(ofs)>=2:
        ofer_tot+=1
        if sum(1 for o in ofs if nn(o.get("precio_unitario")))>=2: ofer_unit+=1
    imgs+=int(d.get("imagenes_leidas") or 0); incons+=len(d.get("inconsistencias") or [])
    rows.append({"id_contrato":cid,"anio":M.get(cid,{}).get("anio"),"modalidad":M.get(cid,{}).get("modalidad"),"unspsc_52161505":"52161505" in (M.get(cid,{}).get("unspsc") or ""),
                 "categoria_resultado":cat,"items":len(items),"requirio_imagen":bool(d.get("requirio_imagen")),"imagenes_leidas":d.get("imagenes_leidas"),"oferentes":len(ofs),"obs":(d.get("observaciones") or "")[:200]})
n=len(rows); en_cat=n-C["fuera_de_categoria_o_sin_tv"]
R={"contratos_extraidos":n,"resultado_por_contrato":{k:C[k] for k in ["fuera_de_categoria_o_sin_tv","tv_sin_precio_unitario","tv_solo_presupuesto_o_cotizacion","tv_precio_adjudicado"]},
   "contratos_en_categoria":en_cat,"cobertura_precio_unitario_adjudicado_sobre_en_categoria_pct":round(100*C["tv_precio_adjudicado"]/max(1,en_cat),1),
   "cobertura_cualquier_precio_unitario_sobre_en_categoria_pct":round(100*(C["tv_precio_adjudicado"]+C["tv_solo_presupuesto_o_cotizacion"])/max(1,en_cat),1),
   "items_tv_con_datos":C["items_tv_con_datos"],"campos_presentes_en_items":dict(campo),"confianza_por_campo":{f"{k}|{v}":c for (k,v),c in sorted(conf.items())},
   "iva_en_items_con_precio":dict(iva),"tipo_precio":dict(tp),"evidencia_completa_pct":round(100*ev_ok/max(1,ev_tot),1),
   "contratos_con_>=2_oferentes":ofer_tot,"contratos_con_precio_unitario_de_>=2_oferentes":ofer_unit,"imagenes_leidas_total":imgs,"inconsistencias_registradas":incons}
# fuera de categoría según UNSPSC
fc=[r for r in rows if r["categoria_resultado"]=="fuera_de_categoria_o_sin_tv"]
R["fuera_categoria_con_unspsc_52161505"]=sum(r["unspsc_52161505"] for r in fc); R["fuera_categoria_solo_texto"]=len(fc)-R["fuera_categoria_con_unspsc_52161505"]
json.dump({"resumen":R,"por_contrato":rows},open(os.path.join(B,"d4_resultados_extraccion.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
for k,v in R.items(): print(f"{k}: {v}")
