# Diagnóstico de capacidad predictiva — Fase 4

Fecha: 2026-11-21. Solo train. Diagnóstico producido antes de ejecutar el nuevo experimento.

## Auditoría y evidencia

Se inspeccionaron informes de corrección de target, preprocesamiento, Impossible Travel, CV1/CV2, clustering, selección y anidada; fábricas de modelos y transformadores, transporte de target y cálculo temporal. El manifiesto de entrega anidada coincide con sus archivos; el inventario nuevo conserva 406 archivos históricos permitidos. Test se excluye antes de hash/lectura; no se acredita su integridad mediante acceso al contenido. No se repitió reconciliación RBA ni pipelines históricos.

Fase 3 mantiene el target unido al evento y valida mediante User ID + timestamp + IP, detectando cambios de identidad/etiqueta. Rolling closed=left y shift(1) respaldan por inspección estática el uso de historial anterior. Los tests y reconciliación previos son evidencia histórica, no pruebas vueltas a ejecutar aquí. La disponibilidad real del historial en producción sigue siendo un contrato necesario; CV por usuario no demuestra generalización temporal.

La representación aprobada usa medianas locales y One-Hot; GaussianNB añade log1p y KNN log1p/StandardScaler. Árboles sin poda, GaussianNB var_smoothing=1e-9, KNN k=5 uniforme euclídeo. Ponderación/ROS se limitan al ajuste local. CV1 estratifica eventos agrupando usuarios; CV2 y anidada estratifican usuarios positivos. Semilla 42. CV1 tuvo usuarios positivos [9,8,1,8,8]; CV2/anidada [6,7,7,7,7], eventos [6,7,7,8,8]. La anidada registra 120 ajustes y 20 pruebas históricas aprobadas. No hay evidencia de discrepancia entre tabla anidada y resumen del encargo.

## Desbalance y predictores

| eventos | usuarios | ATO | usuarios_ATO | prevalencia | grupos_identicos_mixtos | ATO_en_grupos_mixtos | negativos_en_grupos_mixtos | historicos_verificados |
|---|---|---|---|---|---|---|---|---|
| 46305 | 1600 | 36 | 34 | 0.000777454 | 4 | 8 | 621 | 406 |

32 usuarios tienen un ATO y dos tienen dos: 36 eventos no equivalen a 36 sujetos independientes. Un acierto mueve recall global 2,78 puntos porcentuales y el recall de un fold 12,5–16,7 puntos. La prevalencia es 0,07775%; un clasificador que nunca alerta tendría alta accuracy sin detectar ningún ATO.

Los contadores tienen medianas cero en ambas clases, máximos negativos 20/28 y positivos 3/3; su Spearman es 0,9051. La separación descriptiva numérica es débil y no monotónica. El intervalo anterior tiene 1.600 ausentes estructurales (primer evento), 44.608 valores distintos y cola hasta 8.757 horas; su cardinalidad permite sobreajuste. has_previous_login codifica precisamente esa ausencia, no una observación adicional independiente. Ocho positivos son primer login; 28 tienen historia. Los seis predictores no describen hábitos personalizados de país/dispositivo.

30 positivos usan desktop y seis mobile; 15 están en RO, cinco NO, cuatro IT. País tiene 54 categorías y dispositivo cuatro. Estas diferencias descriptivas pueden explicar parte del ranking, pero no prueban causalidad ni transferencia; categorías con pocos ATO generan estimaciones frágiles. Se exportan distribuciones por clase dentro de cada fold, incluidos ceros/ausentes/extremos, sin elegir variables ni umbrales a partir de ellas.

Cuatro vectores idénticos de seis entradas contienen ocho positivos y 621 negativos. Un predictor determinista basado solo en esas entradas asigna el mismo score a cada grupo. No es un límite superior de generalización ni demuestra imposibilidad universal: evidencia una limitación de representación para esos casos observados.

## Modelos y errores

| modelo | TP | FP | FN | precision | recall | f1 | average_precision |
|---|---|---|---|---|---|---|---|
| arbol_baseline | 3 | 64 | 33 | 0.0447761 | 0.0833333 | 0.0582524 | 0.00886213 |
| arbol_ponderado | 5 | 54 | 31 | 0.0847458 | 0.138889 | 0.105263 | 0.0158173 |
| gnb_baseline | 31 | 38839 | 5 | 0.00079753 | 0.861111 | 0.00159358 | 0.000839775 |
| gnb_ponderado | 31 | 38839 | 5 | 0.00079753 | 0.861111 | 0.00159358 | 0.000839775 |
| knn_baseline | 6 | 122 | 30 | 0.046875 | 0.166667 | 0.0731707 | 0.0431628 |
| knn_ros | 5 | 104 | 31 | 0.0458716 | 0.138889 | 0.0689655 | 0.0124615 |
| selector_conjunto | 4 | 72 | 32 | 0.0526316 | 0.111111 | 0.0714286 | nan |

