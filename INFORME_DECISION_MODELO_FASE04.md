# Decisión de modelado — Fase 4

Fecha: 2026-11-21. **Escenario B: no se recomienda un modelo como detector suficientemente respaldado.** La conclusión se limita a estos predictores, muestra y procedimientos evaluados; no demuestra que ningún algoritmo pueda resolver ATO. Fase 4 continúa abierta y test permanece cerrado.

## Qué se probó y qué se preservó

La auditoría y el diagnóstico precedieron a los ajustes nuevos. Se evaluó una sola familia adicional: Random Forest ponderado, cuatro configuraciones de profundidad/hoja, 100 árboles, semilla 42. Se ejecutaron 60 ajustes internos y cinco externos en las particiones anidadas históricas. Se reutilizaron las OOF internas/externas históricas tras verificar hashes y correspondencia; no se repitieron los 120 ajustes anteriores. La selección conjunta de configuración y umbral usa exclusivamente los internos. La propuesta y configuración se guardaron antes de ajustar.

La oportunidad era reducir varianza frente al árbol sin poda mediante agregación y regularización. Se mantuvieron los seis predictores aprobados y sus exclusiones, sin ROS nuevo ni artefactos de preprocesamiento global. Este diseño evalúa una extensión de un procedimiento; el bosque dispone de cuatro configuraciones frente a una por variante histórica. Esa mayor flexibilidad es parte del procedimiento, no una comparación de complejidad idéntica. No se añaden más modelos al observar el desenlace.

## Comparación completa de clasificación externa

Umbrales aprendidos internamente. AP concatenada únicamente para cada variante; no se interpreta como probabilidad calibrada ni como media entre folds. `nan` en selectores significa deliberadamente no calculada.

| modelo | TP | FP | TN | FN | precision | recall | f1 | f2 | average_precision | FPR |
|---|---|---|---|---|---|---|---|---|---|---|
| arbol_baseline | 3 | 64 | 46205 | 33 | 0.0447761 | 0.0833333 | 0.0582524 | 0.07109 | 0.00886213 | 0.00138322 |
| arbol_ponderado | 5 | 54 | 46215 | 31 | 0.0847458 | 0.138889 | 0.105263 | 0.123153 | 0.0158173 | 0.00116709 |
| gnb_baseline | 31 | 38839 | 7430 | 5 | 0.00079753 | 0.861111 | 0.00159358 | 0.00397293 | 0.000839775 | 0.839417 |
| gnb_ponderado | 31 | 38839 | 7430 | 5 | 0.00079753 | 0.861111 | 0.00159358 | 0.00397293 | 0.000839775 | 0.839417 |
| knn_baseline | 6 | 122 | 46147 | 30 | 0.046875 | 0.166667 | 0.0731707 | 0.110294 | 0.0431628 | 0.00263675 |
| knn_ros | 5 | 104 | 46165 | 31 | 0.0458716 | 0.138889 | 0.0689655 | 0.0988142 | 0.0124615 | 0.00224773 |
| random_forest | 4 | 158 | 46111 | 32 | 0.0246914 | 0.111111 | 0.040404 | 0.0653595 | 0.0602113 | 0.00341481 |
| selector_historico | 4 | 72 | 46197 | 32 | 0.0526316 | 0.111111 | 0.0714286 | 0.0909091 | nan | 0.00155612 |
| selector_ampliado | 4 | 158 | 46111 | 32 | 0.0246914 | 0.111111 | 0.040404 | 0.0653595 | nan | 0.00341481 |

El árbol ponderado tiene el mayor F1 agregado (0,1053) y Precision (0,0847) entre estas reglas aprendidas, pero detecta cinco ATO y omite 31; **no se lo eleva retrospectivamente a ganador**. GaussianNB tiene mayor recall (0,8611), a cambio de 38.839 falsas alarmas. KNN baseline detecta seis, con 122 falsas alarmas. El bosque no mejora este equilibrio: cuatro aciertos con 158 FP y 32 FN. El selector ampliado eligió bosque en los cinco internos, por lo que coincide con él externamente; eso no demuestra que la elección fuera útil.

