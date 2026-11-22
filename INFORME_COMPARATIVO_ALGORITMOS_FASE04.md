# Comparación consolidada de algoritmos y justificación de la referencia — Fase 4

Fecha: 2026-11-22. Consolidación documental de resultados existentes; sin entrenamiento, predicción, particiones nuevas ni recálculo de métricas.

## 1. Objetivo y conclusión principal

El árbol ponderado es la **mejor referencia relativa por F1 externo agregado en la validación anidada histórica**, entre las variantes y la extensión Random Forest evaluadas. Esta afirmación tiene un criterio y un protocolo precisos: no significa que haya ganado CV1, CV2 o todas las métricas, ni que constituya un detector satisfactorio.

Su resultado anidado fue 5 TP, 54 FP, 46.215 TN y 31 FN; Precision 0,084746, Recall 0,138889 y F1 0,105263. La elección como referencia académica responde retrospectivamente a esa comparación. La selección conjunta interna histórica no eligió siempre ese árbol y no constituye prueba independiente de la elección posterior.

El aporte académico es explicar por qué los métodos producen compromisos diferentes y por qué se fija una referencia reproducible, incluso cuando el desempeño absoluto resulta limitado. No se necesita presentar un éxito operativo inexistente.

## 2. Datos, desbalance y significado de las medidas

Los informes registran 57.420 eventos y 2.000 usuarios en el dataset corregido de Fase 3, con 45 ATO de 43 usuarios. La comparación utiliza exclusivamente train: **46.305 eventos, 1.600 usuarios, 36 ATO y 34 usuarios positivos**, con prevalencia documentada 0,07775%. Estas cifras se toman de los informes; no se abrió test ni se obtuvieron cifras nuevas de él.

Se mantienen seis predictores: Device Type, Country, failed_attempts_15min, failed_attempts_1h, time_since_previous_login_hours y has_previous_login. User ID solo sirve para separar y auditar usuarios; target e identificadores no son predictores.

TP representa un ATO alertado; FN, un ATO omitido. FP es un login legítimo alertado y TN, un negativo sin alerta. Precision describe qué proporción de alertas es ATO; Recall, qué proporción de ATO se recupera. F1 equilibra ambas medidas, pero no expresa automáticamente costes de investigación o daño de una omisión. AP resume el ranking de scores: puede resultar relativamente alta aunque el umbral operativo detecte pocos ATO. No se usa accuracy como criterio principal.

En las métricas por usuario, «usuario ATO detectado» exige al menos un **evento ATO correctamente alertado** de ese usuario. Una falsa alarma en otro login suyo no basta. «Usuarios sin ATO con alerta» excluye usuarios positivos, mientras que «usuarios con FP» también incluye positivos que tuvieron falsos avisos. Son unidades diferentes de los eventos.

El diagnóstico documentó ocho positivos con entradas idénticas a las de 621 negativos, redundancia de los contadores y pocos sujetos positivos. Esto limita la separación con esta representación; no prueba que todo algoritmo posible deba fallar.

## 3. Algoritmos y tratamiento del desbalance

| Variante | Configuración y representación histórica | Hipótesis y limitación relevante |
|---|---|---|
| Árbol baseline | DecisionTreeClassifier, Gini, splitter best, semilla 42, sin poda/límite de profundidad; mediana numérica y One-Hot | Aprende interacciones y reglas no lineales; un árbol puede memorizar patrones raros e inestables. |
| Árbol ponderado | Mismo árbol, class_weight=balanced calculado en el ajuste local | Da más peso a errores minoritarios; puede producir muchas alertas a 0,5. Ponderar no garantiza probabilidades calibradas. |
| GaussianNB baseline | var_smoothing=1e-9; mediana, log1p de numéricas, indicador y One-Hot | Modelo probabilístico sencillo; supuestos gaussianos e independencia condicional pueden ser poco adecuados para entradas mixtas y correlacionadas. Es una explicación plausible, no una causa demostrada experimentalmente. |
| GaussianNB ponderado | Misma representación y var_smoothing; sample_weight balanced local | Cambia influencia de clases; en estos resultados no mejoró las métricas agregadas frente al baseline. |
| KNN baseline | k=5, pesos uniformes, distancia euclídea, brute, n_jobs=2; numéricas imputadas, log1p y StandardScaler, indicador y One-Hot | Ranking por proximidad; clase minoritaria muy escasa y mezcla de distancias continuas/categóricas. |
| KNN + ROS | Mismo KNN; RandomOverSampler, sampling_strategy=1, semilla 42, solo sobre subtrain transformado | Repite ejemplos minoritarios; cambia vecindarios, pero no aporta usuarios positivos nuevos ni garantiza generalización. |
| Random Forest ponderado | 100 árboles, bootstrap, balanced_subsample, max_features=sqrt, semilla 42, n_jobs=2; representación de árboles | Promedia árboles y contrasta regularización. Mejor ranking observado no garantizó transferencia de umbral. |

