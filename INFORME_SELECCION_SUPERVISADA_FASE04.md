# Selección supervisada y análisis de umbrales — Fase 4

Fecha: 2026-11-21. Proyecto académico; no detector listo para producción. No se entrenó ningún estimador en esta etapa ni se leyó test.

## 1. Dictamen y alcance académico

**No existe evidencia suficiente para congelar una configuración ganadora universal ni autorizar ya su evaluación final.** KNN baseline merece prioridad como candidato para la siguiente validación de selección de umbral: conserva la mayor AP en ambas CV y ofrece un compromiso de pocas falsas alarmas reproducido descriptivamente a 0,4. Esto no satisface por sí mismo la prioridad de detectar ATO: a ese umbral omite 32 de 36. No se recomienda convertir esta prioridad de investigación en un modelo final sin fijar el objetivo de detección y la tolerancia de alertas.

El profesor requiere cinco algoritmos: M1 Árbol de Decisión, M2 GaussianNB, M3 KNN, M4 KMeans y M5 jerárquico (Ward seleccionado, average como alternativa estudiada). Los tres supervisados tienen seis variantes, documentadas íntegramente en CV1 y CV2. Clustering conserva resultados individuales e internos y evaluación externa histórica: no tiene curvas PR ni matrices TP/FP como clasificador porque no existe una regla validada que convierta cluster en predicción ATO. No se inventa tal regla para completar una tabla.

## 2. Fuentes y auditoría previa

Antes de crear archivos se revisaron informes CV1/CV2, fábrica de modelos, métricas, distribuciones y OOF; se verificaron hashes contra el inventario histórico, eventos, etiquetas, usuarios disjuntos y métricas globales y por fold. Todos coincidieron. Cada protocolo contiene 277.830 predicciones: 46.305 eventos × seis variantes; no se mezclan variantes ni protocolos. Se alinean evento_id y clave User ID + Login Timestamp + IP Address con train, conservando User ID entero. Cada usuario pertenece a un único fold de validación, y cada evento tiene una sola OOF por variante/protocolo.

Train tiene 46.305 eventos, 36 ATO de 34 usuarios y 1.600 usuarios totales. Prevalencia 36/46.305 = 0,0777454%. El tamaño de test no interviene en ningún cálculo. La guardia de aperturas rechaza CSV/NPY/joblib de test. El inventario histórico comprueba test solo por tamaño y fecha, nunca contenido.

Hashes SHA-256 de fuentes principales:

| archivo | sha256 |
| --- | --- |
| dataset_train_fase04.csv | 98d4d4970ada7bf11ec2e76f89e93c46c76c3d097043020598638547f977e53f |
| fase04_modelado/resultados/predicciones_oof.csv | 80c55d729006d22d1bc03019b57777708ea2fe76482e12ba13c67482399a0d91 |
| fase04_modelado/resultados/comparacion_modelos.csv | cdce2af5f6b34614c62de3a6cfde6e59e6d02fcbf6a851827acd47729986d052 |
| fase04_modelado/resultados/metricas_por_fold.csv | 9836e99cafe55bf0b3ce2a9f86d5dff2442db1ecca5093fc28c2ca199fbf2722 |
| fase04_modelado/resultados/distribucion_folds.csv | 9c8b3e14b7af2ec422ad874f512781e8ff1a52aae5d83433389df2063fe5be5c |
| fase04_modelado/resultados/configuracion_auditoria.json | 5b49797a1f9c254d60bb7ac9c8dcd93ce889bf543d1182b35eb81c9913f298c4 |
| fase04_modelado/resultados_cv_usuario/predicciones_oof.csv | 30f49c2aeb1e435c1989c1b660d12e708740181b88282bf28ed0124ad7c2b505 |
| fase04_modelado/resultados_cv_usuario/comparacion_modelos.csv | f5274eab3f2e43589de094526d0ee1ccc27c7b37c1f279cd0f08965e604e17bd |
| fase04_modelado/resultados_cv_usuario/metricas_por_fold.csv | 9cffb9aefec5602a26c91971db69e33fb21aaead727696f5a8821169a469958f |
| fase04_modelado/resultados_cv_usuario/distribucion_folds.csv | 23d64f6bcc834b05d740e71c0276f2b86175fe7986b85ee656297ca9aed7e0af |
| fase04_modelado/resultados_cv_usuario/configuracion_auditoria.json | 10241490feef6bc5fd37d654e75b8a1be19b21a21afa3bb6081435d8c8aaedfa |

Se usa la representación histórica dentro de cada fold: mediana, log1p según algoritmo, One-Hot; StandardScaler en KNN, ponderación y ROS solo en subtrain. No se modifican hiperparámetros, transformaciones, etiquetas ni exclusiones Impossible Travel. Este análisis utiliza scores guardados y no puede demostrar por sí solo cada operación del entrenamiento; la auditoría de ajuste existente y su código constituyen la evidencia histórica complementaria.

## 3. Diferencias entre protocolos

CV1 usa StratifiedGroupKFold con estratificación por evento y agrupación por usuario. CV2 aplica StratifiedKFold a una tabla de usuarios con/sin ATO y expande eventos. Ambas usan cinco folds, shuffle y semilla 42. CV2 equilibra mejor usuarios positivos; no se trata de una mejora del algoritmo. Los números de fold no representan los mismos usuarios entre protocolos.

| protocolo | fold | validacion_eventos | validacion_usuarios | validacion_positivos | validacion_usuarios_positivos | usuarios_compartidos |
| --- | --- | --- | --- | --- | --- | --- |
| CV1 | 1 | 8815 | 320 | 10 | 9 | 0 |
| CV1 | 2 | 9214 | 320 | 8 | 8 | 0 |
| CV1 | 3 | 9535 | 319 | 1 | 1 | 0 |
| CV1 | 4 | 10006 | 320 | 8 | 8 | 0 |
| CV1 | 5 | 8735 | 321 | 9 | 8 | 0 |
| CV2 | 1 | 9235 | 320 | 6 | 6 | 0 |
| CV2 | 2 | 10112 | 320 | 7 | 7 | 0 |
| CV2 | 3 | 8321 | 320 | 7 | 7 | 0 |
| CV2 | 4 | 9677 | 320 | 8 | 7 | 0 |
| CV2 | 5 | 8960 | 320 | 8 | 7 | 0 |

## 4. Métricas y resultados históricos de todas las variantes

TP: ATO detectados; FN: ATO omitidos; FP: eventos negativos con alerta; TN: negativos sin alerta. Precision=TP/(TP+FP), recall=TP/(TP+FN), F1=2TP/(2TP+FP+FN). Alertas=TP+FP; porcentaje de alertas=100×alertas/eventos. Cuando no hay predicciones positivas se informa precision=0 por convención y una bandera explícita; no significa una precision estimable. No se usa accuracy como indicador principal.

AP es Average Precision del ranking, no área trapezoidal. Es invariante al umbral de decisión aplicado después: se repite en las tablas para referencia, no se optimiza variando t. AP global concatena puntuaciones de estimadores de cinco folds, no necesariamente calibradas en una misma escala; no equivale al promedio de AP por fold.

### Umbral histórico 0,5

| protocolo | modelo | umbral | TP | FP | TN | FN | precision | recall | f1 | average_precision | alertas | porcentaje_alertas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CV1 | arbol_baseline | 0.5 | 6 | 55 | 46214 | 30 | 0.09836066 | 0.1666667 | 0.1237113 | 0.01944715 | 61 | 0.1317352 |
| CV1 | arbol_ponderado | 0.5 | 8 | 556 | 45713 | 28 | 0.0141844 | 0.2222222 | 0.02666667 | 0.01601708 | 564 | 1.218011 |
| CV1 | gnb_baseline | 0.5 | 31 | 36476 | 9793 | 5 | 0.0008491522 | 0.8611111 | 0.001696631 | 0.0008391941 | 36507 | 78.8403 |
| CV1 | gnb_ponderado | 0.5 | 31 | 36476 | 9793 | 5 | 0.0008491522 | 0.8611111 | 0.001696631 | 0.0008391941 | 36507 | 78.8403 |
| CV1 | knn_baseline | 0.5 | 0 | 5 | 46264 | 36 | 0 | 0 | 0 | 0.04947889 | 5 | 0.01079797 |
| CV1 | knn_ros | 0.5 | 6 | 93 | 46176 | 30 | 0.06060606 | 0.1666667 | 0.08888889 | 0.01984369 | 99 | 0.2137998 |
| CV2 | arbol_baseline | 0.5 | 3 | 61 | 46208 | 33 | 0.046875 | 0.08333333 | 0.06 | 0.00886213 | 64 | 0.138214 |
| CV2 | arbol_ponderado | 0.5 | 9 | 675 | 45594 | 27 | 0.01315789 | 0.25 | 0.025 | 0.01581734 | 684 | 1.477162 |
| CV2 | gnb_baseline | 0.5 | 31 | 36447 | 9822 | 5 | 0.0008498273 | 0.8611111 | 0.001697979 | 0.0008397754 | 36478 | 78.77767 |
| CV2 | gnb_ponderado | 0.5 | 31 | 36447 | 9822 | 5 | 0.0008498273 | 0.8611111 | 0.001697979 | 0.0008397754 | 36478 | 78.77767 |
| CV2 | knn_baseline | 0.5 | 0 | 1 | 46268 | 36 | 0 | 0 | 0 | 0.04316277 | 1 | 0.002159594 |
| CV2 | knn_ros | 0.5 | 5 | 99 | 46170 | 31 | 0.04807692 | 0.1388889 | 0.07142857 | 0.01246152 | 104 | 0.2245978 |

### Resultados individuales por fold a 0,5