El selector histórico tiene los mismos cuatro aciertos agregados y solo 72 FP: 86 falsas alarmas menos que el ampliado, con igual recall agregado. No implica que acierte exactamente los mismos eventos ni que domine cada fold. Las predicciones preservadas permiten verificar las diferencias por evento. Esta comparación no usa el resultado externo para cambiar selección o umbral.

## Estabilidad y AP: magnitudes diferentes

| modelo | f1_mean | f1_std | average_precision_mean | average_precision_std | recall_mean | recall_std |
|---|---|---|---|---|---|---|
| arbol_baseline | 0.0682467 | 0.0725951 | 0.0199548 | 0.0185798 | 0.0833333 | 0.0779512 |
| arbol_ponderado | 0.115259 | 0.129951 | 0.0446052 | 0.0553159 | 0.133333 | 0.154223 |
| gnb_baseline | 0.00161577 | 0.000389351 | 0.000882568 | 0.000124251 | 0.875 | 0.216506 |
| gnb_ponderado | 0.00161577 | 0.000389351 | 0.000882568 | 0.000124251 | 0.875 | 0.216506 |
| knn_baseline | 0.070735 | 0.0788066 | 0.0554458 | 0.0429465 | 0.166667 | 0.155902 |
| knn_ros | 0.0699529 | 0.0687872 | 0.0221792 | 0.0163311 | 0.141667 | 0.149071 |
| random_forest | 0.0983333 | 0.0893996 | 0.0985813 | 0.0654884 | 0.111905 | 0.0648509 |
| selector_ampliado | 0.0983333 | 0.0893996 | 0.0985813 | 0.0654884 | 0.111905 | 0.0648509 |
| selector_historico | 0.0706252 | 0.069343 | 0.0201951 | 0.0158266 | 0.108333 | 0.108653 |

Random Forest presenta AP concatenada 0,06021 y AP media por fold 0,09858 ± 0,06549. KNN baseline tiene 0,04316 y 0,05545 ± 0,04295 respectivamente. Hay señal de ranking relativa, pero no demostración de mejora significativa o utilidad operativa. La AP por fold del bosque va de 0,00927 a 0,17539; el peor fold está lejos del mejor. Las puntuaciones proceden de estimadores y configuraciones diferentes, sin calibración común. Los selectores tienen AP solo por fold; no se concatena su mezcla de familias.

GaussianNB tiene menor dispersión absoluta de F1, pero alrededor de un resultado casi nulo: estabilidad no equivale a calidad. No existe un vencedor global combinando recall, falsas alarmas, estabilidad y coste. El bosque tampoco queda recomendado por encabezar AP.

## Transferencia de decisiones y umbrales

| fold | configuracion | max_depth | min_samples_leaf | umbral | f1_interno | f1_externo | selector |
|---|---|---|---|---|---|---|---|
| 1 | 2 | None | 1 | 0.609263 | 0.140351 | 0.166667 | random_forest |
| 2 | 0 | 8 | 1 | 0.658715 | 0.156863 | 0 | random_forest |
| 3 | 1 | 8 | 10 | 0.840798 | 0.210526 | 0.2 | random_forest |
| 4 | 0 | 8 | 1 | 0.674168 | 0.226415 | 0.0138889 | random_forest |
| 5 | 3 | None | 10 | 0.818964 | 0.181818 | 0.111111 | random_forest |

| fold | TP | FP | FN | precision | recall | f1 | average_precision | usuarios_ato_detectados |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 5 | 5 | 0.166667 | 0.166667 | 0.166667 | 0.17539 | 1 |
| 2 | 0 | 7 | 7 | 0 | 0 | 0 | 0.00926694 | 0 |
| 3 | 1 | 2 | 6 | 0.333333 | 0.142857 | 0.2 | 0.147302 | 1 |
| 4 | 1 | 135 | 7 | 0.00735294 | 0.125 | 0.0138889 | 0.0693224 | 1 |
| 5 | 1 | 9 | 7 | 0.1 | 0.125 | 0.111111 | 0.091624 | 1 |