Las transformaciones se reajustaron dentro de los subtrain de cada experimento. No se reutilizaron matrices ajustadas con todo train para validación. No se reincorporaron Login Successful actual, inteligencia IP de disponibilidad temporal incierta, Impossible Travel ni atributos simulados. No se modificó ninguna exclusión en esta consolidación.

## 4. Protocolos: qué resultados se pueden comparar

| Etapa | Diseño y regla | Interpretación correcta |
|---|---|---|
| CV1 | Cinco folds StratifiedGroupKFold, estratificación por evento con grupos de usuario; semilla 42; umbral 0,5 | Primera comparación. Usuarios positivos por fold: 9, 8, 1, 8, 8; eventos ATO: 10, 8, 1, 8, 9. |
| CV2 | Cinco folds StratifiedKFold sobre tabla de usuarios con/sin ATO, expansión a eventos; semilla 42; umbral 0,5 | Sensibilidad al reparto de usuarios. Usuarios positivos: 6, 7, 7, 7, 7; eventos ATO: 6, 7, 7, 8, 8. |
| Exploración de umbrales | Análisis retrospectivo de scores OOF CV1/CV2 ya disponibles | Describe compromisos de alertas, no valida independientemente un umbral elegido en esas mismas OOF. |
| Validación anidada histórica | Cinco folds externos por usuario y tres internos; F1 OOF interno elige umbral por variante; selector interno entre seis variantes | Evalúa transferencia a usuarios externos a cada ajuste. La variante fija y el selector conjunto son procedimientos distintos. |
| Extensión Random Forest | Mismos externos e internos congelados; cuatro configuraciones y umbral seleccionados internamente | Comparación apareada descriptiva con históricos reutilizados; mayor espacio de búsqueda del bosque y exploración adaptativa. |
| Ejecución de referencia | Familia árbol ponderado ya fijada; tres folds internos sobre todo train para elegir un único umbral | F1 de **selección**, no nueva evaluación anidada externa ni test. |
| Recuperación técnica | Repetición exclusiva del ajuste final y serialización | No aporta nuevas métricas de generalización ni cambia el umbral. |

CV1 y CV2 reutilizan train: no son réplicas independientes. Tampoco son independientes la anidada y su extensión. No se interpreta una diferencia entre protocolos como mejora causal del algoritmo.

Las tablas siguientes transcriben métricas guardadas con seis decimales de presentación. AP es **Average Precision**, no un área trapezoidal recalculada. Las métricas globales concatenadas no equivalen a medias por fold.

## 5. CV1: umbral fijo 0,5

Fuente: [comparacion_modelos.csv de CV1](fase04_modelado/resultados/comparacion_modelos.csv).

| modelo | TP | FP | TN | FN | precision | recall | f1 | average_precision |
|---|---|---|---|---|---|---|---|---|
| arbol_baseline | 6 | 55 | 46214 | 30 | 0.098361 | 0.166667 | 0.123711 | 0.019447 |
| arbol_ponderado | 8 | 556 | 45713 | 28 | 0.014184 | 0.222222 | 0.026667 | 0.016017 |
| gnb_baseline | 31 | 36476 | 9793 | 5 | 0.000849 | 0.861111 | 0.001697 | 0.000839 |
| gnb_ponderado | 31 | 36476 | 9793 | 5 | 0.000849 | 0.861111 | 0.001697 | 0.000839 |
| knn_baseline | 0 | 5 | 46264 | 36 | 0 | 0 | 0 | 0.049479 |
| knn_ros | 6 | 93 | 46176 | 30 | 0.060606 | 0.166667 | 0.088889 | 0.019844 |


