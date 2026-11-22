# Informe final de Fase 4 — CRISP-DM · Proyecto ATO

Fecha de consolidación: 22 de noviembre de 2026. Alcance: cierre documental de la Fase 4. La fase experimental y la evaluación única de test están cerradas. No se certifica que estén satisfechos requisitos adicionales del profesor que no se hayan verificado.

## 1. Introducción

La Fase 4 buscó comparar algoritmos para estudiar la detección de Account Takeover (ATO): eventos en los que una cuenta es utilizada por alguien que ha tomado su control. En este proyecto la etiqueta procede del dataset RBA; no se interpreta cualquier login anómalo o fallido como ATO.

Se siguieron dos enfoques. Los modelos supervisados aprendieron a relacionar características del acceso con la etiqueta conocida. KMeans y clustering jerárquico exploraron grupos de comportamiento sin utilizar ATO para construirlos. La pregunta era si esas representaciones permitían distinguir compromisos de cuenta y qué limitaciones aparecían.

El objetivo fue académico: comparar, validar por usuarios, justificar decisiones y evaluar una referencia congelada en una partición reservada. No se desarrolló ni certificó una solución productiva antifraude. El resultado incluye tanto los aciertos como las omisiones y falsas alarmas.

## 2. Preparación de los datos para modelado

### 2.1. Calidad y corrección del target

La fuente de modelado fue `dataset_final_modelo_corregido.csv`. El [informe de Fase 3](INFORME_CORRECCION_TARGET_FASE03.md) documenta que el código anterior separaba el target y lo reincorporaba por índices después de ordenar/reiniciar filas. Esa operación desasoció etiquetas de eventos.

La corrección mantuvo el target asociado al evento y validó la clave User ID + Login Timestamp + IP Address. La reconciliación previa comprobó las 57.420 etiquetas frente al RBA: cambiaron exactamente 90 etiquetas respecto al enriquecido anterior y las otras 34 columnas permanecieron iguales. En este cierre no se repitió esa reconciliación ni se modificó Fase 3.

### 2.2. Poblaciones y partición

Cifras documentadas en [INFORME_PARTICION_FASE04.md](INFORME_PARTICION_FASE04.md) y confirmadas para test por su auditoría final:

| Población | Eventos | Usuarios | Eventos ATO | Usuarios ATO | Eventos negativos |
|---|---:|---:|---:|---:|---:|
| Total corregido | 57.420 | 2.000 | 45 | 43 | 57.375 |
| Train | 46.305 | 1.600 | 36 | 34 | 46.269 |
| Test | 11.115 | 400 | 9 | 9 | 11.106 |

La división 80/20 se hizo sobre usuarios, estratificando por si cada usuario tenía al menos un ATO, con semilla 42. Todos los eventos de un usuario quedaron en una sola partición; se verificó intersección cero. Por eso el reparto de eventos no es exactamente 80/20. El fuerte desbalance —prevalencia train documentada de 0,077745 %— hace poco informativa la accuracy: acertar muchos negativos no implica detectar ATO.

Test se reservó durante exploración y selección. Fue abierto solo en la evaluación final expresamente autorizada. Este cierre utiliza exclusivamente su informe, auditoría y manifiesto; no vuelve a consultar el CSV ni las predicciones de test.

### 2.3. Predictores y exclusiones

Las seis entradas aprobadas fueron:
- Device Type y Country: contexto nominal del intento.
- failed_attempts_15min y failed_attempts_1h: fallos explícitos anteriores en esas ventanas.
- time_since_previous_login_hours: intervalo desde el login previo.
- has_previous_login: indicador de existencia de historial.

El escenario es puntuar el intento antes de conocer su resultado, con historial anterior disponible. User ID sirve para agrupar y trazar eventos, no para predecir. Country se conserva como contexto sintético nominal, no como coordenada física fiable.

| Exclusión | Justificación documentada |
|---|---|
| User ID, IP Address y Login Timestamp absolutos | Trazabilidad y riesgo de memorizar identidades; no son predictores aprobados. |
| Login Successful y login_exitoso_normalizado actuales | Resultado del intento no disponible en el escenario preautenticación. Los fallos de intentos anteriores sí son historial. |
| Is Attack IP | No se acreditó cuándo estaba disponible la inteligencia por evento. Se excluyó por incertidumbre temporal, no por fuga demostrada. |
| Region, City y enriquecimiento IP | Geografía sintetizada, granularidad poco fiable y fuentes sin contrato temporal suficiente. |
| ASN y derivados nominales de red | Alta cardinalidad, contexto artificial/redundante; no deben tratarse como magnitudes continuas. |
| distance_previous_km, required_speed_kmh e impossible_travel | Evaluabilidad incompleta, ceros ambiguos y geografía no fiable para desplazamiento físico. |
| Empleados, turnos, residencia y atributos asociados | Asignaciones simuladas, sin evidencia conductual real suficiente. |