| protocolo | modelo | fold | TP | FP | TN | FN | precision | recall | f1 | average_precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CV1 | arbol_baseline | 1 | 2 | 17 | 8788 | 8 | 0.1052632 | 0.2 | 0.137931 | 0.01731621 |
| CV1 | arbol_baseline | 2 | 2 | 16 | 9190 | 6 | 0.1111111 | 0.25 | 0.1538462 | 0.03808883 |
| CV1 | arbol_baseline | 3 | 0 | 4 | 9530 | 1 | 0 | 0 | 0 | 0.0001048768 |
| CV1 | arbol_baseline | 4 | 1 | 13 | 9985 | 7 | 0.07142857 | 0.125 | 0.09090909 | 0.02515321 |
| CV1 | arbol_baseline | 5 | 1 | 5 | 8721 | 8 | 0.1666667 | 0.1111111 | 0.1333333 | 0.01943437 |
| CV1 | arbol_ponderado | 1 | 2 | 5 | 8800 | 8 | 0.2857143 | 0.2 | 0.2352941 | 0.08424088 |
| CV1 | arbol_ponderado | 2 | 3 | 158 | 9048 | 5 | 0.01863354 | 0.375 | 0.03550296 | 0.02073698 |
| CV1 | arbol_ponderado | 3 | 0 | 135 | 9399 | 1 | 0 | 0 | 0 | 0.0001048768 |
| CV1 | arbol_ponderado | 4 | 2 | 141 | 9857 | 6 | 0.01398601 | 0.25 | 0.02649007 | 0.02111048 |
| CV1 | arbol_ponderado | 5 | 1 | 117 | 8609 | 8 | 0.008474576 | 0.1111111 | 0.01574803 | 0.01678887 |
| CV1 | gnb_baseline | 1 | 8 | 6939 | 1866 | 2 | 0.001151576 | 0.8 | 0.002299842 | 0.001148147 |
| CV1 | gnb_baseline | 2 | 8 | 6934 | 2272 | 0 | 0.001152406 | 1 | 0.002302158 | 0.001152406 |
| CV1 | gnb_baseline | 3 | 1 | 7821 | 1713 | 0 | 0.0001278445 | 1 | 0.0002556564 | 0.0001278445 |
| CV1 | gnb_baseline | 4 | 8 | 7854 | 2144 | 0 | 0.001017553 | 1 | 0.002033037 | 0.001017553 |
| CV1 | gnb_baseline | 5 | 6 | 6928 | 1798 | 3 | 0.0008653014 | 0.6666667 | 0.001728359 | 0.0009203135 |
| CV1 | gnb_ponderado | 1 | 8 | 6939 | 1866 | 2 | 0.001151576 | 0.8 | 0.002299842 | 0.001148147 |
| CV1 | gnb_ponderado | 2 | 8 | 6934 | 2272 | 0 | 0.001152406 | 1 | 0.002302158 | 0.001152406 |
| CV1 | gnb_ponderado | 3 | 1 | 7821 | 1713 | 0 | 0.0001278445 | 1 | 0.0002556564 | 0.0001278445 |
| CV1 | gnb_ponderado | 4 | 8 | 7854 | 2144 | 0 | 0.001017553 | 1 | 0.002033037 | 0.001017553 |
| CV1 | gnb_ponderado | 5 | 6 | 6928 | 1798 | 3 | 0.0008653014 | 0.6666667 | 0.001728359 | 0.0009203135 |
| CV1 | knn_baseline | 1 | 0 | 0 | 8805 | 10 | 0 | 0 | 0 | 0.2522914 |
| CV1 | knn_baseline | 2 | 0 | 4 | 9202 | 8 | 0 | 0 | 0 | 0.03917902 |
| CV1 | knn_baseline | 3 | 0 | 0 | 9534 | 1 | 0 | 0 | 0 | 0.0001048768 |
| CV1 | knn_baseline | 4 | 0 | 0 | 9998 | 8 | 0 | 0 | 0 | 0.07202821 |
| CV1 | knn_baseline | 5 | 0 | 1 | 8725 | 9 | 0 | 0 | 0 | 0.006206861 |
| CV1 | knn_ros | 1 | 3 | 14 | 8791 | 7 | 0.1764706 | 0.3 | 0.2222222 | 0.09370382 |
| CV1 | knn_ros | 2 | 2 | 40 | 9166 | 6 | 0.04761905 | 0.25 | 0.08 | 0.01721947 |
| CV1 | knn_ros | 3 | 0 | 10 | 9524 | 1 | 0 | 0 | 0 | 0.0001048768 |
| CV1 | knn_ros | 4 | 1 | 17 | 9981 | 7 | 0.05555556 | 0.125 | 0.07692308 | 0.01688115 |
| CV1 | knn_ros | 5 | 0 | 12 | 8714 | 9 | 0 | 0 | 0 | 0.006206861 |
| CV2 | arbol_baseline | 1 | 1 | 29 | 9200 | 5 | 0.03333333 | 0.1666667 | 0.05555556 | 0.008085126 |
| CV2 | arbol_baseline | 2 | 0 | 12 | 10093 | 7 | 0 | 0 | 0 | 0.001700774 |
| CV2 | arbol_baseline | 3 | 0 | 11 | 8303 | 7 | 0 | 0 | 0 | 0.01171008 |
| CV2 | arbol_baseline | 4 | 1 | 3 | 9666 | 7 | 0.25 | 0.125 | 0.1666667 | 0.03197336 |
| CV2 | arbol_baseline | 5 | 1 | 6 | 8946 | 7 | 0.1428571 | 0.125 | 0.1333333 | 0.04630456 |
| CV2 | arbol_ponderado | 1 | 2 | 137 | 9092 | 4 | 0.01438849 | 0.3333333 | 0.02758621 | 0.01949788 |
| CV2 | arbol_ponderado | 2 | 1 | 135 | 9970 | 6 | 0.007352941 | 0.1428571 | 0.01398601 | 0.001643775 |
| CV2 | arbol_ponderado | 3 | 1 | 138 | 8176 | 6 | 0.007194245 | 0.1428571 | 0.01369863 | 0.01171008 |
| CV2 | arbol_ponderado | 4 | 3 | 133 | 9536 | 5 | 0.02205882 | 0.375 | 0.04166667 | 0.1374215 |
| CV2 | arbol_ponderado | 5 | 2 | 132 | 8820 | 6 | 0.01492537 | 0.25 | 0.02816901 | 0.05275298 |
| CV2 | gnb_baseline | 1 | 6 | 7402 | 1827 | 0 | 0.0008099352 | 1 | 0.001618559 | 0.0008099352 |
| CV2 | gnb_baseline | 2 | 7 | 7713 | 2392 | 0 | 0.0009067358 | 1 | 0.001811829 | 0.0009067358 |
| CV2 | gnb_baseline | 3 | 7 | 6622 | 1692 | 0 | 0.001055966 | 1 | 0.002109705 | 0.001055966 |
| CV2 | gnb_baseline | 4 | 7 | 7539 | 2130 | 1 | 0.0009276438 | 0.875 | 0.001853323 | 0.0009150261 |
| CV2 | gnb_baseline | 5 | 4 | 7171 | 1781 | 4 | 0.0005574913 | 0.5 | 0.001113741 | 0.0007251742 |
| CV2 | gnb_ponderado | 1 | 6 | 7402 | 1827 | 0 | 0.0008099352 | 1 | 0.001618559 | 0.0008099352 |
| CV2 | gnb_ponderado | 2 | 7 | 7713 | 2392 | 0 | 0.0009067358 | 1 | 0.001811829 | 0.0009067358 |
| CV2 | gnb_ponderado | 3 | 7 | 6622 | 1692 | 0 | 0.001055966 | 1 | 0.002109705 | 0.001055966 |
| CV2 | gnb_ponderado | 4 | 7 | 7539 | 2130 | 1 | 0.0009276438 | 0.875 | 0.001853323 | 0.0009150261 |
| CV2 | gnb_ponderado | 5 | 4 | 7171 | 1781 | 4 | 0.0005574913 | 0.5 | 0.001113741 | 0.0007251742 |
| CV2 | knn_baseline | 1 | 0 | 0 | 9229 | 6 | 0 | 0 | 0 | 0.09277548 |
| CV2 | knn_baseline | 2 | 0 | 0 | 10105 | 7 | 0 | 0 | 0 | 0.0006922468 |
| CV2 | knn_baseline | 3 | 0 | 1 | 8313 | 7 | 0 | 0 | 0 | 0.01740761 |
| CV2 | knn_baseline | 4 | 0 | 0 | 9669 | 8 | 0 | 0 | 0 | 0.08395336 |
| CV2 | knn_baseline | 5 | 0 | 0 | 8952 | 8 | 0 | 0 | 0 | 0.08240041 |
| CV2 | knn_ros | 1 | 2 | 21 | 9208 | 4 | 0.08695652 | 0.3333333 | 0.137931 | 0.02941864 |
| CV2 | knn_ros | 2 | 0 | 20 | 10085 | 7 | 0 | 0 | 0 | 0.0006922468 |
| CV2 | knn_ros | 3 | 0 | 18 | 8296 | 7 | 0 | 0 | 0 | 0.01740761 |
| CV2 | knn_ros | 4 | 2 | 34 | 9635 | 6 | 0.05555556 | 0.25 | 0.09090909 | 0.01847717 |
| CV2 | knn_ros | 5 | 1 | 6 | 8946 | 7 | 0.1428571 | 0.125 | 0.1333333 | 0.04490041 |

### Media y desviación estándar entre folds a 0,5

| protocolo | modelo | precision_mean | precision_std | recall_mean | recall_std | f1_mean | f1_std | average_precision_mean | average_precision_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CV1 | arbol_baseline | 0.0908939 | 0.06123178 | 0.1372222 | 0.09529033 | 0.1032039 | 0.06221053 | 0.0200195 | 0.01375771 |
| CV1 | arbol_ponderado | 0.06536168 | 0.123376 | 0.1872222 | 0.1416067 | 0.06260703 | 0.09743626 | 0.02859642 | 0.03226958 |
| CV1 | gnb_baseline | 0.0008629361 | 0.000427603 | 0.8933333 | 0.1534782 | 0.001723811 | 0.0008540223 | 0.0008732527 | 0.0004278328 |
| CV1 | gnb_ponderado | 0.0008629361 | 0.000427603 | 0.8933333 | 0.1534782 | 0.001723811 | 0.0008540223 | 0.0008732527 | 0.0004278328 |
| CV1 | knn_baseline | 0 | 0 | 0 | 0 | 0 | 0 | 0.07396206 | 0.1037552 |
| CV1 | knn_ros | 0.05592904 | 0.0722073 | 0.135 | 0.1387444 | 0.07582906 | 0.09076018 | 0.02682324 | 0.0380887 |
| CV2 | arbol_baseline | 0.0852381 | 0.109192 | 0.08333333 | 0.0779512 | 0.07111111 | 0.07641666 | 0.01995478 | 0.01857976 |
| CV2 | arbol_ponderado | 0.01318397 | 0.006187166 | 0.2488095 | 0.1066789 | 0.02502131 | 0.01165692 | 0.04460523 | 0.0553159 |
| CV2 | gnb_baseline | 0.0008515544 | 0.0001862955 | 0.875 | 0.2165064 | 0.001701431 | 0.0003722209 | 0.0008825675 | 0.0001242506 |
| CV2 | gnb_ponderado | 0.0008515544 | 0.0001862955 | 0.875 | 0.2165064 | 0.001701431 | 0.0003722209 | 0.0008825675 | 0.0001242506 |
| CV2 | knn_baseline | 0 | 0 | 0 | 0 | 0 | 0 | 0.05544582 | 0.04294646 |
| CV2 | knn_ros | 0.05707384 | 0.06076368 | 0.1416667 | 0.1490712 | 0.07243469 | 0.06861721 | 0.02217922 | 0.01633115 |