Árbol baseline tuvo el mayor F1 y Precision de esta tabla: seis ATO detectados con 55 falsas alarmas. Árbol ponderado detectó ocho, pero con 556 FP, deteriorando mucho Precision y F1. Por tanto, no es correcto afirmar que ponderar ya había ganado en CV1.

GaussianNB recuperó 31 ATO con 36.476 FP. KNN baseline tuvo la AP más alta pero cero TP al umbral fijo. KNN+ROS obtuvo seis aciertos con 93 FP. La distribución con un solo ATO en un fold motivó la segunda validación; no se cambió semilla para buscar un resultado favorable.

## 6. CV2: mismo umbral, otra distribución de usuarios

Fuente: [comparacion_modelos.csv de CV2](fase04_modelado/resultados_cv_usuario/comparacion_modelos.csv).

| modelo | TP | FP | TN | FN | precision | recall | f1 | average_precision |
|---|---|---|---|---|---|---|---|---|
| arbol_baseline | 3 | 61 | 46208 | 33 | 0.046875 | 0.083333 | 0.060000 | 0.008862 |
| arbol_ponderado | 9 | 675 | 45594 | 27 | 0.013158 | 0.250000 | 0.025000 | 0.015817 |
| gnb_baseline | 31 | 36447 | 9822 | 5 | 0.000850 | 0.861111 | 0.001698 | 0.000840 |
| gnb_ponderado | 31 | 36447 | 9822 | 5 | 0.000850 | 0.861111 | 0.001698 | 0.000840 |
| knn_baseline | 0 | 1 | 46268 | 36 | 0 | 0 | 0 | 0.043163 |
| knn_ros | 5 | 99 | 46170 | 31 | 0.048077 | 0.138889 | 0.071429 | 0.012462 |


Árbol baseline perdió aciertos respecto a CV1; KNN+ROS tuvo el mayor F1 a 0,5 en CV2. El árbol ponderado recuperó nueve ATO a costa de 675 FP. GaussianNB siguió con alto recall y enorme carga de alertas. KNN baseline mantuvo una AP relativamente interesante, sin ningún TP a 0,5.

El mayor equilibrio relativo de una variante depende del protocolo y de la regla de decisión. Estas tablas contradicen una proclamación de ganador universal, pero no invalidan una referencia posterior con otro criterio explícito.

## 7. Exploración de umbrales: utilidad y límite

Fuente: [umbrales_globales.csv](fase04_modelado/seleccion_supervisada/resultados/umbrales_globales.csv). Extracto ya calculado para ilustrar KNN baseline:

| protocolo | umbral | modelo | TP | FP | TN | FN | precision | recall | f1 | average_precision |
|---|---|---|---|---|---|---|---|---|---|---|
| CV1 | 0.200000 | knn_baseline | 11 | 134 | 46135 | 25 | 0.075862 | 0.305556 | 0.121547 | 0.049479 |
| CV1 | 0.400000 | knn_baseline | 4 | 9 | 46260 | 32 | 0.307692 | 0.111111 | 0.163265 | 0.049479 |
| CV2 | 0.200000 | knn_baseline | 8 | 153 | 46116 | 28 | 0.049689 | 0.222222 | 0.081218 | 0.043163 |
| CV2 | 0.400000 | knn_baseline | 4 | 8 | 46261 | 32 | 0.333333 | 0.111111 | 0.166667 | 0.043163 |


Reducir el umbral permite recuperar ATO y eleva falsas alarmas. A 0,4 se observaban cuatro aciertos con pocos FP en ambos protocolos, pero seguían omitiéndose 32 ATO. A 0,2 aumentaba recuperación y carga de revisión. Esto justificó estudiar transferencia mediante selección interna; **no justificó adoptar un umbral después de mirar resultados externos**.

Las tablas completas de todas las variantes se conservan en la carpeta de selección supervisada, junto con métricas por fold, distribuciones de scores y errores. No se ocultaron reglas desfavorables. El umbral actualmente congelado del árbol no procede de elegir retrospectivamente una fila favorable de esas tablas.

## 8. Validación anidada y extensión: clasificación externa

Fuentes primarias: [metricas_globales.csv anidada](fase04_modelado/validacion_anidada/resultados/metricas_globales.csv) y [comparacion_global.csv de la extensión](fase04_modelado/mejora_controlada/resultados/comparacion_global.csv). Se comprobó concordancia de las seis variantes entre ambas tablas guardadas, sin recalcular métricas.

