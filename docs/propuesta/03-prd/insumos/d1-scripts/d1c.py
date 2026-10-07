import json, urllib.request, urllib.parse, sys
sys.stdout.reconfigure(encoding="utf-8")
def q(ds, **p):
    u=f"https://www.datos.gov.co/resource/{ds}.json?"+urllib.parse.urlencode({"$"+k:v for k,v in p.items()})
    with urllib.request.urlopen(u, timeout=180) as r: return json.load(r)
C="jbjy-vk9h"
print("sample categoria:", q(C, select="codigo_de_categoria_principal", limit=3))
# por categoria UNSPSC televisores 52161505
for name, where in [
  ("UNSPSC 52161505 (cat principal)", "codigo_de_categoria_principal like '%52161505%'"),
  ("UNSPSC familia 521615 (audio/video consumo)", "codigo_de_categoria_principal like '%521615%'"),
  ("texto 'televisor' en objeto/descr", "upper(objeto_del_contrato) like '%TELEVISOR%' OR upper(descripcion_del_proceso) like '%TELEVISOR%'"),
]:
    r=q(C, select="date_extract_y(fecha_de_firma) as y, count(*) as n, sum(valor_del_contrato) as v", where=f"({where}) AND fecha_de_firma >= '2023-01-01'", group="y", order="y")
    print("==",name); [print("  ",x) for x in r]
