# Informe de validación anidada — Fase 4

Fecha: 2026-11-21. Diseño autorizado 5×3, seis variantes, F1 interno agrupado por evento, semilla 42. **No se entrenó modelo final ni se accedió a test.**

## 1. Dictamen

Se completaron 90 ajustes internos y 30 reajustes externos. Las cinco decisiones se guardaron antes de calcular cualquier métrica externa. El selector conjunto eligió árbol ponderado en el fold 1, KNN+ROS en 2, 4 y 5, y KNN baseline en 3. Sus decisiones externas detectaron **4 de 36 ATO**, omitieron **32** y produjeron **72 falsas alarmas**: precision 5,2632%, recall 11,1111%, F1 0,071429, 76 alertas (0,16413% de los eventos).

Esto no demuestra un ganador estable ni autoriza convertir la variante con mejor métrica externa en un ganador retrospectivo. El selector y los umbrales cambian entre folds. La validación anidada evalúa el procedimiento predefinido, no garantiza robustez con 34 usuarios positivos ni independencia respecto a la exploración histórica de estos mismos datos. No se declara terminada Fase 4.

## 2. Especificación, auditoría y fuentes

Especificación: [PROPUESTA_VALIDACION_ANIDADA_FASE04.md](PROPUESTA_VALIDACION_ANIDADA_FASE04.md), SHA-256 `0beb039be4e7f2660fb53ccfcb79596867b0ae07a06a10ff87e06d57288807b5`. Se aplicaron las decisiones explícitas de la autorización: F1 agrupado, score >= umbral, desempate por distancia a 0,5 y luego mayor, y orden histórico entre variantes. No se colapsaron candidatos con decisiones equivalentes para evitar perder el desempate autorizado; se registraron todos los empates.

Train: 46.305 eventos, 1.600 usuarios, 36 eventos ATO de 34 usuarios. SHA-256 `98d4d4970ada7bf11ec2e76f89e93c46c76c3d097043020598638547f977e53f`. Datos de entrenamiento: únicamente `dataset_train_fase04.csv`. Las lecturas de otros artefactos históricos en el registro de accesos son comprobaciones de integridad o referencias históricas; no se reutilizaron matrices ajustadas ni preprocesadores.

Se preservaron fábricas de modelos, selección de seis predictores y preprocesamiento específico de cada familia. Predictores: Device Type, Country, failed_attempts_15min, failed_attempts_1h, time_since_previous_login_hours y has_previous_login. IDs y etiqueta no están en X. Se mantuvieron exclusiones Impossible Travel y todos los hiperparámetros históricos. No se añadió calibración ni búsqueda de hiperparámetros.

La guardia de aperturas bloquea CSV/NPY/joblib de test antes de abrirlos. Test se excluye también del inventario: **no se abrió, inspeccionó, cargó ni calculó su hash o metadatos**. Se comprobaron 326 archivos históricos permitidos antes/después de ejecutar. La verificación final y hashes de entregables se guardan en `manifiesto_entrega.json`. No hubo instalaciones ni operaciones Git.

## 3. Particiones externas e internas

Se construye una tabla ordenada por User ID con max(ATO), se aplica StratifiedKFold con shuffle y semilla 42 a usuarios, y se expanden todos sus eventos. Cinco folds externos; dentro de cada entrenamiento externo se construye una tabla nueva y tres folds internos. Los índices internos son relativos a su población y se traducen explícitamente a evento_id global. Ningún usuario se comparte entre ajuste y validación en ninguno de los niveles; cada evento recibe una OOF interna dentro de cada población externa en que participa y una externa por variante.

| fold_externo | fold_interno | usuarios_compartidos | ajuste_eventos | ajuste_usuarios | ajuste_ato | ajuste_negativos | ajuste_usuarios_ato | validacion_eventos | validacion_usuarios | validacion_ato | validacion_negativos | validacion_usuarios_ato |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0 | 0 | 37070 | 1280 | 30 | 37040 | 28 | 9235 | 320 | 6 | 9229 | 6 |
| 1 | 1 | 0 | 25709 | 853 | 21 | 25688 | 19 | 11361 | 427 | 9 | 11352 | 9 |
| 1 | 2 | 0 | 23492 | 853 | 19 | 23473 | 18 | 13578 | 427 | 11 | 13567 | 10 |
| 1 | 3 | 0 | 24939 | 854 | 20 | 24919 | 19 | 12131 | 426 | 10 | 12121 | 9 |
| 2 | 0 | 0 | 36193 | 1280 | 29 | 36164 | 27 | 10112 | 320 | 7 | 10105 | 7 |
| 2 | 1 | 0 | 24257 | 853 | 20 | 24237 | 18 | 11936 | 427 | 9 | 11927 | 9 |
| 2 | 2 | 0 | 23740 | 853 | 19 | 23721 | 18 | 12453 | 427 | 10 | 12443 | 9 |
| 2 | 3 | 0 | 24389 | 854 | 19 | 24370 | 18 | 11804 | 426 | 10 | 11794 | 9 |
| 3 | 0 | 0 | 37984 | 1280 | 29 | 37955 | 27 | 8321 | 320 | 7 | 8314 | 7 |
| 3 | 1 | 0 | 25369 | 853 | 19 | 25350 | 18 | 12615 | 427 | 10 | 12605 | 9 |
| 3 | 2 | 0 | 25829 | 853 | 20 | 25809 | 18 | 12155 | 427 | 9 | 12146 | 9 |
| 3 | 3 | 0 | 24770 | 854 | 19 | 24751 | 18 | 13214 | 426 | 10 | 13204 | 9 |
| 4 | 0 | 0 | 36628 | 1280 | 28 | 36600 | 27 | 9677 | 320 | 8 | 9669 | 7 |
| 4 | 1 | 0 | 25489 | 853 | 18 | 25471 | 18 | 11139 | 427 | 10 | 11129 | 9 |
| 4 | 2 | 0 | 24084 | 853 | 19 | 24065 | 18 | 12544 | 427 | 9 | 12535 | 9 |
| 4 | 3 | 0 | 23683 | 854 | 19 | 23664 | 18 | 12945 | 426 | 9 | 12936 | 9 |
| 5 | 0 | 0 | 37345 | 1280 | 28 | 37317 | 27 | 8960 | 320 | 8 | 8952 | 7 |
| 5 | 1 | 0 | 25345 | 853 | 19 | 25326 | 18 | 12000 | 427 | 9 | 11991 | 9 |
| 5 | 2 | 0 | 24433 | 853 | 18 | 24415 | 18 | 12912 | 427 | 10 | 12902 | 9 |
| 5 | 3 | 0 | 24912 | 854 | 19 | 24893 | 18 | 12433 | 426 | 9 | 12424 | 9 |

Las etiquetas externas se usaron para estratificación y conteos de la partición, nunca para seleccionar umbrales, variantes o desempates. Los folds de validación externa coinciden con CV2 por diseño, no por búsqueda de métricas favorables. No se modificó la semilla.

## 4. Ajuste, selección y congelación