La [revisión Impossible Travel](INFORME_REVISION_IMPOSSIBLE_TRAVEL_FASE04.md) distinguió una representación corregible de una medición geográfica no validada. No se reintrodujeron esas variables para obtener mejores métricas.

### 2.4. Preprocesamiento por familia

| Familia | Numéricas | Binaria | Categóricas |
|---|---|---|---|
| Árbol y Random Forest | Imputación por mediana; sin log1p ni escalado | Sin transformación | Imputación Desconocido y One-Hot |
| GaussianNB | Mediana seguida de log1p | Sin transformación | Imputación Desconocido y One-Hot |
| KNN y clustering | Mediana, log1p y StandardScaler | Sin transformación | Imputación Desconocido y One-Hot |

En validación supervisada, medianas, escalas y vocabularios se ajustaron solo con el subtrain. ROS se limitó al subtrain transformado de KNN. No se reutilizaron transformadores ajustados en todo train dentro de los folds. El vocabulario completo de train produce 62 columnas: tres numéricas, una binaria, cuatro dispositivos y 54 países; los folds pueden tener menos categorías.

El clustering ajustó su representación en train completo para descripción no supervisada. Eso no equivale a validación predictiva externa. Fuente: [preprocesamiento](INFORME_PREPROCESAMIENTO_FASE04.md).

## 3. Modelado supervisado

**Árbol baseline.** Divide sucesivamente los datos mediante reglas. Se esperaba capturar interacciones sin exigir relaciones lineales. Fue una referencia sencilla y obtuvo el mejor F1 a 0,5 en CV1, pero su recuperación cayó en CV2 y la anidada. Un árbol sin poda puede aprender particularidades de pocos positivos; los resultados muestran sensibilidad, no una causalidad demostrada del sobreajuste.

**Árbol ponderado.** Es el mismo árbol, dando más peso a la clase rara mediante class_weight=balanced. Se esperaba evitar que los negativos dominaran el ajuste. A 0,5 recuperó más ATO con muchas más falsas alarmas. Con umbrales elegidos internamente tuvo el mejor F1 agregado de la comparación anidada, aunque detectó pocos usuarios positivos.

**GaussianNB baseline.** Combina evidencias probabilísticas de las variables con supuestos de distribución e independencia condicional. Es sencillo y podía servir de contraste a los árboles. Recuperó muchos ATO, pero generó decenas de miles de FP. Sus supuestos pueden ser poco adecuados para entradas mixtas y correlacionadas; esa explicación es plausible, no una causa aislada demostrada.

**GaussianNB ponderado.** Aumentó la influencia de positivos mediante sample_weight balanced local. Sus métricas agregadas coincidieron con el baseline en los protocolos reportados. La ponderación no aportó beneficio observable en esta configuración, sin que eso permita afirmar equivalencia universal de ambos métodos.

**KNN baseline.** Clasifica según cinco vecinos próximos, con pesos uniformes y distancia euclídea. Podía reconocer similitudes locales, pero la escasez de positivos y la mezcla de distancias son limitaciones. Mostró ranking relativamente interesante por AP, aunque a 0,5 no detectó ATO en CV1/CV2. Cambiar la regla altera la cantidad de alertas, no garantiza transferencia.

**KNN con RandomOverSampler.** Repitió ejemplos positivos solo en el subtrain para influir en los vecindarios. Mejoró detección frente al baseline a 0,5 y tuvo mayor F1 en CV2. En anidada no superó al árbol ponderado: obtuvo cinco TP con 104 FP. Duplicar ejemplos no crea nuevos usuarios positivos ni elimina solapamiento.

**Random Forest ponderado.** Promedia árboles entrenados sobre muestras bootstrap. Se esperaba reducir la variabilidad de un árbol individual. Se evaluaron 100 árboles, balanced_subsample, max_features=sqrt, semilla 42 y cuatro combinaciones de max_depth={8,None} y min_samples_leaf={1,10}. Configuración y umbral se eligieron solo dentro de los folds internos. Mejoró AP descriptiva, pero no el equilibrio de alertas con el umbral transferido.