Las seis primeras filas son la anidada histórica; Random Forest es la extensión sobre las mismas particiones. Los selectores se muestran como procedimientos adicionales, no como algoritmos nuevos.

| modelo | TP | FP | TN | FN | precision | recall | f1 | average_precision |
|---|---|---|---|---|---|---|---|---|
| arbol_baseline | 3 | 64 | 46205 | 33 | 0.044776 | 0.083333 | 0.058252 | 0.008862 |
| arbol_ponderado | 5 | 54 | 46215 | 31 | 0.084746 | 0.138889 | 0.105263 | 0.015817 |
| gnb_baseline | 31 | 38839 | 7430 | 5 | 0.000798 | 0.861111 | 0.001594 | 0.000840 |
| gnb_ponderado | 31 | 38839 | 7430 | 5 | 0.000798 | 0.861111 | 0.001594 | 0.000840 |
| knn_baseline | 6 | 122 | 46147 | 30 | 0.046875 | 0.166667 | 0.073171 | 0.043163 |
| knn_ros | 5 | 104 | 46165 | 31 | 0.045872 | 0.138889 | 0.068966 | 0.012462 |
| random_forest | 4 | 158 | 46111 | 32 | 0.024691 | 0.111111 | 0.040404 | 0.060211 |
| selector_historico | 4 | 72 | 46197 | 32 | 0.052632 | 0.111111 | 0.071429 | — |
| selector_ampliado | 4 | 158 | 46111 | 32 | 0.024691 | 0.111111 | 0.040404 | — |


El árbol ponderado tiene F1 0,105263, superior al de las otras variantes aquí. Frente a KNN+ROS mantiene cinco aciertos con menos FP (54 frente a 104). Frente a KNN baseline sacrifica un acierto (cinco frente a seis) y produce menos falsas alarmas (54 frente a 122). Frente al árbol baseline recupera más ATO y produce menos FP. Esos compromisos explican su mayor F1 **en esta tabla**.

GaussianNB consigue mucho mayor recall, pero 38.839 FP impiden interpretarlo como mejor equilibrio por F1. Random Forest detecta cuatro con 158 FP; su AP mayor no se traduce en mejor clasificación en la regla elegida.

El selector histórico obtuvo cuatro TP y 72 FP. Eligió árbol ponderado solo en el fold 1, KNN+ROS en 2, 4 y 5, y KNN baseline en 3. Por ello, **el árbol ponderado no fue el ganador estable de la selección interna conjunta**. Fijarlo después por F1 externo agregado es una decisión académica retrospectiva, que se reconoce expresamente.

### 8.1. Usuarios: alcance real de las alertas

Todos los procedimientos se refieren a los mismos 34 usuarios ATO y 1.600 usuarios de train, con predicciones externas correspondientes.

| modelo | usuarios_ato_detectados | usuarios_ato_omitidos | usuarios_sin_ato_con_alerta | usuarios_con_fp |
|---|---|---|---|---|
| arbol_baseline | 3 | 31 | 18 | 31 |
| arbol_ponderado | 5 | 29 | 21 | 33 |
| gnb_baseline | 30 | 4 | 1357 | 1390 |
| gnb_ponderado | 30 | 4 | 1357 | 1390 |
| knn_baseline | 6 | 28 | 37 | 52 |
| knn_ros | 5 | 29 | 24 | 39 |
| random_forest | 4 | 30 | 126 | 140 |
| selector_historico | 4 | 30 | 16 | 27 |
| selector_ampliado | 4 | 30 | 126 | 140 |


El árbol ponderado detectó cinco usuarios ATO y omitió 29; alertó a 21 usuarios sin ATO. Los 33 usuarios con FP incluyen también usuarios positivos. GaussianNB detectó 30 usuarios ATO, pero alertó a 1.357 usuarios sin ATO. Random Forest detectó cuatro y alertó a 126 usuarios sin ATO.

La evaluación por usuario refuerza que un F1 relativamente mayor no significa cobertura suficiente de cuentas comprometidas. Los eventos de un mismo usuario no son observaciones independientes y los usuarios activos pesan más en las métricas por evento.

### 8.2. Estabilidad y AP por fold

