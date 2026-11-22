"""Informes derivados de tablas; no ajusta estimadores ni cambia resultados."""
from pathlib import Path
import json
import pandas as pd

def tabla(df):
    def valor(v):return f'{v:.6g}' if isinstance(v,float) else str(v)
    return '| '+' | '.join(df.columns)+' |\n| '+' | '.join(['---']*len(df.columns))+' |\n'+'\n'.join('| '+' | '.join(valor(v) for v in fila)+' |' for fila in df.itertuples(index=False,name=None))

def figuras(carpeta):
    descripciones={'seleccion_interna':'Codo de inercia e índices internos para todos los candidatos; silhouette muestral, DB/CH poblacionales.','estabilidad_kmeans':'ARI entre semillas; pérdida de estabilidad al aumentar K.','dendrograma_ward':'Árbol Ward truncado y altura de corte para dos grupos.','metricas_oof':'Precision, recall, F1 y AP OOF globales de las seis variantes.','curvas_pr':'Curvas OOF, AP y prevalencia; GaussianNB tiene curvas coincidentes.','estabilidad_folds':'Valores individuales por fold: composición y variabilidad.','variabilidad_folds':'Distribuciones de cinco folds, puntos individuales y media.','fp_fn':'Falsas alarmas y omisiones absolutas, con escalas explícitas.','comparacion_protocolos':'Mismas variantes bajo dos protocolos de partición.'}
    lineas=[]
    for p in sorted(Path(carpeta).rglob('*.png')):
        nombre=p.stem;desc=descripciones.get(nombre,'Conteos absolutos de confusión, filas reales y columnas predichas.' if nombre.startswith('confusion') else 'Evaluación externa ATO después de congelar clusters.' if nombre.startswith('externa') else 'Perfiles de fallos e intervalos en sus unidades originales.')
        lineas.append(f'- [{p.as_posix()}]({p.as_posix()}) · [SVG]({p.with_suffix(".svg").as_posix()}): {desc}')
    return '\n'.join(lineas)