Cada ajuste crea un preprocesador nuevo: mediana y categorías One-Hot aprendidas solo con ajuste; log1p según familia; StandardScaler en KNN. Se verifica que transform no modifica estado, medianas/categorías coincidan con filas autorizadas y matrices sean finitas. GaussianNB ponderado calcula sample_weight local; árbol ponderado conserva class_weight='balanced', calculado por sklearn con etiquetas locales. ROS solo se aplica a entrenamiento transformado, con índices verificados como remuestreo del subtrain, nunca a validaciones.

Para cada variante se concatenaron las OOF de sus tres validaciones internas. Se enumeraron scores únicos, referencia 0,5, política todos (umbral 0) y ninguno (siguiente float mayor que 1, registrado explícitamente). Las decisiones usan >=, incluidos empates. F1 se compara mediante la fracción exacta 2TP/(2TP+FP+FN), evitando falsas desigualdades de coma flotante. Entre máximos se elige el candidato más próximo a 0,5 y luego el mayor; entre variantes se usa el orden histórico. No se inventaron costes o restricciones FP/FN.

Cada `decisiones_congeladas_N.json` contiene umbrales, todos los empates y selector, con hash de OOF internas. Se escribe antes de los seis reajustes externos y se verifica que permanezca intacto. La función de ajuste recibe X/y de entrenamiento y solo X de validación. Las etiquetas externas se adjuntan al resultado después de congelar las decisiones de los cinco folds. Las métricas externas se calculan en un módulo posterior, sin correcciones de umbral.

```text
Por cada fold externo:
    construir tres particiones nuevas solo dentro de su entrenamiento
    generar seis OOF internas con preprocesamiento local
    elegir umbral por variante y variante del selector por F1 interno
    guardar decisiones y hashes inmutables
    reajustar seis variantes en entrenamiento externo
    guardar scores externos originales, decisiones aprendidas y a 0,5
Después de congelar los cinco folds:
    adjuntar etiquetas externas, auditar y evaluar
```

### Umbrales y selecciones reales

| fold_externo | modelo | umbral | politica | f1_interno | selector | numero_empates_umbral | numero_empates_variantes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | arbol_baseline | 0.25 | umbral | 0.1081081 | False | 1 | 1 |
| 1 | arbol_ponderado | 0.9975535 | umbral | 0.1219512 | True | 1 | 1 |
| 1 | gnb_baseline | 0.5 | umbral | 0.001763357 | False | 2 | 1 |
| 1 | gnb_ponderado | 0.5 | umbral | 0.001763357 | False | 2 | 1 |
| 1 | knn_baseline | 0.2 | umbral | 0.09302326 | False | 1 | 1 |
| 1 | knn_ros | 0.4 | umbral | 0.1 | False | 1 | 1 |
| 2 | arbol_baseline | 0.25 | umbral | 0.1012658 | False | 1 | 1 |
| 2 | arbol_ponderado | 0.9976028 | umbral | 0.1111111 | False | 1 | 1 |
| 2 | gnb_baseline | 0 | todos | 0.001601237 | False | 1 | 1 |
| 2 | gnb_ponderado | 0 | todos | 0.001601237 | False | 1 | 1 |
| 2 | knn_baseline | 0.2 | umbral | 0.1111111 | False | 1 | 1 |
| 2 | knn_ros | 0.8 | umbral | 0.1333333 | True | 1 | 1 |
| 3 | arbol_baseline | 0.5 | umbral | 0.07207207 | False | 2 | 1 |
| 3 | arbol_ponderado | 1 | umbral | 0.06 | False | 1 | 1 |
| 3 | gnb_baseline | 0.5 | umbral | 0.002082249 | False | 2 | 1 |
| 3 | gnb_ponderado | 0.5 | umbral | 0.002082249 | False | 2 | 1 |
| 3 | knn_baseline | 0.4 | umbral | 0.1578947 | True | 1 | 1 |
| 3 | knn_ros | 0.8 | umbral | 0.112 | False | 1 | 1 |
| 4 | arbol_baseline | 0.25 | umbral | 0.1971831 | False | 1 | 1 |
| 4 | arbol_ponderado | 0.9978844 | umbral | 0.1967213 | False | 1 | 1 |
| 4 | gnb_baseline | 0.5 | umbral | 0.001674808 | False | 2 | 1 |
| 4 | gnb_ponderado | 0.5 | umbral | 0.001674808 | False | 2 | 1 |
| 4 | knn_baseline | 0.2 | umbral | 0.1929825 | False | 1 | 1 |
| 4 | knn_ros | 0.4 | umbral | 0.2 | True | 2 | 1 |
| 5 | arbol_baseline | 0.5 | umbral | 0.1041667 | False | 1 | 1 |
| 5 | arbol_ponderado | 0.9992633 | umbral | 0.1 | False | 1 | 1 |
| 5 | gnb_baseline | 0.5 | umbral | 0.001691868 | False | 2 | 1 |
| 5 | gnb_ponderado | 0.5 | umbral | 0.001691868 | False | 2 | 1 |
| 5 | knn_baseline | 0.2 | umbral | 0.1126761 | False | 1 | 1 |
| 5 | knn_ros | 0.8 | umbral | 0.1188119 | True | 1 | 1 |

### Empates registrados

| fold | modelo | umbral | umbrales_maximo_f1 | variantes_maximo_f1 |
| --- | --- | --- | --- | --- |
| 1 | arbol_baseline | 0.25 | [0.25] | ['arbol_ponderado'] |
| 1 | arbol_ponderado | 0.9975535 | [0.9975534930682306] | ['arbol_ponderado'] |
| 1 | gnb_baseline | 0.5 | [0.5, 1.0] | ['arbol_ponderado'] |
| 1 | gnb_ponderado | 0.5 | [0.5, 1.0] | ['arbol_ponderado'] |
| 1 | knn_baseline | 0.2 | [0.2] | ['arbol_ponderado'] |
| 1 | knn_ros | 0.4 | [0.4] | ['arbol_ponderado'] |
| 2 | arbol_baseline | 0.25 | [0.25] | ['knn_ros'] |
| 2 | arbol_ponderado | 0.9976028 | [0.9976028261418118] | ['knn_ros'] |
| 2 | gnb_baseline | 0 | [0.0] | ['knn_ros'] |
| 2 | gnb_ponderado | 0 | [0.0] | ['knn_ros'] |
| 2 | knn_baseline | 0.2 | [0.2] | ['knn_ros'] |
| 2 | knn_ros | 0.8 | [0.8] | ['knn_ros'] |
| 3 | arbol_baseline | 0.5 | [0.5, 1.0] | ['knn_baseline'] |
| 3 | arbol_ponderado | 1 | [1.0] | ['knn_baseline'] |
| 3 | gnb_baseline | 0.5 | [0.5, 1.0] | ['knn_baseline'] |
| 3 | gnb_ponderado | 0.5 | [0.5, 1.0] | ['knn_baseline'] |
| 3 | knn_baseline | 0.4 | [0.4] | ['knn_baseline'] |
| 3 | knn_ros | 0.8 | [0.8] | ['knn_baseline'] |
| 4 | arbol_baseline | 0.25 | [0.25] | ['knn_ros'] |
| 4 | arbol_ponderado | 0.9978844 | [0.9978844270323213] | ['knn_ros'] |
| 4 | gnb_baseline | 0.5 | [0.5, 1.0] | ['knn_ros'] |
| 4 | gnb_ponderado | 0.5 | [0.5, 1.0] | ['knn_ros'] |
| 4 | knn_baseline | 0.2 | [0.2] | ['knn_ros'] |
| 4 | knn_ros | 0.4 | [0.4, 0.8] | ['knn_ros'] |
| 5 | arbol_baseline | 0.5 | [0.5] | ['knn_ros'] |
| 5 | arbol_ponderado | 0.9992633 | [0.999263291450088] | ['knn_ros'] |
| 5 | gnb_baseline | 0.5 | [0.5, 1.0] | ['knn_ros'] |
| 5 | gnb_ponderado | 0.5 | [0.5, 1.0] | ['knn_ros'] |
| 5 | knn_baseline | 0.2 | [0.2] | ['knn_ros'] |
| 5 | knn_ros | 0.8 | [0.8] | ['knn_ros'] |

