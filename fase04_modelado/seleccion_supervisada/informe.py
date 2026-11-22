"""Informe académico de cinco algoritmos, seis variantes y dos protocolos."""
from pathlib import Path
import json
import pandas as pd
from .auditoria import RAIZ,NOMBRES,activar_guardia

def tabla(df):
    def formato(v):
        if isinstance(v,float):
            if v>1 and v<1.000001:return '>1 (sin alertas)'
            return f'{v:.7g}'
        return str(v)
    return '| '+' | '.join(df.columns)+' |\n| '+' | '.join(['---']*len(df.columns))+' |\n'+'\n'.join('| '+' | '.join(formato(v) for v in fila)+' |' for fila in df.itertuples(index=False,name=None))

def leer(nombre):return pd.read_csv(RAIZ/'resultados'/f'{nombre}.csv',float_precision='round_trip')

def main():
    activar_guardia();t=leer('umbrales_globales');f=leer('umbrales_por_fold');h=leer('historicos_globales');hf=leer('historicos_por_fold');res=leer('resumen_folds');scores=leer('distribucion_scores');d=leer('distribucion_folds');u=leer('errores_usuarios_referencias');con=leer('concordancia_protocolos');a=json.loads((RAIZ/'resultados/auditoria_fuentes.json').read_text(encoding='utf-8'));cat=json.loads((RAIZ/'catalogo_graficas.json').read_text(encoding='utf-8'))
    columnas=['protocolo','modelo','umbral','TP','FP','TN','FN','precision','recall','f1','average_precision','alertas','porcentaje_alertas']
    texto=f'''# Selección supervisada y análisis de umbrales — Fase 4

Fecha: 2026-11-21. Proyecto académico; no detector listo para producción. No se entrenó ningún estimador en esta etapa ni se leyó test.

## 1. Dictamen y alcance académico

**No existe evidencia suficiente para congelar una configuración ganadora universal ni autorizar ya su evaluación final.** KNN baseline merece prioridad como candidato para la siguiente validación de selección de umbral: conserva la mayor AP en ambas CV y ofrece un compromiso de pocas falsas alarmas reproducido descriptivamente a 0,4. Esto no satisface por sí mismo la prioridad de detectar ATO: a ese umbral omite 32 de 36. No se recomienda convertir esta prioridad de investigación en un modelo final sin fijar el objetivo de detección y la tolerancia de alertas.

El profesor requiere cinco algoritmos: M1 Árbol de Decisión, M2 GaussianNB, M3 KNN, M4 KMeans y M5 jerárquico (Ward seleccionado, average como alternativa estudiada). Los tres supervisados tienen seis variantes, documentadas íntegramente en CV1 y CV2. Clustering conserva resultados individuales e internos y evaluación externa histórica: no tiene curvas PR ni matrices TP/FP como clasificador porque no existe una regla validada que convierta cluster en predicción ATO. No se inventa tal regla para completar una tabla.

## 2. Fuentes y auditoría previa

Antes de crear archivos se revisaron informes CV1/CV2, fábrica de modelos, métricas, distribuciones y OOF; se verificaron hashes contra el inventario histórico, eventos, etiquetas, usuarios disjuntos y métricas globales y por fold. Todos coincidieron. Cada protocolo contiene 277.830 predicciones: 46.305 eventos × seis variantes; no se mezclan variantes ni protocolos. Se alinean evento_id y clave User ID + Login Timestamp + IP Address con train, conservando User ID entero. Cada usuario pertenece a un único fold de validación, y cada evento tiene una sola OOF por variante/protocolo.

Train tiene 46.305 eventos, 36 ATO de 34 usuarios y 1.600 usuarios totales. Prevalencia 36/46.305 = 0,0777454%. El tamaño de test no interviene en ningún cálculo. La guardia de aperturas rechaza CSV/NPY/joblib de test. El inventario histórico comprueba test solo por tamaño y fecha, nunca contenido.

Hashes SHA-256 de fuentes principales:

{tabla(pd.DataFrame([{'archivo':k,'sha256':v} for k,v in a['hashes'].items()]))}

Se usa la representación histórica dentro de cada fold: mediana, log1p según algoritmo, One-Hot; StandardScaler en KNN, ponderación y ROS solo en subtrain. No se modifican hiperparámetros, transformaciones, etiquetas ni exclusiones Impossible Travel. Este análisis utiliza scores guardados y no puede demostrar por sí solo cada operación del entrenamiento; la auditoría de ajuste existente y su código constituyen la evidencia histórica complementaria.

## 3. Diferencias entre protocolos

CV1 usa StratifiedGroupKFold con estratificación por evento y agrupación por usuario. CV2 aplica StratifiedKFold a una tabla de usuarios con/sin ATO y expande eventos. Ambas usan cinco folds, shuffle y semilla 42. CV2 equilibra mejor usuarios positivos; no se trata de una mejora del algoritmo. Los números de fold no representan los mismos usuarios entre protocolos.

{tabla(d[['protocolo','fold','validacion_eventos','validacion_usuarios','validacion_positivos','validacion_usuarios_positivos','usuarios_compartidos']])}

## 4. Métricas y resultados históricos de todas las variantes

TP: ATO detectados; FN: ATO omitidos; FP: eventos negativos con alerta; TN: negativos sin alerta. Precision=TP/(TP+FP), recall=TP/(TP+FN), F1=2TP/(2TP+FP+FN). Alertas=TP+FP; porcentaje de alertas=100×alertas/eventos. Cuando no hay predicciones positivas se informa precision=0 por convención y una bandera explícita; no significa una precision estimable. No se usa accuracy como indicador principal.

AP es Average Precision del ranking, no área trapezoidal. Es invariante al umbral de decisión aplicado después: se repite en las tablas para referencia, no se optimiza variando t. AP global concatena puntuaciones de estimadores de cinco folds, no necesariamente calibradas en una misma escala; no equivale al promedio de AP por fold.

### Umbral histórico 0,5

{tabla(t[t.umbral.eq(.5)][columnas])}

### Resultados individuales por fold a 0,5

{tabla(hf[['protocolo','modelo','fold','TP','FP','TN','FN','precision','recall','f1','average_precision']])}

### Media y desviación estándar entre folds a 0,5

{tabla(res[res.umbral.eq(.5)][['protocolo','modelo','precision_mean','precision_std','recall_mean','recall_std','f1_mean','f1_std','average_precision_mean','average_precision_std']])}

DE usa ddof=1, describe cinco folds con subtrain solapados; no es intervalo de confianza. La media por fold no pondera por eventos; las métricas OOF sí agregan eventos. El fold CV1 con un solo ATO puede cambiar de recall 0 a 1 por un evento.

### Coste computacional histórico y parámetros

{tabla(h[['protocolo','modelo']+[c for c in h.columns if c.endswith('_s') or c=='parametros']])}

Son tiempos históricos de sus ejecuciones, no un benchmark nuevo controlado. Árbol ofrece reglas potencialmente inspeccionables pero sin poda puede memorizar; GaussianNB supone independencia y distribuciones gaussianas incompatibles con muchas dummies; KNN requiere almacenar referencias y calcular distancias, y ROS aumenta su tamaño/coste. No se reajustó ninguna variante.

## 5. Distribución de scores y rango de umbrales

Se enumeran todos los scores únicos observados de cada variante en la unión de CV1/CV2, más 0, 0,2, 0,4, 0,5, 1 y el siguiente float mayor que 1. La misma rejilla se aplica a ambas CV. Regla exacta: score ≥ t. Entre scores consecutivos la decisión es constante; para valores s_prev < s, t en (s_prev,s] conserva la decisión en s. El extremo >1 representa ninguna alerta, no una probabilidad admisible. t=0 genera alerta en todos los eventos.

No se aplica una rejilla decimal arbitraria que perdería las puntuaciones del árbol cercanas a 0 o 1. Los CSV conservan 17 dígitos y las lecturas usan round_trip. Las tablas Markdown redondean únicamente presentación; para reproducir los puntos exactos se usa CSV. Las figuras conectan escalones, no interpolan scores o rendimientos.

{tabla(scores.groupby(['protocolo','modelo']).agg(scores_distintos=('score','size'),score_min=('score','min'),score_max=('score','max')).reset_index())}

### GaussianNB: observación e interpretación separadas

**Observado:** ambos GaussianNB producen exactamente scores 0 y 1, y sus vectores coinciden dentro de cada protocolo. Cualquier t en (0,1] produce 31 TP, 5 FN y 36.476 FP en CV1 / 36.447 FP en CV2, unas 36.500 alertas (casi 79% del conjunto). Su recall elevado proviene de marcar positiva gran parte de los eventos, con precision aproximadamente 0,085%. No hay umbral intermedio que arregle este compromiso en los scores almacenados. t=0 solo añade más falsas alarmas y los cinco ATO restantes; t>1 elimina toda detección.

**Interpretación limitada:** scores extremos son compatibles con saturación numérica y supuestos probabilísticos inadecuados; no se demuestra aquí su causa porque no se inspeccionan distribuciones internas ajustadas ni se reentrena. No se afirma que la ponderación haya sido omitida: el código histórico aplica sample_weight, pero el resultado OOF coincide.

### KNN: AP alta relativa y recall cero a 0,5

**Observado:** KNN baseline produce 0; 0,2; 0,4; 0,6. Con cinco vecinos y pesos uniformes corresponden a fracciones de vecinos positivos. Ningún ATO obtiene score ≥0,5 en estas OOF, aunque parte queda por encima de numerosos negativos con score 0. AP mide ordenamiento y puede superar a otros modelos sin producir TP al umbral 0,5. Los pocos scores 0,6 pertenecen a negativos. ROS redistribuye scores hacia valores altos, pero no crea necesariamente información de ranking: a t=0,2 sus conjuntos de alertas coinciden con baseline en estos datos (ver pruebas).

### Árbol baseline y ponderado

La ponderación modifica la partición y las proporciones ponderadas de hojas; score no se interpreta automáticamente como probabilidad calibrada. Las hojas compartidas por numerosos negativos generan bloques de scores y saltos grandes de FP. El árbol baseline mejora sus detecciones al bajar de 0,5 a 0,2, pero pierde TP entre CV1 y CV2 (8→5). El ponderado a 0,5 aumenta detección y mucho más FP. Algunos umbrales cercanos a 0,997 ofrecen compromisos distintos en CV2; no son prueba de un óptimo estable y se muestran íntegramente.

## 6. Barrido exhaustivo por variante (sin omitir resultados)

Todas las matrices de confusión están representadas por sus cuatro conteos en las tablas siguientes; las figuras individuales muestran 0,2 / 0,4 / 0,5. Los CSV incluyen también cada fold y media, DE, mínimo y máximo para cada punto. `distribucion_scores.csv` conserva todos los valores y sus conteos por clase. Ninguna variante se elimina por rendimiento desfavorable.
'''
    for nombre,titulo in NOMBRES.items():
        texto+=f'\n### {titulo}\n\n'+tabla(t[t.modelo.eq(nombre)][columnas])+'\n'
    texto+=f'''
## 7. Errores y estabilidad por evento/usuario

Se exportan FP y FN identificados por evento y clave para referencias 0,2 / 0,4 / 0,5 en `errores_eventos_referencias.csv`. Los errores no se convierten en explicación causal ni justifican añadir predictores mirando el resultado. `errores_usuarios_referencias.csv` informa usuarios positivos detectados y usuarios con al menos un FP. Un usuario puede tener varios eventos y ambos tipos de error; los conteos de eventos no son observaciones independientes.

{tabla(u)}

Concordancia de detecciones y omisiones entre protocolos:

{tabla(con)}

KNN baseline a 0,4 detecta cuatro usuarios positivos en cada CV, pero solo tres eventos ATO coinciden; uno cambia en cada protocolo. No son dos confirmaciones independientes. Su recall por fold sigue siendo inestable y dos folds de cada CV no detectan ningún ATO:

{tabla(f[f.modelo.eq('knn_baseline')&f.umbral.eq(.4)][['protocolo','fold','TP','FP','FN','precision','recall','f1']])}

## 8. Prevención de selección optimista y viabilidad anidada

**Exploración realizada:** barrido de scores OOF y comparación de todos los puntos. **Selección:** no se congela un umbral final; 0,4 y 0,2 son referencias candidatas para KNN. **Estimación independiente:** no se ha obtenido en esta etapa para la configuración seleccionada. Reutilizar estas mismas OOF tras elegir su mejor punto produciría optimismo de selección. CV2 usa los mismos eventos que CV1, por lo que tampoco valida independientemente una elección hecha en CV1.

Protocolo defendible para una próxima etapa autorizada: cinco folds externos por usuario con estratificación de usuario ATO, semilla fijada; en cada subtrain externo construir CV interna de usuarios y ajustar de cero transformaciones y modelos solo en subtrain interno. Elegir variante/umbral según un criterio académico previamente acordado (p. ej. recall mínimo y restricción explícita de alertas, sin inventar costes). Reajustar en subtrain externo y aplicar la decisión congelada a su validación externa. La unión de predicciones externas evalúa el **procedimiento de selección**, no una configuración elegida retrospectivamente con toda la evidencia. La elección final sobre train necesita registrar ese procedimiento y sus límites.

Viabilidad: CV2 deja 27–28 usuarios positivos en cada subtrain externo. Con cinco folds internos habría aproximadamente 5–6 usuarios positivos por validación interna; los externos solo tienen 6–7. Un ATO puede cambiar mucho el umbral elegido, especialmente en scores discretos y árboles ponderados. Repeticiones agrupadas pueden describir sensibilidad, pero no crean más usuarios positivos ni validaciones independientes. La selección conjunta de seis variantes requeriría aproximadamente 150 ajustes internos + 30 reajustes externos, sin búsqueda adicional de hiperparámetros. Aquí no se ejecutaron.

No basta dividir las OOF existentes por usuario y elegir t en una parte para medirlo en otra: el estimador que produjo scores de selección pudo haberse ajustado con usuarios de la supuesta evaluación. Tampoco dejar un fold OOF aparte y seleccionar con los restantes corrige esa dependencia. Hace falta entrenamiento anidado nuevo o una configuración fijada previamente que luego reciba evaluación independiente autorizada. La disponibilidad de recursos computacionales no resuelve la escasez estadística.

## 9. Compromisos y recomendación razonada

No hay coste económico FP/FN definido ni una equivalencia entre ellos. Se muestran fronteras no dominadas en TP/FP dentro de cada variante y entre variantes, por protocolo (`pareto_*` en CSV). Pareto no compara incertidumbre, calibración, interpretabilidad o recursos y no selecciona un ganador; incluye extremos triviales de alertar todo/nada. Los siguientes son escenarios descriptivos, no restricciones operativas aprobadas:

- **Menos falsas alarmas:** KNN baseline t=0,4: CV1 4 TP, 9 FP, 32 FN; CV2 4 TP, 8 FP, 32 FN. Precision 30,77%/33,33%, recall 11,11%, alertas 13/12. Rechazable si se exige detectar una proporción alta de ATO.
- **Más detección dentro de KNN:** t=0,2: 11/8 TP, 134/153 FP, 25/28 FN. Recall 30,56%/22,22%, precision 7,59%/4,97%, alertas 145/161. Mayor carga y sensibilidad al protocolo. ROS da exactamente estas mismas alertas a 0,2, sin ventaja observable en ese punto.
- **Cobertura elevada:** GaussianNB t en (0,1] detecta 31 ATO, omite 5 y alerta sobre decenas de miles de negativos. No se recomienda por recall aislado. No mejora al ajustar umbral en los scores disponibles.
- **Reglas y alternativas de detección:** árbol baseline es más directamente interpretable, pero su ventaja a 0,5 no se mantiene. Árbol ponderado no se descarta automáticamente: ciertos umbrales altos son no dominados en CV2, con sensibilidad a escala de hojas y cambio de protocolo. Requieren validación interna nueva, no escoger el pico favorable.

**Recomendación:** priorizar KNN baseline para la siguiente etapa de validación de selección de umbral, manteniendo Árbol como comparador de interpretabilidad/detección. No pasar todavía a entrenamiento final con t=0,4 como ganador: la baja cobertura contradice una prioridad fuerte de detección, y t=0,2 tampoco proporciona recall alto. Si se exige hoy una variante para planificar el trabajo, KNN baseline es el candidato provisional condicionado a validar el criterio; el umbral final queda pendiente. No se elige por F1: se consideran AP consistente, FP, FN, discretización interpretable, estabilidad limitada y coste de KNN. GaussianNB y ROS mantienen íntegros sus resultados; ROS no aporta mejora a 0,2 y su coste es mayor, sin que ello pruebe inutilidad universal.

## 10. M4 KMeans y M5 jerárquico: resultados académicos conservados

Son análisis descriptivos de train, no modelos CV1/CV2. Se usaron los seis predictores aprobados y matriz de distancias de 62 columnas; target se consultó después de congelar K y etiquetas. Los resultados siguientes se leen de entregables históricos sin recalcular clustering.

'''
    candidatos=pd.read_csv('fase04_clustering/resultados/candidatos.csv');texto+=tabla(candidatos[['algoritmo','k','inercia','silhouette','davies_bouldin','calinski_harabasz','ari_min','minimo','maximo','segundos']])+'\n\n'
    for n,titulo in [('kmeans_2','M4 · KMeans K=2'),('ward_2','M5 · Ward K=2')]:
        texto+=f'### {titulo}\n\n'+tabla(pd.read_csv(f'fase04_clustering/resultados/evaluacion_externa_{n}.csv'))+'\n\n'
        texto+=f'Perfiles completos: [numéricos](fase04_clustering/resultados/perfil_numerico_{n}.csv), [categóricos](fase04_clustering/resultados/perfil_categorico_{n}.csv), [gráfica de perfiles](fase04_clustering/resultados/graficas/perfiles_{n}.png), [evaluación externa](fase04_clustering/resultados/graficas/externa_{n}.png).\n\n'
    texto+='''KMeans usa 46.305 eventos: grupos 41.296 y 5.009, silhouette 0,6060 y ARI entre semillas 1. Ward usa muestra uniforme de 4.000 eventos y 1.360 usuarios: grupos 3.534 y 466, silhouette 0,5978. Average se conserva como alternativa: K=2 produce grupos 3.983/17 y silhouette 0,7854, sin seleccionar solo por ese máximo. ARI KMeans/Ward en muestra común 0,9281. K se fijó por índices, tamaños y perfiles, no por ATO.

Prevalencias ATO KMeans prácticamente iguales (0,07749% y 0,07986%); muestra Ward con solo un ATO: no demuestra separación útil para detección. Los perfiles describen fallos recientes e intervalos, no ataques. Las métricas internas no son comparables directamente con precision/recall/AP. No se asigna un umbral de score supervisado a KMeans/Ward: sus distancias o clusters no constituyen una probabilidad ATO ni una regla de clasificación autorizada.

Informe íntegro: [INFORME_CLUSTERING_FASE04.md](INFORME_CLUSTERING_FASE04.md). Gráficas históricas: [índices internos](fase04_clustering/resultados/graficas/seleccion_interna.png), [dendrograma Ward](fase04_clustering/resultados/graficas/dendrograma_ward.png), [estabilidad KMeans](fase04_clustering/resultados/graficas/estabilidad_kmeans.png). Se conservan todas las alternativas K=2–8 y ambos enlaces. El análisis de errores supervisados no se aplica ficticiamente a estas particiones.

## 11. Catálogo de nuevas gráficas

PNG a 300 DPI y SVG, paleta consistente, variantes numeradas M1a–M3b, tamaños de muestra y notas de exploración. Confusiones en cantidades absolutas y misma escala cromática, filas reales/columnas predichas. Escalas log/symlog se declaran, incluyen vistas completas o cero cuando corresponde. No se utiliza 3D ni accuracy.

'''
    for grafica in cat:texto+=f'- [{grafica["nombre"]} · PNG]({grafica["png"]}) / [SVG]({grafica["svg"]}): {grafica["descripcion"]}\n'
    texto+='''
## 12. Limitaciones, pruebas y próximos pasos

Vista adicional: [detalle FP para umbrales positivos · PNG](fase04_modelado/seleccion_supervisada/graficas/08_detalle_fp_umbrales_positivos.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/08_detalle_fp_umbrales_positivos.svg). Se excluye únicamente t=0 para distinguir diferencias pequeñas, conservando las vistas completas. Escala vertical explícita por variante. Total: 25 figuras, 50 archivos PNG/SVG. Reproducción adicional: `python -B -m fase04_modelado.seleccion_supervisada.detalle_grafico`.

Solo 36 eventos positivos de 34 usuarios; un evento cambia recall global 2,78 puntos porcentuales. Los eventos de un usuario son dependientes. Los scores proceden de cinco estimadores por protocolo y sus escalas pueden diferir; el modelo reajustado en todo train podría generar una distribución distinta. La geografía es sintética, las características son limitadas y la partición por usuario no es validación temporal. El barrido exhaustivo aumenta la oportunidad de selección optimista. El extremo de t>1 se informa como control, nunca como modelo útil. No se calcularon costes inventados, significación o intervalos no justificados.

Las pruebas de esta entrega verifican correspondencia de eventos y etiquetas, hashes, separación de usuarios, métricas globales/por fold, estados de umbral con empates y ausencia de alertas, AP invariante, reproducción de decisiones, igualdad de alertas KNN/ROS a 0,2, guardia de acceso a test, ausencia de ajuste en módulos de análisis, integridad PNG/SVG y número de matrices. El resultado de ejecución queda en `fase04_modelado/seleccion_supervisada/resultados/pruebas.txt`.

Código modular: `auditoria.py` (clase AuditorResultados), `umbrales.py` (métricas y estados), `analisis.py` (tablas y errores), `graficas.py` (clase ExportadorFiguras), `informe.py` y `verificar_entrega.py`. Responsabilidad única, composición y exportaciones exclusivas; no se refactoriza código histórico.

Reproducción en un destino nuevo, manteniendo versiones y orden de filas: `python -B -m fase04_modelado.seleccion_supervisada.analisis`, luego `.graficas` y `.informe`. Los generadores rechazan sobrescribir entregables. Pruebas: `python -B -m pytest -p no:cacheprovider -q fase04_modelado/seleccion_supervisada/tests`. No ejecutar pipelines históricos ni modelos finales para reproducir tablas de esta etapa.

Resultados nuevos en `fase04_modelado/seleccion_supervisada/resultados/`: auditoría de fuentes; umbrales globales y por fold; resumen de folds; scores por clase; errores por evento/usuario; concordancia entre CV; métricas y tiempos históricos consolidados. `verificacion_entrega.json` registra preservación de históricos y SHA-256 de entregables. Test solo por metadatos. No se leen ni copian sus datos.

Próximo paso sujeto a decisión: acordar un objetivo académico explícito de detección y alertas; autorizar validación anidada por usuario para seleccionar variante/umbral; después congelar configuración y decidir entrenamiento final. Test requiere autorización independiente. No se realizaron operaciones Git, instalaciones, ajustes de modelos ni cambios históricos. **Fase 4 no se declara terminada.**
'''
    with Path('INFORME_SELECCION_SUPERVISADA_FASE04.md').open('x',encoding='utf-8') as archivo:archivo.write(texto)

if __name__=='__main__':main()
