"""Genera PPTX editable desde catálogo y figuras históricas, sin ajustar modelos."""
from pathlib import Path
import sys,json,re,hashlib
sys.path.insert(0,str(Path(__file__).parent/'.herramientas'))
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'entrega_final'
c=json.loads((ROOT/'frontend/public/contenido/catalogo.json').read_text(encoding='utf-8'))
guion=(ROOT/'docs/GUIÓN_PRESENTACION_ACADEMICA.md').read_text(encoding='utf-8')
notas=re.split(r'^## \d+\. ',guion,flags=re.M)[1:13]
tiempos=[15,35,50,55,20,45,40,40,40,40,90,70]
assert sum(tiempos)==540 and len(notas)==12
pr=Presentation();pr.slide_width=Inches(13.333);pr.slide_height=Inches(7.5)
AZUL='183D59';TEXTO='20364A';VERDE='126E70';GRIS='526779';CLARO='EDF4F7'
def rect(s,x,y,w,h,color):
 sh=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h));sh.fill.solid();sh.fill.fore_color.rgb=RGBColor.from_string(color);sh.line.fill.background();return sh
def text(s,t,x,y,w,h,size=20,color=TEXTO,bold=False):
 sh=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=sh.text_frame;tf.word_wrap=True
 tf.margin_left=tf.margin_right=Inches(.02);tf.margin_top=Inches(.02)
 for i,line in enumerate(t.split('\n')):
  p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line;p.font.name='Aptos';p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=RGBColor.from_string(color);p.space_after=Pt(7)
 return sh
def slide(t,sub=''):
 s=pr.slides.add_slide(pr.slide_layouts[6]);idx=len(pr.slides);s.background.fill.solid();s.background.fill.fore_color.rgb=RGBColor(255,255,255)
 rect(s,.45,.35,.07,.58,VERDE);text(s,t,.7,.3,12,.65,28,AZUL,True)
 if sub:text(s,sub,.7,1.03,12,.6,15,GRIS)
 text(s,'ATO · Evidencia académica',.7,7.12,8,.25,10,GRIS);text(s,str(idx)+'/12',12,7.1,.7,.3,10,GRIS)
 s.notes_slide.notes_text_frame.text='Tiempo previsto: '+str(tiempos[idx-1])+' segundos.\n\n'+notas[idx-1]
 return s
def pic(s,ruta,x,y,w,h):
 p=ROOT/ruta
 with Image.open(p) as im:iw,ih=im.size
 factor=min(w/iw,h/ih);ww=iw*factor;hh=ih*factor
 s.shapes.add_picture(str(p),Inches(x+(w-ww)/2),Inches(y+(h-hh)/2),width=Inches(ww),height=Inches(hh))
def table(s,headers,rows,x,y,w,h,fontsize=16):
 sh=s.shapes.add_table(len(rows)+1,len(headers),Inches(x),Inches(y),Inches(w),Inches(h));ta=sh.table
 for i,row in enumerate([headers,*rows]):
  for j,val in enumerate(row):
   cell=ta.cell(i,j);cell.text=str(int(val)) if isinstance(val,float) and val.is_integer() else str(val);cell.fill.solid();cell.fill.fore_color.rgb=RGBColor.from_string(AZUL if i==0 else ('EDF4F7' if i%2 else 'FFFFFF'))
   for p in cell.text_frame.paragraphs:p.font.name='Aptos';p.font.size=Pt(fontsize);p.font.bold=i==0;p.font.color.rgb=RGBColor.from_string('FFFFFF' if i==0 else TEXTO)
 return ta