Los umbrales del bosque oscilan entre 0,6093 y 0,8408; se utilizan las cuatro configuraciones en algún fold. F1 interno mejora, pero externo cae: especialmente fold 4, de 0,2264 interno a 0,0139 externo, con 135 FP (85,4% de todos los FP del bosque). El fold 2 no detecta ningún ATO. Una evaluación sin separación interna/externa habría ocultado esta fragilidad.

Referencia fija 0,5, prevista antes del experimento:

| regla | TP | FP | FN | precision | recall | f1 | f2 | usuarios_ato_detectados | usuarios_sin_ato_con_alerta |
|---|---|---|---|---|---|---|---|---|---|
| aprendido | 4 | 158 | 32 | 0.0246914 | 0.111111 | 0.040404 | 0.0653595 | 4 | 126 |
| fijo_05 | 16 | 1474 | 20 | 0.0107383 | 0.444444 | 0.0209699 | 0.0489596 | 16 | 662 |

Con 0,5 se detectan 16 ATO, pero se generan 1.474 FP (aproximadamente 92 por acierto). Con umbrales aprendidos son 158/4 = 39,5 FP por acierto y 97,53% de alertas falsas. La regla interna de F1 sacrifica recuperación para reducir alertas y no transfiere bien. No se ha escogido otro umbral mirando estos resultados. Las veinte tablas umbrales_internos_{fold}_{configuracion}.csv conservan todos los estados internos, incluidos alertar a todos o a ninguno. F1 no representa costes universales; falta capacidad de revisión humana y coste relativo de omisiones/falsas alarmas para decidir un criterio operativo defendible.

## Eventos y usuarios

| modelo | usuarios_ato | usuarios_ato_detectados | usuarios_ato_omitidos | recall_usuarios | usuarios_sin_ato_con_alerta | usuarios_con_fp |
|---|---|---|---|---|---|---|
| arbol_baseline | 34 | 3 | 31 | 0.0882353 | 18 | 31 |
| arbol_ponderado | 34 | 5 | 29 | 0.147059 | 21 | 33 |
| gnb_baseline | 34 | 30 | 4 | 0.882353 | 1357 | 1390 |
| gnb_ponderado | 34 | 30 | 4 | 0.882353 | 1357 | 1390 |
| knn_baseline | 34 | 6 | 28 | 0.176471 | 37 | 52 |
| knn_ros | 34 | 5 | 29 | 0.147059 | 24 | 39 |
| random_forest | 34 | 4 | 30 | 0.117647 | 126 | 140 |
| selector_historico | 34 | 4 | 30 | 0.117647 | 16 | 27 |
| selector_ampliado | 34 | 4 | 30 | 0.117647 | 126 | 140 |

Se define usuario ATO detectado como aquel con al menos un **evento ATO correctamente alertado**, no simplemente una alerta en cualquier login. El bosque detecta 4/34 usuarios positivos (11,76%), omite 30 y genera FP en 140 usuarios; 126 son usuarios sin ATO. Los 158 FP no se concentran únicamente en un sujeto: máximo siete en un usuario, 28 entre los diez con más FP. Todos los cuatro aciertos del bosque están en RO; allí omite once ATO. NO aporta 122 FP y cinco FN. Este contraste descriptivo tiene denominadores por perfil en los CSV y no autoriza a crear reglas por país o memorizar usuarios.

La métrica por evento da más peso a usuarios activos; por usuario cambia la unidad. Con solo 34 usuarios positivos, los intervalos de generalización serían amplios y la independencia entre eventos no es defendible. No se calculan pruebas de significación que traten los cinco folds solapados como réplicas independientes.

## CV1, CV2 y cinco modelos académicos