DE usa ddof=1, describe cinco folds con subtrain solapados; no es intervalo de confianza. La media por fold no pondera por eventos; las métricas OOF sí agregan eventos. El fold CV1 con un solo ATO puede cambiar de recall 0 a 1 por un evento.

### Coste computacional histórico y parámetros

| protocolo | modelo | preprocesamiento_s | sobremuestreo_s | entrenamiento_s | prediccion_s | parametros |
| --- | --- | --- | --- | --- | --- | --- |
| CV1 | arbol_baseline | 0.2715204 | 4.200032e-06 | 0.7009798 | 0.0112169 | {"ccp_alpha": 0.0, "class_weight": null, "criterion": "gini", "max_depth": null, "max_features": null, "max_leaf_nodes": null, "min_impurity_decrease": 0.0, "min_samples_leaf": 1, "min_samples_split": 2, "min_weight_fraction_leaf": 0.0, "monotonic_cst": null, "random_state": 42, "splitter": "best"} |
| CV1 | arbol_ponderado | 0.252802 | 4.899921e-06 | 0.290272 | 0.0084571 | {"ccp_alpha": 0.0, "class_weight": "balanced", "criterion": "gini", "max_depth": null, "max_features": null, "max_leaf_nodes": null, "min_impurity_decrease": 0.0, "min_samples_leaf": 1, "min_samples_split": 2, "min_weight_fraction_leaf": 0.0, "monotonic_cst": null, "random_state": 42, "splitter": "best"} |
| CV1 | gnb_baseline | 0.2699062 | 4.300033e-06 | 0.0955441 | 0.0356842 | {"priors": null, "var_smoothing": 1e-09} |
| CV1 | gnb_ponderado | 0.2699668 | 4.300033e-06 | 0.1494445 | 0.0281248 | {"priors": null, "var_smoothing": 1e-09} |
| CV1 | knn_baseline | 0.2826355 | 3.90003e-06 | 0.02464 | 5.910446 | {"algorithm": "brute", "leaf_size": 30, "metric": "euclidean", "metric_params": null, "n_jobs": 2, "n_neighbors": 5, "p": 2, "weights": "uniform"} |
| CV1 | knn_ros | 0.2724239 | 0.2599516 | 0.0306037 | 8.644942 | {"algorithm": "brute", "leaf_size": 30, "metric": "euclidean", "metric_params": null, "n_jobs": 2, "n_neighbors": 5, "p": 2, "weights": "uniform"} |
| CV2 | arbol_baseline | 0.2552494 | 3.700028e-06 | 0.8330152 | 0.0098801 | {"ccp_alpha": 0.0, "class_weight": null, "criterion": "gini", "max_depth": null, "max_features": null, "max_leaf_nodes": null, "min_impurity_decrease": 0.0, "min_samples_leaf": 1, "min_samples_split": 2, "min_weight_fraction_leaf": 0.0, "monotonic_cst": null, "random_state": 42, "splitter": "best"} |
| CV2 | arbol_ponderado | 0.2684547 | 4.200032e-06 | 0.3056588 | 0.010975 | {"ccp_alpha": 0.0, "class_weight": "balanced", "criterion": "gini", "max_depth": null, "max_features": null, "max_leaf_nodes": null, "min_impurity_decrease": 0.0, "min_samples_leaf": 1, "min_samples_split": 2, "min_weight_fraction_leaf": 0.0, "monotonic_cst": null, "random_state": 42, "splitter": "best"} |
| CV2 | gnb_baseline | 0.3673168 | 4.699919e-06 | 0.0992588 | 0.0293268 | {"priors": null, "var_smoothing": 1e-09} |
| CV2 | gnb_ponderado | 0.2491825 | 3.800029e-06 | 0.1447251 | 0.0283161 | {"priors": null, "var_smoothing": 1e-09} |
| CV2 | knn_baseline | 0.2989349 | 4.100031e-06 | 0.021717 | 6.490172 | {"algorithm": "brute", "leaf_size": 30, "metric": "euclidean", "metric_params": null, "n_jobs": 2, "n_neighbors": 5, "p": 2, "weights": "uniform"} |
| CV2 | knn_ros | 0.3388386 | 0.2946242 | 0.0413016 | 9.591115 | {"algorithm": "brute", "leaf_size": 30, "metric": "euclidean", "metric_params": null, "n_jobs": 2, "n_neighbors": 5, "p": 2, "weights": "uniform"} |

Son tiempos históricos de sus ejecuciones, no un benchmark nuevo controlado. Árbol ofrece reglas potencialmente inspeccionables pero sin poda puede memorizar; GaussianNB supone independencia y distribuciones gaussianas incompatibles con muchas dummies; KNN requiere almacenar referencias y calcular distancias, y ROS aumenta su tamaño/coste. No se reajustó ninguna variante.

## 5. Distribución de scores y rango de umbrales

Se enumeran todos los scores únicos observados de cada variante en la unión de CV1/CV2, más 0, 0,2, 0,4, 0,5, 1 y el siguiente float mayor que 1. La misma rejilla se aplica a ambas CV. Regla exacta: score ≥ t. Entre scores consecutivos la decisión es constante; para valores s_prev < s, t en (s_prev,s] conserva la decisión en s. El extremo >1 representa ninguna alerta, no una probabilidad admisible. t=0 genera alerta en todos los eventos.

No se aplica una rejilla decimal arbitraria que perdería las puntuaciones del árbol cercanas a 0 o 1. Los CSV conservan 17 dígitos y las lecturas usan round_trip. Las tablas Markdown redondean únicamente presentación; para reproducir los puntos exactos se usa CSV. Las figuras conectan escalones, no interpolan scores o rendimientos.

| protocolo | modelo | scores_distintos | score_min | score_max |
| --- | --- | --- | --- | --- |
| CV1 | arbol_baseline | 11 | 0 | 1 |
| CV1 | arbol_ponderado | 16 | 0 | 1 |
| CV1 | gnb_baseline | 2 | 0 | 1 |
| CV1 | gnb_ponderado | 2 | 0 | 1 |
| CV1 | knn_baseline | 4 | 0 | 0.6 |
| CV1 | knn_ros | 6 | 0 | 1 |
| CV2 | arbol_baseline | 11 | 0 | 1 |
| CV2 | arbol_ponderado | 19 | 0 | 1 |
| CV2 | gnb_baseline | 2 | 0 | 1 |
| CV2 | gnb_ponderado | 2 | 0 | 1 |
| CV2 | knn_baseline | 4 | 0 | 0.6 |
| CV2 | knn_ros | 6 | 0 | 1 |

### GaussianNB: observación e interpretación separadas

**Observado:** ambos GaussianNB producen exactamente scores 0 y 1, y sus vectores coinciden dentro de cada protocolo. Cualquier t en (0,1] produce 31 TP, 5 FN y 36.476 FP en CV1 / 36.447 FP en CV2, unas 36.500 alertas (casi 79% del conjunto). Su recall elevado proviene de marcar positiva gran parte de los eventos, con precision aproximadamente 0,085%. No hay umbral intermedio que arregle este compromiso en los scores almacenados. t=0 solo añade más falsas alarmas y los cinco ATO restantes; t>1 elimina toda detección.

**Interpretación limitada:** scores extremos son compatibles con saturación numérica y supuestos probabilísticos inadecuados; no se demuestra aquí su causa porque no se inspeccionan distribuciones internas ajustadas ni se reentrena. No se afirma que la ponderación haya sido omitida: el código histórico aplica sample_weight, pero el resultado OOF coincide.

### KNN: AP alta relativa y recall cero a 0,5

**Observado:** KNN baseline produce 0; 0,2; 0,4; 0,6. Con cinco vecinos y pesos uniformes corresponden a fracciones de vecinos positivos. Ningún ATO obtiene score ≥0,5 en estas OOF, aunque parte queda por encima de numerosos negativos con score 0. AP mide ordenamiento y puede superar a otros modelos sin producir TP al umbral 0,5. Los pocos scores 0,6 pertenecen a negativos. ROS redistribuye scores hacia valores altos, pero no crea necesariamente información de ranking: a t=0,2 sus conjuntos de alertas coinciden con baseline en estos datos (ver pruebas).

### Árbol baseline y ponderado

La ponderación modifica la partición y las proporciones ponderadas de hojas; score no se interpreta automáticamente como probabilidad calibrada. Las hojas compartidas por numerosos negativos generan bloques de scores y saltos grandes de FP. El árbol baseline mejora sus detecciones al bajar de 0,5 a 0,2, pero pierde TP entre CV1 y CV2 (8→5). El ponderado a 0,5 aumenta detección y mucho más FP. Algunos umbrales cercanos a 0,997 ofrecen compromisos distintos en CV2; no son prueba de un óptimo estable y se muestran íntegramente.

## 6. Barrido exhaustivo por variante (sin omitir resultados)

Todas las matrices de confusión están representadas por sus cuatro conteos en las tablas siguientes; las figuras individuales muestran 0,2 / 0,4 / 0,5. Los CSV incluyen también cada fold y media, DE, mínimo y máximo para cada punto. `distribucion_scores.csv` conserva todos los valores y sus conteos por clase. Ninguna variante se elimina por rendimiento desfavorable.

### M1a · Árbol baseline