Los parámetros y configuraciones completas se preservan en [la comparación consolidada](INFORME_COMPARATIVO_ALGORITMOS_FASE04.md) y sus fuentes. No se ejecutó ningún modelo en esta intervención documental.

## 4. Comparación de algoritmos

Las tablas transcriben resultados existentes, redondeados a seis decimales para lectura. TP/FP/TN/FN son conteos de eventos. AP es Average Precision de scores sin aplicar umbral. No se recalcularon medidas.

### 4.1. CV1: cinco folds agrupados por usuario, umbral 0,5

CV1 utilizó StratifiedGroupKFold con estratificación por evento y agrupación de usuarios, semilla 42. La distribución de usuarios positivos fue 9, 8, 1, 8, 8; la de eventos positivos, 10, 8, 1, 8, 9.

| modelo | TP | FP | TN | FN | precision | recall | f1 | average_precision |
|---|---|---|---|---|---|---|---|---|
| arbol_baseline | 6 | 55 | 46214 | 30 | 0.098361 | 0.166667 | 0.123711 | 0.019447 |
| arbol_ponderado | 8 | 556 | 45713 | 28 | 0.014184 | 0.222222 | 0.026667 | 0.016017 |
| gnb_baseline | 31 | 36476 | 9793 | 5 | 0.000849 | 0.861111 | 0.001697 | 0.000839 |
| gnb_ponderado | 31 | 36476 | 9793 | 5 | 0.000849 | 0.861111 | 0.001697 | 0.000839 |
| knn_baseline | 0 | 5 | 46264 | 36 | 0 | 0 | 0 | 0.049479 |
| knn_ros | 6 | 93 | 46176 | 30 | 0.060606 | 0.166667 | 0.088889 | 0.019844 |


El árbol baseline ofreció el mayor F1 y Precision de esta tabla. Ponderar recuperó más ATO, pero multiplicó FP. GaussianNB tuvo recall alto con una carga de revisión enorme. La AP relativamente alta de KNN no se convirtió en detección a 0,5. Fuente: [resultados CV1](fase04_modelado/resultados/comparacion_modelos.csv).

### 4.2. CV2: estratificación sobre usuarios, umbral 0,5

Se construyó una tabla de usuarios con/sin ATO, se aplicó StratifiedKFold y se expandió cada fold a eventos. Usuarios positivos: 6, 7, 7, 7, 7; eventos ATO: 6, 7, 7, 8, 8.

| modelo | TP | FP | TN | FN | precision | recall | f1 | average_precision |
|---|---|---|---|---|---|---|---|---|
| arbol_baseline | 3 | 61 | 46208 | 33 | 0.046875 | 0.083333 | 0.060000 | 0.008862 |
| arbol_ponderado | 9 | 675 | 45594 | 27 | 0.013158 | 0.250000 | 0.025000 | 0.015817 |
| gnb_baseline | 31 | 36447 | 9822 | 5 | 0.000850 | 0.861111 | 0.001698 | 0.000840 |
| gnb_ponderado | 31 | 36447 | 9822 | 5 | 0.000850 | 0.861111 | 0.001698 | 0.000840 |
| knn_baseline | 0 | 1 | 46268 | 36 | 0 | 0 | 0 | 0.043163 |
| knn_ros | 5 | 99 | 46170 | 31 | 0.048077 | 0.138889 | 0.071429 | 0.012462 |


KNN+ROS alcanzó el mayor F1 a 0,5 en CV2; el árbol baseline perdió aciertos. Cambió la distribución de usuarios, no el algoritmo. **CV1 y CV2 reutilizan train y no son replicaciones independientes.** Fuente: [resultados CV2](fase04_modelado/resultados_cv_usuario/comparacion_modelos.csv).

### 4.3. Umbrales exploratorios y validación anidada

0,5 es una regla convencional, no una frontera garantizada de utilidad. El análisis exploratorio examinó las OOF existentes de CV1/CV2: por ejemplo, KNN a 0,4 detectaba cuatro ATO, con nueve FP en CV1 y ocho en CV2, pero omitía 32. Elegir una regla en esas mismas OOF no valida independientemente su rendimiento.

La validación anidada separó cinco folds externos de tres internos por externo. El umbral se eligió por F1 OOF interno; solo después se aplicó a usuarios externos al ajuste. El selector conjunto también eligió internamente una variante. El experimento RF extendió exactamente esas particiones, reutilizando resultados históricos, con cuatro configuraciones seleccionadas internamente.

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