No hubo empates del máximo entre variantes en los cinco selectores conjuntos; sí entre umbrales en varias variantes. Las tablas de candidatos guardan también hashes de decisiones, permitiendo identificar equivalencias aunque los umbrales numéricos difieran.

## 5. Transferencia OOF interna → reajuste

El umbral interno se aplicó sin cambios al estimador reajustado con todo el entrenamiento externo. No se afirma que su escala o rendimiento se conserve: esa transferencia forma parte del procedimiento evaluado. Los scores externos originales se mantienen en `predicciones_externas.csv`; no se calibraron ni transformaron para mejorar resultados.

Todos los scores externos y decisiones a 0,5 reproducen CV2, dentro de tolerancia numérica 1e-12 relativa / 1e-15 absoluta para scores. Esto verifica que el cambio principal es el procedimiento de selección de umbral, no una alteración silenciosa del ajuste histórico. La comprobación se realizó después de congelar decisiones; CV2 no eligió umbrales.

`distribucion_scores_transferencia.csv` registra scores distintos, proporciones 0/1, media, mediana, percentil 99 y máximo internos/externos. `transferencia.csv` compara F1 interno elegido con resultado externo. Sus diferencias no aíslan causalmente transferencia de escala: también cambia población y tamaño de ajuste, y F1 interno es optimizado, por lo que no debe interpretarse como rendimiento independiente.

| fold_externo | modelo | umbral | f1_interno | f1 | diferencia_f1_externo_interno |
| --- | --- | --- | --- | --- | --- |
| 1 | arbol_baseline | 0.25 | 0.1081081 | 0.05405405 | -0.05405405 |
| 1 | arbol_ponderado | 0.9975535 | 0.1219512 | 0.1176471 | -0.004304161 |
| 1 | gnb_baseline | 0.5 | 0.001763357 | 0.001618559 | -0.000144798 |
| 1 | gnb_ponderado | 0.5 | 0.001763357 | 0.001618559 | -0.000144798 |
| 1 | knn_baseline | 0.2 | 0.09302326 | 0.09302326 | 0 |
| 1 | knn_ros | 0.4 | 0.1 | 0.1142857 | 0.01428571 |
| 2 | arbol_baseline | 0.25 | 0.1012658 | 0 | -0.1012658 |
| 2 | arbol_ponderado | 0.9976028 | 0.1111111 | 0 | -0.1111111 |
| 2 | gnb_baseline | 0 | 0.001601237 | 0.001383536 | -0.0002177009 |
| 2 | gnb_ponderado | 0 | 0.001601237 | 0.001383536 | -0.0002177009 |
| 2 | knn_baseline | 0.2 | 0.1111111 | 0 | -0.1111111 |
| 2 | knn_ros | 0.8 | 0.1333333 | 0 | -0.1333333 |
| 3 | arbol_baseline | 0.5 | 0.07207207 | 0 | -0.07207207 |
| 3 | arbol_ponderado | 1 | 0.06 | 0 | -0.06 |
| 3 | gnb_baseline | 0.5 | 0.002082249 | 0.002109705 | 2.745581e-05 |
| 3 | gnb_ponderado | 0.5 | 0.002082249 | 0.002109705 | 2.745581e-05 |
| 3 | knn_baseline | 0.4 | 0.1578947 | 0 | -0.1578947 |
| 3 | knn_ros | 0.8 | 0.112 | 0 | -0.112 |
| 4 | arbol_baseline | 0.25 | 0.1971831 | 0.1538462 | -0.04333694 |
| 4 | arbol_ponderado | 0.9978844 | 0.1967213 | 0.3157895 | 0.1190682 |
| 4 | gnb_baseline | 0.5 | 0.001674808 | 0.001853323 | 0.0001785146 |
| 4 | gnb_ponderado | 0.5 | 0.001674808 | 0.001853323 | 0.0001785146 |
| 4 | knn_baseline | 0.2 | 0.1929825 | 0.07017544 | -0.122807 |
| 4 | knn_ros | 0.4 | 0.2 | 0.08163265 | -0.1183673 |
| 5 | arbol_baseline | 0.5 | 0.1041667 | 0.1333333 | 0.02916667 |
| 5 | arbol_ponderado | 0.9992633 | 0.1 | 0.1428571 | 0.04285714 |
| 5 | gnb_baseline | 0.5 | 0.001691868 | 0.001113741 | -0.0005781277 |
| 5 | gnb_ponderado | 0.5 | 0.001691868 | 0.001113741 | -0.0005781277 |
| 5 | knn_baseline | 0.2 | 0.1126761 | 0.1904762 | 0.07780013 |
| 5 | knn_ros | 0.8 | 0.1188119 | 0.1538462 | 0.03503427 |

## 6. Resultados completos agrupados por evento

Aprendido significa un umbral seleccionado por fold; no un único umbral global. Fijo_05 usa los mismos scores externos con umbral 0,5. La referencia del selector conserva las variantes seleccionadas internamente mediante F1 con umbral aprendido, pero aplica 0,5; **no es otro selector entrenado para elegir por F1 a 0,5**.

