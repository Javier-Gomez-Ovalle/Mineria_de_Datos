# Evaluación final única de test — Fase 4

Fecha/hora de ejecución: 2026-11-22T02:06:13.836864-05:00 a 2026-11-22T02:06:14.843995-05:00 (America/Bogota, UTC−05:00).

## Objetivo, autorización y dictamen

Evaluación independiente del procedimiento congelado referencia_arbol_ponderado_v1, autorizada expresamente por el adjunto 50422d45-422d-4786-9fba-2671a6d18e57. Se realizó una única lectura física del CSV, una carga desde memoria, una transformación y **una llamada predict_proba sobre los 11.115 eventos completos**. Cero fit, fit_transform, selección de umbral o comparaciones con otros algoritmos.

El modelo detectó 1 de nueve ATO y omitió 8; generó 12 falsas alarmas. Detectó 1 de nueve usuarios positivos. La precision fue 0.076923 y el recall 0.111111. Hubo detección de ATO en esta partición, cuyo alcance debe valorarse junto con las omisiones y falsas alarmas, sin extrapolar aptitud productiva.

Se aceptan estos resultados como definitivos de esta evaluación del proyecto. No se modifica ningún elemento ni se repetirá la evaluación. No se presenta el modelo como listo para producción.

## Entradas e integridad

Ruta exacta test: dataset_test_fase04.csv, identificada en INFORME_PARTICION_FASE04.md. SHA-256 `90c50ab404c3fcef6cc33e59387aec4ac405f41200e6aa61c0f8bf1db43c72fa`. El archivo se leyó una sola vez como bytes para verificar hash antes de analizar su contenido; el parseo posterior se hizo desde esos mismos bytes, sin reabrirlo.

Directorio de referencia: fase04_modelado/recuperacion_referencia_v1_20261122/.

| Artefacto | SHA-256 verificado |
|---|---|
| modelo_final.joblib | d23a2a0f93d64682931608829a030e9615be43990e4ae43d99262b5a9254ff5e |
| preprocesador_final.joblib | 01fbfd1f162dda4c7e31946da3e4cc19e87d9badfac235d662345369096168c6 |
| umbral_definitivo.json | e5327bd50594edd9d1c67e5076bd53f101c9194b068911e8faf16567f7109095 |
| MANIFIESTO_MODELO_FINAL.json | 4772485050832583db357e376e094c88b807345315abfe31895bc5a9b6730297 |

El hash del manifiesto se contrastó con VERIFICACION_MANIFIESTO.json. Se verificaron identidad, parámetros completos, versiones y seis predictores contra la evidencia congelada. Modelo Gini/best, class_weight=balanced, semilla 42, sin nuevos parámetros. Parámetros y versiones completos en AUDITORIA_EVALUACION_TEST.json.

## Contratos e inferencia

Se confirmaron 11.115 filas y 35 columnas en el orden del esquema train, 400 usuarios, nueve ATO y nueve usuarios positivos. Clave User ID + Login Timestamp + IP Address única/no nula, target binario/no nulo e intersección de usuarios train/test cero. No se exportaron IP ni User ID.

Seis predictores en orden: failed_attempts_15min, failed_attempts_1h, time_since_previous_login_hours, has_previous_login, Device Type, Country. Se aplicó la normalización de entrada aprobada y únicamente transform del preprocesador recuperado: medianas aprendidas, indicador intacto y One-Hot aprendido con desconocidas ignoradas. Matriz finita 11.115×62. No se ajustaron vocabularios ni imputadores. El score es predict_proba de clase 1 y y_pred=(score >= 0.9976439543869569). Modelo y preprocesador conservaron su estado en memoria y sus hashes en disco.

## Matriz de confusión y métricas por evento

| Real / predicción | No ATO | ATO |
|---|---:|---:|
| No ATO | 11094 | 12 |
| ATO | 8 | 1 |

| Métrica | Valor |
|---|---:|
| TP | 1 |
| FP | 12 |
| TN | 11094 |
| FN | 8 |
| precision | 0.07692307692307693 |
| recall | 0.1111111111111111 |
| f1 | 0.09090909090909091 |
| average_precision | 0.00926675663517769 |
| roc_auc | 0.5490775756848151 |
| f2 | 0.10204081632653061 |
| especificidad | 0.9989195029713668 |
| FPR | 0.0010804970286331713 |
| alertas | 13 |

Funciones sklearn.metrics: confusion_matrix(labels=[0,1]); precision_score, recall_score y f1_score con zero_division=0; average_precision_score(y,score) y roc_auc_score(y,score), sin binarizar scores para estas dos últimas. Precision=TP/(TP+FP), Recall=TP/(TP+FN), F1=2TP/(2TP+FP+FN); denominador cero se representa como 0. F2=5TP/(5TP+4FN+FP), especificidad=TN/(TN+FP), FPR=FP/(FP+TN). No se utiliza accuracy como criterio principal.