Fuente: [resumen_folds.csv](fase04_modelado/mejora_controlada/resultados/resumen_folds.csv). Son medias y desviaciones estándar **ya guardadas**, diferentes de los valores globales anteriores.

| modelo | precision_mean | precision_std | recall_mean | recall_std | f1_mean | f1_std | average_precision_mean | average_precision_std |
|---|---|---|---|---|---|---|---|---|
| arbol_baseline | 0.075023 | 0.091250 | 0.083333 | 0.077951 | 0.068247 | 0.072595 | 0.019955 | 0.018580 |
| arbol_ponderado | 0.106061 | 0.116381 | 0.133333 | 0.154223 | 0.115259 | 0.129951 | 0.044605 | 0.055316 |
| gnb_baseline | 0.000809 | 0.000195 | 0.875000 | 0.216506 | 0.001616 | 0.000389 | 0.000883 | 0.000124 |
| gnb_ponderado | 0.000809 | 0.000195 | 0.875000 | 0.216506 | 0.001616 | 0.000389 | 0.000883 | 0.000124 |
| knn_baseline | 0.049743 | 0.063017 | 0.166667 | 0.155902 | 0.070735 | 0.078807 | 0.055446 | 0.042946 |
| knn_ros | 0.063549 | 0.082072 | 0.141667 | 0.149071 | 0.069953 | 0.068787 | 0.022179 | 0.016331 |
| random_forest | 0.121471 | 0.137083 | 0.111905 | 0.064851 | 0.098333 | 0.089400 | 0.098581 | 0.065488 |
| selector_ampliado | 0.121471 | 0.137083 | 0.111905 | 0.064851 | 0.098333 | 0.089400 | 0.098581 | 0.065488 |
| selector_historico | 0.067938 | 0.083015 | 0.108333 | 0.108653 | 0.070625 | 0.069343 | 0.020195 | 0.015827 |


Para el árbol ponderado, F1 agregado 0,105263 no equivale a media por fold 0,115259; su desviación 0,129951 evidencia variabilidad importante. Detalle histórico:

| fold_externo | TP | FP | FN | f1 |
|---|---|---|---|---|
| 1 | 1 | 10 | 5 | 0.117647 |
| 2 | 0 | 20 | 7 | 0 |
| 3 | 0 | 11 | 7 | 0 |
| 4 | 3 | 8 | 5 | 0.315789 |
| 5 | 1 | 5 | 7 | 0.142857 |


Los folds 2 y 3 no recuperaron ATO; el fold 4 aportó tres de los cinco aciertos. Por tanto, no puede defenderse estabilidad fuerte. GaussianNB tiene baja desviación absoluta de F1 alrededor de un valor casi nulo: ser estable en una métrica mala no convierte el método en útil.

AP global concatena scores de diferentes estimadores de folds, que pueden no estar en una escala comparable. AP media calcula primero dentro de cada fold. Ninguna sustituye a la otra. Para los selectores se omite AP global porque pueden mezclar familias; su AP por fold se refiere a la familia elegida en ese fold.

## 9. Random Forest: búsqueda limitada y resultado reportado

La configuración común fue 100 árboles, balanced_subsample, bootstrap=True, max_features=sqrt, random_state=42 y n_jobs=2. Las cuatro configuraciones, en orden fijo, fueron:
- 0: max_depth=8, min_samples_leaf=1.
- 1: max_depth=8, min_samples_leaf=10.
- 2: max_depth=None, min_samples_leaf=1.
- 3: max_depth=None, min_samples_leaf=10.

Dentro de cada externo se eligieron configuración y umbral por F1 OOF interno. Se aplicó desempate de umbral por cercanía a 0,5 y luego mayor; empate de configuración por orden fijo. El resultado agregado **no corresponde a una configuración única de bosque elegida en todo train**.

Fuente: [transferencia_seleccion.csv](fase04_modelado/mejora_controlada/resultados/transferencia_seleccion.csv).

| fold | configuracion | max_depth | min_samples_leaf | umbral | f1_interno | f1_externo | selector |
|---|---|---|---|---|---|---|---|
| 1 | 2 | — | 1 | 0.609263 | 0.140351 | 0.166667 | random_forest |
| 2 | 0 | 8 | 1 | 0.658715 | 0.156863 | 0 | random_forest |
| 3 | 1 | 8 | 10 | 0.840798 | 0.210526 | 0.200000 | random_forest |
| 4 | 0 | 8 | 1 | 0.674168 | 0.226415 | 0.013889 | random_forest |
| 5 | 3 | — | 10 | 0.818964 | 0.181818 | 0.111111 | random_forest |