| modelo | regla | TP | FP | TN | FN | precision | recall | f1 | average_precision | alertas | porcentaje_alertas | sin_predicciones_positivas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arbol_baseline | aprendido | 3 | 64 | 46205 | 33 | 0.04477612 | 0.08333333 | 0.05825243 | 0.00886213 | 67 | 0.1446928 | False |
| arbol_baseline | fijo_05 | 3 | 61 | 46208 | 33 | 0.046875 | 0.08333333 | 0.06 | 0.00886213 | 64 | 0.138214 | False |
| arbol_ponderado | aprendido | 5 | 54 | 46215 | 31 | 0.08474576 | 0.1388889 | 0.1052632 | 0.01581734 | 59 | 0.127416 | False |
| arbol_ponderado | fijo_05 | 9 | 675 | 45594 | 27 | 0.01315789 | 0.25 | 0.025 | 0.01581734 | 684 | 1.477162 | False |
| gnb_baseline | aprendido | 31 | 38839 | 7430 | 5 | 0.0007975302 | 0.8611111 | 0.001593585 | 0.0008397754 | 38870 | 83.94342 | False |
| gnb_baseline | fijo_05 | 31 | 36447 | 9822 | 5 | 0.0008498273 | 0.8611111 | 0.001697979 | 0.0008397754 | 36478 | 78.77767 | False |
| gnb_ponderado | aprendido | 31 | 38839 | 7430 | 5 | 0.0007975302 | 0.8611111 | 0.001593585 | 0.0008397754 | 38870 | 83.94342 | False |
| gnb_ponderado | fijo_05 | 31 | 36447 | 9822 | 5 | 0.0008498273 | 0.8611111 | 0.001697979 | 0.0008397754 | 36478 | 78.77767 | False |
| knn_baseline | aprendido | 6 | 122 | 46147 | 30 | 0.046875 | 0.1666667 | 0.07317073 | 0.04316277 | 128 | 0.276428 | False |
| knn_baseline | fijo_05 | 0 | 1 | 46268 | 36 | 0 | 0 | 0 | 0.04316277 | 1 | 0.002159594 | False |
| knn_ros | aprendido | 5 | 104 | 46165 | 31 | 0.04587156 | 0.1388889 | 0.06896552 | 0.01246152 | 109 | 0.2353957 | False |
| knn_ros | fijo_05 | 5 | 99 | 46170 | 31 | 0.04807692 | 0.1388889 | 0.07142857 | 0.01246152 | 104 | 0.2245978 | False |
| selector_conjunto | aprendido | 4 | 72 | 46197 | 32 | 0.05263158 | 0.1111111 | 0.07142857 | No procede | 76 | 0.1641291 | False |
| selector_conjunto | fijo_05 | 5 | 198 | 46071 | 31 | 0.02463054 | 0.1388889 | 0.041841 | No procede | 203 | 0.4383976 | False |

Precision=TP/(TP+FP); recall=TP/(TP+FN); F1=2TP/(2TP+FP+FN). Cuando no hay alertas se informa precision=0 por convención, acompañada por bandera explícita. AP se calcula a partir del ranking de scores y no cambia al modificar el umbral. La AP global de cada variante concatena scores de cinco estimadores, con escalas no necesariamente comparables; se conserva con esa limitación.

La AP global del selector se deja **sin calcular** porque combina familias distintas. No se trata el NaN del CSV como cero ni se ordena el selector mediante esa AP. Su AP se presenta solo por fold, con la familia correspondiente, y como media/DE descriptiva de esos valores locales.

## 7. Resultados individuales por fold