Las seis primeras filas son variantes anidadas históricas; Random Forest pertenece a la extensión. Los selectores son procedimientos de selección, no familias adicionales. “—” en AP global de selectores significa que no se calculó una AP que mezcle familias. Fuente: [comparación anidada/extensión](fase04_modelado/mejora_controlada/resultados/comparacion_global.csv).

Aquí el árbol ponderado tiene F1 mayor. Frente a KNN+ROS conserva cinco aciertos con menos FP; frente a KNN baseline recupera un ATO menos y reduce FP. GaussianNB recupera 31, pero con 38.839 FP. El criterio F1 favorece al árbol ponderado dentro de este compromiso, sin convertirlo en el mejor por recall o AP.

### 4.4. Ranking, clasificación y estabilidad

AP evalúa el orden de los scores; F1 depende del umbral. Random Forest tuvo AP global 0,060211 y AP media por fold 0,098581, pero solo cuatro TP con la regla aprendida. No hay contradicción: ordenar relativamente mejor algunos positivos no garantiza una buena frontera de alertas.

No se confunden métricas concatenadas con medias por fold. El árbol ponderado tuvo F1 global 0,105263 frente a media 0,115259 y desviación 0,129951. No detectó ATO en dos folds; tres de sus cinco aciertos estuvieron en un solo fold. GaussianNB tuvo baja dispersión absoluta de F1 alrededor de un valor muy bajo: estabilidad numérica no implica utilidad.

RF seleccionó por fold, respectivamente, (None,1), (8,1), (8,10), (8,1), (None,10) para profundidad/hoja. No existe una configuración única de bosque detrás de su agregado. El fold 4 acumuló 135 de sus 158 FP. A 0,5 obtenía 16 TP y 1.474 FP; no se adoptó esa regla por observar el resultado externo. La búsqueda de RF tuvo más flexibilidad que cada variante histórica y fue posterior al diagnóstico; no es evidencia independiente ni prueba de superioridad estadística.

En usuarios, la anidada del árbol ponderado detectó cinco de 34, omitió 29 y alertó a 21 usuarios sin ATO. GaussianNB detectó 30, pero alertó a 1.357 usuarios sin ATO. KNN baseline detectó seis y alertó a 37 sin ATO; KNN+ROS, cinco y 24; RF, cuatro y 126. Los denominadores por usuario no deben confundirse con conteos por evento.

## 5. Análisis de clustering

### 5.1. Propósito y representación

KMeans y jerárquico exploraron si existían patrones de actividad sin usar ATO para formar grupos. Utilizaron los mismos seis predictores, representación de distancias de 62 columnas y train exclusivamente. Después de congelar la selección se consultó ATO para describir los grupos. “Evaluación externa” del clustering significa contraste posterior con la etiqueta, **no evaluación en el test independiente**.

KMeans agrupa observaciones cercanas a centros. Ward construye un árbol de fusiones que minimizan incrementos de dispersión. Average fue otro enlace jerárquico explorado. Los nombres de cluster son arbitrarios; no indican gravedad o ataque.

### 5.2. Selección interna, estabilidad y memoria

Se exploró k=2–8. KMeans usó k-means++, n_init=10, max_iter=300 y semillas 42, 43, 44 para estabilidad. La selección combinó silhouette, Davies–Bouldin, Calinski–Harabasz, tamaños y perfiles. Inercia/codo fue gradual, sin un k “verdadero” inequívoco. Silhouette se calculó históricamente en muestras fijas de 2.000 eventos; DB y CH sobre la población de cada método.

| Método seleccionado | Eventos analizados | Tamaños de grupos | Silhouette | Davies–Bouldin | Calinski–Harabasz |
|---|---:|---|---:|---:|---:|
| KMeans k=2 | 46.305 | 41.296 / 5.009 | 0,606043 | 0,732742 | 38.739,4 |
| Ward k=2 | 4.000 | 3.534 / 466 | 0,597778 | 0,785535 | 3.147 |

KMeans k=2 obtuvo ARI=1 entre las tres semillas; k=7/8 fue menos estable. Ward k=2 resumió perfiles similares. Average k=2, pese a silhouette 0,785401, produjo 3.983/17 y no se eligió como segmentación principal. Un índice alto con un grupo diminuto no bastó para justificarlo.

El jerárquico completo sobre 46.305 eventos requería aproximadamente 8,58 GB de matriz condensada o 17,15 GB cuadrada, sin temporales. Se usaron 4.000 eventos uniformes, semilla 42, que representaban 1.360 usuarios; no se estratificó por ATO. La matriz condensada muestral era de unos 64 MB. Son estimaciones históricas de matrices, no picos de memoria medidos. No se extrapolaron etiquetas Ward al resto.