El experimento ejecutó históricamente 60 ajustes internos y cinco externos; los seis modelos anteriores se reutilizaron desde artefactos verificados. El selector ampliado eligió bosque internamente en los cinco folds y terminó coincidiendo con sus predicciones externas.

Referencia de umbral fijo frente al aprendido, conservada sin seleccionar una regla nueva:

| regla | modelo | TP | FP | TN | FN | precision | recall | f1 | average_precision |
|---|---|---|---|---|---|---|---|---|---|
| aprendido | random_forest | 4 | 158 | 46111 | 32 | 0.024691 | 0.111111 | 0.040404 | 0.060211 |
| fijo_05 | random_forest | 16 | 1474 | 44795 | 20 | 0.010738 | 0.444444 | 0.020970 | 0.060211 |


Con 0,5 aumenta la recuperación, pero también los FP. Con umbral aprendido, el bosque tiene AP concatenada 0,060211 y AP media 0,098581, pero solo cuatro TP. El fold 4 concentra 135 FP y F1 0,013889; su F1 interno había sido 0,226415. Es evidencia de transferencia frágil.

No se atribuye superioridad estadística al ranking del bosque. Tuvo más flexibilidad de búsqueda y se propuso después de analizar el mismo train; los folds compartidos permiten comparar descriptivamente, no convierten la extensión en una validación independiente.

## 10. Balance individual de fortalezas y debilidades

**Árbol baseline.** Fue una referencia inicial razonable por el compromiso observado en CV1. La caída de aciertos en CV2 y los tres TP anidados muestran sensibilidad a usuarios. Su resultado inicial no sostiene una selección estable para la referencia final.

**Árbol ponderado.** Ponderar recupera más positivos a 0,5, pero multiplica falsas alarmas en CV1/CV2. La selección interna de umbral reduce FP en la anidada y consigue el mayor F1 agregado relativo. Su principal fortaleza comparativa es ese compromiso; sus debilidades son baja recuperación, omisiones de usuarios e inestabilidad. No se atribuye una mejora al peso de clases de forma aislada: también interviene la regla de decisión.

**GaussianNB baseline.** Alta recuperación, pero miles de alertas legítimas. Para ATO, revisar prácticamente una gran parte de los logins destruye el valor de priorización. El patrón observado y sus supuestos sugieren dificultades de representación; no se ha demostrado causalmente cuál supuesto explica el fallo.

**GaussianNB ponderado.** Las métricas agregadas coinciden con el baseline en estas etapas. Eso muestra falta de beneficio observado de la ponderación en esta configuración, no equivalencia universal de ambos métodos ni una garantía sobre cualquier dataset.

**KNN baseline.** Ofrece ranking relativo destacable en CV1/CV2 y anidada, pero a 0,5 no recupera ATO. La selección interna rescata seis aciertos con 122 FP, con F1 menor que el árbol ponderado. Es un ejemplo claro de que AP y clasificación a umbral responden preguntas distintas.

**KNN con ROS.** Puede aumentar recuperación frente al baseline a 0,5 y fue el mejor F1 de CV2 a ese umbral. No conserva ventaja en la regla anidada aprendida: cinco TP y 104 FP. Sobremuestrear exclusivamente subtrain respeta validación, pero duplicar positivos no crea diversidad de usuarios ni elimina el solapamiento.

**Random Forest ponderado.** Agregación y regularización fueron una alternativa técnicamente motivada. Mejoró AP descriptiva, pero no el equilibrio TP/FP con umbral transferido, y mostró una concentración de errores en un fold. Su no elección como referencia se debe a ese resultado, no a que un bosque sea inherentemente inadecuado para ATO.

En ninguno de los casos «no seleccionado» significa algoritmo inútil en general. Significa menor adecuación al criterio académico definido en estos experimentos.

## 11. Justificación de la referencia y límites de la elección