| modelo | regla | fold_externo | TP | FP | TN | FN | precision | recall | f1 | average_precision | alertas | porcentaje_alertas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arbol_baseline | aprendido | 1 | 1 | 30 | 9199 | 5 | 0.03225806 | 0.1666667 | 0.05405405 | 0.008085126 | 31 | 0.3356795 |
| arbol_baseline | aprendido | 2 | 0 | 13 | 10092 | 7 | 0 | 0 | 0 | 0.001700774 | 13 | 0.1285601 |
| arbol_baseline | aprendido | 3 | 0 | 11 | 8303 | 7 | 0 | 0 | 0 | 0.01171008 | 11 | 0.1321956 |
| arbol_baseline | aprendido | 4 | 1 | 4 | 9665 | 7 | 0.2 | 0.125 | 0.1538462 | 0.03197336 | 5 | 0.05166891 |
| arbol_baseline | aprendido | 5 | 1 | 6 | 8946 | 7 | 0.1428571 | 0.125 | 0.1333333 | 0.04630456 | 7 | 0.078125 |
| arbol_baseline | fijo_05 | 1 | 1 | 29 | 9200 | 5 | 0.03333333 | 0.1666667 | 0.05555556 | 0.008085126 | 30 | 0.3248511 |
| arbol_baseline | fijo_05 | 2 | 0 | 12 | 10093 | 7 | 0 | 0 | 0 | 0.001700774 | 12 | 0.1186709 |
| arbol_baseline | fijo_05 | 3 | 0 | 11 | 8303 | 7 | 0 | 0 | 0 | 0.01171008 | 11 | 0.1321956 |
| arbol_baseline | fijo_05 | 4 | 1 | 3 | 9666 | 7 | 0.25 | 0.125 | 0.1666667 | 0.03197336 | 4 | 0.04133512 |
| arbol_baseline | fijo_05 | 5 | 1 | 6 | 8946 | 7 | 0.1428571 | 0.125 | 0.1333333 | 0.04630456 | 7 | 0.078125 |
| arbol_ponderado | aprendido | 1 | 1 | 10 | 9219 | 5 | 0.09090909 | 0.1666667 | 0.1176471 | 0.01949788 | 11 | 0.1191121 |
| arbol_ponderado | aprendido | 2 | 0 | 20 | 10085 | 7 | 0 | 0 | 0 | 0.001643775 | 20 | 0.1977848 |
| arbol_ponderado | aprendido | 3 | 0 | 11 | 8303 | 7 | 0 | 0 | 0 | 0.01171008 | 11 | 0.1321956 |
| arbol_ponderado | aprendido | 4 | 3 | 8 | 9661 | 5 | 0.2727273 | 0.375 | 0.3157895 | 0.1374215 | 11 | 0.1136716 |
| arbol_ponderado | aprendido | 5 | 1 | 5 | 8947 | 7 | 0.1666667 | 0.125 | 0.1428571 | 0.05275298 | 6 | 0.06696429 |
| arbol_ponderado | fijo_05 | 1 | 2 | 137 | 9092 | 4 | 0.01438849 | 0.3333333 | 0.02758621 | 0.01949788 | 139 | 1.505143 |
| arbol_ponderado | fijo_05 | 2 | 1 | 135 | 9970 | 6 | 0.007352941 | 0.1428571 | 0.01398601 | 0.001643775 | 136 | 1.344937 |
| arbol_ponderado | fijo_05 | 3 | 1 | 138 | 8176 | 6 | 0.007194245 | 0.1428571 | 0.01369863 | 0.01171008 | 139 | 1.670472 |
| arbol_ponderado | fijo_05 | 4 | 3 | 133 | 9536 | 5 | 0.02205882 | 0.375 | 0.04166667 | 0.1374215 | 136 | 1.405394 |
| arbol_ponderado | fijo_05 | 5 | 2 | 132 | 8820 | 6 | 0.01492537 | 0.25 | 0.02816901 | 0.05275298 | 134 | 1.495536 |
| gnb_baseline | aprendido | 1 | 6 | 7402 | 1827 | 0 | 0.0008099352 | 1 | 0.001618559 | 0.0008099352 | 7408 | 80.21657 |
| gnb_baseline | aprendido | 2 | 7 | 10105 | 0 | 0 | 0.0006922468 | 1 | 0.001383536 | 0.0009067358 | 10112 | 100 |
| gnb_baseline | aprendido | 3 | 7 | 6622 | 1692 | 0 | 0.001055966 | 1 | 0.002109705 | 0.001055966 | 6629 | 79.66591 |
| gnb_baseline | aprendido | 4 | 7 | 7539 | 2130 | 1 | 0.0009276438 | 0.875 | 0.001853323 | 0.0009150261 | 7546 | 77.97871 |
| gnb_baseline | aprendido | 5 | 4 | 7171 | 1781 | 4 | 0.0005574913 | 0.5 | 0.001113741 | 0.0007251742 | 7175 | 80.07812 |
| gnb_baseline | fijo_05 | 1 | 6 | 7402 | 1827 | 0 | 0.0008099352 | 1 | 0.001618559 | 0.0008099352 | 7408 | 80.21657 |
| gnb_baseline | fijo_05 | 2 | 7 | 7713 | 2392 | 0 | 0.0009067358 | 1 | 0.001811829 | 0.0009067358 | 7720 | 76.34494 |
| gnb_baseline | fijo_05 | 3 | 7 | 6622 | 1692 | 0 | 0.001055966 | 1 | 0.002109705 | 0.001055966 | 6629 | 79.66591 |
| gnb_baseline | fijo_05 | 4 | 7 | 7539 | 2130 | 1 | 0.0009276438 | 0.875 | 0.001853323 | 0.0009150261 | 7546 | 77.97871 |
| gnb_baseline | fijo_05 | 5 | 4 | 7171 | 1781 | 4 | 0.0005574913 | 0.5 | 0.001113741 | 0.0007251742 | 7175 | 80.07812 |
| gnb_ponderado | aprendido | 1 | 6 | 7402 | 1827 | 0 | 0.0008099352 | 1 | 0.001618559 | 0.0008099352 | 7408 | 80.21657 |
| gnb_ponderado | aprendido | 2 | 7 | 10105 | 0 | 0 | 0.0006922468 | 1 | 0.001383536 | 0.0009067358 | 10112 | 100 |
| gnb_ponderado | aprendido | 3 | 7 | 6622 | 1692 | 0 | 0.001055966 | 1 | 0.002109705 | 0.001055966 | 6629 | 79.66591 |
| gnb_ponderado | aprendido | 4 | 7 | 7539 | 2130 | 1 | 0.0009276438 | 0.875 | 0.001853323 | 0.0009150261 | 7546 | 77.97871 |
| gnb_ponderado | aprendido | 5 | 4 | 7171 | 1781 | 4 | 0.0005574913 | 0.5 | 0.001113741 | 0.0007251742 | 7175 | 80.07812 |
| gnb_ponderado | fijo_05 | 1 | 6 | 7402 | 1827 | 0 | 0.0008099352 | 1 | 0.001618559 | 0.0008099352 | 7408 | 80.21657 |
| gnb_ponderado | fijo_05 | 2 | 7 | 7713 | 2392 | 0 | 0.0009067358 | 1 | 0.001811829 | 0.0009067358 | 7720 | 76.34494 |
| gnb_ponderado | fijo_05 | 3 | 7 | 6622 | 1692 | 0 | 0.001055966 | 1 | 0.002109705 | 0.001055966 | 6629 | 79.66591 |
| gnb_ponderado | fijo_05 | 4 | 7 | 7539 | 2130 | 1 | 0.0009276438 | 0.875 | 0.001853323 | 0.0009150261 | 7546 | 77.97871 |
| gnb_ponderado | fijo_05 | 5 | 4 | 7171 | 1781 | 4 | 0.0005574913 | 0.5 | 0.001113741 | 0.0007251742 | 7175 | 80.07812 |
| knn_baseline | aprendido | 1 | 2 | 35 | 9194 | 4 | 0.05405405 | 0.3333333 | 0.09302326 | 0.09277548 | 37 | 0.4006497 |
| knn_baseline | aprendido | 2 | 0 | 28 | 10077 | 7 | 0 | 0 | 0 | 0.0006922468 | 28 | 0.2768987 |
| knn_baseline | aprendido | 3 | 0 | 1 | 8313 | 7 | 0 | 0 | 0 | 0.01740761 | 1 | 0.01201779 |
| knn_baseline | aprendido | 4 | 2 | 47 | 9622 | 6 | 0.04081633 | 0.25 | 0.07017544 | 0.08395336 | 49 | 0.5063553 |
| knn_baseline | aprendido | 5 | 2 | 11 | 8941 | 6 | 0.1538462 | 0.25 | 0.1904762 | 0.08240041 | 13 | 0.1450893 |
| knn_baseline | fijo_05 | 1 | 0 | 0 | 9229 | 6 | 0 | 0 | 0 | 0.09277548 | 0 | 0 |
| knn_baseline | fijo_05 | 2 | 0 | 0 | 10105 | 7 | 0 | 0 | 0 | 0.0006922468 | 0 | 0 |
| knn_baseline | fijo_05 | 3 | 0 | 1 | 8313 | 7 | 0 | 0 | 0 | 0.01740761 | 1 | 0.01201779 |
| knn_baseline | fijo_05 | 4 | 0 | 0 | 9669 | 8 | 0 | 0 | 0 | 0.08395336 | 0 | 0 |
| knn_baseline | fijo_05 | 5 | 0 | 0 | 8952 | 8 | 0 | 0 | 0 | 0.08240041 | 0 | 0 |
| knn_ros | aprendido | 1 | 2 | 27 | 9202 | 4 | 0.06896552 | 0.3333333 | 0.1142857 | 0.02941864 | 29 | 0.3140227 |
| knn_ros | aprendido | 2 | 0 | 18 | 10087 | 7 | 0 | 0 | 0 | 0.0006922468 | 18 | 0.1780063 |
| knn_ros | aprendido | 3 | 0 | 16 | 8298 | 7 | 0 | 0 | 0 | 0.01740761 | 16 | 0.1922846 |
| knn_ros | aprendido | 4 | 2 | 39 | 9630 | 6 | 0.04878049 | 0.25 | 0.08163265 | 0.01847717 | 41 | 0.423685 |
| knn_ros | aprendido | 5 | 1 | 4 | 8948 | 7 | 0.2 | 0.125 | 0.1538462 | 0.04490041 | 5 | 0.05580357 |
| knn_ros | fijo_05 | 1 | 2 | 21 | 9208 | 4 | 0.08695652 | 0.3333333 | 0.137931 | 0.02941864 | 23 | 0.2490525 |
| knn_ros | fijo_05 | 2 | 0 | 20 | 10085 | 7 | 0 | 0 | 0 | 0.0006922468 | 20 | 0.1977848 |
| knn_ros | fijo_05 | 3 | 0 | 18 | 8296 | 7 | 0 | 0 | 0 | 0.01740761 | 18 | 0.2163202 |
| knn_ros | fijo_05 | 4 | 2 | 34 | 9635 | 6 | 0.05555556 | 0.25 | 0.09090909 | 0.01847717 | 36 | 0.3720161 |
| knn_ros | fijo_05 | 5 | 1 | 6 | 8946 | 7 | 0.1428571 | 0.125 | 0.1333333 | 0.04490041 | 7 | 0.078125 |
| selector_conjunto | aprendido | 1 | 1 | 10 | 9219 | 5 | 0.09090909 | 0.1666667 | 0.1176471 | 0.01949788 | 11 | 0.1191121 |
| selector_conjunto | aprendido | 2 | 0 | 18 | 10087 | 7 | 0 | 0 | 0 | 0.0006922468 | 18 | 0.1780063 |
| selector_conjunto | aprendido | 3 | 0 | 1 | 8313 | 7 | 0 | 0 | 0 | 0.01740761 | 1 | 0.01201779 |
| selector_conjunto | aprendido | 4 | 2 | 39 | 9630 | 6 | 0.04878049 | 0.25 | 0.08163265 | 0.01847717 | 41 | 0.423685 |
| selector_conjunto | aprendido | 5 | 1 | 4 | 8948 | 7 | 0.2 | 0.125 | 0.1538462 | 0.04490041 | 5 | 0.05580357 |
| selector_conjunto | fijo_05 | 1 | 2 | 137 | 9092 | 4 | 0.01438849 | 0.3333333 | 0.02758621 | 0.01949788 | 139 | 1.505143 |
| selector_conjunto | fijo_05 | 2 | 0 | 20 | 10085 | 7 | 0 | 0 | 0 | 0.0006922468 | 20 | 0.1977848 |
| selector_conjunto | fijo_05 | 3 | 0 | 1 | 8313 | 7 | 0 | 0 | 0 | 0.01740761 | 1 | 0.01201779 |
| selector_conjunto | fijo_05 | 4 | 2 | 34 | 9635 | 6 | 0.05555556 | 0.25 | 0.09090909 | 0.01847717 | 36 | 0.3720161 |
| selector_conjunto | fijo_05 | 5 | 1 | 6 | 8946 | 7 | 0.1428571 | 0.125 | 0.1333333 | 0.04490041 | 7 | 0.078125 |