ARI entre KMeans y Ward sobre los mismos 4.000 eventos fue 0,928144. Esa concordancia entre métodos y la estabilidad de inicialización no prueban estabilidad ante nuevas muestras ni detección ATO. No se documentó un estudio de múltiples muestras jerárquicas.

### 5.3. Perfiles y contraste posterior con ATO

KMeans separó un grupo sin fallos en 15 minutos y mediana de intervalo de 53,558 horas, de otro con media de 1,57656 fallos en 15 minutos, 2,26273 en una hora e intervalo mediano de 0,0284672 horas. Ward reprodujo una estructura parecida: grupo de poca actividad inmediata frente a accesos próximos con fallos. En KMeans, el grupo de actividad más inmediata tuvo mayor proporción mobile; eso describe comportamiento, no identifica atacantes.

| Método / grupo | Eventos | ATO | Interpretación |
|---|---:|---:|---|
| KMeans 0 | 41.296 | 32 | Prevalencia 0,07749 % |
| KMeans 1 | 5.009 | 4 | Prevalencia 0,07986 % |
| Ward 0 | 3.534 | 1 | Solo un ATO en toda la muestra |
| Ward 1 | 466 | 0 | Evidencia insuficiente de separación ATO |

Las prevalencias KMeans son casi iguales descriptivamente. Ward tuvo demasiado poco soporte positivo para evaluar enriquecimiento. Un usuario puede aparecer en varios clusters; sus conteos no se suman como usuarios únicos.

No se asignaron predicciones “ataque/no ataque” a grupos ni se calcularon Precision/Recall/F1 como si fueran clasificadores. El clustering aportó perfiles de fallos e intervalos, **no una separación convincente de ATO**.

Evidencia y visualizaciones preservadas:
- [Informe de clustering](INFORME_CLUSTERING_FASE04.md), auditoría interna, selección congelada y verificación de integridad en `fase04_clustering/resultados/`.
- [Perfiles KMeans](fase04_clustering/resultados/graficas/perfiles_kmeans_2.png), [dendrograma Ward](fase04_clustering/resultados/graficas/dendrograma_ward.png), [selección interna](fase04_clustering/resultados/graficas/seleccion_interna.png) y [estabilidad](fase04_clustering/resultados/graficas/estabilidad_kmeans.png).
- El informe histórico registra nueve pruebas aprobadas. Se inspeccionó su evidencia y código; **no se volvieron a ejecutar** en este cierre.

## 6. Diagnóstico de capacidad predictiva

La prevalencia baja dificulta aprender y medir patrones positivos. 36 ATO de 34 usuarios no equivalen a decenas de miles de ejemplos positivos. Un cambio de pocos eventos altera mucho recall y F1.

El diagnóstico encontró cuatro vectores de entradas con clases mezcladas: ocho ATO compartían exactamente los seis predictores con 621 negativos. Un predictor determinista con esas mismas entradas no puede distinguir individualmente esos casos. No es un límite universal de detección; muestra una limitación de esta representación observada.

Los contadores de fallos son redundantes (Spearman documentado 0,9051), con medianas cero en ambas clases. El intervalo tiene cola larga y 1.600 ausentes estructurales en train; has_previous_login refleja esa ausencia. País y dispositivo aportan contexto, pero no describen completamente los hábitos particulares de cada usuario y la geografía es sintética.

El bajo desempeño no puede atribuirse causalmente a un único factor: desbalance, pocos usuarios positivos, solapamiento, representación y supuestos de los modelos confluyen. Ponderación/ROS no resolvieron el problema; cambiar a bosque tampoco. Estos resultados no demuestran que sea imposible detectar ATO con otros datos o protocolos. Fuente: [diagnóstico](INFORME_DIAGNOSTICO_CAPACIDAD_PREDICTIVA_FASE04.md).

## 7. Selección del modelo de referencia

El árbol ponderado obtuvo el mejor F1 agregado en la comparación anidada histórica: **5 TP, 54 FP, 46.215 TN, 31 FN; Precision 0,08474576, Recall 0,13888889 y F1 0,10526316**.

Se eligió como referencia académica por ese criterio relativo. La elección se hizo después de revisar las comparaciones; es retrospectiva y debe reconocerse como tal. El selector anidado no eligió la familia en todos los folds: seleccionó árbol ponderado en el primero, KNN+ROS en 2/4/5 y KNN baseline en 3.

