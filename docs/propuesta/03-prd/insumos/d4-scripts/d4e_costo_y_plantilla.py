# D4e: estimación de tokens/costo por contrato y plantilla de validación manual (ground truth) para el PO
import json, os, glob, sys, statistics as st
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation
sys.stdout.reconfigure(encoding="utf-8")
B=os.path.join(os.path.dirname(__file__),"..","d4")
P={p["id_contrato"]:p for p in json.load(open(os.path.join(B,"d4_perfil_documentos.json"),encoding="utf-8"))}
M={c["id_contrato"]:c for c in json.load(open(os.path.join(B,"d4_muestra_inventario.json"),encoding="utf-8"))}
# --- costo: enviar todo el paquete priorizado (texto + imágenes) en una llamada por contrato
TOK_IMG=1500; TOK_OUT=2000; PRICES={"Haiku 4.5":(1,5),"Sonnet 5.5":(2,10),"Opus 5.5":(4,20)}
inp=[P[c]["chars_texto"]/3.5 + len(P[c]["imagenes"])*TOK_IMG for c in P]
med, p90, tot = st.median(inp), sorted(inp)[int(.9*len(inp))], sum(inp)
cost={m:{"usd_por_contrato_mediana":round((med*i+TOK_OUT*o)/1e6,4),"usd_por_contrato_p90":round((p90*i+TOK_OUT*o)/1e6,4),
         "usd_universo_355_contratos":round((tot/len(inp)*355*i+355*TOK_OUT*o)/1e6,2)} for m,(i,o) in PRICES.items()}
R={"supuestos":{"tokens_por_caracter":"1/3,5 (texto en español)","tokens_por_imagen":TOK_IMG,"tokens_salida_por_contrato":TOK_OUT,"nota":"No incluye tokens de razonamiento (thinking), reintentos ni caché; multiplicar ×1,5–3 como margen."},
   "tokens_entrada_por_contrato":{"mediana":round(med),"p90":round(p90),"max":round(max(inp))},"costo_estimado":cost}
json.dump(R,open(os.path.join(B,"d4_costo_estimado.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(json.dumps(R,ensure_ascii=False,indent=1))
# --- plantilla de validación
wb=openpyxl.Workbook(); ws=wb.active; ws.title="Validación por campo"
H=["id_contrato","entidad","año","item_n","descripcion_extraida","campo","valor_extraido","confianza","evidencia (documento | página)","carpeta_documentos","VALOR_CORRECTO (PO)","RESULTADO (PO)","NOTA (PO)"]
ws.append(H)
CAMPOS=["marca","modelo","tamano_pulgadas","cantidad","precio_unitario","iva"]
n=0
for f in sorted(glob.glob(os.path.join(B,"extraccion","*.json"))):
    d=json.load(open(f,encoding="utf-8")); cid=d.get("id_contrato") or os.path.basename(f)[:-5]
    for k,i in enumerate([x for x in d.get("items",[]) if isinstance(x,dict)],1):
        for c in CAMPOS:
            v=i.get(c); ev=(i.get("evidencia") or {}).get(c); cf=(i.get("confianza") or {}).get(c)
            ws.append([cid,M.get(cid,{}).get("entidad"),M.get(cid,{}).get("anio"),k,(i.get("descripcion") or "")[:120],c,"" if v is None else str(v),cf,ev,"documentos/"+cid.replace(".","_"),"","",""]); n+=1
dv=DataValidation(type="list",formula1='"correcto,incorrecto,ausente_y_no_extraido,inventado,no_verificable"',allow_blank=True); ws.add_data_validation(dv); dv.add(f"L2:L{n+1}")
ws2=wb.create_sheet("Validación por contrato")
ws2.append(["id_contrato","entidad","objeto","resultado_extractor","¿ES COMPRA DE TV EN CATEGORÍA? (PO: si/no)","¿EXISTE PRECIO UNITARIO EN DOCUMENTOS? (PO: si/no)","NOTA (PO)"])
res={r["id_contrato"]:r for r in json.load(open(os.path.join(B,"d4_resultados_extraccion.json"),encoding="utf-8"))["por_contrato"]}
for cid,c in M.items(): ws2.append([cid,c["entidad"],c["objeto"][:200],res.get(cid,{}).get("categoria_resultado"),"","",""])
ws3=wb.create_sheet("Instrucciones")
for line in ["Plantilla de validación manual — Spike D4 (Seguimiento Compras Públicas)",
 "1. Hoja 'Validación por campo': para cada fila, abre la carpeta de documentos y verifica el valor en la evidencia indicada.",
 "2. RESULTADO: correcto | incorrecto (escribe el valor correcto) | ausente_y_no_extraido (el dato no está en el documento y el extractor dejó vacío) | inventado (el extractor puso un valor que no está en el documento) | no_verificable.",
 "3. Precisión (NFR-CAL-002) = correctos / (correctos + incorrectos + inventados). 'ausente_y_no_extraido' no cuenta.",
 "4. Hoja 'Validación por contrato': confirma si el contrato es compra de TV en categoría y si existe precio unitario en los documentos (para la cobertura real y el error de clasificación).",
 "5. Prioriza validar precio_unitario, cantidad y tamaño; marca/modelo tienen pocas filas."]:
    ws3.append([line])
for w in (ws,ws2):
    for c in w[1]: c.font=Font(bold=True,color="FFFFFF"); c.fill=PatternFill("solid",fgColor="1F4E78"); c.alignment=Alignment(wrap_text=True)
    w.freeze_panes="A2"
    for col in w.columns: w.column_dimensions[col[0].column_letter].width=22
for col in ("K","L","M"): ws.column_dimensions[col].width=26
wb.save(os.path.join(B,"D4_plantilla_validacion_PO.xlsx")); print("filas campo:",n)