### Media no ponderada y DE descriptiva

| modelo | regla | precision_mean | precision_std | recall_mean | recall_std | f1_mean | f1_std | average_precision_mean | average_precision_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arbol_baseline | aprendido | 0.07502304 | 0.09125029 | 0.08333333 | 0.0779512 | 0.06824671 | 0.0725951 | 0.01995478 | 0.01857976 |
| arbol_baseline | fijo_05 | 0.0852381 | 0.109192 | 0.08333333 | 0.0779512 | 0.07111111 | 0.07641666 | 0.01995478 | 0.01857976 |
| arbol_ponderado | aprendido | 0.1060606 | 0.116381 | 0.1333333 | 0.154223 | 0.1152587 | 0.1299511 | 0.04460523 | 0.0553159 |
| arbol_ponderado | fijo_05 | 0.01318397 | 0.006187166 | 0.2488095 | 0.1066789 | 0.02502131 | 0.01165692 | 0.04460523 | 0.0553159 |
| gnb_baseline | aprendido | 0.0008086567 | 0.0001949082 | 0.875 | 0.2165064 | 0.001615773 | 0.0003893509 | 0.0008825675 | 0.0001242506 |
| gnb_baseline | fijo_05 | 0.0008515544 | 0.0001862955 | 0.875 | 0.2165064 | 0.001701431 | 0.0003722209 | 0.0008825675 | 0.0001242506 |
| gnb_ponderado | aprendido | 0.0008086567 | 0.0001949082 | 0.875 | 0.2165064 | 0.001615773 | 0.0003893509 | 0.0008825675 | 0.0001242506 |
| gnb_ponderado | fijo_05 | 0.0008515544 | 0.0001862955 | 0.875 | 0.2165064 | 0.001701431 | 0.0003722209 | 0.0008825675 | 0.0001242506 |
| knn_baseline | aprendido | 0.04974331 | 0.0630168 | 0.1666667 | 0.1559024 | 0.07073498 | 0.07880659 | 0.05544582 | 0.04294646 |
| knn_baseline | fijo_05 | 0 | 0 | 0 | 0 | 0 | 0 | 0.05544582 | 0.04294646 |
| knn_ros | aprendido | 0.0635492 | 0.08207203 | 0.1416667 | 0.1490712 | 0.0699529 | 0.06878719 | 0.02217922 | 0.01633115 |
| knn_ros | fijo_05 | 0.05707384 | 0.06076368 | 0.1416667 | 0.1490712 | 0.07243469 | 0.06861721 | 0.02217922 | 0.01633115 |
| selector_conjunto | aprendido | 0.06793792 | 0.08301536 | 0.1083333 | 0.1086534 | 0.07062517 | 0.06934296 | 0.02019506 | 0.01582657 |
| selector_conjunto | fijo_05 | 0.04256024 | 0.06050773 | 0.1416667 | 0.1490712 | 0.05036573 | 0.05941319 | 0.02019506 | 0.01582657 |

La media por fold no pondera por eventos; las métricas globales agrupan todos los eventos. DE utiliza ddof=1. No son intervalos de confianza: los conjuntos de entrenamiento se solapan. El selector omite todos los ATO de los folds 2 y 3; su resultado agregado no oculta esos ceros.

## 8. Métricas por usuario y errores

Un usuario ATO es detectado cuando al menos uno de sus **eventos ATO** genera alerta. Omitido significa que ninguno de sus ATO se detecta, aunque pudiera tener una alerta falsa en otro evento. Usuarios sin ATO con alerta se refiere a usuarios cuyos eventos son todos negativos. Usuarios con FP incluye también usuarios ATO que sufren falsas alarmas en eventos negativos; son conceptos diferentes.

| modelo | regla | usuarios | usuarios_ato | usuarios_ato_detectados | usuarios_ato_omitidos | usuarios_sin_ato_con_alerta | usuarios_con_fp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| arbol_baseline | aprendido | 1600 | 34 | 3 | 31 | 18 | 31 |
| arbol_baseline | fijo_05 | 1600 | 34 | 3 | 31 | 17 | 29 |
| arbol_ponderado | aprendido | 1600 | 34 | 5 | 29 | 21 | 33 |
| arbol_ponderado | fijo_05 | 1600 | 34 | 9 | 25 | 618 | 641 |
| gnb_baseline | aprendido | 1600 | 34 | 30 | 4 | 1357 | 1390 |
| gnb_baseline | fijo_05 | 1600 | 34 | 30 | 4 | 1306 | 1339 |
| gnb_ponderado | aprendido | 1600 | 34 | 30 | 4 | 1357 | 1390 |
| gnb_ponderado | fijo_05 | 1600 | 34 | 30 | 4 | 1306 | 1339 |
| knn_baseline | aprendido | 1600 | 34 | 6 | 28 | 37 | 52 |
| knn_baseline | fijo_05 | 1600 | 34 | 0 | 34 | 0 | 1 |
| knn_ros | aprendido | 1600 | 34 | 5 | 29 | 24 | 39 |
| knn_ros | fijo_05 | 1600 | 34 | 5 | 29 | 20 | 35 |
| selector_conjunto | aprendido | 1600 | 34 | 4 | 30 | 16 | 27 |
| selector_conjunto | fijo_05 | 1600 | 34 | 5 | 29 | 139 | 153 |

Los detalles de FP/FN por evento, usuario, fold, variante y regla están en `errores_externos.csv`. Predicciones completas permiten reconstruir cualquier confusión sin volver a entrenar. Los IDs se conservan como enteros; no se agregan métricas de usuario a los conteos de eventos.