| Concepto | Qué significa aquí |
|---|---|
| Mejor referencia relativa | Mayor F1 agregado en la comparación anidada histórica bajo el criterio adoptado. No ganó todas las métricas o protocolos. |
| Modelo final materializado | Árbol ajustado sobre todo train, serializado y asociado a preprocesador/umbral congelados. Es un artefacto reproducible. |
| Detector eficiente o productivo | Requeriría cobertura, falsas alarmas, robustez y costes aceptables demostrados. No se alcanzó evidencia suficiente. |

Omitir 31 de 36 ATO y 29 de 34 usuarios positivos impide confundir la primera categoría con la tercera. La selección permite evaluar una referencia concreta, no afirmar superioridad universal.

## 8. Congelación del procedimiento de referencia

Identificador: `referencia_arbol_ponderado_v1`. Parámetros completos del árbol congelado:

```json
{
  "ccp_alpha": 0,
  "class_weight": "balanced",
  "criterion": "gini",
  "max_depth": null,
  "max_features": null,
  "max_leaf_nodes": null,
  "min_impurity_decrease": 0,
  "min_samples_leaf": 1,
  "min_samples_split": 2,
  "min_weight_fraction_leaf": 0,
  "monotonic_cst": null,
  "random_state": 42,
  "splitter": "best"
}
```

Se conservan los seis predictores y representación de árbol: mediana numérica, binaria intacta, categóricas imputadas y One-Hot, sin log1p/escalado/ROS. El ajuste completo produce 62 columnas. El procedimiento usa predict_proba de clase 1 y decisión score >= umbral.

El umbral se seleccionó con tres folds por usuario en train, estratificando presencia de ATO, shuffle=True y semilla 42. Se maximizó F1 por evento sobre OOF concatenadas, mediante fracciones exactas. Candidatos: scores únicos, 0, 0,5 y siguiente flotante sobre 1. Desempate: cercanía a 0,5 y después mayor.

Umbral definitivo: **0.9976439543869569**. Las OOF de selección dieron TP=8, FP=48, TN=46.221, FN=28 y F1=0,17391304347826086. Ese F1 se utilizó para elegir t: **no constituye una evaluación independiente ni reemplaza la anidada o test**. Los tres estimadores OOF y el ajuste final completo no tienen garantizada la misma escala de probabilidades.

Se ajustó el modelo completo y hubo una incidencia al escribir numpy.int64 en el campo hojas_observadas. La recuperación del 22 de noviembre repitió únicamente el ajuste final, preservó umbral/OOF y aplicó conversión JSON explícita con rechazo de no finitos. Modelo y preprocesador se serializaron y recargaron; sus predicciones en train fueron idénticas antes/después, según la evidencia existente. Esa prueba comprueba persistencia, no generalización.

Directorio final: `fase04_modelado/recuperacion_referencia_v1_20261122/`.

| Artefacto | SHA-256 |
|---|---|
| modelo_final.joblib | d23a2a0f93d64682931608829a030e9615be43990e4ae43d99262b5a9254ff5e |
| preprocesador_final.joblib | 01fbfd1f162dda4c7e31946da3e4cc19e87d9badfac235d662345369096168c6 |
| umbral_definitivo.json | e5327bd50594edd9d1c67e5076bd53f101c9194b068911e8faf16567f7109095 |

Fuentes: [especificación](PROCEDIMIENTO_REFERENCIA_CONGELADO_FASE04.md), [justificación](INFORME_PROCEDIMIENTO_REFERENCIA_FASE04.md) e [informe de recuperación](fase04_modelado/recuperacion_referencia_v1_20261122/INFORME_RECUPERACION_TECNICA_FASE04.md).

## 9. Evaluación independiente final de test

La evaluación fue autorizada expresamente, ejecutada una sola vez el 22 de noviembre y cerrada. La auditoría registra una lectura física, una carga, una transformación, una inferencia completa y cero intentos de fit. No se cambiaron reglas después de ver resultados. En esta consolidación solo se consultaron sus tres documentos finales.

### 9.1. Matriz y métricas por evento

| Real / predicción | No ATO | ATO |
|---|---:|---:|
| No ATO | 11.094 | 12 |
| ATO | 8 | 1 |

| Métrica | Test |
|---|---:|
| TP | 1 |
| FP | 12 |
| TN | 11.094 |
| FN | 8 |
| Precision | 0,076923 |
| Recall | 0,111111 |
| F1 | 0,090909 |
| Average Precision | 0,009267 |
| ROC-AUC | 0,549078 |

Se emitieron 13 alertas: una verdadera y doce falsas. Se detectó uno de los nueve ATO y se omitieron ocho. Las alertas verdaderas representaron 7,69 %. Precision, Recall y F1 se calcularon con zero_division=0; AP y ROC-AUC usaron los scores sin aplicar umbral.