| protocolo | modelo | umbral | TP | FP | TN | FN | precision | recall | f1 | average_precision | alertas | porcentaje_alertas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CV1 | arbol_baseline | 0 | 36 | 46269 | 0 | 0 | 0.0007774538 | 1 | 0.0015537 | 0.01944715 | 46305 | 100 |
| CV1 | arbol_baseline | 0.002024291 | 8 | 546 | 45723 | 28 | 0.01444043 | 0.2222222 | 0.02711864 | 0.01944715 | 554 | 1.196415 |
| CV1 | arbol_baseline | 0.002061856 | 8 | 546 | 45723 | 28 | 0.01444043 | 0.2222222 | 0.02711864 | 0.01944715 | 554 | 1.196415 |
| CV1 | arbol_baseline | 0.003992016 | 8 | 546 | 45723 | 28 | 0.01444043 | 0.2222222 | 0.02711864 | 0.01944715 | 554 | 1.196415 |
| CV1 | arbol_baseline | 0.00408998 | 8 | 437 | 45832 | 28 | 0.01797753 | 0.2222222 | 0.03326403 | 0.01944715 | 445 | 0.9610193 |
| CV1 | arbol_baseline | 0.004098361 | 8 | 316 | 45953 | 28 | 0.02469136 | 0.2222222 | 0.04444444 | 0.01944715 | 324 | 0.6997085 |
| CV1 | arbol_baseline | 0.004132231 | 8 | 194 | 46075 | 28 | 0.03960396 | 0.2222222 | 0.06722689 | 0.01944715 | 202 | 0.436238 |
| CV1 | arbol_baseline | 0.004149378 | 8 | 194 | 46075 | 28 | 0.03960396 | 0.2222222 | 0.06722689 | 0.01944715 | 202 | 0.436238 |
| CV1 | arbol_baseline | 0.1428571 | 8 | 66 | 46203 | 28 | 0.1081081 | 0.2222222 | 0.1454545 | 0.01944715 | 74 | 0.15981 |
| CV1 | arbol_baseline | 0.1666667 | 8 | 65 | 46204 | 28 | 0.109589 | 0.2222222 | 0.146789 | 0.01944715 | 73 | 0.1576504 |
| CV1 | arbol_baseline | 0.2 | 8 | 63 | 46206 | 28 | 0.1126761 | 0.2222222 | 0.1495327 | 0.01944715 | 71 | 0.1533312 |
| CV1 | arbol_baseline | 0.3333333 | 6 | 58 | 46211 | 30 | 0.09375 | 0.1666667 | 0.12 | 0.01944715 | 64 | 0.138214 |
| CV1 | arbol_baseline | 0.4 | 6 | 55 | 46214 | 30 | 0.09836066 | 0.1666667 | 0.1237113 | 0.01944715 | 61 | 0.1317352 |
| CV1 | arbol_baseline | 0.5 | 6 | 55 | 46214 | 30 | 0.09836066 | 0.1666667 | 0.1237113 | 0.01944715 | 61 | 0.1317352 |
| CV1 | arbol_baseline | 0.6666667 | 6 | 55 | 46214 | 30 | 0.09836066 | 0.1666667 | 0.1237113 | 0.01944715 | 61 | 0.1317352 |
| CV1 | arbol_baseline | 1 | 3 | 54 | 46215 | 33 | 0.05263158 | 0.08333333 | 0.06451613 | 0.01944715 | 57 | 0.1230969 |
| CV1 | arbol_baseline | >1 (sin alertas) | 0 | 0 | 46269 | 36 | 0 | 0 | 0 | 0.01944715 | 0 | 0 |
| CV2 | arbol_baseline | 0 | 36 | 46269 | 0 | 0 | 0.0007774538 | 1 | 0.0015537 | 0.00886213 | 46305 | 100 |
| CV2 | arbol_baseline | 0.002024291 | 7 | 679 | 45590 | 29 | 0.01020408 | 0.1944444 | 0.01939058 | 0.00886213 | 686 | 1.481481 |
| CV2 | arbol_baseline | 0.002061856 | 6 | 564 | 45705 | 30 | 0.01052632 | 0.1666667 | 0.01980198 | 0.00886213 | 570 | 1.230969 |
| CV2 | arbol_baseline | 0.003992016 | 5 | 440 | 45829 | 31 | 0.01123596 | 0.1388889 | 0.02079002 | 0.00886213 | 445 | 0.9610193 |
| CV2 | arbol_baseline | 0.00408998 | 5 | 440 | 45829 | 31 | 0.01123596 | 0.1388889 | 0.02079002 | 0.00886213 | 445 | 0.9610193 |
| CV2 | arbol_baseline | 0.004098361 | 5 | 319 | 45950 | 31 | 0.0154321 | 0.1388889 | 0.02777778 | 0.00886213 | 324 | 0.6997085 |
| CV2 | arbol_baseline | 0.004132231 | 5 | 197 | 46072 | 31 | 0.02475248 | 0.1388889 | 0.04201681 | 0.00886213 | 202 | 0.436238 |
| CV2 | arbol_baseline | 0.004149378 | 5 | 71 | 46198 | 31 | 0.06578947 | 0.1388889 | 0.08928571 | 0.00886213 | 76 | 0.1641291 |
| CV2 | arbol_baseline | 0.1428571 | 5 | 71 | 46198 | 31 | 0.06578947 | 0.1388889 | 0.08928571 | 0.00886213 | 76 | 0.1641291 |
| CV2 | arbol_baseline | 0.1666667 | 5 | 69 | 46200 | 31 | 0.06756757 | 0.1388889 | 0.09090909 | 0.00886213 | 74 | 0.15981 |
| CV2 | arbol_baseline | 0.2 | 5 | 69 | 46200 | 31 | 0.06756757 | 0.1388889 | 0.09090909 | 0.00886213 | 74 | 0.15981 |
| CV2 | arbol_baseline | 0.3333333 | 3 | 64 | 46205 | 33 | 0.04477612 | 0.08333333 | 0.05825243 | 0.00886213 | 67 | 0.1446928 |
| CV2 | arbol_baseline | 0.4 | 3 | 61 | 46208 | 33 | 0.046875 | 0.08333333 | 0.06 | 0.00886213 | 64 | 0.138214 |
| CV2 | arbol_baseline | 0.5 | 3 | 61 | 46208 | 33 | 0.046875 | 0.08333333 | 0.06 | 0.00886213 | 64 | 0.138214 |
| CV2 | arbol_baseline | 0.6666667 | 3 | 61 | 46208 | 33 | 0.046875 | 0.08333333 | 0.06 | 0.00886213 | 64 | 0.138214 |
| CV2 | arbol_baseline | 1 | 0 | 60 | 46209 | 36 | 0 | 0 | 0 | 0.00886213 | 60 | 0.1295756 |
| CV2 | arbol_baseline | >1 (sin alertas) | 0 | 0 | 46269 | 36 | 0 | 0 | 0 | 0.00886213 | 0 | 0 |

### M1b · Árbol ponderado

