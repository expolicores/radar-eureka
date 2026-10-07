import json, urllib.request, urllib.parse, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
def q(ds, **p):
    u=f"https://www.datos.gov.co/resource/{ds}.json?"+urllib.parse.urlencode({"$"+k:v for k,v in p.items()})
    with urllib.request.urlopen(u, timeout=300) as r: return json.load(r)
TXT="(codigo_de_categoria_principal like '%52161505%' OR upper(objeto_del_contrato) like '%TELEVISOR%' OR upper(descripcion_del_proceso) like '%TELEVISOR%' OR upper(objeto_del_contrato) like '%SMART TV%')"
cs=q("jbjy-vk9h", select="id_contrato,proceso_de_compra,fecha_de_firma,valor_del_contrato,nombre_entidad,objeto_del_contrato,modalidad_de_contratacion,codigo_de_categoria_principal,documento_proveedor,proveedor_adjudicado", where=TXT+" AND fecha_de_firma >= '2023-01-01'", limit=5000)
json.dump(cs,open("d1_tv_contracts.json","w",encoding="utf-8"),ensure_ascii=False)
print("TV contracts 2023+:",len(cs), "| procesos unicos:",len({c['proceso_de_compra'] for c in cs}), "| entidades:",len({c['nombre_entidad'] for c in cs}))
vals=sorted(float(c.get('valor_del_contrato',0) or 0) for c in cs); print("valor mediana COP:",vals[len(vals)//2], "| p90:",vals[int(len(vals)*.9)])
print("principal es 52161505:", sum('52161505' in c.get('codigo_de_categoria_principal','') for c in cs))
# documentos por año segun dataset
DS={"2023":"3skv-9na7","2024":"nbae-kzan","2025":"dmgg-8hin","2026":"dmgg-8hin"}
ext=collections.Counter(); nd=[]; miss=0; sample=collections.defaultdict(list)
for c in cs: sample[c['fecha_de_firma'][:4]].append(c)
for y,lst in sorted(sample.items()):
    got=0
    for c in lst[:25]:
        fs=[]
        for ds in ([DS[y]] + (["dmgg-8hin"] if DS[y]!="dmgg-8hin" else [])):
            try: fs+=q(ds, select="extensi_n,nombre_archivo", where=f"proceso='{c['proceso_de_compra']}'", limit=300)
            except Exception as e: pass
        if fs: got+=1; nd.append(len(fs)); ext.update((f.get('extensi_n') or '').lower() for f in fs)
        else: miss+=1
    print(f"year {y}: muestra {min(25,len(lst))}, con documentos: {got}")
print("docs por proceso (mediana):", sorted(nd)[len(nd)//2] if nd else None, "| extensiones:", ext.most_common(8))
for name,ds,w in [("SECOP I TV 2023+","f789-7hwg","upper(detalle_del_objeto_a_contratar) like '%TELEVISOR%' AND fecha_de_firma_del_contrato >= '2023-01-01'")]:
    try: print(name, q(ds, select="count(*)", where=w))
    except Exception as e: print(name,"ERR",e)