Los seis experimentos supervisados históricos siguen completos, también los desfavorables. Las siguientes métricas corresponden a umbral 0,5; cambiar la distribución de folds no cambia el algoritmo ni constituye una mejora causal:

| protocolo | modelo | TP | FP | FN | precision | recall | f1 | average_precision |
|---|---|---|---|---|---|---|---|---|
| CV1 | arbol_baseline | 6 | 55 | 30 | 0.0983607 | 0.166667 | 0.123711 | 0.0194472 |
| CV1 | arbol_ponderado | 8 | 556 | 28 | 0.0141844 | 0.222222 | 0.0266667 | 0.0160171 |
| CV1 | gnb_baseline | 31 | 36476 | 5 | 0.000849152 | 0.861111 | 0.00169663 | 0.000839194 |
| CV1 | gnb_ponderado | 31 | 36476 | 5 | 0.000849152 | 0.861111 | 0.00169663 | 0.000839194 |
| CV1 | knn_baseline | 0 | 5 | 36 | 0 | 0 | 0 | 0.0494789 |
| CV1 | knn_ros | 6 | 93 | 30 | 0.0606061 | 0.166667 | 0.0888889 | 0.0198437 |
| CV2 | arbol_baseline | 3 | 61 | 33 | 0.046875 | 0.0833333 | 0.06 | 0.00886213 |
| CV2 | arbol_ponderado | 9 | 675 | 27 | 0.0131579 | 0.25 | 0.025 | 0.0158173 |
| CV2 | gnb_baseline | 31 | 36447 | 5 | 0.000849827 | 0.861111 | 0.00169798 | 0.000839775 |
| CV2 | gnb_ponderado | 31 | 36447 | 5 | 0.000849827 | 0.861111 | 0.00169798 | 0.000839775 |
| CV2 | knn_baseline | 0 | 1 | 36 | 0 | 0 | 0 | 0.0431628 |
| CV2 | knn_ros | 5 | 99 | 31 | 0.0480769 | 0.138889 | 0.0714286 | 0.0124615 |

Los cinco modelos exigidos por el curso siguen documentados: árbol, GaussianNB, KNN, KMeans y jerárquico (con sus variantes). Random Forest es una extensión adicional. KMeans/jerárquico son segmentaciones exploratorias y no reciben TP/FP ni se venden como detectores sin una regla supervisada válida. KMeans k=2: silhouette 0,6060, grupos 41.296/5.009; Ward k=2 sobre 4.000 observaciones: silhouette 0,5978, grupos 3.534/466. Las prevalencias KMeans 32/41.296 y 4/5.009 son similares; separar geometría no demuestra separar ATO. Sus resultados y limitaciones permanecen en [INFORME_CLUSTERING_FASE04.md](INFORME_CLUSTERING_FASE04.md).

Para presentación académica se conservan íntegros `fase04_modelado/resultados/`, `resultados_cv_usuario/`, `resultados_presentacion_supervisado/`, `seleccion_supervisada/resultados/`, `validacion_anidada/resultados/` y `fase04_clustering/resultados/`: métricas por fold, matrices, PR, análisis de umbrales, errores y gráficas. Este informe añade una conclusión; no reemplaza resultados individuales. CV1, CV2, anidada y extensión reutilizan train; no son experimentos independientes.

## Coste y pruebas

| nivel | preprocesamiento_s | entrenamiento_s | prediccion_s |
|---|---|---|---|
| externo | 0.386952 | 8.08671 | 0.141015 |
| interno | 3.77581 | 58.0213 | 2.10285 |

Tiempo total del experimento: 80.370 s, 65 ajustes y 6.500 árboles; máximo RSS observado al final de un fold 230.16 MiB. Es muestreo de RSS, no pico continuo ni consumo exclusivo del modelo. Tiempos históricos se conservan en sus informes y CSV; no se equipara tiempo de búsqueda de 65 ajustes con un único ajuste histórico. No se instaló ni actualizó ningún paquete.

