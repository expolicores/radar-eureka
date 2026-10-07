import json, urllib.request, urllib.parse, sys
sys.stdout.reconfigure(encoding="utf-8")
def q(ds, **p):
    u=f"https://www.datos.gov.co/resource/{ds}.json?"+urllib.parse.urlencode({"$"+k:v for k,v in p.items()})
    with urllib.request.urlopen(u, timeout=240) as r: return json.load(r)
TXT="(codigo_de_categoria_principal like '%52161505%' OR upper(objeto_del_contrato) like '%TELEVISOR%')"
cs=q("jbjy-vk9h", select="id_contrato,proceso_de_compra,referencia_del_contrato,nombre_entidad,objeto_del_contrato,valor_del_contrato,fecha_de_firma,modalidad_de_contratacion,urlproceso,codigo_de_categoria_principal",
     where=TXT+" AND fecha_de_firma >= '2025-01-01'", order="fecha_de_firma DESC", limit=6)
json.dump(cs,open("d1_sample_contracts.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
for c in cs:
    print("\n##",c["id_contrato"],c["proceso_de_compra"],c["fecha_de_firma"][:10],c["modalidad_de_contratacion"],c["valor_del_contrato"])
    print("  ",c["nombre_entidad"],"|",c["objeto_del_contrato"][:150])
    print("  url:",c.get("urlproceso",{}).get("url") if isinstance(c.get("urlproceso"),dict) else c.get("urlproceso"))
    for key,val in [("proceso",c["proceso_de_compra"]),("n_mero_de_contrato",c["id_contrato"])]:
        try:
            f=q("dmgg-8hin", where=f"{key}='{val}'", limit=50)
        except Exception as e: f=[]; print("  err",e)
        print(f"   archivos by {key}: {len(f)}")
        for x in f[:12]:
            print("     -",x.get("extensi_n"),x.get("tamanno_archivo"),"|",x.get("nombre_archivo","")[:70],"|",x.get("descripci_n","")[:50])
        if f: 
            print("     url ej:", f[0].get("url_descarga_documento"))
            break