def main():
    r=Path('fase04_clustering/resultados');c=pd.read_csv(r/'candidatos.csv');audit=json.loads((r/'auditoria_interna.json').read_text());seleccion=json.loads((r/'seleccion_congelada.json').read_text(encoding='utf-8'));comparacion=json.loads((r/'comparacion_particiones.json').read_text())
    externas=[];perfiles=[];categorias=[]
    for n in ['kmeans_2','ward_2']:
        e=pd.read_csv(r/f'evaluacion_externa_{n}.csv');e.insert(0,'algoritmo',n);e['porcentaje_eventos']=100*e.eventos/e.eventos.sum();externas.append(e)
        p=pd.read_csv(r/f'perfil_numerico_{n}.csv');p.insert(0,'algoritmo',n);perfiles.append(p[['algoritmo','cluster','failed_attempts_15min_mean','failed_attempts_1h_mean','time_since_previous_login_hours_median','has_previous_login_mean']])
        cat=pd.read_csv(r/f'perfil_categorico_{n}.csv');cat=cat[cat.variable.isin(['Device Type','Country'])].sort_values('eventos',ascending=False).groupby(['cluster','variable']).head(3);cat.insert(0,'algoritmo',n);categorias.append(cat.sort_values(['cluster','variable','eventos'],ascending=[True,True,False]))
    texto=f'''# Informe de clustering — Fase 4

Fecha: 2026-11-19. Estudio exploratorio de train; no constituye un detector ATO ni cierra Fase 4.

## 1. Auditoría y datos

Se revisaron los informes de preprocesamiento, Impossible Travel, modelado supervisado y segunda validación, la fábrica de transformaciones y selección de variables, las métricas y visualizaciones supervisadas y la matriz train de distancias. Se preservó la implementación aprobada. Solo se cargaron predictores y claves de train en la etapa interna. El target se abrió en evaluación externa, después de escribir y verificar `seleccion_congelada.json` y los hashes de etiquetas. Los informes históricos contienen información ATO ya conocida; esa información no intervino en las decisiones del clustering.

Origen: `dataset_train_fase04.csv`, 46.305 eventos de 1.600 usuarios. SHA-256: `{audit['train_sha256']}`. La matriz reconstruida coincide exactamente con la histórica (46.305 × 62). Ningún identificador, target, resultado del login, bandera de ataque ni variable Impossible Travel entra en X. Las claves se usan únicamente para alinear y describir eventos.

## 2. Representación y datos mixtos

Se conserva la lista positiva de seis predictores: Device Type, Country, failed_attempts_15min, failed_attempts_1h, time_since_previous_login_hours y has_previous_login. Se ajustan de nuevo, en todo train y sin y, mediana de numéricas, log1p, StandardScaler de las tres numéricas, indicador binario intacto y One-Hot de nominales con categoría desconocida. No se reutiliza un transformador ajustado en test. El ajuste en todo train es apropiado para esta descripción no supervisada de train; los índices internos no son una validación predictiva externa.

Tres columnas numéricas, una binaria, cuatro dummies de dispositivo y 54 de país. Cada bloque One-Hot aporta como máximo 2 a la distancia euclídea cuadrática, independientemente del número de categorías. Contribuciones esperadas entre dos eventos extraídos independientemente: numéricas 6, binaria 0,06672, dispositivo 1,08076 y país 0,74478. Aproximadamente 76,0%, 0,85%, 13,69% y 9,44% respectivamente. No se escalan dummies ni se añaden pesos buscando separación visual.

Euclídea mezcla diferencias nominales y continuas; sus centroides nominales son proporciones, no categorías reales. No se afirma que sea una distancia semántica única o ideal. Las dos cuentas de fallos están relacionadas y enfatizan actividad reciente. La mediana imputada más el indicador de historial distingue ausencia de observación, pero no elimina toda distorsión de distancia. Country es contexto sintético, no geografía física; se mantienen las exclusiones Impossible Travel. No se exploraron representaciones alternativas guiadas por ATO.

## 3. KMeans y selección interna

K=2–8, init=k-means++, n_init=10, max_iter=300, algoritmo Lloyd, semilla principal 42. Semillas adicionales 43 y 44 previamente fijadas para ARI de estabilidad. Dos hilos computacionales. Silhouette sobre 2.000 eventos uniformes sin reemplazo con semilla 42; DB y CH sobre los 46.305 eventos. Inercia no se normaliza y corresponde a esa matriz. Los segundos incluyen los tres ajustes por K, excluyen métricas internas y gráficos; no son tiempo de un único ajuste.

{tabla(c[c.algoritmo.eq('kmeans')][['k','inercia','iteraciones','segundos','silhouette','davies_bouldin','calinski_harabasz','ari_min','minimo','maximo']])}

{seleccion['justificacion']}

El codo presenta reducción gradual: pasar de K=2 a 3 reduce inercia un 25,4%; K=4 y 5 siguen reduciéndola alrededor del 17%. No existe un codo inequívoco que pruebe dos clusters naturales. K=2 se conserva como resumen parsimonioso y estable respaldado por índices y perfiles, no exclusivamente por silhouette. No se alteró K después de abrir y. La estabilidad entre inicializaciones no demuestra estabilidad frente a nuevas muestras o usuarios.

## 4. Jerárquico: coste, enlaces y corte

La matriz condensada de 46.305 eventos exigiría 8,58 GB y una cuadrada 17,15 GB, sin temporales ni copias. La memoria libre observada era aproximadamente 11,3 GiB. Se evitó ese riesgo con 4.000 eventos uniformes sin reemplazo, semilla 42, índices ordenados después de muestrear: {audit['usuarios_muestra']} usuarios. No se estratificó por target ni por usuario. Los usuarios con más eventos tienen mayor probabilidad de representación.

La muestra requiere unos 64 MB condensados o 128 MB cuadrados; el tiempo y espacio de los enlaces son cuadráticos. Ward y average usan distancia euclídea; Ward minimiza incrementos de dispersión y no se utiliza con una distancia incompatible. Se ajustó la representación a train completo y luego se muestrearon filas de esa misma geometría. No se extrapolan etiquetas jerárquicas a los eventos no muestreados.

{tabla(c[~c.algoritmo.eq('kmeans')][['algoritmo','k','segundos','silhouette','davies_bouldin','calinski_harabasz','minimo','maximo']])}

El tiempo de cada enlace se repite por K: corresponde a un único árbol por método, no debe sumarse siete veces. Silhouette utiliza 2.000 eventos fijos dentro de la muestra jerárquica. DB y CH usan los 4.000. Average conserva su resultado desfavorable como segmentación general, aunque puede describir extremos; no se interpreta ese pequeño grupo como ataques. Ward K=2 se corta a altura {seleccion['corte_ward']:.6f}, entre las dos últimas fusiones. El dendrograma muestra 25 ramas terminales para legibilidad, no solo 25 observaciones.

## 5. Tamaños, perfiles y comparación

{tabla(pd.concat(perfiles))}

KMeans separa un grupo sin fallos en los últimos 15 minutos y mediana de intervalo 53,56 horas, frente a actividad con fallos e intervalo mediano 0,02847 horas (1,71 minutos). Ward reproduce una estructura similar. Los nombres de clusters son identificadores arbitrarios; no ordenan gravedad.

Categorías más frecuentes (hasta tres por variable y cluster; distribuciones completas en CSV):

{tabla(pd.concat(categorias))}

Los CSV `perfil_numerico_*` contienen count, media, DE, mínimo, mediana, máximo y cuartiles en unidades originales. Count excluye intervalos ausentes. `perfil_categorico_*` contiene todos los niveles de Device Type, Country e indicador de historial con conteos y porcentajes.

ARI entre KMeans completo y Ward muestral sobre los mismos 4.000 eventos: **{comparacion['ari']:.6f}**. Contingencia (filas KMeans, columnas Ward): `{comparacion['contingencia']}`. Hay 46 asignaciones distintas tras alinear estos dos grupos; los algoritmos y poblaciones de ajuste difieren. La similitud no valida etiquetas ATO ni sustituye estabilidad frente al muestreo.

## 6. Evaluación externa posterior a congelación

{tabla(pd.concat(externas))}

Usuarios con ATO significa usuarios con al menos un evento ATO **dentro de ese cluster**. Un usuario puede tener eventos en ambos clusters: no se suman estos conteos como usuarios únicos. Hay 36 eventos ATO de 34 usuarios en train; la muestra jerárquica contiene solo un ATO. No ATO significa etiqueta negativa, no una garantía de actividad benigna.

Las prevalencias KMeans son 0,07749% y 0,07986%, prácticamente iguales descriptivamente. No hay evidencia aquí de una separación ATO útil. Esto no demuestra ausencia de cualquier señal no supervisada ni justifica buscar K con la etiqueta. La evaluación jerárquica externa es insuficiente para comparar enriquecimiento. No se calcularon accuracy, precision, recall ni F1 para clusters; ningún grupo se denomina malicioso.

## 7. Pruebas, arquitectura y límites

Se ejecutaron 9 pruebas y aprobaron 9: exclusión e invariancia ante target/IDs, transformaciones y finitud, reproducción exacta KMeans/Ward y muestreo, correspondencia de etiquetas/perfiles/evaluación externa, métricas OOF y confusiones de ambos protocolos, pares PNG/SVG a 300 DPI y consistencia de exportación supervisada. Los tests solo reajustan clustering para comprobar reproducción, no modelos supervisados. Comando: `python -B -m pytest -p no:cacheprovider -q fase04_clustering/tests`.

Clases con constructor: PreparadorDatos, ExperimentoKMeans y ExperimentoJerarquico. Responsabilidades separadas en datos, experimentos, evaluación interna, congelación, evaluación externa, estilo/visualizaciones, exportación e informes. Se aplica responsabilidad única y composición de transformadores; no se afirma implementar todos los principios SOLID mediante jerarquías innecesarias. Funciones y métodos snake_case; clases PascalCase. No se modificó código aprobado.

La muestra enriquecida, geografía sintética, correlación entre eventos de un usuario, imputación y representación euclídea limitan interpretación. Los grupos pueden capturar mecanismos de ingeniería de características. Los índices internos no miden detección ATO. No se estimaron intervalos de confianza ni estabilidad jerárquica entre múltiples muestras. No se midió pico RSS; los tamaños de memoria son estimaciones de matrices, no consumo máximo observado. El rango K=2–8 no explora toda estructura posible.

## 8. Reproducción y entregables

Versiones: `{json.dumps(audit['versiones'])}`. Mantener orden de filas y versiones. Desde raíz, en un destino nuevo (los exportadores rechazan sobrescritura): ejecutar en orden `python -B -m fase04_clustering.ejecutar`, revisar índices sin y, `python -B -m fase04_clustering.congelar`, `python -B -m fase04_clustering.evaluacion_externa`, `python -B -m fase04_clustering.visualizaciones`, `python -B -m fase04_clustering.presentacion_supervisada`, pruebas y `python -B -m fase04_clustering.informes`. No volver a ejecutar sobre esta entrega ni borrar históricos para reproducirla.

Código y diseño: `fase04_clustering/`. Resultados: `fase04_clustering/resultados/`: candidatos CSV/NPZ (incluye todos los K y enlaces), auditoría de representación, selección congelada con hashes, etiquetas por evento, perfiles numéricos/categóricos, evaluación externa y comparación de particiones. `inventario_previo.json` registra históricos y `verificacion_integridad.json` sus comprobaciones y SHA-256 de nuevos entregables (excepto su propio hash).

{figuras(r/'graficas')}

## 9. Conclusión

KMeans y Ward ofrecen un resumen exploratorio coherente de intensidad de fallos e intervalos, sin separación ATO demostrada. Se conservan para documentación descriptiva, no como clasificación ni selección de un detector. Test no se leyó ni utilizó; sus archivos solo se verificaron por metadatos. No hubo operaciones Git, instalaciones ni entrenamiento supervisado. Permanecen pendientes la selección supervisada definitiva y la evaluación final de test con autorización independiente.
'''
    with Path('INFORME_CLUSTERING_FASE04.md').open('x',encoding='utf-8') as f:f.write(texto)
    destino=Path('fase04_modelado/resultados_presentacion_supervisado');t=pd.read_csv(destino/'metricas_verificadas.csv')
    texto=f'''# Presentación académica supervisada — Fase 4

Fecha: 2026-11-19. Se redibujaron resultados históricos sin entrenar modelos, cambiar predicciones, umbrales ni métricas. Fuentes: `fase04_modelado/resultados/` (CV1: StratifiedGroupKFold por eventos con grupos usuario) y `resultados_cv_usuario/` (CV2: StratifiedKFold sobre usuarios con/sin ATO y expansión a eventos).

## Verificación y tabla principal

Cada conteo y métrica global y por fold se recalculó desde sus predicciones OOF y coincide con los CSV históricos. Los 46.305 eventos tienen una predicción por variante. `metricas_verificadas.csv` conserva también tiempos, parámetros, medias y desviaciones originales, sin modificarlos.

{tabla(t[['protocolo','modelo','TP','FP','TN','FN','precision','recall','f1','average_precision']])}

## Lectura e interpretación

Las seis variantes se muestran siempre, incluidos ceros y resultados desfavorables. GaussianNB tiene curvas coincidentes entre baseline y ponderado; se advierte explícitamente. KNN baseline mantiene mayor AP y recall cero a 0,5. GaussianNB mantiene recall alto a costa de decenas de miles de FP. Árbol baseline pierde rendimiento en CV2; estos cambios provienen de los folds, no de mejoras del algoritmo. No se declara ganador.

AP es Average Precision, no integración trapezoidal de la curva. La AP OOF global concatena puntuaciones de estimadores de folds distintos, cuya escala puede no ser comparable ni estar calibrada. No es equivalente a la media de AP por fold. Las líneas de estabilidad muestran cinco folds con subtrain solapados: cajas, DE y dispersión no representan intervalos de confianza. Solo hay 36 ATO de 34 usuarios; las dos CV no son replicaciones independientes. Las métricas son por evento y pesan más a usuarios con muchos eventos.

## Cambios visuales

23 figuras nuevas: 11 para cada CV (cuatro métricas, seis matrices individuales, PR, trayectoria por fold, variabilidad, FP/FN) y una comparación de protocolos. Cada figura tiene PNG 300 DPI y SVG, tipografía DejaVu Sans, paleta accesible consistente, títulos, etiquetas y valores visibles. Los ejes de barras parten de cero y sus escalas se declaran; no se usa accuracy como indicador principal. Matrices absolutas con TN/FP/FN/TP: filas etiqueta real y columnas predicción, umbral 0,5. Todas las fuentes son OOF de train.

## Catálogo de figuras

{figuras(destino)}

## Auditoría y protección

9/9 pruebas de la entrega global aprobadas, incluyendo métricas históricas, confusiones, exportación y archivos gráficos. Se inspeccionó visualmente la comparación de protocolos y figuras representativas. Originales en `resultados/` y `resultados_cv_usuario/` preservados; la nueva carpeta es independiente. Hashes e inventario de históricos en `fase04_clustering/resultados/verificacion_integridad.json`; test únicamente por metadatos, sin leerlo. Sin operaciones Git, instalaciones ni entrenamiento supervisado. Fase 4 no se declara terminada.
'''
    with Path('INFORME_PRESENTACION_SUPERVISADO_FASE04.md').open('x',encoding='utf-8') as f:f.write(texto)

if __name__=='__main__':main()
