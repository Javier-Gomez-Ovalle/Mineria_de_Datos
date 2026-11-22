# Presentación académica supervisada — Fase 4

Fecha: 2026-11-19. Se redibujaron resultados históricos sin entrenar modelos, cambiar predicciones, umbrales ni métricas. Fuentes: `fase04_modelado/resultados/` (CV1: StratifiedGroupKFold por eventos con grupos usuario) y `resultados_cv_usuario/` (CV2: StratifiedKFold sobre usuarios con/sin ATO y expansión a eventos).

## Verificación y tabla principal

Cada conteo y métrica global y por fold se recalculó desde sus predicciones OOF y coincide con los CSV históricos. Los 46.305 eventos tienen una predicción por variante. `metricas_verificadas.csv` conserva también tiempos, parámetros, medias y desviaciones originales, sin modificarlos.

| protocolo | modelo | TP | FP | TN | FN | precision | recall | f1 | average_precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CV1 | arbol_baseline | 6 | 55 | 46214 | 30 | 0.0983607 | 0.166667 | 0.123711 | 0.0194472 |
| CV1 | arbol_ponderado | 8 | 556 | 45713 | 28 | 0.0141844 | 0.222222 | 0.0266667 | 0.0160171 |
| CV1 | gnb_baseline | 31 | 36476 | 9793 | 5 | 0.000849152 | 0.861111 | 0.00169663 | 0.000839194 |
| CV1 | gnb_ponderado | 31 | 36476 | 9793 | 5 | 0.000849152 | 0.861111 | 0.00169663 | 0.000839194 |
| CV1 | knn_baseline | 0 | 5 | 46264 | 36 | 0 | 0 | 0 | 0.0494789 |
| CV1 | knn_ros | 6 | 93 | 46176 | 30 | 0.0606061 | 0.166667 | 0.0888889 | 0.0198437 |
| CV2 | arbol_baseline | 3 | 61 | 46208 | 33 | 0.046875 | 0.0833333 | 0.06 | 0.00886213 |
| CV2 | arbol_ponderado | 9 | 675 | 45594 | 27 | 0.0131579 | 0.25 | 0.025 | 0.0158173 |
| CV2 | gnb_baseline | 31 | 36447 | 9822 | 5 | 0.000849827 | 0.861111 | 0.00169798 | 0.000839775 |
| CV2 | gnb_ponderado | 31 | 36447 | 9822 | 5 | 0.000849827 | 0.861111 | 0.00169798 | 0.000839775 |
| CV2 | knn_baseline | 0 | 1 | 46268 | 36 | 0 | 0 | 0 | 0.0431628 |
| CV2 | knn_ros | 5 | 99 | 46170 | 31 | 0.0480769 | 0.138889 | 0.0714286 | 0.0124615 |

## Lectura e interpretación

Las seis variantes se muestran siempre, incluidos ceros y resultados desfavorables. GaussianNB tiene curvas coincidentes entre baseline y ponderado; se advierte explícitamente. KNN baseline mantiene mayor AP y recall cero a 0,5. GaussianNB mantiene recall alto a costa de decenas de miles de FP. Árbol baseline pierde rendimiento en CV2; estos cambios provienen de los folds, no de mejoras del algoritmo. No se declara ganador.

AP es Average Precision, no integración trapezoidal de la curva. La AP OOF global concatena puntuaciones de estimadores de folds distintos, cuya escala puede no ser comparable ni estar calibrada. No es equivalente a la media de AP por fold. Las líneas de estabilidad muestran cinco folds con subtrain solapados: cajas, DE y dispersión no representan intervalos de confianza. Solo hay 36 ATO de 34 usuarios; las dos CV no son replicaciones independientes. Las métricas son por evento y pesan más a usuarios con muchos eventos.

## Cambios visuales