| protocolo | modelo | umbral | TP | FP | TN | FN | precision | recall | f1 | average_precision | alertas | porcentaje_alertas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CV1 | arbol_ponderado | 0 | 36 | 46269 | 0 | 0 | 0.0007774538 | 1 | 0.0015537 | 0.01601708 | 46305 | 100 |
| CV1 | arbol_ponderado | 0.2 | 8 | 556 | 45713 | 28 | 0.0141844 | 0.2222222 | 0.02666667 | 0.01601708 | 564 | 1.218011 |
| CV1 | arbol_ponderado | 0.4 | 8 | 556 | 45713 | 28 | 0.0141844 | 0.2222222 | 0.02666667 | 0.01601708 | 564 | 1.218011 |
| CV1 | arbol_ponderado | 0.5 | 8 | 556 | 45713 | 28 | 0.0141844 | 0.2222222 | 0.02666667 | 0.01601708 | 564 | 1.218011 |
| CV1 | arbol_ponderado | 0.7166723 | 8 | 556 | 45713 | 28 | 0.0141844 | 0.2222222 | 0.02666667 | 0.01601708 | 564 | 1.218011 |
| CV1 | arbol_ponderado | 0.7183863 | 8 | 556 | 45713 | 28 | 0.0141844 | 0.2222222 | 0.02666667 | 0.01601708 | 564 | 1.218011 |
| CV1 | arbol_ponderado | 0.8138917 | 8 | 556 | 45713 | 28 | 0.0141844 | 0.2222222 | 0.02666667 | 0.01601708 | 564 | 1.218011 |
| CV1 | arbol_ponderado | 0.8420429 | 8 | 428 | 45841 | 28 | 0.01834862 | 0.2222222 | 0.03389831 | 0.01601708 | 436 | 0.941583 |
| CV1 | arbol_ponderado | 0.8431353 | 8 | 306 | 45963 | 28 | 0.02547771 | 0.2222222 | 0.04571429 | 0.01601708 | 314 | 0.6781125 |
| CV1 | arbol_ponderado | 0.8432403 | 8 | 306 | 45963 | 28 | 0.02547771 | 0.2222222 | 0.04571429 | 0.01601708 | 314 | 0.6781125 |
| CV1 | arbol_ponderado | 0.8446252 | 8 | 306 | 45963 | 28 | 0.02547771 | 0.2222222 | 0.04571429 | 0.01601708 | 314 | 0.6781125 |
| CV1 | arbol_ponderado | 0.8468626 | 8 | 185 | 46084 | 28 | 0.04145078 | 0.2222222 | 0.069869 | 0.01601708 | 193 | 0.4168016 |
| CV1 | arbol_ponderado | 0.8478641 | 8 | 185 | 46084 | 28 | 0.04145078 | 0.2222222 | 0.069869 | 0.01601708 | 193 | 0.4168016 |
| CV1 | arbol_ponderado | 0.9954308 | 8 | 76 | 46193 | 28 | 0.0952381 | 0.2222222 | 0.1333333 | 0.01601708 | 84 | 0.1814059 |
| CV1 | arbol_ponderado | 0.9954365 | 8 | 76 | 46193 | 28 | 0.0952381 | 0.2222222 | 0.1333333 | 0.01601708 | 84 | 0.1814059 |
| CV1 | arbol_ponderado | 0.9958533 | 8 | 76 | 46193 | 28 | 0.0952381 | 0.2222222 | 0.1333333 | 0.01601708 | 84 | 0.1814059 |
| CV1 | arbol_ponderado | 0.996155 | 8 | 75 | 46194 | 28 | 0.09638554 | 0.2222222 | 0.1344538 | 0.01601708 | 83 | 0.1792463 |
| CV1 | arbol_ponderado | 0.9967707 | 8 | 73 | 46196 | 28 | 0.09876543 | 0.2222222 | 0.1367521 | 0.01601708 | 81 | 0.1749271 |
| CV1 | arbol_ponderado | 0.9969216 | 8 | 73 | 46196 | 28 | 0.09876543 | 0.2222222 | 0.1367521 | 0.01601708 | 81 | 0.1749271 |
| CV1 | arbol_ponderado | 0.9969531 | 7 | 72 | 46197 | 29 | 0.08860759 | 0.1944444 | 0.1217391 | 0.01601708 | 79 | 0.1706079 |
| CV1 | arbol_ponderado | 0.9969872 | 7 | 72 | 46197 | 29 | 0.08860759 | 0.1944444 | 0.1217391 | 0.01601708 | 79 | 0.1706079 |
| CV1 | arbol_ponderado | 0.9970077 | 6 | 68 | 46201 | 30 | 0.08108108 | 0.1666667 | 0.1090909 | 0.01601708 | 74 | 0.15981 |
| CV1 | arbol_ponderado | 0.9980981 | 6 | 68 | 46201 | 30 | 0.08108108 | 0.1666667 | 0.1090909 | 0.01601708 | 74 | 0.15981 |
| CV1 | arbol_ponderado | 0.9983827 | 6 | 65 | 46204 | 30 | 0.08450704 | 0.1666667 | 0.1121495 | 0.01601708 | 71 | 0.1533312 |
| CV1 | arbol_ponderado | 0.9983988 | 6 | 65 | 46204 | 30 | 0.08450704 | 0.1666667 | 0.1121495 | 0.01601708 | 71 | 0.1533312 |
| CV1 | arbol_ponderado | 0.9984723 | 6 | 65 | 46204 | 30 | 0.08450704 | 0.1666667 | 0.1121495 | 0.01601708 | 71 | 0.1533312 |
| CV1 | arbol_ponderado | 0.9985637 | 6 | 65 | 46204 | 30 | 0.08450704 | 0.1666667 | 0.1121495 | 0.01601708 | 71 | 0.1533312 |
| CV1 | arbol_ponderado | 0.9986139 | 6 | 63 | 46206 | 30 | 0.08695652 | 0.1666667 | 0.1142857 | 0.01601708 | 69 | 0.149012 |
| CV1 | arbol_ponderado | 0.9995952 | 6 | 61 | 46208 | 30 | 0.08955224 | 0.1666667 | 0.1165049 | 0.01601708 | 67 | 0.1446928 |
| CV1 | arbol_ponderado | 0.9996142 | 6 | 61 | 46208 | 30 | 0.08955224 | 0.1666667 | 0.1165049 | 0.01601708 | 67 | 0.1446928 |
| CV1 | arbol_ponderado | 0.9996176 | 5 | 61 | 46208 | 31 | 0.07575758 | 0.1388889 | 0.09803922 | 0.01601708 | 66 | 0.1425332 |
| CV1 | arbol_ponderado | 0.9996224 | 5 | 61 | 46208 | 31 | 0.07575758 | 0.1388889 | 0.09803922 | 0.01601708 | 66 | 0.1425332 |
| CV1 | arbol_ponderado | 0.999625 | 4 | 61 | 46208 | 32 | 0.06153846 | 0.1111111 | 0.07920792 | 0.01601708 | 65 | 0.1403736 |
| CV1 | arbol_ponderado | 0.9996531 | 4 | 61 | 46208 | 32 | 0.06153846 | 0.1111111 | 0.07920792 | 0.01601708 | 65 | 0.1403736 |
| CV1 | arbol_ponderado | 0.9997328 | 3 | 61 | 46208 | 33 | 0.046875 | 0.08333333 | 0.06 | 0.01601708 | 64 | 0.138214 |
| CV1 | arbol_ponderado | 1 | 3 | 61 | 46208 | 33 | 0.046875 | 0.08333333 | 0.06 | 0.01601708 | 64 | 0.138214 |
| CV1 | arbol_ponderado | >1 (sin alertas) | 0 | 0 | 46269 | 36 | 0 | 0 | 0 | 0.01601708 | 0 | 0 |
| CV2 | arbol_ponderado | 0 | 36 | 46269 | 0 | 0 | 0.0007774538 | 1 | 0.0015537 | 0.01581734 | 46305 | 100 |
| CV2 | arbol_ponderado | 0.2 | 9 | 675 | 45594 | 27 | 0.01315789 | 0.25 | 0.025 | 0.01581734 | 684 | 1.477162 |
| CV2 | arbol_ponderado | 0.4 | 9 | 675 | 45594 | 27 | 0.01315789 | 0.25 | 0.025 | 0.01581734 | 684 | 1.477162 |
| CV2 | arbol_ponderado | 0.5 | 9 | 675 | 45594 | 27 | 0.01315789 | 0.25 | 0.025 | 0.01581734 | 684 | 1.477162 |
| CV2 | arbol_ponderado | 0.7166723 | 9 | 675 | 45594 | 27 | 0.01315789 | 0.25 | 0.025 | 0.01581734 | 684 | 1.477162 |
| CV2 | arbol_ponderado | 0.7183863 | 8 | 560 | 45709 | 28 | 0.01408451 | 0.2222222 | 0.02649007 | 0.01581734 | 568 | 1.226649 |
| CV2 | arbol_ponderado | 0.8138917 | 7 | 436 | 45833 | 29 | 0.01580135 | 0.1944444 | 0.02922756 | 0.01581734 | 443 | 0.9567001 |
| CV2 | arbol_ponderado | 0.8420429 | 7 | 436 | 45833 | 29 | 0.01580135 | 0.1944444 | 0.02922756 | 0.01581734 | 443 | 0.9567001 |
| CV2 | arbol_ponderado | 0.8431353 | 7 | 436 | 45833 | 29 | 0.01580135 | 0.1944444 | 0.02922756 | 0.01581734 | 443 | 0.9567001 |
| CV2 | arbol_ponderado | 0.8432403 | 7 | 315 | 45954 | 29 | 0.02173913 | 0.1944444 | 0.03910615 | 0.01581734 | 322 | 0.6953893 |
| CV2 | arbol_ponderado | 0.8446252 | 7 | 193 | 46076 | 29 | 0.035 | 0.1944444 | 0.05932203 | 0.01581734 | 200 | 0.4319188 |
| CV2 | arbol_ponderado | 0.8468626 | 7 | 193 | 46076 | 29 | 0.035 | 0.1944444 | 0.05932203 | 0.01581734 | 200 | 0.4319188 |
| CV2 | arbol_ponderado | 0.8478641 | 7 | 67 | 46202 | 29 | 0.09459459 | 0.1944444 | 0.1272727 | 0.01581734 | 74 | 0.15981 |
| CV2 | arbol_ponderado | 0.9954308 | 7 | 67 | 46202 | 29 | 0.09459459 | 0.1944444 | 0.1272727 | 0.01581734 | 74 | 0.15981 |
| CV2 | arbol_ponderado | 0.9954365 | 7 | 64 | 46205 | 29 | 0.09859155 | 0.1944444 | 0.1308411 | 0.01581734 | 71 | 0.1533312 |
| CV2 | arbol_ponderado | 0.9958533 | 7 | 59 | 46210 | 29 | 0.1060606 | 0.1944444 | 0.1372549 | 0.01581734 | 66 | 0.1425332 |
| CV2 | arbol_ponderado | 0.996155 | 7 | 59 | 46210 | 29 | 0.1060606 | 0.1944444 | 0.1372549 | 0.01581734 | 66 | 0.1425332 |
| CV2 | arbol_ponderado | 0.9967707 | 7 | 59 | 46210 | 29 | 0.1060606 | 0.1944444 | 0.1372549 | 0.01581734 | 66 | 0.1425332 |
| CV2 | arbol_ponderado | 0.9969216 | 7 | 56 | 46213 | 29 | 0.1111111 | 0.1944444 | 0.1414141 | 0.01581734 | 63 | 0.1360544 |
| CV2 | arbol_ponderado | 0.9969531 | 7 | 56 | 46213 | 29 | 0.1111111 | 0.1944444 | 0.1414141 | 0.01581734 | 63 | 0.1360544 |
| CV2 | arbol_ponderado | 0.9969872 | 6 | 55 | 46214 | 30 | 0.09836066 | 0.1666667 | 0.1237113 | 0.01581734 | 61 | 0.1317352 |
| CV2 | arbol_ponderado | 0.9970077 | 6 | 55 | 46214 | 30 | 0.09836066 | 0.1666667 | 0.1237113 | 0.01581734 | 61 | 0.1317352 |
| CV2 | arbol_ponderado | 0.9980981 | 5 | 54 | 46215 | 31 | 0.08474576 | 0.1388889 | 0.1052632 | 0.01581734 | 59 | 0.127416 |
| CV2 | arbol_ponderado | 0.9983827 | 5 | 54 | 46215 | 31 | 0.08474576 | 0.1388889 | 0.1052632 | 0.01581734 | 59 | 0.127416 |
| CV2 | arbol_ponderado | 0.9983988 | 5 | 53 | 46216 | 31 | 0.0862069 | 0.1388889 | 0.106383 | 0.01581734 | 58 | 0.1252565 |
| CV2 | arbol_ponderado | 0.9984723 | 5 | 52 | 46217 | 31 | 0.0877193 | 0.1388889 | 0.1075269 | 0.01581734 | 57 | 0.1230969 |
| CV2 | arbol_ponderado | 0.9985637 | 5 | 48 | 46221 | 31 | 0.09433962 | 0.1388889 | 0.1123596 | 0.01581734 | 53 | 0.1144585 |
| CV2 | arbol_ponderado | 0.9986139 | 5 | 48 | 46221 | 31 | 0.09433962 | 0.1388889 | 0.1123596 | 0.01581734 | 53 | 0.1144585 |
| CV2 | arbol_ponderado | 0.9995952 | 5 | 48 | 46221 | 31 | 0.09433962 | 0.1388889 | 0.1123596 | 0.01581734 | 53 | 0.1144585 |
| CV2 | arbol_ponderado | 0.9996142 | 4 | 48 | 46221 | 32 | 0.07692308 | 0.1111111 | 0.09090909 | 0.01581734 | 52 | 0.1122989 |
| CV2 | arbol_ponderado | 0.9996176 | 4 | 48 | 46221 | 32 | 0.07692308 | 0.1111111 | 0.09090909 | 0.01581734 | 52 | 0.1122989 |
| CV2 | arbol_ponderado | 0.9996224 | 3 | 48 | 46221 | 33 | 0.05882353 | 0.08333333 | 0.06896552 | 0.01581734 | 51 | 0.1101393 |
| CV2 | arbol_ponderado | 0.999625 | 3 | 48 | 46221 | 33 | 0.05882353 | 0.08333333 | 0.06896552 | 0.01581734 | 51 | 0.1101393 |
| CV2 | arbol_ponderado | 0.9996531 | 2 | 48 | 46221 | 34 | 0.04 | 0.05555556 | 0.04651163 | 0.01581734 | 50 | 0.1079797 |
| CV2 | arbol_ponderado | 0.9997328 | 2 | 48 | 46221 | 34 | 0.04 | 0.05555556 | 0.04651163 | 0.01581734 | 50 | 0.1079797 |
| CV2 | arbol_ponderado | 1 | 2 | 47 | 46222 | 34 | 0.04081633 | 0.05555556 | 0.04705882 | 0.01581734 | 49 | 0.1058201 |
| CV2 | arbol_ponderado | >1 (sin alertas) | 0 | 0 | 46269 | 36 | 0 | 0 | 0 | 0.01581734 | 0 | 0 |

### M2a · GaussianNB baseline