**15 tests ejecutados y aprobados en 7,87 s**, una pasada. Incluyen dos ajustes sintéticos adicionales, no parte de los 65 experimentales. Se comprobaron particiones reproducibles, separación de usuarios, cobertura OOF interna/externa, clave natural/target, medianas/categorías locales de los 65 ajustes, inmutabilidad de validación, ausencia de ROS nuevo, selección y desempates frente al algoritmo exhaustivo histórico, recálculo de métricas globales/por fold, hashes, configuración y 14 pares PNG/SVG. El test de guardia simula el intento prohibido antes de acceso al archivo. No se repitió el experimento completo para demostrar igualdad bit a bit: reproducibilidad de entrenamiento comprobada con datos sintéticos, semillas y selección real reproducibles.

Integridad comprobada: 406 archivos históricos con SHA-256, tamaño y mtime iguales al inventario previo. Test no se leyó, inspeccionó ni hasheó. No se ejecutó Git, no se modificaron datasets, Fase 3 ni preprocesamiento aprobado. No hay modelo final entrenado. Los tests validan implementación; no demuestran validez científica por sí solos.

## Gráficas y datos reproducibles

- [graficas/comparacion_metricas.png](fase04_modelado/mejora_controlada/resultados/graficas/comparacion_metricas.png): Precision, Recall, F1 y F2 de las siete variantes y dos selectores; sin accuracy. SVG en `fase04_modelado/mejora_controlada/resultados/graficas/comparacion_metricas.svg`.
- [graficas/estabilidad_folds.png](fase04_modelado/mejora_controlada/resultados/graficas/estabilidad_folds.png): Cinco puntos por procedimiento; DE muestral. AP por fold, incluida la familia seleccionada en cada fold. SVG en `fase04_modelado/mejora_controlada/resultados/graficas/estabilidad_folds.svg`.
- [graficas/falsas_alarmas_omisiones.png](fase04_modelado/mejora_controlada/resultados/graficas/falsas_alarmas_omisiones.png): Cantidad absoluta de FP y FN, incluyendo GaussianNB sin ocultarlo. SVG en `fase04_modelado/mejora_controlada/resultados/graficas/falsas_alarmas_omisiones.svg`.
- [graficas/confusion_arbol_baseline.png](fase04_modelado/mejora_controlada/resultados/graficas/confusion_arbol_baseline.png): Matriz absoluta de Árbol base. SVG en `fase04_modelado/mejora_controlada/resultados/graficas/confusion_arbol_baseline.svg`.
- [graficas/confusion_arbol_ponderado.png](fase04_modelado/mejora_controlada/resultados/graficas/confusion_arbol_ponderado.png): Matriz absoluta de Árbol ponderado. SVG en `fase04_modelado/mejora_controlada/resultados/graficas/confusion_arbol_ponderado.svg`.
- [graficas/confusion_gnb_baseline.png](fase04_modelado/mejora_controlada/resultados/graficas/confusion_gnb_baseline.png): Matriz absoluta de GNB base. SVG en `fase04_modelado/mejora_controlada/resultados/graficas/confusion_gnb_baseline.svg`.
- [graficas/confusion_gnb_ponderado.png](fase04_modelado/mejora_controlada/resultados/graficas/confusion_gnb_ponderado.png): Matriz absoluta de GNB ponderado. SVG en `fase04_modelado/mejora_controlada/resultados/graficas/confusion_gnb_ponderado.svg`.
- [graficas/confusion_knn_baseline.png](fase04_modelado/mejora_controlada/resultados/graficas/confusion_knn_baseline.png): Matriz absoluta de KNN base. SVG en `fase04_modelado/mejora_controlada/resultados/graficas/confusion_knn_baseline.svg`.
- [graficas/confusion_knn_ros.png](fase04_modelado/mejora_controlada/resultados/graficas/confusion_knn_ros.png): Matriz absoluta de KNN ROS. SVG en `fase04_modelado/mejora_controlada/resultados/graficas/confusion_knn_ros.svg`.
- [graficas/confusion_random_forest.png](fase04_modelado/mejora_controlada/resultados/graficas/confusion_random_forest.png): Matriz absoluta de Random Forest. SVG en `fase04_modelado/mejora_controlada/resultados/graficas/confusion_random_forest.svg`.
- [graficas/confusion_selector_historico.png](fase04_modelado/mejora_controlada/resultados/graficas/confusion_selector_historico.png): Matriz absoluta de Selector 6. SVG en `fase04_modelado/mejora_controlada/resultados/graficas/confusion_selector_historico.svg`.
- [graficas/confusion_selector_ampliado.png](fase04_modelado/mejora_controlada/resultados/graficas/confusion_selector_ampliado.png): Matriz absoluta de Selector 7. SVG en `fase04_modelado/mejora_controlada/resultados/graficas/confusion_selector_ampliado.svg`.
- [graficas/pr_por_fold.png](fase04_modelado/mejora_controlada/resultados/graficas/pr_por_fold.png): Curvas Precision–Recall y AP de las siete variantes en cada fold externo; sin concatenar familias. SVG en `fase04_modelado/mejora_controlada/resultados/graficas/pr_por_fold.svg`.
- [graficas/bosque_por_fold.png](fase04_modelado/mejora_controlada/resultados/graficas/bosque_por_fold.png): Detectados, omitidos y falsas alarmas del bosque por fold. SVG en `fase04_modelado/mejora_controlada/resultados/graficas/bosque_por_fold.svg`.