La AP concatenada por variante no equivale a AP media por fold; el selector no tiene AP global. KNN ofrece ranking relativo interesante, pero pocos aciertos al decidir alertas. GaussianNB produce scores extremos y miles de falsas alarmas; ponderar tampoco resuelve esa limitación. El árbol ponderado mejora F1 agregado respecto a otros, pero no fue seleccionado de forma estable por el procedimiento interno. El clustering segmenta geometría de X; la similitud de prevalencias entre grupos no lo convierte en detector.

Perfil de errores del selector histórico por país (denominadores incluidos):

| modelo | perfil | valor | eventos | ATO | TP | FP | FN | FPR | recall |
|---|---|---|---|---|---|---|---|---|---|
| selector_conjunto | Country | RO | 329 | 15 | 4 | 20 | 11 | 0.0636943 | 0.266667 |
| selector_conjunto | Country | NO | 36532 | 5 | 0 | 8 | 5 | 0.000219016 | 0 |
| selector_conjunto | Country | IT | 90 | 4 | 0 | 4 | 4 | 0.0465116 | 0 |
| selector_conjunto | Country | BR | 930 | 3 | 0 | 37 | 3 | 0.0399137 | 0 |
| selector_conjunto | Country | CA | 41 | 2 | 0 | 1 | 2 | 0.025641 | 0 |
| selector_conjunto | Country | CL | 8 | 2 | 0 | 1 | 2 | 0.166667 | 0 |
| selector_conjunto | Country | CZ | 249 | 2 | 0 | 1 | 2 | 0.00404858 | 0 |
| selector_conjunto | Country | ID | 245 | 2 | 0 | 0 | 2 | 0 | 0 |
| selector_conjunto | Country | MZ | 2 | 1 | 0 | 0 | 1 | 0 | 0 |
| selector_conjunto | Country | AR | 3 | 0 | 0 | 0 | 0 | 0 | nan |

El archivo errores_historicos_por_perfil.csv incluye todos los modelos y selector, usuarios, país, dispositivo, presencia de historia, tramos de actividad y fallos previos. Se incluyen eventos/ATO y FPR/recall por grupo para evitar confundir tamaño con concentración de riesgo. Identificadores se usan solo para auditoría, nunca como predictores. No se construyen reglas para memorizar los errores conocidos.

## Exclusiones y temporalidad

| Variables | Decisión y requisito pendiente |
|---|---|
| Login Successful / login_exitoso_normalizado | Resultado del intento actual: no disponible en el escenario preautenticación. Solo reconsiderable cambiando explícitamente el escenario. Fallos de intentos anteriores sí son historial. |
| Is Attack IP | Sin fecha de disponibilidad de inteligencia por evento; no se demuestra conocimiento contemporáneo. Mantener fuera. |
| Region / City / enriquecimiento IP | Geografía sintética y asociaciones no verificadas; enriquecimiento externo sin contrato temporal fiable. No reincorporar por asociación con y. |
| distance_previous_km / required_speed_kmh / impossible_travel | Cero mezcla ausencia de evaluación y normalidad; centroides incompletos y geografía no física. Informe previo: 5.662 evaluables, 40.643 no evaluables (39.043 centroides y 1.600 sin anterior), nueve alertas según regla existente. travel_evaluable corregiría representación, no fiabilidad. |
| Turnos, residencia, empleados | Atributos simulados sin evidencia observada/temporal por usuario. No inferir causalidad de relaciones artificiales. |

[La documentación primaria de RBA](https://github.com/das-group/rba-dataset) describe datos sintetizados y limitaciones geográficas. No se reabre el RBA original. Ninguna variable excluida reúne nueva evidencia suficiente para reintroducirla en esta intervención.

## Diagnóstico y oportunidad

No puede atribuirse causalmente el bajo rendimiento a un único factor: pocos positivos, solapamiento, representación limitada y supuestos de los modelos confluyen. El fracaso parcial de pesos/ROS contradice que solo baste equilibrar clases. No se demuestra que todo algoritmo posible vaya a fallar.

Se justifica un único contraste: bosque ponderado con búsqueda pequeña de regularización interna, para probar si promediar árboles reduce inestabilidad. No se justifica una batería abierta de algoritmos ni rescatar señales de semántica dudosa. Diseño y criterios congelados en PROPUESTA_EXPERIMENTOS_MEJORA_FASE04.md. El análisis repetido del mismo train aumenta el riesgo de adaptación; los resultados nuevos serán exploratorios y no una validación externa independiente.

## Archivos y limitaciones

Tablas completas en fase04_modelado/mejora_controlada/resultados/: diagnostico.json, distribuciones_numericas.csv, distribuciones_categoricas.csv (fold=0 global, 1–5 externo), correlaciones_spearman.csv, perfiles_identicos_clases_mixtas.csv, distribucion_usuarios_train.csv y errores_historicos_por_perfil.csv. No se afirma haber comprobado causalidad ni disponibilidad operacional por ejecutar tests. La auditoría de código es estática salvo los contratos explícitamente comprobados con datos y hashes.