| protocolo | modelo | umbral | TP | FP | TN | FN | precision | recall | f1 | average_precision | alertas | porcentaje_alertas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CV1 | gnb_baseline | 0 | 36 | 46269 | 0 | 0 | 0.0007774538 | 1 | 0.0015537 | 0.0008391941 | 46305 | 100 |
| CV1 | gnb_baseline | 0.2 | 31 | 36476 | 9793 | 5 | 0.0008491522 | 0.8611111 | 0.001696631 | 0.0008391941 | 36507 | 78.8403 |
| CV1 | gnb_baseline | 0.4 | 31 | 36476 | 9793 | 5 | 0.0008491522 | 0.8611111 | 0.001696631 | 0.0008391941 | 36507 | 78.8403 |
| CV1 | gnb_baseline | 0.5 | 31 | 36476 | 9793 | 5 | 0.0008491522 | 0.8611111 | 0.001696631 | 0.0008391941 | 36507 | 78.8403 |
| CV1 | gnb_baseline | 1 | 31 | 36476 | 9793 | 5 | 0.0008491522 | 0.8611111 | 0.001696631 | 0.0008391941 | 36507 | 78.8403 |
| CV1 | gnb_baseline | >1 (sin alertas) | 0 | 0 | 46269 | 36 | 0 | 0 | 0 | 0.0008391941 | 0 | 0 |
| CV2 | gnb_baseline | 0 | 36 | 46269 | 0 | 0 | 0.0007774538 | 1 | 0.0015537 | 0.0008397754 | 46305 | 100 |
| CV2 | gnb_baseline | 0.2 | 31 | 36447 | 9822 | 5 | 0.0008498273 | 0.8611111 | 0.001697979 | 0.0008397754 | 36478 | 78.77767 |
| CV2 | gnb_baseline | 0.4 | 31 | 36447 | 9822 | 5 | 0.0008498273 | 0.8611111 | 0.001697979 | 0.0008397754 | 36478 | 78.77767 |
| CV2 | gnb_baseline | 0.5 | 31 | 36447 | 9822 | 5 | 0.0008498273 | 0.8611111 | 0.001697979 | 0.0008397754 | 36478 | 78.77767 |
| CV2 | gnb_baseline | 1 | 31 | 36447 | 9822 | 5 | 0.0008498273 | 0.8611111 | 0.001697979 | 0.0008397754 | 36478 | 78.77767 |
| CV2 | gnb_baseline | >1 (sin alertas) | 0 | 0 | 46269 | 36 | 0 | 0 | 0 | 0.0008397754 | 0 | 0 |

### M2b · GaussianNB ponderado

| protocolo | modelo | umbral | TP | FP | TN | FN | precision | recall | f1 | average_precision | alertas | porcentaje_alertas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CV1 | gnb_ponderado | 0 | 36 | 46269 | 0 | 0 | 0.0007774538 | 1 | 0.0015537 | 0.0008391941 | 46305 | 100 |
| CV1 | gnb_ponderado | 0.2 | 31 | 36476 | 9793 | 5 | 0.0008491522 | 0.8611111 | 0.001696631 | 0.0008391941 | 36507 | 78.8403 |
| CV1 | gnb_ponderado | 0.4 | 31 | 36476 | 9793 | 5 | 0.0008491522 | 0.8611111 | 0.001696631 | 0.0008391941 | 36507 | 78.8403 |
| CV1 | gnb_ponderado | 0.5 | 31 | 36476 | 9793 | 5 | 0.0008491522 | 0.8611111 | 0.001696631 | 0.0008391941 | 36507 | 78.8403 |
| CV1 | gnb_ponderado | 1 | 31 | 36476 | 9793 | 5 | 0.0008491522 | 0.8611111 | 0.001696631 | 0.0008391941 | 36507 | 78.8403 |
| CV1 | gnb_ponderado | >1 (sin alertas) | 0 | 0 | 46269 | 36 | 0 | 0 | 0 | 0.0008391941 | 0 | 0 |
| CV2 | gnb_ponderado | 0 | 36 | 46269 | 0 | 0 | 0.0007774538 | 1 | 0.0015537 | 0.0008397754 | 46305 | 100 |
| CV2 | gnb_ponderado | 0.2 | 31 | 36447 | 9822 | 5 | 0.0008498273 | 0.8611111 | 0.001697979 | 0.0008397754 | 36478 | 78.77767 |
| CV2 | gnb_ponderado | 0.4 | 31 | 36447 | 9822 | 5 | 0.0008498273 | 0.8611111 | 0.001697979 | 0.0008397754 | 36478 | 78.77767 |
| CV2 | gnb_ponderado | 0.5 | 31 | 36447 | 9822 | 5 | 0.0008498273 | 0.8611111 | 0.001697979 | 0.0008397754 | 36478 | 78.77767 |
| CV2 | gnb_ponderado | 1 | 31 | 36447 | 9822 | 5 | 0.0008498273 | 0.8611111 | 0.001697979 | 0.0008397754 | 36478 | 78.77767 |
| CV2 | gnb_ponderado | >1 (sin alertas) | 0 | 0 | 46269 | 36 | 0 | 0 | 0 | 0.0008397754 | 0 | 0 |

### M3a · KNN baseline

| protocolo | modelo | umbral | TP | FP | TN | FN | precision | recall | f1 | average_precision | alertas | porcentaje_alertas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CV1 | knn_baseline | 0 | 36 | 46269 | 0 | 0 | 0.0007774538 | 1 | 0.0015537 | 0.04947889 | 46305 | 100 |
| CV1 | knn_baseline | 0.2 | 11 | 134 | 46135 | 25 | 0.07586207 | 0.3055556 | 0.121547 | 0.04947889 | 145 | 0.3131411 |
| CV1 | knn_baseline | 0.4 | 4 | 9 | 46260 | 32 | 0.3076923 | 0.1111111 | 0.1632653 | 0.04947889 | 13 | 0.02807472 |
| CV1 | knn_baseline | 0.5 | 0 | 5 | 46264 | 36 | 0 | 0 | 0 | 0.04947889 | 5 | 0.01079797 |
| CV1 | knn_baseline | 0.6 | 0 | 5 | 46264 | 36 | 0 | 0 | 0 | 0.04947889 | 5 | 0.01079797 |
| CV1 | knn_baseline | 1 | 0 | 0 | 46269 | 36 | 0 | 0 | 0 | 0.04947889 | 0 | 0 |
| CV1 | knn_baseline | >1 (sin alertas) | 0 | 0 | 46269 | 36 | 0 | 0 | 0 | 0.04947889 | 0 | 0 |
| CV2 | knn_baseline | 0 | 36 | 46269 | 0 | 0 | 0.0007774538 | 1 | 0.0015537 | 0.04316277 | 46305 | 100 |
| CV2 | knn_baseline | 0.2 | 8 | 153 | 46116 | 28 | 0.04968944 | 0.2222222 | 0.08121827 | 0.04316277 | 161 | 0.3476946 |
| CV2 | knn_baseline | 0.4 | 4 | 8 | 46261 | 32 | 0.3333333 | 0.1111111 | 0.1666667 | 0.04316277 | 12 | 0.02591513 |
| CV2 | knn_baseline | 0.5 | 0 | 1 | 46268 | 36 | 0 | 0 | 0 | 0.04316277 | 1 | 0.002159594 |
| CV2 | knn_baseline | 0.6 | 0 | 1 | 46268 | 36 | 0 | 0 | 0 | 0.04316277 | 1 | 0.002159594 |
| CV2 | knn_baseline | 1 | 0 | 0 | 46269 | 36 | 0 | 0 | 0 | 0.04316277 | 0 | 0 |
| CV2 | knn_baseline | >1 (sin alertas) | 0 | 0 | 46269 | 36 | 0 | 0 | 0 | 0.04316277 | 0 | 0 |

### M3b · KNN + ROS

| protocolo | modelo | umbral | TP | FP | TN | FN | precision | recall | f1 | average_precision | alertas | porcentaje_alertas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CV1 | knn_ros | 0 | 36 | 46269 | 0 | 0 | 0.0007774538 | 1 | 0.0015537 | 0.01984369 | 46305 | 100 |
| CV1 | knn_ros | 0.2 | 11 | 134 | 46135 | 25 | 0.07586207 | 0.3055556 | 0.121547 | 0.01984369 | 145 | 0.3131411 |
| CV1 | knn_ros | 0.4 | 7 | 113 | 46156 | 29 | 0.05833333 | 0.1944444 | 0.08974359 | 0.01984369 | 120 | 0.2591513 |
| CV1 | knn_ros | 0.5 | 6 | 93 | 46176 | 30 | 0.06060606 | 0.1666667 | 0.08888889 | 0.01984369 | 99 | 0.2137998 |
| CV1 | knn_ros | 0.6 | 6 | 93 | 46176 | 30 | 0.06060606 | 0.1666667 | 0.08888889 | 0.01984369 | 99 | 0.2137998 |
| CV1 | knn_ros | 0.8 | 6 | 83 | 46186 | 30 | 0.06741573 | 0.1666667 | 0.096 | 0.01984369 | 89 | 0.1922039 |
| CV1 | knn_ros | 1 | 2 | 61 | 46208 | 34 | 0.03174603 | 0.05555556 | 0.04040404 | 0.01984369 | 63 | 0.1360544 |
| CV1 | knn_ros | >1 (sin alertas) | 0 | 0 | 46269 | 36 | 0 | 0 | 0 | 0.01984369 | 0 | 0 |
| CV2 | knn_ros | 0 | 36 | 46269 | 0 | 0 | 0.0007774538 | 1 | 0.0015537 | 0.01246152 | 46305 | 100 |
| CV2 | knn_ros | 0.2 | 8 | 153 | 46116 | 28 | 0.04968944 | 0.2222222 | 0.08121827 | 0.01246152 | 161 | 0.3476946 |
| CV2 | knn_ros | 0.4 | 5 | 118 | 46151 | 31 | 0.04065041 | 0.1388889 | 0.06289308 | 0.01246152 | 123 | 0.2656301 |
| CV2 | knn_ros | 0.5 | 5 | 99 | 46170 | 31 | 0.04807692 | 0.1388889 | 0.07142857 | 0.01246152 | 104 | 0.2245978 |
| CV2 | knn_ros | 0.6 | 5 | 99 | 46170 | 31 | 0.04807692 | 0.1388889 | 0.07142857 | 0.01246152 | 104 | 0.2245978 |
| CV2 | knn_ros | 0.8 | 5 | 85 | 46184 | 31 | 0.05555556 | 0.1388889 | 0.07936508 | 0.01246152 | 90 | 0.1943635 |
| CV2 | knn_ros | 1 | 0 | 42 | 46227 | 36 | 0 | 0 | 0 | 0.01246152 | 42 | 0.09070295 |
| CV2 | knn_ros | >1 (sin alertas) | 0 | 0 | 46269 | 36 | 0 | 0 | 0 | 0.01246152 | 0 | 0 |

## 7. Errores y estabilidad por evento/usuario

Se exportan FP y FN identificados por evento y clave para referencias 0,2 / 0,4 / 0,5 en `errores_eventos_referencias.csv`. Los errores no se convierten en explicación causal ni justifican añadir predictores mirando el resultado. `errores_usuarios_referencias.csv` informa usuarios positivos detectados y usuarios con al menos un FP. Un usuario puede tener varios eventos y ambos tipos de error; los conteos de eventos no son observaciones independientes.