Se emitieron 13 alertas, de las cuales 12 fueron falsas y 1 verdaderas. La proporción de alertas verdaderas es 0.076923 (si no hubiera alertas, Precision=0 por convención no implicaría una proporción empírica estimable).

AP mide ranking con las probabilidades originales, no éxito de la regla de clasificación. ROC-AUC es calculable porque hay ambas clases, pero abundantes negativos y solo nueve positivos pueden ocultar el problema de falsas alarmas; no sustituye Precision/Recall/AP ni demuestra utilidad operativa. No se ensayan otros umbrales para reinterpretar el resultado.

## Métricas por usuario

| Conteo | Valor |
|---|---:|
| usuarios_totales | 400 |
| usuarios_con_ato | 9 |
| usuarios_ato_detectados | 1 |
| usuarios_ato_omitidos | 8 |
| usuarios_sin_ato_con_alerta_falsa | 6 |
| usuarios_con_algun_fp | 7 |
| usuarios_con_ato_y_algun_fp | 1 |
| usuarios_sin_ato_y_algun_fp | 6 |

Un usuario ATO se considera detectado únicamente si al menos un evento ATO suyo fue correctamente alertado. Una falsa alarma en otro login no lo convierte en detectado. Los usuarios con FP se separan entre cuentas que tuvieron ATO y cuentas sin ATO. Son conteos de personas/cuentas distintas, no número de eventos.

## Comparación histórica, sin mezclar evidencias

| Métrica | Anidada histórica externa, train | OOF para seleccionar t, train | Test independiente, único |
|---|---:|---:|---:|
| TP | 5 | 8 | 1 |
| FP | 54 | 48 | 12 |
| TN | 46215 | 46221 | 11094 |
| FN | 31 | 28 | 8 |
| f1 | 0.1052631578947368 | 0.17391304347826086 | 0.09090909090909091 |

La anidada histórica tuvo Precision 0.08474576 y Recall 0.13888889; en test son 0.07692308 y 0.11111111. Se trata de poblaciones de tamaño distinto, distintos estimadores y umbrales históricos por fold frente a un único modelo/umbral final. No se suman matrices ni se atribuye causalidad a las diferencias. El resultado test muestra recall menor y F1 menor que esos valores históricos; con nueve ATO no demuestra una diferencia estable de rendimiento.

El F1 0.17391304347826086 de OOF se usó para elegir el umbral: no es una estimación independiente, ni un resultado de test, ni evidencia adicional de generalización. El modelo final se entrenó con todo train y la transferencia del umbral desde tres estimadores OOF no garantizaba equivalencia de probabilidades. No se ajustó esa transferencia con test.

## Interpretación académica y limitaciones

Cada uno de los nueve ATO representa 1/9 de los positivos: un solo acierto cambia recall en aproximadamente 11,11 puntos porcentuales. Hay nueve usuarios positivos, por lo que pocos casos condicionan mucho las métricas. Los eventos de un usuario no son independientes; el resultado describe esta partición por usuarios y no garantiza rendimiento temporal futuro.

La comparación académica permite justificar la referencia por F1 anidado histórico, no una superioridad universal. Esta prueba independiente complementa la historia sin borrar el carácter retrospectivo de la elección de familia. El escaso soporte positivo, limitaciones de representación y falta de criterio operativo de costes impiden acreditar producción, tanto si el resultado es favorable como si es desfavorable. Un resultado adverso no autoriza ajustes y uno favorable no demuestra robustez.

## Auditoría, entregables y cierre de evaluación

Se verificó integridad de 542 archivos históricos permitidos antes/después, incluidos modelo, preprocesador y umbral. No se reabrió test para un segundo hash: se conserva la huella de los bytes exactos analizados. Sin incidencias ni discrepancias. No se realizaron operaciones Git, instalaciones, modificaciones de Fase 3 ni escrituras en datasets/históricos.

PREDICCIONES_TEST.csv conserva solo evento_id (posición original base cero), probabilidad_positiva, prediccion y etiqueta_real. No incluye IP ni identificadores de usuario. AUDITORIA_EVALUACION_TEST.json guarda contratos, parámetros, métricas, contadores y versiones. MANIFIESTO_EVALUACION_TEST.json registra hashes de entradas y salidas. Los marcadores exclusivos impiden volver a ejecutar este script sobre el destino; la guardia impide una segunda apertura del test durante el proceso. fit/fit_transform quedaron bloqueados.

**La evaluación única queda cerrada.** Se detiene el trabajo sin nuevos ajustes, análisis exploratorios, predicciones o evaluaciones. Los resultados se aceptan para el proyecto; esta conclusión no certifica aptitud productiva.