La justificación defendible es: **“Se fijó el árbol ponderado como referencia académica porque obtuvo el mayor F1 externo agregado entre las variantes comparadas en la validación anidada histórica con umbrales aprendidos internamente. Su reducción relativa de falsas alarmas compensó, según F1, la baja recuperación. La elección es retrospectiva y no prueba superioridad general.”**

No es defendible afirmar que ganó todos los protocolos, que tuvo mayor recall o AP, que fue elegido consistentemente por el selector conjunto, o que puede desplegarse como detector satisfactorio. Tampoco debe sumarse evidencia de CV1/CV2/anidada como si fueran muestras independientes.

No se impone un nuevo criterio de aceptación operativa. F1 permite una referencia académica comparable; no incorpora presupuesto de revisión humana, coste monetario o daño de falsos negativos. La exigencia del curso de explicar resultados queda satisfecha por una conclusión limitada y trazable, sin necesidad de fabricar éxito predictivo.

## 12. Etapa distinta: umbral definitivo y recuperación técnica

Después de fijar la familia, se ejecutaron tres folds internos sobre todo train para obtener el umbral único `0.9976439543869569`. El registro existente conserva F1 de selección `0.17391304347826086`, TP=8, FP=48, TN=46.221 y FN=28; Precision 0,142857 y Recall 0,222222. Son **OOF de selección del umbral**, no los resultados anidados 5/54/46.215/31, ni una mejora externa demostrada.

La familia ya estaba fijada; las mismas OOF eligieron t. Por tanto, F1 0,173913 no es una estimación independiente del rendimiento final. Las probabilidades provienen de tres modelos; el modelo final, ajustado en todo train, no tiene garantizada la misma escala ni calibración.

La primera ejecución falló al serializar `hojas_observadas` como numpy.int64. La recuperación autorizada del 2026-11-22 repitió solo el ajuste final, mantuvo OOF/umbral y convirtió tipos JSON de forma explícita. El modelo y preprocesador recuperados se recargaron con 62 columnas y probabilidades idénticas sobre train, según la evidencia guardada. **Esa equivalencia de serialización no es una evaluación predictiva nueva.**

Estado criptográfico verificado en esta consolidación:

| Artefacto recuperado | SHA-256 |
|---|---|
| modelo_final.joblib | d23a2a0f93d64682931608829a030e9615be43990e4ae43d99262b5a9254ff5e |
| preprocesador_final.joblib | 01fbfd1f162dda4c7e31946da3e4cc19e87d9badfac235d662345369096168c6 |
| umbral_definitivo.json | e5327bd50594edd9d1c67e5076bd53f101c9194b068911e8faf16567f7109095 |

No se cargaron los estimadores para generar predicciones. Se verificaron sus bytes contra el manifiesto.

Los documentos históricos que dicen “modelo pendiente” o “ejecución incompleta” describen el momento anterior a la recuperación; no se corrigieron retrospectivamente. El estado actual es modelo recuperado y congelado, sin evaluación test.

## 13. Limitaciones y datos faltantes

1. Solo 36 ATO de 34 usuarios en train; escaso soporte por fold y alta sensibilidad a pocos aciertos.
2. Dependencia entre eventos del mismo usuario; métricas por evento y por cuenta no son intercambiables.
3. Solapamiento de entradas y representación limitada; las exclusiones temporales/semánticas no se revierten para mejorar números.
4. Investigación repetida sobre el mismo train y elección de familia retrospectiva. No hay prueba de significación ni superioridad universal.
5. Transferencia del umbral desde distintos estimadores OOF al ajuste completo sin calibración garantizada.
6. Las siete variantes no tienen resultados en todos los protocolos: **Random Forest no se evaluó en CV1/CV2**. Se marca por su etapa, no se inventan filas faltantes.
7. Las tablas principales CV1/CV2 no presentan las mismas métricas por usuario que la anidada; aquí se usan las disponibles en la etapa externa anidada/extensión, sin calcular retroactivamente nuevas métricas.
8. No existe evaluación final de test ni criterio operativo de coste/revisión humana. No se pueden concluir eficacia productiva o rendimiento fuera de muestra definitivo.

No se encontró discrepancia numérica material en las seis variantes compartidas por las tablas anidada/extensión. Las diferencias entre protocolos y entre F1 concatenado/media por fold son esperables y se mantienen separadas. La incidencia de JSON está documentada y resuelta en una carpeta posterior, conservando el original parcial.