| protocolo | modelo | umbral | usuarios_ato_detectados | usuarios_con_fp |
| --- | --- | --- | --- | --- |
| CV1 | arbol_baseline | 0.2 | 8 | 35 |
| CV1 | arbol_baseline | 0.4 | 6 | 28 |
| CV1 | arbol_baseline | 0.5 | 6 | 28 |
| CV1 | arbol_ponderado | 0.2 | 8 | 510 |
| CV1 | arbol_ponderado | 0.4 | 8 | 510 |
| CV1 | arbol_ponderado | 0.5 | 8 | 510 |
| CV1 | gnb_baseline | 0.2 | 31 | 1339 |
| CV1 | gnb_baseline | 0.4 | 31 | 1339 |
| CV1 | gnb_baseline | 0.5 | 31 | 1339 |
| CV1 | gnb_ponderado | 0.2 | 31 | 1339 |
| CV1 | gnb_ponderado | 0.4 | 31 | 1339 |
| CV1 | gnb_ponderado | 0.5 | 31 | 1339 |
| CV1 | knn_baseline | 0.2 | 11 | 63 |
| CV1 | knn_baseline | 0.4 | 4 | 9 |
| CV1 | knn_baseline | 0.5 | 0 | 5 |
| CV1 | knn_ros | 0.2 | 11 | 63 |
| CV1 | knn_ros | 0.4 | 7 | 51 |
| CV1 | knn_ros | 0.5 | 6 | 41 |
| CV2 | arbol_baseline | 0.2 | 5 | 35 |
| CV2 | arbol_baseline | 0.4 | 3 | 29 |
| CV2 | arbol_baseline | 0.5 | 3 | 29 |
| CV2 | arbol_ponderado | 0.2 | 9 | 641 |
| CV2 | arbol_ponderado | 0.4 | 9 | 641 |
| CV2 | arbol_ponderado | 0.5 | 9 | 641 |
| CV2 | gnb_baseline | 0.2 | 30 | 1339 |
| CV2 | gnb_baseline | 0.4 | 30 | 1339 |
| CV2 | gnb_baseline | 0.5 | 30 | 1339 |
| CV2 | gnb_ponderado | 0.2 | 30 | 1339 |
| CV2 | gnb_ponderado | 0.4 | 30 | 1339 |
| CV2 | gnb_ponderado | 0.5 | 30 | 1339 |
| CV2 | knn_baseline | 0.2 | 8 | 61 |
| CV2 | knn_baseline | 0.4 | 4 | 8 |
| CV2 | knn_baseline | 0.5 | 0 | 1 |
| CV2 | knn_ros | 0.2 | 8 | 61 |
| CV2 | knn_ros | 0.4 | 5 | 44 |
| CV2 | knn_ros | 0.5 | 5 | 35 |

Concordancia de detecciones y omisiones entre protocolos:

| modelo | umbral | ato_detectados_ambos | ato_solo_cv1 | ato_solo_cv2 | ato_omitidos_ambos | decisiones_distintas |
| --- | --- | --- | --- | --- | --- | --- |
| arbol_baseline | 0.2 | 5 | 3 | 0 | 28 | 55 |
| arbol_baseline | 0.4 | 3 | 3 | 0 | 30 | 51 |
| arbol_baseline | 0.5 | 3 | 3 | 0 | 30 | 51 |
| arbol_ponderado | 0.2 | 6 | 2 | 3 | 25 | 226 |
| arbol_ponderado | 0.4 | 6 | 2 | 3 | 25 | 226 |
| arbol_ponderado | 0.5 | 6 | 2 | 3 | 25 | 226 |
| gnb_baseline | 0.2 | 29 | 2 | 2 | 3 | 135 |
| gnb_baseline | 0.4 | 29 | 2 | 2 | 3 | 135 |
| gnb_baseline | 0.5 | 29 | 2 | 2 | 3 | 135 |
| gnb_ponderado | 0.2 | 29 | 2 | 2 | 3 | 135 |
| gnb_ponderado | 0.4 | 29 | 2 | 2 | 3 | 135 |
| gnb_ponderado | 0.5 | 29 | 2 | 2 | 3 | 135 |
| knn_baseline | 0.2 | 7 | 4 | 1 | 24 | 82 |
| knn_baseline | 0.4 | 3 | 1 | 1 | 31 | 9 |
| knn_baseline | 0.5 | 0 | 0 | 0 | 36 | 4 |
| knn_ros | 0.2 | 7 | 4 | 1 | 24 | 82 |
| knn_ros | 0.4 | 3 | 4 | 2 | 27 | 69 |
| knn_ros | 0.5 | 3 | 3 | 2 | 28 | 57 |

KNN baseline a 0,4 detecta cuatro usuarios positivos en cada CV, pero solo tres eventos ATO coinciden; uno cambia en cada protocolo. No son dos confirmaciones independientes. Su recall por fold sigue siendo inestable y dos folds de cada CV no detectan ningún ATO:

| protocolo | fold | TP | FP | FN | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CV1 | 1 | 2 | 0 | 8 | 1 | 0.2 | 0.3333333 |
| CV1 | 2 | 1 | 4 | 7 | 0.2 | 0.125 | 0.1538462 |
| CV1 | 3 | 0 | 0 | 1 | 0 | 0 | 0 |
| CV1 | 4 | 1 | 1 | 7 | 0.5 | 0.125 | 0.2 |
| CV1 | 5 | 0 | 4 | 9 | 0 | 0 | 0 |
| CV2 | 1 | 1 | 1 | 5 | 0.5 | 0.1666667 | 0.25 |
| CV2 | 2 | 0 | 1 | 7 | 0 | 0 | 0 |
| CV2 | 3 | 0 | 1 | 7 | 0 | 0 | 0 |
| CV2 | 4 | 2 | 4 | 6 | 0.3333333 | 0.25 | 0.2857143 |
| CV2 | 5 | 1 | 1 | 7 | 0.5 | 0.125 | 0.2 |

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

| algoritmo | k | inercia | silhouette | davies_bouldin | calinski_harabasz | ari_min | minimo | maximo | segundos |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kmeans | 2 | 99488.53 | 0.6060427 | 0.7327424 | 38739.4 | 1 | 5009 | 41296 | 2.018981 |
| kmeans | 3 | 74176.67 | 0.3178927 | 1.137261 | 33878.8 | 0.999602 | 5002 | 21686 | 1.11924 |
| kmeans | 4 | 61480.61 | 0.3721761 | 0.9880627 | 30436.5 | 0.9999351 | 4962 | 17306 | 1.210785 |
| kmeans | 5 | 50712.93 | 0.3759873 | 0.9833283 | 30131.3 | 0.9995348 | 808 | 17306 | 1.604998 |
| kmeans | 6 | 43921.58 | 0.3805586 | 0.9866308 | 29263.46 | 0.9972585 | 808 | 12215 | 1.858795 |
| kmeans | 7 | 40142.65 | 0.3786988 | 0.9820659 | 27407.72 | 0.6551768 | 772 | 12230 | 2.002811 |
| kmeans | 8 | 36800.53 | 0.3813538 | 0.9701908 | 26225.93 | 0.5889259 | 772 | 10034 | 2.064121 |
| ward | 2 | nan | 0.5977782 | 0.7855347 | 3147.001 | nan | 466 | 3534 | 0.2820524 |
| ward | 3 | nan | 0.2915934 | 1.228357 | 2488.872 | nan | 466 | 2271 | 0.2820524 |
| ward | 4 | nan | 0.2970614 | 1.222108 | 2191.748 | nan | 116 | 2271 | 0.2820524 |
| ward | 5 | nan | 0.3120881 | 1.082628 | 2175.16 | nan | 116 | 1681 | 0.2820524 |
| ward | 6 | nan | 0.3161293 | 0.9927593 | 2107.395 | nan | 116 | 1681 | 0.2820524 |
| ward | 7 | nan | 0.3324097 | 1.092907 | 2016.966 | nan | 116 | 945 | 0.2820524 |
| ward | 8 | nan | 0.3319135 | 1.047097 | 1963.326 | nan | 17 | 945 | 0.2820524 |
| average | 2 | nan | 0.7854011 | 0.3169922 | 519.9964 | nan | 17 | 3983 | 0.2652664 |
| average | 3 | nan | 0.5802418 | 0.6739503 | 1946.35 | nan | 17 | 3534 | 0.2652664 |
| average | 4 | nan | 0.4845843 | 0.8456832 | 1467.209 | nan | 17 | 3534 | 0.2652664 |
| average | 5 | nan | 0.4845843 | 0.87531 | 1108.405 | nan | 4 | 3534 | 0.2652664 |
| average | 6 | nan | 0.4881205 | 0.8948461 | 995.0794 | nan | 4 | 3534 | 0.2652664 |
| average | 7 | nan | 0.4863775 | 0.9780004 | 840.9508 | nan | 4 | 3534 | 0.2652664 |
| average | 8 | nan | 0.4320119 | 1.025147 | 727.8421 | nan | 4 | 3534 | 0.2652664 |

### M4 · KMeans K=2

| cluster | eventos | eventos_ato | eventos_no_ato | prevalencia | usuarios | usuarios_con_ato |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 41296 | 32 | 41264 | 0.0007748935 | 1600 | 31 |
| 1 | 5009 | 4 | 5005 | 0.0007985626 | 941 | 4 |

Perfiles completos: [numéricos](fase04_clustering/resultados/perfil_numerico_kmeans_2.csv), [categóricos](fase04_clustering/resultados/perfil_categorico_kmeans_2.csv), [gráfica de perfiles](fase04_clustering/resultados/graficas/perfiles_kmeans_2.png), [evaluación externa](fase04_clustering/resultados/graficas/externa_kmeans_2.png).

### M5 · Ward K=2

| cluster | eventos | eventos_ato | eventos_no_ato | prevalencia | usuarios | usuarios_con_ato |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 3534 | 1 | 3533 | 0.0002829655 | 1264 | 1 |
| 1 | 466 | 0 | 466 | 0 | 317 | 0 |

Perfiles completos: [numéricos](fase04_clustering/resultados/perfil_numerico_ward_2.csv), [categóricos](fase04_clustering/resultados/perfil_categorico_ward_2.csv), [gráfica de perfiles](fase04_clustering/resultados/graficas/perfiles_ward_2.png), [evaluación externa](fase04_clustering/resultados/graficas/externa_ward_2.png).

KMeans usa 46.305 eventos: grupos 41.296 y 5.009, silhouette 0,6060 y ARI entre semillas 1. Ward usa muestra uniforme de 4.000 eventos y 1.360 usuarios: grupos 3.534 y 466, silhouette 0,5978. Average se conserva como alternativa: K=2 produce grupos 3.983/17 y silhouette 0,7854, sin seleccionar solo por ese máximo. ARI KMeans/Ward en muestra común 0,9281. K se fijó por índices, tamaños y perfiles, no por ATO.

Prevalencias ATO KMeans prácticamente iguales (0,07749% y 0,07986%); muestra Ward con solo un ATO: no demuestra separación útil para detección. Los perfiles describen fallos recientes e intervalos, no ataques. Las métricas internas no son comparables directamente con precision/recall/AP. No se asigna un umbral de score supervisado a KMeans/Ward: sus distancias o clusters no constituyen una probabilidad ATO ni una regla de clasificación autorizada.