ROC-AUC es calculable al haber ambas clases, pero con muchos negativos y nueve positivos no sustituye la evaluación de falsas alarmas y recuperación. No se utilizó accuracy como criterio principal.

### 9.2. Resultados por usuario

| Conteo | Test |
|---|---:|
| Usuarios totales | 400 |
| Usuarios con ATO | 9 |
| Usuarios ATO detectados | 1 |
| Usuarios ATO omitidos | 8 |
| Usuarios sin ATO con falsa alerta | 6 |
| Usuarios con algún FP, total | 7 |
| Usuarios con ATO que también tuvieron FP | 1 |

Detectado significa al menos un ATO correctamente alertado del usuario, no cualquier alerta en su historial. Los FP afectaron a seis usuarios sin ATO y a uno con ATO. No se confunden doce eventos FP con siete usuarios.

### 9.3. Evidencias distintas y alcance

| Etapa | TP | FP | TN | FN | F1 |
|---|---:|---:|---:|---:|---:|
| Anidada histórica externa de train | 5 | 54 | 46.215 | 31 | 0,105263 |
| OOF de train usadas para seleccionar t | 8 | 48 | 46.221 | 28 | 0,173913 |
| Test independiente, único | 1 | 12 | 11.094 | 8 | 0,090909 |

No se suman matrices ni se interpretan estas etapas como réplicas. La segunda fila está optimizada para selección; no añade evidencia independiente de generalización. La anidada usa varios modelos/umbrales por fold, mientras que test usa un modelo y umbral únicos.

Test mantuvo baja recuperación y predominio de falsas alarmas, coherentes con la limitación general de validación. Cada ATO equivale a 1/9 de los positivos: un acierto u omisión cambia recall aproximadamente **11,11 puntos porcentuales**. Las diferencias de F1/recall no demuestran un cambio estable de capacidad predictiva.

El resultado representa este procedimiento en esta partición, no una garantía futura. No se hicieron ajustes posteriores ni se repetirá la evaluación para buscar otra conclusión.

Fuentes exclusivas de test:
- [Informe final](fase04_modelado/evaluacion_final_test_20261122/INFORME_EVALUACION_FINAL_TEST_FASE04.md).
- [Auditoría](fase04_modelado/evaluacion_final_test_20261122/AUDITORIA_EVALUACION_TEST.json).
- [Manifiesto](fase04_modelado/evaluacion_final_test_20261122/MANIFIESTO_EVALUACION_TEST.json).

## 10. Conclusiones de la Fase 4

Se compararon siete variantes supervisadas de árbol, GaussianNB, KNN y Random Forest, y dos enfoques no supervisados, KMeans y jerárquico. Se mantuvieron visibles resultados desfavorables y se distinguieron clasificación, ranking y descripción de grupos.

El árbol ponderado fue la mejor referencia relativa por F1 anidado histórico y permitió materializar una configuración concreta para evaluación final. No fue ganador universal ni opción productiva demostrada. Ponderación y sobremuestreo cambiaron el compromiso de alertas sin resolver la escasez y representación de positivos.

El clustering identificó perfiles de intensidad de fallos e intervalos, con estabilidad de inicialización y similitud entre métodos, pero sin separación convincente de ATO. Los grupos son una contribución descriptiva, no predicciones de ataque.

El diagnóstico mostró pocos usuarios positivos, solapamiento de entradas, redundancia y límites semánticos de variables. La prueba final detectó un ATO, omitió ocho y produjo doce falsas alarmas: **no se obtuvo evidencia suficiente de un detector eficiente ni apto para producción**.

La comparación, los controles de integridad, la explicación de límites y una prueba independiente aceptada sin ajustes son resultados académicos válidos. No se presenta el proyecto como fracaso ni se disfraza el rendimiento bajo como éxito operativo.

La experimentación y evaluación están cerradas; se completa aquí su consolidación documental. No se certifica cumplimiento de rúbricas, formatos o entregables del profesor que no hayan sido comprobados.

## 11. Limitaciones y trabajo futuro

Para investigaciones posteriores, no como reapertura de esta evaluación, tendría sentido estudiar:
- Más eventos ATO reales y representativos y más usuarios positivos.
- Predictores discriminativos con disponibilidad temporal verificable.
- Mejor contexto e historial de comportamiento.
- Datos geográficos fiables, antes de interpretar desplazamientos.
- Validaciones temporales y externas sobre nuevas poblaciones.
- Costes de falsas alarmas, omisiones y capacidad humana de revisión.