## 14. Conclusión para sustentación y estado de Fase 4

La comparación permite defender tres conclusiones: ponderación y sobremuestreo cambian el compromiso de alertas sin resolver necesariamente el problema; un ranking relativo mejor no asegura detección útil a un umbral; y la separación por usuario revela inestabilidad que una tabla agregada puede ocultar.

El árbol ponderado es la referencia relativa bajo F1 anidado histórico, con una elección académica explícita y limitada. Detectar cinco usuarios y omitir 29 exige reconocer que no constituye un detector satisfactorio. Esta conclusión negativa en términos operativos es compatible con una investigación académica rigurosa.

El procedimiento y sus artefactos están congelados. El siguiente paso es revisión de esta consolidación y autorización posterior e independiente para evaluar una única vez el test con la configuración y umbral existentes. No se usa test para escoger otra variante o retocar umbral. **Fase 4 continúa abierta.**

## 15. Fuentes consultadas y auditoría de esta intervención

Informes revisados:
- [CV1](INFORME_MODELADO_SUPERVISADO_FASE04.md).
- [CV2](INFORME_SEGUNDA_VALIDACION_FASE04.md).
- [Selección y umbrales](INFORME_SELECCION_SUPERVISADA_FASE04.md).
- [Validación anidada](INFORME_VALIDACION_ANIDADA_FASE04.md).
- [Diagnóstico](INFORME_DIAGNOSTICO_CAPACIDAD_PREDICTIVA_FASE04.md).
- [Decisión tras Random Forest](INFORME_DECISION_MODELO_FASE04.md).
- [Procedimiento congelado](PROCEDIMIENTO_REFERENCIA_CONGELADO_FASE04.md).
- [Ejecución inicial e incidencia](fase04_modelado/ejecucion_referencia_v1/INFORME_EJECUCION_REFERENCIA_FASE04.md).
- [Recuperación técnica](fase04_modelado/recuperacion_referencia_v1_20261122/INFORME_RECUPERACION_TECNICA_FASE04.md).

Tablas consultadas:
- [fase04_modelado/resultados/comparacion_modelos.csv](fase04_modelado/resultados/comparacion_modelos.csv)
- [fase04_modelado/resultados_cv_usuario/comparacion_modelos.csv](fase04_modelado/resultados_cv_usuario/comparacion_modelos.csv)
- [fase04_modelado/validacion_anidada/resultados/metricas_globales.csv](fase04_modelado/validacion_anidada/resultados/metricas_globales.csv)
- [fase04_modelado/mejora_controlada/resultados/comparacion_global.csv](fase04_modelado/mejora_controlada/resultados/comparacion_global.csv)
- [fase04_modelado/mejora_controlada/resultados/resumen_folds.csv](fase04_modelado/mejora_controlada/resultados/resumen_folds.csv)
- [fase04_modelado/mejora_controlada/resultados/transferencia_seleccion.csv](fase04_modelado/mejora_controlada/resultados/transferencia_seleccion.csv)
- [fase04_modelado/seleccion_supervisada/resultados/umbrales_globales.csv](fase04_modelado/seleccion_supervisada/resultados/umbrales_globales.csv)
- [fase04_modelado/validacion_anidada/resultados/metricas_por_fold.csv](fase04_modelado/validacion_anidada/resultados/metricas_por_fold.csv)
- [Configuración RF](fase04_modelado/mejora_controlada/resultados/configuracion_congelada.json).
- [Manifiesto del modelo recuperado](fase04_modelado/recuperacion_referencia_v1_20261122/MANIFIESTO_MODELO_FINAL.json).

Se transcribieron y seleccionaron filas/columnas de tablas existentes; solo se redondeó la presentación. No se calcularon métricas, medias, desviaciones, folds ni predicciones. No se entrenó, evaluó ni deserializó ningún modelo. Test permaneció totalmente cerrado, excluido de hashes e inspección.

Se crean este informe y `AUDITORIA_CONSOLIDACION_FASE04.json`, que registra hashes y verificación de integridad. No se actualiza README ni se modifica archivo previo. Se inventariaron 540 archivos históricos permitidos para verificar igualdad antes/después, incluidos modelo, preprocesador, umbral y evidencia de la incidencia. Sin instalaciones, operaciones Git ni modificaciones de Fase 3.