def result(m,p='cv2',regla=None):return next(r['valores'] for r in c['resultados'] if r['protocolo']==p and r['ambito']=='oof_global' and r['valores']['modelo']==m and (regla is None or r['valores'].get('regla')==regla))
def f(v):return format(v,'.4f').replace('.',',')
# 1
s=slide('Detección de Account Takeover')
text(s,'Una credencial válida.\n¿La persona correcta?',.8,1.75,10.9,1.75,42,AZUL,True)
text(s,'Proyecto académico de minería de datos\nCaso hospitalario simulado • Metodología CRISP-DM',.85,4,10,1.1,24)
rect(s,.8,5.7,11.7,.8,CLARO);text(s,'Comparación reproducible, evidencia y límites de la detección',1,5.88,11.2,.5,21,VERDE)
# 2
s=slide('Contexto y planteamiento del problema','Abuso de credenciales en un contexto hospitalario simulado')
text(s,'Credencial válida',.9,1.95,5,1,32,AZUL,True);text(s,'Identidad no garantizada',7,1.95,5.3,1,30,VERDE,True)
text(s,'Turnos y actividad continua\nAccesos legítimos poco habituales\nSuplantación de identidad',.9,3.25,5.4,2.1,24)
text(s,'Detectar inicios de sesión sospechosos sin saturar con falsas alarmas.',7,3.25,5.3,1.8,26)
text(s,'Alcance: eventos sintéticos y experimentación académica. Sin validación hospitalaria operativa.',.9,6.05,11.5,.7,18,GRIS)
# 3
s=slide('Objetivo general y objetivos específicos','Formulación original: PDF de Fases 1–2, página 7')
text(s,c['narrativa']['objetivo_general'],.85,1.65,11.6,1.6,22,AZUL)
extractos=['Fusionar tres fuentes de datos independientes…','Crear variables de comportamiento basadas en ciberseguridad…','Entrenar un algoritmo de Árbol de Decisión…','Evaluar el rendimiento del modelo utilizando métricas específicas para datos desbalanceados…']
for i,t in enumerate(extractos):text(s,str(i+1)+'. '+t,.9,3.5+i*.62,11.5,.6,20)
text(s,'Extractos literales; texto completo en notas. La alta efectividad es un propósito original, no un resultado garantizado.',.9,6.3,11.5,.65,15,GRIS)
# 4
s=slide('Metodología CRISP-DM','Preparación trazable antes de comparar procedimientos')
for i,(t,d) in enumerate([('Negocio','Abuso de credenciales'),('Datos','RBA + IPinfo + personal sintético'),('Preparación','90 etiquetas reconciliadas'),('Modelado','Supervisados y clustering'),('Evaluación','Usuarios separados; protocolos explícitos'),('Despliegue','Consulta académica de evidencia')]):
 x=.8+(i%3)*4.15;y=1.7+(i//3)*1.55
 rect(s,x,y,3.85,1.28,CLARO);text(s,t,x+.15,y+.12,3.55,.4,21,AZUL,True);text(s,d,x+.15,y+.6,3.55,.6,17)
text(s,'57.420 eventos • 2.000 usuarios • 45 ATO\nTrain: 46.305 eventos, 1.600 usuarios y 36 ATO de 34 usuarios.',.85,5.15,11.7,.85,20)
text(s,'Seis predictores: fallos 15 min / 1 h, intervalo previo (h), historial, dispositivo y país. CV1 / CV2 / anidada separados; preprocesamiento dentro de cada subtrain.',.85,6.1,11.7,.8,16,GRIS)
# 5
estado=json.loads((OUT/'estado_despliegue.json').read_text(encoding='utf-8'))
s=slide('Despliegue y arquitectura del proyecto','Componentes efectivamente publicados y comprobados')
for i,(t,d) in enumerate([('Repositorio GitHub','Código y documentación'),('GitHub Pages','Vite + TypeScript estático'),('Recursos públicos','Catálogo, 58 figuras y 15 CSV agregados')]):
 x=.8+i*4.15;rect(s,x,2,3.85,2,CLARO);text(s,t,x+.15,2.2,3.5,.6,24,AZUL,True);text(s,d,x+.15,2.95,3.5,.9,20)
text(s,estado['url'],.85,4.65,11.7,.65,21,VERDE,True)
text(s,'Sin backend de inferencia ni base de datos operativa. No se publican datasets de eventos en este sitio. La aplicación amplía la sustentación.',.85,5.65,11.7,1,20)
# 6–8
for title,models,explanation,conclusion in [
 ('Árbol de decisión',['arbol_baseline','arbol_ponderado'],'Reglas de partición; ponderación de clases en subtrain. Sin poda.','Ponderar aumenta detecciones y falsas alarmas; interpretabilidad no garantiza generalización.'),
 ('Gaussian Naive Bayes',['gnb_baseline','gnb_ponderado'],'Distribuciones gaussianas e independencia condicional aproximadas.','Recall alto con una precisión muy baja. Las dummies y ventanas correlacionadas limitan los supuestos.'),
 ('KNN',['knn_baseline','knn_ros'],'Cinco vecinos, distancia euclídea; escalado y ROS solo en subtrain.','AP de ranking y detecciones a 0,5 son distintos. El baseline no detectó ATO a ese umbral.')]:
 s=slide(title,'CV2 · OOF global · umbral fijo 0,5 · '+explanation)
 for i,m in enumerate(models):pic(s,'fase04_modelado/resultados_cv_usuario/graficas/confusion_'+m+'.png',.75+i*6.1,1.7,5.8,3.6)
 rows=[]
 for m in models:
  a=result(m);rows.append([m.replace('_',' '),f(a['precision']),f(a['recall']),f(a['f1']),f(a['average_precision'])])
 table(s,['Variante','Precision','Recall','F1','AP'],rows,.85,5.35,11.6,.85,14)
 text(s,conclusion,.85,6.35,11.6,.65,17,GRIS)
# 9
s=slide('K-Means','Segmentación exploratoria, no clasificación de ATO')
pic(s,'fase04_clustering/resultados/graficas/perfiles_kmeans_2.png',.7,1.65,7.4,4.8)
text(s,'K = 2\n41.296 / 5.009 eventos\nSilhouette: 0,6060',8.5,1.95,4,1.8,24,AZUL,True)
text(s,'Centroides y cercanía geométrica.\nPrevalencias ATO similares: 32/41.296 y 4/5.009.\nSelección sin usar el target.',8.5,4,4,2.2,20)
text(s,'Índices internos y perfiles no demuestran capacidad de detectar ataques.',.85,6.5,11.6,.45,17,GRIS)
# 10
s=slide('Clustering jerárquico','Ward como protagonista; Average como contraste exploratorio')
pic(s,'fase04_clustering/resultados/graficas/dendrograma_ward.png',.7,1.7,7.5,4.65)
text(s,'Ward • muestra de 4.000\nK = 2: 3.534 / 466\nSilhouette: 0,5978',8.5,1.9,4.1,1.8,22,AZUL,True)
text(s,'Average K = 2\n3.983 / 17 eventos\nSilhouette: 0,7854\nSeparación extrema: no se elige como representación principal.',8.5,3.9,4.05,2.6,19)
text(s,'El dendrograma resume 25 ramas terminales. Distancia de enlace en el espacio transformado.',.85,6.5,11.6,.5,16,GRIS)
# 11
s=slide('Modelo de referencia seleccionado: resultados y limitaciones','Árbol ponderado; sin superioridad universal ni garantía productiva')
sel=next(r['valores'] for r in c['resultados'] if r['protocolo']=='seleccion_referencia')
fin=next(r['valores'] for r in c['resultados'] if r['protocolo']=='evaluacion_final_documentada')
text(s,'Comparación externa histórica: reglas aprendidas',.8,1.6,7.5,.5,19,AZUL,True)
rows=[]
for m in ['arbol_ponderado','gnb_ponderado','knn_baseline','random_forest']:
 a=result(m,'extension_rf','aprendido');rows.append([m.replace('_',' '),a['tp'],a['fp'],a['fn'],f(a['f1'])])
table(s,['Modelo','TP','FP','FN','F1'],rows,.8,2.15,7.3,1.8,14)
text(s,'Evaluación final cerrada',8.6,1.6,4,.5,21,AZUL,True)
table(s,['Real / pred.','No ATO','ATO'],[['No ATO',fin['tn'],fin['fp']],['ATO',fin['fn'],fin['tp']]],8.6,2.15,3.9,1.45,16)
text(s,'Recall '+f(fin['recall'])+'\nPrecision '+f(fin['precision'])+'\nF1 '+f(fin['f1'])+' • AP '+f(fin['average_precision']),8.6,3.9,4,1.4,20)
text(s,'Umbral congelado: '+str(sel['umbral'])+'\nF1 OOF de selección: '+f(sel['f1'])+'; no es evaluación independiente.',.85,4.65,7.1,1.1,19)
text(s,'Detectó 1 de 9 ATO, omitió 8 y generó 12 falsas alarmas. Pocos positivos, inestabilidad y datos sintéticos limitan generalización.',.85,6,11.6,.85,21,VERDE,True)
# 12
n=c['metodos_numericos'];a=n['regresion']
s=slide('Regresión lineal e interpolación de Lagrange','Distancia x (km) y velocidad y (km/h). Ejercicios descriptivos complementarios.')
pic(s,'fase04_metodos_numericos/resultados/graficas/regresion_lineal.png',.65,1.6,6.05,3.8)
pic(s,'fase04_metodos_numericos/resultados/graficas/interpolacion_lagrange.png',6.8,1.6,5.9,3.8)
text(s,'ŷ = 2,641194 x − 7,007985\nR² = 0,167134 • RMSE = 2.371,47 km/h\n5.662 pares; 5.633 en cero.',.85,5.45,5.8,1.05,16)
text(s,'P(x) = −646,473854 + 0,778670 x\n             − 0,0000888395 x²\nIntervalo: [931,57; 7.821,98] km.',6.95,5.45,5.7,1.05,16)
text(s,'Sin causalidad. Sensibilidad de 29 pares separada. El polinomio interpola tres nodos; no extrapola ni acredita predicción general.',.85,6.65,11.6,.35,14,GRIS)
# Validate shape boundaries, preserve originals and emit.
assert len(pr.slides)==12
for s in pr.slides:
 for sh in s.shapes:
  assert sh.left>=0 and sh.top>=0 and sh.left+sh.width<=pr.slide_width+100 and sh.top+sh.height<=pr.slide_height+100
archivo=OUT/'ATO_PRESENTACION_ACADEMICA.pptx'
pr.save(archivo)
reloaded=Presentation(archivo);assert len(reloaded.slides)==12
assert sum(int(re.search(r'Tiempo previsto: (\d+)',s.notes_slide.notes_text_frame.text).group(1)) for s in reloaded.slides)==540
validacion=dict(diapositivas=12,segundos=540,sha256=hashlib.sha256(archivo.read_bytes()).hexdigest(),archivo=archivo.name,url=estado['url'],fuente='Catálogo público y guion aprobado; ninguna métrica recalculada')
(OUT/'VALIDACION_PRESENTACION.json').write_text(json.dumps(validacion,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(validacion,ensure_ascii=False))