Informe íntegro: [INFORME_CLUSTERING_FASE04.md](INFORME_CLUSTERING_FASE04.md). Gráficas históricas: [índices internos](fase04_clustering/resultados/graficas/seleccion_interna.png), [dendrograma Ward](fase04_clustering/resultados/graficas/dendrograma_ward.png), [estabilidad KMeans](fase04_clustering/resultados/graficas/estabilidad_kmeans.png). Se conservan todas las alternativas K=2–8 y ambos enlaces. El análisis de errores supervisados no se aplica ficticiamente a estas particiones.

## 11. Catálogo de nuevas gráficas

PNG a 300 DPI y SVG, paleta consistente, variantes numeradas M1a–M3b, tamaños de muestra y notas de exploración. Confusiones en cantidades absolutas y misma escala cromática, filas reales/columnas predichas. Escalas log/symlog se declaran, incluyen vistas completas o cero cuando corresponde. No se utiliza 3D ni accuracy.

- [01_comparacion_protocolos · PNG](fase04_modelado/seleccion_supervisada/graficas/01_comparacion_protocolos.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/01_comparacion_protocolos.svg): Métricas de todas las variantes a 0,5. Cambia la partición, no el algoritmo.
- [02_pr_CV1 · PNG](fase04_modelado/seleccion_supervisada/graficas/02_pr_CV1.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/02_pr_CV1.svg): AP y prevalencia. AP global concatena escalas de cinco estimadores no necesariamente calibradas; detalle log explícito.
- [02_pr_CV2 · PNG](fase04_modelado/seleccion_supervisada/graficas/02_pr_CV2.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/02_pr_CV2.svg): AP y prevalencia. AP global concatena escalas de cinco estimadores no necesariamente calibradas; detalle log explícito.
- [03_umbrales_arbol_baseline · PNG](fase04_modelado/seleccion_supervisada/graficas/03_umbrales_arbol_baseline.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/03_umbrales_arbol_baseline.svg): Precision/recall, TP/FN, FP y porcentaje de alertas por umbral y protocolo. Estados exactos y sus métricas en CSV.
- [04_confusiones_CV1_arbol_baseline · PNG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV1_arbol_baseline.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV1_arbol_baseline.svg): Matrices a 0,2 / 0,4 / 0,5. No omite variantes desfavorables; resto de umbrales en tabla completa.
- [04_confusiones_CV2_arbol_baseline · PNG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV2_arbol_baseline.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV2_arbol_baseline.svg): Matrices a 0,2 / 0,4 / 0,5. No omite variantes desfavorables; resto de umbrales en tabla completa.
- [03_umbrales_arbol_ponderado · PNG](fase04_modelado/seleccion_supervisada/graficas/03_umbrales_arbol_ponderado.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/03_umbrales_arbol_ponderado.svg): Precision/recall, TP/FN, FP y porcentaje de alertas por umbral y protocolo. Estados exactos y sus métricas en CSV.
- [04_confusiones_CV1_arbol_ponderado · PNG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV1_arbol_ponderado.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV1_arbol_ponderado.svg): Matrices a 0,2 / 0,4 / 0,5. No omite variantes desfavorables; resto de umbrales en tabla completa.
- [04_confusiones_CV2_arbol_ponderado · PNG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV2_arbol_ponderado.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV2_arbol_ponderado.svg): Matrices a 0,2 / 0,4 / 0,5. No omite variantes desfavorables; resto de umbrales en tabla completa.
- [03_umbrales_gnb_baseline · PNG](fase04_modelado/seleccion_supervisada/graficas/03_umbrales_gnb_baseline.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/03_umbrales_gnb_baseline.svg): Precision/recall, TP/FN, FP y porcentaje de alertas por umbral y protocolo. Estados exactos y sus métricas en CSV.
- [04_confusiones_CV1_gnb_baseline · PNG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV1_gnb_baseline.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV1_gnb_baseline.svg): Matrices a 0,2 / 0,4 / 0,5. No omite variantes desfavorables; resto de umbrales en tabla completa.
- [04_confusiones_CV2_gnb_baseline · PNG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV2_gnb_baseline.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV2_gnb_baseline.svg): Matrices a 0,2 / 0,4 / 0,5. No omite variantes desfavorables; resto de umbrales en tabla completa.
- [03_umbrales_gnb_ponderado · PNG](fase04_modelado/seleccion_supervisada/graficas/03_umbrales_gnb_ponderado.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/03_umbrales_gnb_ponderado.svg): Precision/recall, TP/FN, FP y porcentaje de alertas por umbral y protocolo. Estados exactos y sus métricas en CSV.
- [04_confusiones_CV1_gnb_ponderado · PNG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV1_gnb_ponderado.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV1_gnb_ponderado.svg): Matrices a 0,2 / 0,4 / 0,5. No omite variantes desfavorables; resto de umbrales en tabla completa.
- [04_confusiones_CV2_gnb_ponderado · PNG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV2_gnb_ponderado.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV2_gnb_ponderado.svg): Matrices a 0,2 / 0,4 / 0,5. No omite variantes desfavorables; resto de umbrales en tabla completa.
- [03_umbrales_knn_baseline · PNG](fase04_modelado/seleccion_supervisada/graficas/03_umbrales_knn_baseline.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/03_umbrales_knn_baseline.svg): Precision/recall, TP/FN, FP y porcentaje de alertas por umbral y protocolo. Estados exactos y sus métricas en CSV.
- [04_confusiones_CV1_knn_baseline · PNG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV1_knn_baseline.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV1_knn_baseline.svg): Matrices a 0,2 / 0,4 / 0,5. No omite variantes desfavorables; resto de umbrales en tabla completa.
- [04_confusiones_CV2_knn_baseline · PNG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV2_knn_baseline.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV2_knn_baseline.svg): Matrices a 0,2 / 0,4 / 0,5. No omite variantes desfavorables; resto de umbrales en tabla completa.
- [03_umbrales_knn_ros · PNG](fase04_modelado/seleccion_supervisada/graficas/03_umbrales_knn_ros.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/03_umbrales_knn_ros.svg): Precision/recall, TP/FN, FP y porcentaje de alertas por umbral y protocolo. Estados exactos y sus métricas en CSV.
- [04_confusiones_CV1_knn_ros · PNG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV1_knn_ros.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV1_knn_ros.svg): Matrices a 0,2 / 0,4 / 0,5. No omite variantes desfavorables; resto de umbrales en tabla completa.
- [04_confusiones_CV2_knn_ros · PNG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV2_knn_ros.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/04_confusiones_CV2_knn_ros.svg): Matrices a 0,2 / 0,4 / 0,5. No omite variantes desfavorables; resto de umbrales en tabla completa.
- [05_variabilidad_folds · PNG](fase04_modelado/seleccion_supervisada/graficas/05_variabilidad_folds.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/05_variabilidad_folds.svg): Cinco valores por variante y protocolo. Medias y DE a todos los umbrales disponibles en resumen_folds.csv.
- [06_compromisos_tp_fp · PNG](fase04_modelado/seleccion_supervisada/graficas/06_compromisos_tp_fp.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/06_compromisos_tp_fp.svg): Puntos exploratorios sin coste FP/FN supuesto. Frontera Pareto identificada en CSV, no implica ganador.
- [07_tabla_compromisos · PNG](fase04_modelado/seleccion_supervisada/graficas/07_tabla_compromisos.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/07_tabla_compromisos.svg): Comparación legible de conteos y tasas a referencia 0,4; no ordena variantes por una sola métrica.

## 12. Limitaciones, pruebas y próximos pasos

Vista adicional: [detalle FP para umbrales positivos · PNG](fase04_modelado/seleccion_supervisada/graficas/08_detalle_fp_umbrales_positivos.png) / [SVG](fase04_modelado/seleccion_supervisada/graficas/08_detalle_fp_umbrales_positivos.svg). Se excluye únicamente t=0 para distinguir diferencias pequeñas, conservando las vistas completas. Escala vertical explícita por variante. Total: 25 figuras, 50 archivos PNG/SVG. Reproducción adicional: `python -B -m fase04_modelado.seleccion_supervisada.detalle_grafico`.

Solo 36 eventos positivos de 34 usuarios; un evento cambia recall global 2,78 puntos porcentuales. Los eventos de un usuario son dependientes. Los scores proceden de cinco estimadores por protocolo y sus escalas pueden diferir; el modelo reajustado en todo train podría generar una distribución distinta. La geografía es sintética, las características son limitadas y la partición por usuario no es validación temporal. El barrido exhaustivo aumenta la oportunidad de selección optimista. El extremo de t>1 se informa como control, nunca como modelo útil. No se calcularon costes inventados, significación o intervalos no justificados.

Las pruebas de esta entrega verifican correspondencia de eventos y etiquetas, hashes, separación de usuarios, métricas globales/por fold, estados de umbral con empates y ausencia de alertas, AP invariante, reproducción de decisiones, igualdad de alertas KNN/ROS a 0,2, guardia de acceso a test, ausencia de ajuste en módulos de análisis, integridad PNG/SVG y número de matrices. El resultado de ejecución queda en `fase04_modelado/seleccion_supervisada/resultados/pruebas.txt`.

Código modular: `auditoria.py` (clase AuditorResultados), `umbrales.py` (métricas y estados), `analisis.py` (tablas y errores), `graficas.py` (clase ExportadorFiguras), `informe.py` y `verificar_entrega.py`. Responsabilidad única, composición y exportaciones exclusivas; no se refactoriza código histórico.

Reproducción en un destino nuevo, manteniendo versiones y orden de filas: `python -B -m fase04_modelado.seleccion_supervisada.analisis`, luego `.graficas` y `.informe`. Los generadores rechazan sobrescribir entregables. Pruebas: `python -B -m pytest -p no:cacheprovider -q fase04_modelado/seleccion_supervisada/tests`. No ejecutar pipelines históricos ni modelos finales para reproducir tablas de esta etapa.

Resultados nuevos en `fase04_modelado/seleccion_supervisada/resultados/`: auditoría de fuentes; umbrales globales y por fold; resumen de folds; scores por clase; errores por evento/usuario; concordancia entre CV; métricas y tiempos históricos consolidados. `verificacion_entrega.json` registra preservación de históricos y SHA-256 de entregables. Test solo por metadatos. No se leen ni copian sus datos.

Próximo paso sujeto a decisión: acordar un objetivo académico explícito de detección y alertas; autorizar validación anidada por usuario para seleccionar variante/umbral; después congelar configuración y decidir entrenamiento final. Test requiere autorización independiente. No se realizaron operaciones Git, instalaciones, ajustes de modelos ni cambios históricos. **Fase 4 no se declara terminada.**