## 9. Estabilidad e interpretación de las seis variantes

| modelo | umbral_min | umbral_max | umbral_media | umbral_de | umbrales_distintos | veces_seleccionado |
| --- | --- | --- | --- | --- | --- | --- |
| arbol_baseline | 0.25 | 0.5 | 0.35 | 0.1369306 | 2 | 0 |
| arbol_ponderado | 0.9975535 | 1 | 0.9984608 | 0.001107323 | 5 | 1 |
| gnb_baseline | 0 | 0.5 | 0.4 | 0.2236068 | 2 | 0 |
| gnb_ponderado | 0 | 0.5 | 0.4 | 0.2236068 | 2 | 0 |
| knn_baseline | 0.2 | 0.4 | 0.24 | 0.08944272 | 2 | 1 |
| knn_ros | 0.4 | 0.8 | 0.64 | 0.219089 | 2 | 3 |

- **Árbol baseline:** 0,25 en tres folds y 0,5 en dos. Conserva 3 TP externos, con 64 FP frente a 61 a 0,5; no hay beneficio global en detección.
- **Árbol ponderado:** umbrales próximos a 1, incluido 1 en un fold. Reduce FP de 675 a 54, pero TP cae de 9 a 5. F1 externo mayor no lo convierte retrospectivamente en ganador independiente del selector. Pequeñas diferencias numéricas de umbral pueden atravesar bloques grandes de scores de hojas.
- **GaussianNB baseline y ponderado:** ambos eligen todos en el fold 2 y 0,5 en los restantes. Esa política maximiza F1 interno en ese fold, aunque su valor absoluto sea muy bajo. En el exterior añade falsas alarmas sin aumentar los 31 TP agregados. Las dos variantes siguen visibles; no se corrige una decisión válida por ser desfavorable. Es evidencia de las limitaciones de optimizar F1 bajo scores poco discriminativos, no un fallo de la regla.
- **KNN baseline:** elige 0,2 en cuatro folds y 0,4 en uno. Obtiene 6 TP y 122 FP; la referencia 0,5 tiene cero TP y un FP. No se conserva un 0,4 universal por el buen aspecto de su exploración anterior.
- **KNN + ROS:** umbrales 0,4 u 0,8. Se elige en tres folds, pero su resultado global con umbral aprendido es 5 TP y 104 FP, frente a 5 TP y 99 FP a 0,5. Ser seleccionado más veces no demuestra superioridad.

El selector mejora F1 frente a su propia referencia 0,5 (0,07143 vs 0,04184), reduce FP (72 vs 198) y pierde una detección (4 vs 5). Es un compromiso observado, no una mejora universal ni evidencia de un coste FP/FN que el usuario no haya fijado. No se utilizaron estos resultados para cambiar variantes, criterios o umbrales.

## 10. Coste, contratos y reproducibilidad

Tiempo de ejecución registrado para la fase experimental: 87.92 s, con 120 ajustes y escritura de artefactos; excluye pruebas, gráficos y elaboración de este informe. RSS máximo muestreado al cerrar folds: 256.39 MiB, no un pico continuo medido. Dos hilos, lotes de predicción de 512 y working_memory=256 MiB.

| modelo | nivel | preprocesamiento_s | ros_s | entrenamiento_s | prediccion_s |
| --- | --- | --- | --- | --- | --- |
| arbol_baseline | externo | 0.3455026 | 0.0274883 | 1.296818 | 0.013968 |
| arbol_baseline | interno | 0.8562929 | 0.0948492 | 1.644991 | 0.0447544 |
| arbol_ponderado | externo | 0.3932895 | 0.030274 | 0.4777415 | 0.0172696 |
| arbol_ponderado | interno | 0.8945236 | 0.0962502 | 0.6820939 | 0.0484231 |
| gnb_baseline | externo | 0.343959 | 0.028342 | 0.1807305 | 0.0474972 |
| gnb_baseline | interno | 0.9184549 | 0.0992124 | 0.3037113 | 0.1842609 |
| gnb_ponderado | externo | 0.3645594 | 0.0263454 | 0.2679498 | 0.046111 |
| gnb_ponderado | interno | 0.9057583 | 0.1022859 | 0.4531724 | 0.1701666 |
| knn_baseline | externo | 0.4602983 | 0.0319363 | 0.0395562 | 5.961807 |
| knn_baseline | interno | 0.9509667 | 0.0980521 | 0.047957 | 16.76106 |
| knn_ros | externo | 0.3906612 | 0.592757 | 0.0700672 | 11.00976 |
| knn_ros | interno | 0.9260674 | 0.9757017 | 0.0907178 | 27.7845 |

Versiones: `{"python": "3.12.7", "numpy": "2.3.4", "pandas": "2.3.3", "sklearn": "1.7.2", "imblearn": "0.14.2"}`. La reproducción exige estas versiones, datos y orden de filas; tiempos no deterministas. No se guardó un modelo final entrenado con todo train.

Arquitectura en `fase04_modelado/validacion_anidada/`: `particiones.py`, `oof_internas.py`, `seleccion_umbral.py`, `seleccion_variante.py`, `ajuste.py`, `ejecutar.py`, `evaluacion.py`, `diagnosticos.py`, `auditoria.py`, `graficas.py`, `informe.py` y `verificar_entrega.py`. Clases AjustadorVariante y ExportadorFiguras separan responsabilidades; funciones snake_case. Se reutiliza código histórico en lectura, sin refactorización general.

Orden para reproducir en un destino nuevo: `python -B -m fase04_modelado.validacion_anidada.ejecutar`, luego módulos `evaluacion`, `diagnosticos`, `graficas`, pruebas y `informe`. Las rutas actuales rechazan sobrescritura. No borrar artefactos históricos para repetir una ejecución. Test permanece bloqueado.

## 11. Pruebas y auditoría de entrega

Resultado real final: **20/20 pruebas aprobadas en 12,28 segundos**. La primera pasada, anterior a añadir las comprobaciones gráficas, aprobó 18/18 en 12,69 segundos. No hubo fallos ni se repitió el experimento completo.

El registro real está en `fase04_modelado/validacion_anidada/resultados/pruebas.txt`. Comando: `python -B -m pytest -p no:cacheprovider -q fase04_modelado/validacion_anidada/tests`.

Se comprueban separación en ambos niveles, reproducción de particiones, cobertura interna/externa, correspondencia de claves y etiquetas, predictores permitidos, estadísticas de preprocesamiento local, índices de ajuste, ROS local, pesos locales, reglas >=, desempates, métricas sin alertas, invariancia de selección al alterar etiquetas externas manteniendo splits, integridad histórica, bloqueo efectivo de aperturas de test y gráficos PNG/SVG. La prueba de invariancia usa un doble determinista de ajuste para aislar la frontera de selección; los artefactos reales se verifican por separado. Cada ejecución de pruebas realiza seis ajustes pequeños, uno por variante: se ejecutaron dos pasadas, doce ajustes pequeños en total, distintos de los 120 experimentales; ninguno usa todo train ni test.

