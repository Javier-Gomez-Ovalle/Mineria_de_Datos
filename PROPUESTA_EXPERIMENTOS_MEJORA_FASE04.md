# Propuesta congelada: mejora controlada de Fase 4

Fecha: 2026-11-21. Se escribe antes de ejecutar los nuevos ajustes. Solo train; test cerrado.

## Hipótesis y alcance

Un único árbol sin poda puede tener alta varianza con 34 usuarios positivos. Un bosque ponderado puede promediar decisiones y regularizar hojas, sin requerir nuevas variables. Es una oportunidad experimental, no una promesa de mejora. El diagnóstico previo encuentra 8 ATO con vectores idénticos a 621 negativos y redundancia entre contadores (Spearman 0,9051); ningún bosque puede distinguir individualmente eventos con entradas idénticas.

Se probará **una familia nueva, RandomForestClassifier**, con 100 árboles, bootstrap=True, class_weight=balanced_subsample, max_features=sqrt, random_state=42, n_jobs=2. Cuatro configuraciones en este orden fijo: (max_depth=8, min_samples_leaf=1), (8,10), (None,1), (None,10). Los otros parámetros quedan registrados mediante get_params. Profundidad y tamaño de hoja contrastan regularización contra conservación de patrones raros. No se amplía la búsqueda tras observar resultados.

Se mantienen los seis predictores y la representación de árboles aprobada: medianas locales, indicador binario y One-Hot local. No se escalan variables ni se aplica ROS al bosque. Los pesos balanced_subsample se calculan en cada muestra bootstrap del subtrain, nunca sobre validación. La ponderación y ROS históricos no han resuelto por sí solos el problema; no se presupone que el desbalance sea la única causa.

## Diseño y decisiones

Se reutilizan exactamente los cinco folds externos y tres internos por externo del experimento anidado. Se verifican hashes y correspondencia de eventos. Se ejecutan 60 ajustes internos y cinco reajustes externos del bosque seleccionado: **65 ajustes**, sin repetir los 120 históricos. Cada ajuste aprende su propio preprocesamiento. Las OOF internas históricas y decisiones congeladas se reutilizan sin recalcular modelos antiguos.

Dentro de cada externo se elige conjuntamente configuración y umbral del bosque maximizando F1 OOF interno. Candidatos: todos los scores únicos, 0, 0,5 y el siguiente flotante sobre 1. Desempate de umbral: proximidad a 0,5, después mayor; empate de configuración: orden anterior. F1 se compara como fracción exacta. No se calibra.

Se evalúan dos procedimientos: bosque con selección interna propia y selector ampliado de siete familias/variantes (seis históricas más el bosque ajustado). El selector ampliado usa únicamente F1 interno; empate favorece el orden histórico y finalmente bosque. No se selecciona retrospectivamente usando F1 externo. Se conserva también la referencia 0,5 para el bosque. Cada decisión se guarda y verifica antes de predecir su fold externo. No se ajusta modelo final sobre todo train.

## Evaluación, coste y descarte

Comparación apareada descriptiva en los mismos eventos externos: TP/FP/TN/FN, Precision, Recall, F1, F2, especificidad, FPR, AP por fold y su media/desviación, AP concatenada por familia con advertencia sobre escalas, métricas por usuario, costes y distribución de errores. Para selectores de familias distintas no se informa AP global ni curva PR concatenada. F1 es continuidad académica, no coste operativo universal; no existe presupuesto de revisión humana definido.

Coste previsto: 6.500 árboles en 65 ajustes secuenciales, dos hilos por ajuste, matrices locales de aproximadamente 60 columnas y menos de 47.000 filas; minutos, dependiente del equipo. Se registrarán tiempos reales y RSS muestreado (no se confundirá con máximo continuo). No se guardan estimadores finales.

Se descartará la afirmación de mejora si no hay beneficio consistente de recuperación y falsas alarmas entre usuarios/folds, si queda dominado o si depende de pocos aciertos. No se impone una frontera numérica arbitraria de aprobación. Una subida de F1 agregado aislada no basta. Se documentarán resultados negativos sin añadir más algoritmos por ensayo y error.

Riesgos: selección interna con muy pocos positivos, pérdida de patrones raros por regularización, probabilidad sin calibrar por ponderación, sobreajuste de búsqueda, distintas escalas entre folds, e investigación adaptativa tras múltiples análisis del mismo train. CV1, CV2, anidada y esta extensión no son réplicas independientes ni pruebas de superioridad significativa. No habrá pruebas de significación ingenuas con cinco folds solapados.

## Fuentes y reproducibilidad

[Documentación oficial de Random Forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html): bagging de árboles y pesos por bootstrap. La versión instalada y parámetros efectivos se registran, sin actualizar paquetes. La arquitectura nueva separa contratos, ajuste, diagnóstico, evaluación y presentación; reutiliza fábricas sin estado históricas mediante imports de solo lectura. Se prueban separación, ajuste local, selección exacta, correspondencia OOF, reproducibilidad, métricas e integridad. ROS no se aplica en nuevos ajustes; sus resultados históricos quedan referenciados.
