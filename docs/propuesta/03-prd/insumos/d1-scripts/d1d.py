import json, urllib.request, urllib.parse, sys
sys.stdout.reconfigure(encoding="utf-8")
def q(ds, **p):
    u=f"https://www.datos.gov.co/resource/{ds}.json?"+urllib.parse.urlencode({"$"+k:v for k,v in p.items()})
    with urllib.request.urlopen(u, timeout=240) as r: return json.load(r)
def run(label, ds, **p):
    try: r=q(ds, **p)
    except Exception as e: r=str(e)
    print("==",label); 
    if isinstance(r,list): [print("  ",x) for x in r]
    else: print("  ERR",r)
TXT="(upper(objeto_del_contrato) like '%TELEVISOR%' OR upper(descripcion_del_proceso) like '%TELEVISOR%' OR upper(objeto_del_contrato) like '%SMART TV%')"
run("Contratos: union UNSPSC 52161505 OR texto", "jbjy-vk9h",
    select="date_extract_y(fecha_de_firma) as y, count(*) as n", where=f"(codigo_de_categoria_principal like '%52161505%' OR {TXT}) AND fecha_de_firma >= '2023-01-01'", group="y", order="y")
run("Procesos: categorias_adicionales contiene 52161505 (cat principal distinta)", "p6dx-8zbt",
    select="date_extract_y(fecha_de_publicacion_del) as y, count(*) as n", where="categorias_adicionales like '%52161505%' AND codigo_principal_de_categoria not like '%52161505%' AND fecha_de_publicacion_del >= '2023-01-01'", group="y", order="y")
run("Procesos: descripcion contiene TELEVISOR", "p6dx-8zbt",
    select="date_extract_y(fecha_de_publicacion_del) as y, count(*) as n", where="(upper(descripci_n_del_procedimiento) like '%TELEVISOR%' OR upper(nombre_del_procedimiento) like '%TELEVISOR%') AND fecha_de_publicacion_del >= '2023-01-01'", group="y", order="y")
run("Procesos TV: estado_resumen", "p6dx-8zbt",
    select="estado_resumen, count(*) as n", where="(codigo_principal_de_categoria like '%52161505%' OR upper(nombre_del_procedimiento) like '%TELEVISOR%') AND fecha_de_publicacion_del >= '2023-01-01'", group="estado_resumen")
run("Contratos TV: modalidad", "jbjy-vk9h",
    select="modalidad_de_contratacion, count(*) as n", where=f"(codigo_de_categoria_principal like '%52161505%' OR {TXT}) AND fecha_de_firma >= '2023-01-01'", group="modalidad_de_contratacion", order="n DESC")
run("TVEC: muestra items", "rgxm-mmea", select="a_o,entidad,solicitud,items,total,agregacion", where="upper(items) like '%TELEVISOR%'", limit=3)
run("TVEC: ordenes con TELEVISOR por año/agregacion", "rgxm-mmea",
    select="a_o, agregacion, count(*) as n", where="upper(items) like '%TELEVISOR%' AND a_o >= '2023'", group="a_o, agregacion", order="a_o, n DESC")
