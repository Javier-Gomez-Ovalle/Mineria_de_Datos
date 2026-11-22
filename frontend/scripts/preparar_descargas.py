"""Exporta exclusivamente valores agregados del catálogo público; sin datasets."""
from pathlib import Path
import csv
import hashlib
import html
import io
import json

FRONTEND=Path(__file__).resolve().parents[1]
PUBLICO=FRONTEND/'public'


def preparar():
    catalogo=json.loads((PUBLICO/'contenido/catalogo.json').read_text(encoding='utf-8'))
    destino=PUBLICO/'descargas'
    destino.mkdir(exist_ok=True)
    grupos={}
    for fila in catalogo['resultados']:
        grupos.setdefault(fila['protocolo']+'_'+fila['ambito'],[]).append(fila['valores'])
    grupos['regresion_principal_y_sensibilidad']=[{'ajuste':k,**catalogo['metodos_numericos'][k]} for k in ['regresion','sensibilidad']]
    interp=catalogo['metodos_numericos']['interpolacion']
    grupos['interpolacion_coeficientes_intervalo']=[dict(coeficiente_constante=interp['coeficientes_x_ascendentes'][0],coeficiente_lineal=interp['coeficientes_x_ascendentes'][1],coeficiente_cuadratico=interp['coeficientes_x_ascendentes'][2],minimo_km=interp['intervalo_km'][0],maximo_km=interp['intervalo_km'][1],error_maximo_nodos_kmh=interp['error_maximo_nodos_kmh'])]
    inventario=[]
    for nombre,filas in grupos.items():
        columnas=list(dict.fromkeys(k for fila in filas for k in fila))
        assert not {'user_id','ip_address','evento_id','fila_train_0','login_timestamp'}.intersection(columnas)
        s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=columnas);w.writeheader();w.writerows(filas)
        datos=s.getvalue().encode('utf-8')
        archivo=nombre+'.csv';(destino/archivo).write_bytes(datos)
        inventario.append(dict(archivo=archivo,filas=len(filas),columnas=columnas,bytes=len(datos),sha256=hashlib.sha256(datos).hexdigest(),procedencia='Proyección del catálogo público, sin cálculo de métricas',redistribucion='Publicación autorizada por responsables del proyecto. No se inventa una licencia general de los resultados propios. Atribuciones RBA/IPinfo en documentación.'))
    (destino/'inventario.json').write_text(json.dumps(inventario,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    enlaces=''.join('<li><a download href="./descargas/'+x['archivo']+'">'+html.escape(x['archivo'].removesuffix('.csv').replace('_',' '))+'</a><small>'+str(x['filas'])+' filas agregadas · '+str(x['bytes'])+' bytes</small></li>' for x in inventario)
    pagina='''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Recursos públicos | ATO</title><style>body{font:18px/1.6 system-ui;color:#183d59;max-width:900px;margin:40px auto;padding:0 24px}a{color:#126e70}li{margin:18px 0}small{display:block}a:focus-visible{outline:3px solid #126e70;outline-offset:4px}</style><a href="./">Volver al proyecto</a><h1>Recursos académicos públicos</h1><p>Tablas agregadas de experimentos documentados. No contienen filas de autenticación, identificadores ni predicciones individuales. No son datasets para reentrenar.</p><p>Precision, Recall, F1 y AP: escala 0–1. Conteos: eventos. Tiempos de cómputo: segundos. Regresión: distancia en km, velocidad/intercepto/RMSE en km/h, pendiente en h⁻¹, MSE en (km/h)². Coeficientes de interpolación: km/h, h⁻¹, km⁻¹ h⁻¹. El diagnóstico no sustituye al ajuste principal.</p><ul>'''+enlaces+'''</ul><p><a href="./descargas/inventario.json">Inventario, procedencia y hashes de las descargas</a></p><p><a href="https://github.com/Javier-Gomez-Ovalle/Mineria_de_Datos/blob/main/docs/PROCEDENCIA_Y_LICENCIAS.md">Procedencia y condiciones de las fuentes originales</a></p><p>Publicación autorizada de resultados propios. No se declara una licencia general que sus titulares no hayan elegido.</p><p><a href="./presentacion/ATO_PRESENTACION_ACADEMICA.pptx">Descargar presentación PowerPoint</a></p></html>'''
    (PUBLICO/'recursos.html').write_text(pagina,encoding='utf-8')
    return inventario

if __name__=='__main__': print('CSV agregados preparados:',len(preparar()))