Tablas y predicciones nuevas en `fase04_modelado/mejora_controlada/resultados/`: comparacion_global.csv (ambas reglas), metricas_por_fold.csv, resumen_folds.csv (DE muestral), metricas_por_usuario.csv, errores_por_perfil.csv, referencias_cv1_cv2.csv, tiempos.csv, transferencia_seleccion.csv, predicciones_externas_rf.csv, predicciones_selector_ampliado.csv, cinco OOF internas, veinte tablas de umbrales, cinco decisiones congeladas, configuracion_congelada.json, auditoria_ajustes.json, ejecucion.json y pruebas.txt. Las claves/índices originales permiten trazabilidad; no son predictores. Todas las figuras incluyen las variantes desfavorables. Se inspeccionó visualmente la comparación principal; validación automática de formato/tamaño de todas las figuras.

## Decisión y próximos pasos

No hay candidato con equilibrio suficientemente respaldado para recomendarlo como detector útil. El árbol ponderado es una referencia descriptiva por F1, el bosque/KNN referencias por ranking, y GaussianNB por recuperación extrema; ninguno reúne de manera estable los objetivos. El criterio de descarte del nuevo experimento se cumple: mayor AP no se traduce en recuperación/falsas alarmas consistentes, y ampliar la selección empeora FP agregados sin aumentar aciertos.

La evidencia respalda limitaciones de esta muestra y representación, no imposibilidad universal ni una atribución causal exclusiva al desbalance. Hay ocho positivos indistinguibles de negativos por X, redundancia, pocos sujetos positivos, señales temporales escasas y geografía sintética. Excluir variables semánticamente inválidas no se revierte porque otros modelos rindan poco. Ni más algoritmos indiscriminados ni elegir el mejor umbral externo corrigen ese problema.

Se recomienda cerrar esta búsqueda exploratoria y acordar con el responsable académico si se presentará el resultado negativo comparativo o se solicitarán más usuarios ATO y señales preautenticación verificadas. Para completar evaluación final habrá que aprobar un **procedimiento de referencia explícito** (sin afirmar que es bueno), fijar su selección/configuración/preprocesamiento/umbral usando solo train, y pedir autorización independiente antes de abrir test. No se usa test para desempatar. Si se amplía la muestra o representación, será un protocolo nuevo y documentado. No se declara terminada Fase 4.
