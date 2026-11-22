# Metodología y resultados

## CRISP-DM

Comprensión del negocio: estudiar ATO en un escenario académico. Comprensión de datos: eventos RBA sintetizados y atributos simulados. Preparación (Fase 3): selección de usuarios, enriquecimiento IP y empleados, features históricas y corrección de asociación del target. Modelado (Fase 4): comparar protocolos y algoritmos; evaluación histórica final separada. No se certifica despliegue ni utilidad productiva.

## Integridad y partición

El informe de corrección acredita 57.420 eventos, 35 columnas, 2.000 usuarios y 45 ATO en 43 usuarios. Se corrigieron 90 etiquetas; no se recalcularon features. La clave es User ID + Login Timestamp + IP Address. La partición por usuario usa estratificación por presencia de ATO y semilla 42: train 46.305 eventos/1.600 usuarios/36 ATO; test 11.115/400/9. Son cifras de informes, no cálculos de esta entrega.

## Variables y preprocesamiento

Predictores: failed_attempts_15min, failed_attempts_1h, time_since_previous_login_hours, has_previous_login, Device Type y Country. Target e identificadores no entran al modelo. Se excluyen resultado actual del login, Is Attack IP sin contrato temporal, atributos aleatorios de empleados y señales de desplazamiento cuya geografía no respalda una interpretación física.

Medianas y One-Hot se ajustan dentro de cada subtrain; desconocidos se ignoran en el codificador. Árboles: sin escalado ni log. GaussianNB: log1p tras imputación. KNN/clustering: log1p y StandardScaler. ROS solamente en el subtrain transformado de la variante KNN. El modelo final tiene 62 entradas transformadas. Historial previo disponible es un supuesto; la partición por usuarios no es validación temporal.

## Comparación preservada

CV1 agrupa por usuario con StratifiedGroupKFold sobre eventos. CV2 estratifica una tabla de usuarios con StratifiedKFold y expande a eventos; no cambia algoritmos para favorecer resultados. Se conservan Árbol baseline/ponderado, GaussianNB baseline/ponderado y KNN baseline/ROS. Validación anidada selecciona variantes y umbrales internamente. Random Forest ponderado se documenta como extensión controlada, no se oculta. KMeans y Ward exploran estructura sin entrenarse con ATO; evaluación externa de clusters no los convierte en clasificadores.

Consultar [informe final](../INFORME_FINAL_FASE04_CRISP_DM.md), [comparación](../INFORME_COMPARATIVO_ALGORITMOS_FASE04.md), [CV1](../INFORME_MODELADO_SUPERVISADO_FASE04.md), [CV2](../INFORME_SEGUNDA_VALIDACION_FASE04.md), [anidada](../INFORME_VALIDACION_ANIDADA_FASE04.md) y [clustering](../INFORME_CLUSTERING_FASE04.md). Contienen tablas de todas las variantes, matrices y referencias a gráficas conservadas en sus rutas originales.

## Referencia y evaluación histórica

Árbol Gini/best, class_weight=balanced, random_state=42, sin poda; parámetros completos en el manifiesto recuperado. Umbral 0.9976439543869569 elegido con OOF de tres modelos. F1 de selección 0.17391304347826086, TP=8, FP=48, TN=46221, FN=28. No es rendimiento independiente. La escala de probabilidades puede cambiar al reajustar con todo train.

El test se evaluó una vez anteriormente: TP=1, FP=12, TN=11094, FN=8; Precision=0.07692307692307693, Recall=0.1111111111111111, F1=0.09090909090909091, AP=0.00926675663517769. Fuente: [informe final de test](../fase04_modelado/evaluacion_final_test_20261122/INFORME_EVALUACION_FINAL_TEST_FASE04.md). No se volvió a evaluar ni se incluyen sus predicciones individuales.

## Limitaciones

Solo 34 usuarios positivos en train y nueve en test; inestabilidad entre folds, muestra enriquecida, dependencia entre eventos, exploración previa y geografía sintetizada limitan generalización. AP global OOF concatena scores de distintos estimadores. El bajo recall final y las falsas alarmas impiden presentar esta referencia como detector listo para producción. El resultado negativo también es evidencia académica.