La verificación independiente de los registros se apoya en hashes, reconstrucción de índices y estadísticas; no constituye una auditoría de un tercero. La capa de integridad no toca test, ni siquiera sus metadatos. Los intentos de apertura en la prueba de bloqueo se rechazan antes del acceso al archivo.

## 12. Figuras y archivos

13 figuras, cada una PNG a 300 DPI y SVG. Siete figuras contienen las 14 matrices absolutas de seis variantes y selector frente a la referencia. Se conservan curvas/visualizaciones históricas sin sobrescribirlas.

- [01_metricas_globales · PNG](fase04_modelado/validacion_anidada/resultados/graficas/01_metricas_globales.png) / [SVG](fase04_modelado/validacion_anidada/resultados/graficas/01_metricas_globales.svg): Precision, recall y F1. Selector a 0,5 usa las mismas variantes seleccionadas con umbral aprendido.
- [02_confusion_arbol_baseline · PNG](fase04_modelado/validacion_anidada/resultados/graficas/02_confusion_arbol_baseline.png) / [SVG](fase04_modelado/validacion_anidada/resultados/graficas/02_confusion_arbol_baseline.svg): Confusiones absolutas: umbral aprendido y referencia; filas reales, columnas predichas.
- [02_confusion_arbol_ponderado · PNG](fase04_modelado/validacion_anidada/resultados/graficas/02_confusion_arbol_ponderado.png) / [SVG](fase04_modelado/validacion_anidada/resultados/graficas/02_confusion_arbol_ponderado.svg): Confusiones absolutas: umbral aprendido y referencia; filas reales, columnas predichas.
- [02_confusion_gnb_baseline · PNG](fase04_modelado/validacion_anidada/resultados/graficas/02_confusion_gnb_baseline.png) / [SVG](fase04_modelado/validacion_anidada/resultados/graficas/02_confusion_gnb_baseline.svg): Confusiones absolutas: umbral aprendido y referencia; filas reales, columnas predichas.
- [02_confusion_gnb_ponderado · PNG](fase04_modelado/validacion_anidada/resultados/graficas/02_confusion_gnb_ponderado.png) / [SVG](fase04_modelado/validacion_anidada/resultados/graficas/02_confusion_gnb_ponderado.svg): Confusiones absolutas: umbral aprendido y referencia; filas reales, columnas predichas.
- [02_confusion_knn_baseline · PNG](fase04_modelado/validacion_anidada/resultados/graficas/02_confusion_knn_baseline.png) / [SVG](fase04_modelado/validacion_anidada/resultados/graficas/02_confusion_knn_baseline.svg): Confusiones absolutas: umbral aprendido y referencia; filas reales, columnas predichas.
- [02_confusion_knn_ros · PNG](fase04_modelado/validacion_anidada/resultados/graficas/02_confusion_knn_ros.png) / [SVG](fase04_modelado/validacion_anidada/resultados/graficas/02_confusion_knn_ros.svg): Confusiones absolutas: umbral aprendido y referencia; filas reales, columnas predichas.
- [02_confusion_selector_conjunto · PNG](fase04_modelado/validacion_anidada/resultados/graficas/02_confusion_selector_conjunto.png) / [SVG](fase04_modelado/validacion_anidada/resultados/graficas/02_confusion_selector_conjunto.svg): Confusiones absolutas: umbral aprendido y referencia; filas reales, columnas predichas.
- [03_umbrales · PNG](fase04_modelado/validacion_anidada/resultados/graficas/03_umbrales.png) / [SVG](fase04_modelado/validacion_anidada/resultados/graficas/03_umbrales.svg): Umbrales de las seis variantes por fold. Diferencias pequeñas en árboles no implican decisiones similares.
- [04_selector · PNG](fase04_modelado/validacion_anidada/resultados/graficas/04_selector.png) / [SVG](fase04_modelado/validacion_anidada/resultados/graficas/04_selector.svg): Frecuencia de selección interna y F1 externo; no selecciona retrospectivamente un ganador.
- [05_variabilidad · PNG](fase04_modelado/validacion_anidada/resultados/graficas/05_variabilidad.png) / [SVG](fase04_modelado/validacion_anidada/resultados/graficas/05_variabilidad.svg): Cinco métricas por variante, regla y selector. AP del selector conserva su significado local por fold.
- [06_usuarios · PNG](fase04_modelado/validacion_anidada/resultados/graficas/06_usuarios.png) / [SVG](fase04_modelado/validacion_anidada/resultados/graficas/06_usuarios.svg): Usuarios positivos detectados/omitidos y usuarios completamente negativos con alertas; no confundir con eventos.
- [07_conteos · PNG](fase04_modelado/validacion_anidada/resultados/graficas/07_conteos.png) / [SVG](fase04_modelado/validacion_anidada/resultados/graficas/07_conteos.svg): TP/FP/FN por variante y selector, sin ocultar falsas alarmas de GaussianNB.

Artefactos en `fase04_modelado/validacion_anidada/resultados/`: configuración congelada; particiones y distribución; cinco OOF internas y tablas de candidatos; cinco decisiones congeladas; predicciones externas completas y selector; auditoría de 120 ajustes; métricas globales/por fold y resumen; errores; estabilidad y transferencia; tiempos; comparación de referencia CV2; catálogo de figuras; pruebas y manifiesto final. Los hashes de fuentes permitidas anteriores están en `inventario_previo.json`; los de entregables en `manifiesto_entrega.json`.

## 13. Limitaciones y cierre

Solo 36 ATO de 34 usuarios: un acierto cambia recall global 2,78 puntos porcentuales. La estratificación mejora soporte por fold, no crea evidencia independiente. Eventos de un usuario pueden estar correlacionados; los folds de ajuste se solapan. Tres folds internos dejan unos 18–19 usuarios positivos por ajuste interno. El umbral optimizado en OOF de modelos pequeños puede comportarse distinto al reajustar; el resultado externo incluye ese efecto y la variabilidad poblacional.

Los datos y resultados CV1/CV2 ya habían sido explorados. Este procedimiento congelado reduce fuga directa de la selección interna, pero no borra la adaptación histórica del diseño. F1 fue una decisión académica autorizada, no una equivalencia económica FP/FN ni una garantía de alta detección. La muestra y geografía sintéticas, seis predictores limitados y ausencia de validación temporal restringen extrapolación.

No se elige retrospectivamente al árbol ponderado por su F1 externo ni a KNN+ROS por frecuencia de selección. El resultado del selector es la evidencia del procedimiento autorizado y su cobertura de ATO es baja. El dictamen es **selección inestable y evidencia insuficiente para declarar un ganador definitivo o un umbral universal**. Una siguiente decisión necesita valorar este compromiso y la suficiencia estadística; no se añade una nueva optimización silenciosa.

KMeans y Ward permanecen documentados por separado en [INFORME_CLUSTERING_FASE04.md](INFORME_CLUSTERING_FASE04.md). No participan en selección supervisada ni se convierten en etiquetas de ataque. Se conserva la entrega académica de cinco algoritmos y todas las variantes de CV1/CV2.

**Test permaneció cerrado. No se entrenó un modelo final con todo train, no hubo operaciones Git ni cambios históricos. Fase 4 no está terminada.**