Estas posibilidades no garantizan mejores resultados y no se ejecutaron. El test de este proyecto ya fue utilizado; no queda disponible como reserva nueva para otra búsqueda.

El reducido soporte positivo limita precisión estadística; la dependencia por usuario, el análisis repetido del mismo train y la elección retrospectiva de familia limitan inferencias. La equivalencia de serialización no prueba transferencia de umbral. No se han demostrado causas únicas del bajo rendimiento ni imposibilidad universal de detectar ATO.

## Trazabilidad y control documental

Se consultaron las fuentes existentes antes de redactar. No faltó evidencia necesaria para completar las once secciones. No se encontraron discrepancias numéricas materiales entre informe/auditoría final de test y cifras incorporadas. Los estados antiguos de “test cerrado” o “modelo pendiente” corresponden a documentos anteriores; se preservan como historial y se contextualizan, no se cambian sus resultados.

Se conservan problemas menores de codificación de tildes en algunas adendas históricas; no afectan las cifras y no se corrigieron los originales. Las nueve pruebas de clustering y demás pruebas anteriores se citan como evidencia histórica, no como ejecuciones nuevas.

El registro [AUDITORIA_CIERRE_DOCUMENTAL_FASE04.json](AUDITORIA_CIERRE_DOCUMENTAL_FASE04.json) contiene fuentes, resultados incorporados, hashes y alcance de verificaciones. Solo se crean este informe, el resumen ejecutivo y la auditoría, y se actualiza README conservando su cuerpo histórico. No se ejecutaron modelos, métricas, predicciones ni experimentos; no se abrió o hasheó de nuevo el CSV original de test, ni se consultaron sus predicciones guardadas.

### Índice de fuentes principales

- [INFORME_CORRECCION_TARGET_FASE03.md](INFORME_CORRECCION_TARGET_FASE03.md)
- [INFORME_PARTICION_FASE04.md](INFORME_PARTICION_FASE04.md)
- [INFORME_PREPROCESAMIENTO_FASE04.md](INFORME_PREPROCESAMIENTO_FASE04.md)
- [INFORME_REVISION_IMPOSSIBLE_TRAVEL_FASE04.md](INFORME_REVISION_IMPOSSIBLE_TRAVEL_FASE04.md)
- [INFORME_COMPARATIVO_ALGORITMOS_FASE04.md](INFORME_COMPARATIVO_ALGORITMOS_FASE04.md)
- [INFORME_MODELADO_SUPERVISADO_FASE04.md](INFORME_MODELADO_SUPERVISADO_FASE04.md)
- [INFORME_SEGUNDA_VALIDACION_FASE04.md](INFORME_SEGUNDA_VALIDACION_FASE04.md)
- [INFORME_SELECCION_SUPERVISADA_FASE04.md](INFORME_SELECCION_SUPERVISADA_FASE04.md)
- [INFORME_VALIDACION_ANIDADA_FASE04.md](INFORME_VALIDACION_ANIDADA_FASE04.md)
- [INFORME_DIAGNOSTICO_CAPACIDAD_PREDICTIVA_FASE04.md](INFORME_DIAGNOSTICO_CAPACIDAD_PREDICTIVA_FASE04.md)
- [PROPUESTA_EXPERIMENTOS_MEJORA_FASE04.md](PROPUESTA_EXPERIMENTOS_MEJORA_FASE04.md)
- [INFORME_DECISION_MODELO_FASE04.md](INFORME_DECISION_MODELO_FASE04.md)
- [INFORME_CLUSTERING_FASE04.md](INFORME_CLUSTERING_FASE04.md)
- [PROCEDIMIENTO_REFERENCIA_CONGELADO_FASE04.md](PROCEDIMIENTO_REFERENCIA_CONGELADO_FASE04.md)
- [INFORME_PROCEDIMIENTO_REFERENCIA_FASE04.md](INFORME_PROCEDIMIENTO_REFERENCIA_FASE04.md)
- [fase04_modelado/recuperacion_referencia_v1_20261122/INFORME_RECUPERACION_TECNICA_FASE04.md](fase04_modelado/recuperacion_referencia_v1_20261122/INFORME_RECUPERACION_TECNICA_FASE04.md)
- [fase04_modelado/evaluacion_final_test_20261122/INFORME_EVALUACION_FINAL_TEST_FASE04.md](fase04_modelado/evaluacion_final_test_20261122/INFORME_EVALUACION_FINAL_TEST_FASE04.md)