23 figuras nuevas: 11 para cada CV (cuatro métricas, seis matrices individuales, PR, trayectoria por fold, variabilidad, FP/FN) y una comparación de protocolos. Cada figura tiene PNG 300 DPI y SVG, tipografía DejaVu Sans, paleta accesible consistente, títulos, etiquetas y valores visibles. Los ejes de barras parten de cero y sus escalas se declaran; no se usa accuracy como indicador principal. Matrices absolutas con TN/FP/FN/TP: filas etiqueta real y columnas predicción, umbral 0,5. Todas las fuentes son OOF de train.

## Catálogo de figuras

- [fase04_modelado/resultados_presentacion_supervisado/comparacion_protocolos.png](fase04_modelado/resultados_presentacion_supervisado/comparacion_protocolos.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/comparacion_protocolos.svg): Mismas variantes bajo dos protocolos de partición.
- [fase04_modelado/resultados_presentacion_supervisado/CV1/confusion_arbol_baseline.png](fase04_modelado/resultados_presentacion_supervisado/CV1/confusion_arbol_baseline.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV1/confusion_arbol_baseline.svg): Conteos absolutos de confusión, filas reales y columnas predichas.
- [fase04_modelado/resultados_presentacion_supervisado/CV1/confusion_arbol_ponderado.png](fase04_modelado/resultados_presentacion_supervisado/CV1/confusion_arbol_ponderado.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV1/confusion_arbol_ponderado.svg): Conteos absolutos de confusión, filas reales y columnas predichas.
- [fase04_modelado/resultados_presentacion_supervisado/CV1/confusion_gnb_baseline.png](fase04_modelado/resultados_presentacion_supervisado/CV1/confusion_gnb_baseline.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV1/confusion_gnb_baseline.svg): Conteos absolutos de confusión, filas reales y columnas predichas.
- [fase04_modelado/resultados_presentacion_supervisado/CV1/confusion_gnb_ponderado.png](fase04_modelado/resultados_presentacion_supervisado/CV1/confusion_gnb_ponderado.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV1/confusion_gnb_ponderado.svg): Conteos absolutos de confusión, filas reales y columnas predichas.
- [fase04_modelado/resultados_presentacion_supervisado/CV1/confusion_knn_baseline.png](fase04_modelado/resultados_presentacion_supervisado/CV1/confusion_knn_baseline.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV1/confusion_knn_baseline.svg): Conteos absolutos de confusión, filas reales y columnas predichas.
- [fase04_modelado/resultados_presentacion_supervisado/CV1/confusion_knn_ros.png](fase04_modelado/resultados_presentacion_supervisado/CV1/confusion_knn_ros.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV1/confusion_knn_ros.svg): Conteos absolutos de confusión, filas reales y columnas predichas.
- [fase04_modelado/resultados_presentacion_supervisado/CV1/curvas_pr.png](fase04_modelado/resultados_presentacion_supervisado/CV1/curvas_pr.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV1/curvas_pr.svg): Curvas OOF, AP y prevalencia; GaussianNB tiene curvas coincidentes.
- [fase04_modelado/resultados_presentacion_supervisado/CV1/estabilidad_folds.png](fase04_modelado/resultados_presentacion_supervisado/CV1/estabilidad_folds.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV1/estabilidad_folds.svg): Valores individuales por fold: composición y variabilidad.
- [fase04_modelado/resultados_presentacion_supervisado/CV1/fp_fn.png](fase04_modelado/resultados_presentacion_supervisado/CV1/fp_fn.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV1/fp_fn.svg): Falsas alarmas y omisiones absolutas, con escalas explícitas.
- [fase04_modelado/resultados_presentacion_supervisado/CV1/metricas_oof.png](fase04_modelado/resultados_presentacion_supervisado/CV1/metricas_oof.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV1/metricas_oof.svg): Precision, recall, F1 y AP OOF globales de las seis variantes.
- [fase04_modelado/resultados_presentacion_supervisado/CV1/variabilidad_folds.png](fase04_modelado/resultados_presentacion_supervisado/CV1/variabilidad_folds.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV1/variabilidad_folds.svg): Distribuciones de cinco folds, puntos individuales y media.
- [fase04_modelado/resultados_presentacion_supervisado/CV2/confusion_arbol_baseline.png](fase04_modelado/resultados_presentacion_supervisado/CV2/confusion_arbol_baseline.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV2/confusion_arbol_baseline.svg): Conteos absolutos de confusión, filas reales y columnas predichas.
- [fase04_modelado/resultados_presentacion_supervisado/CV2/confusion_arbol_ponderado.png](fase04_modelado/resultados_presentacion_supervisado/CV2/confusion_arbol_ponderado.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV2/confusion_arbol_ponderado.svg): Conteos absolutos de confusión, filas reales y columnas predichas.
- [fase04_modelado/resultados_presentacion_supervisado/CV2/confusion_gnb_baseline.png](fase04_modelado/resultados_presentacion_supervisado/CV2/confusion_gnb_baseline.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV2/confusion_gnb_baseline.svg): Conteos absolutos de confusión, filas reales y columnas predichas.
- [fase04_modelado/resultados_presentacion_supervisado/CV2/confusion_gnb_ponderado.png](fase04_modelado/resultados_presentacion_supervisado/CV2/confusion_gnb_ponderado.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV2/confusion_gnb_ponderado.svg): Conteos absolutos de confusión, filas reales y columnas predichas.
- [fase04_modelado/resultados_presentacion_supervisado/CV2/confusion_knn_baseline.png](fase04_modelado/resultados_presentacion_supervisado/CV2/confusion_knn_baseline.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV2/confusion_knn_baseline.svg): Conteos absolutos de confusión, filas reales y columnas predichas.
- [fase04_modelado/resultados_presentacion_supervisado/CV2/confusion_knn_ros.png](fase04_modelado/resultados_presentacion_supervisado/CV2/confusion_knn_ros.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV2/confusion_knn_ros.svg): Conteos absolutos de confusión, filas reales y columnas predichas.
- [fase04_modelado/resultados_presentacion_supervisado/CV2/curvas_pr.png](fase04_modelado/resultados_presentacion_supervisado/CV2/curvas_pr.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV2/curvas_pr.svg): Curvas OOF, AP y prevalencia; GaussianNB tiene curvas coincidentes.
- [fase04_modelado/resultados_presentacion_supervisado/CV2/estabilidad_folds.png](fase04_modelado/resultados_presentacion_supervisado/CV2/estabilidad_folds.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV2/estabilidad_folds.svg): Valores individuales por fold: composición y variabilidad.
- [fase04_modelado/resultados_presentacion_supervisado/CV2/fp_fn.png](fase04_modelado/resultados_presentacion_supervisado/CV2/fp_fn.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV2/fp_fn.svg): Falsas alarmas y omisiones absolutas, con escalas explícitas.
- [fase04_modelado/resultados_presentacion_supervisado/CV2/metricas_oof.png](fase04_modelado/resultados_presentacion_supervisado/CV2/metricas_oof.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV2/metricas_oof.svg): Precision, recall, F1 y AP OOF globales de las seis variantes.
- [fase04_modelado/resultados_presentacion_supervisado/CV2/variabilidad_folds.png](fase04_modelado/resultados_presentacion_supervisado/CV2/variabilidad_folds.png) · [SVG](fase04_modelado/resultados_presentacion_supervisado/CV2/variabilidad_folds.svg): Distribuciones de cinco folds, puntos individuales y media.

## Auditoría y protección

9/9 pruebas de la entrega global aprobadas, incluyendo métricas históricas, confusiones, exportación y archivos gráficos. Se inspeccionó visualmente la comparación de protocolos y figuras representativas. Originales en `resultados/` y `resultados_cv_usuario/` preservados; la nueva carpeta es independiente. Hashes e inventario de históricos en `fase04_clustering/resultados/verificacion_integridad.json`; test únicamente por metadatos, sin leerlo. Sin operaciones Git, instalaciones ni entrenamiento supervisado. Fase 4 no se declara terminada.
