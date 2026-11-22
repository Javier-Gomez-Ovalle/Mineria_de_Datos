# Informe de clustering — Fase 4

Fecha: 2026-11-19. Estudio exploratorio de train; no constituye un detector ATO ni cierra Fase 4.

## 1. Auditoría y datos

Se revisaron los informes de preprocesamiento, Impossible Travel, modelado supervisado y segunda validación, la fábrica de transformaciones y selección de variables, las métricas y visualizaciones supervisadas y la matriz train de distancias. Se preservó la implementación aprobada. Solo se cargaron predictores y claves de train en la etapa interna. El target se abrió en evaluación externa, después de escribir y verificar `seleccion_congelada.json` y los hashes de etiquetas. Los informes históricos contienen información ATO ya conocida; esa información no intervino en las decisiones del clustering.

Origen: `dataset_train_fase04.csv`, 46.305 eventos de 1.600 usuarios. SHA-256: `98d4d4970ada7bf11ec2e76f89e93c46c76c3d097043020598638547f977e53f`. La matriz reconstruida coincide exactamente con la histórica (46.305 × 62). Ningún identificador, target, resultado del login, bandera de ataque ni variable Impossible Travel entra en X. Las claves se usan únicamente para alinear y describir eventos.

## 2. Representación y datos mixtos

Se conserva la lista positiva de seis predictores: Device Type, Country, failed_attempts_15min, failed_attempts_1h, time_since_previous_login_hours y has_previous_login. Se ajustan de nuevo, en todo train y sin y, mediana de numéricas, log1p, StandardScaler de las tres numéricas, indicador binario intacto y One-Hot de nominales con categoría desconocida. No se reutiliza un transformador ajustado en test. El ajuste en todo train es apropiado para esta descripción no supervisada de train; los índices internos no son una validación predictiva externa.

Tres columnas numéricas, una binaria, cuatro dummies de dispositivo y 54 de país. Cada bloque One-Hot aporta como máximo 2 a la distancia euclídea cuadrática, independientemente del número de categorías. Contribuciones esperadas entre dos eventos extraídos independientemente: numéricas 6, binaria 0,06672, dispositivo 1,08076 y país 0,74478. Aproximadamente 76,0%, 0,85%, 13,69% y 9,44% respectivamente. No se escalan dummies ni se añaden pesos buscando separación visual.

Euclídea mezcla diferencias nominales y continuas; sus centroides nominales son proporciones, no categorías reales. No se afirma que sea una distancia semántica única o ideal. Las dos cuentas de fallos están relacionadas y enfatizan actividad reciente. La mediana imputada más el indicador de historial distingue ausencia de observación, pero no elimina toda distorsión de distancia. Country es contexto sintético, no geografía física; se mantienen las exclusiones Impossible Travel. No se exploraron representaciones alternativas guiadas por ATO.

## 3. KMeans y selección interna

K=2–8, init=k-means++, n_init=10, max_iter=300, algoritmo Lloyd, semilla principal 42. Semillas adicionales 43 y 44 previamente fijadas para ARI de estabilidad. Dos hilos computacionales. Silhouette sobre 2.000 eventos uniformes sin reemplazo con semilla 42; DB y CH sobre los 46.305 eventos. Inercia no se normaliza y corresponde a esa matriz. Los segundos incluyen los tres ajustes por K, excluyen métricas internas y gráficos; no son tiempo de un único ajuste.

| k | inercia | iteraciones | segundos | silhouette | davies_bouldin | calinski_harabasz | ari_min | minimo | maximo |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 99488.5 | 4 | 2.01898 | 0.606043 | 0.732742 | 38739.4 | 1 | 5009 | 41296 |
| 3 | 74176.7 | 8 | 1.11924 | 0.317893 | 1.13726 | 33878.8 | 0.999602 | 5002 | 21686 |
| 4 | 61480.6 | 6 | 1.21079 | 0.372176 | 0.988063 | 30436.5 | 0.999935 | 4962 | 17306 |
| 5 | 50712.9 | 7 | 1.605 | 0.375987 | 0.983328 | 30131.3 | 0.999535 | 808 | 17306 |
| 6 | 43921.6 | 18 | 1.8588 | 0.380559 | 0.986631 | 29263.5 | 0.997259 | 808 | 12215 |
| 7 | 40142.7 | 15 | 2.00281 | 0.378699 | 0.982066 | 27407.7 | 0.655177 | 772 | 12230 |
| 8 | 36800.5 | 8 | 2.06412 | 0.381354 | 0.970191 | 26225.9 | 0.588926 | 772 | 10034 |

KMeans K=2: silhouette 0.606, DB mínimo y CH máximo del rango, ARI=1 entre semillas, grupos 41296/5009 y perfiles de fallos/intervalos interpretables. Codo gradual: no prueba un K verdadero. Ward K=2: mejores tres índices dentro de Ward, grupos 3534/466. Average K=2 se descarta como representación principal pese a silhouette 0.785 por división 3983/17 (0.425% en grupo menor). K=7/8 KMeans es menos estable. Selección descriptiva parsimoniosa, no óptimo universal.

El codo presenta reducción gradual: pasar de K=2 a 3 reduce inercia un 25,4%; K=4 y 5 siguen reduciéndola alrededor del 17%. No existe un codo inequívoco que pruebe dos clusters naturales. K=2 se conserva como resumen parsimonioso y estable respaldado por índices y perfiles, no exclusivamente por silhouette. No se alteró K después de abrir y. La estabilidad entre inicializaciones no demuestra estabilidad frente a nuevas muestras o usuarios.

## 4. Jerárquico: coste, enlaces y corte

La matriz condensada de 46.305 eventos exigiría 8,58 GB y una cuadrada 17,15 GB, sin temporales ni copias. La memoria libre observada era aproximadamente 11,3 GiB. Se evitó ese riesgo con 4.000 eventos uniformes sin reemplazo, semilla 42, índices ordenados después de muestrear: 1360 usuarios. No se estratificó por target ni por usuario. Los usuarios con más eventos tienen mayor probabilidad de representación.

La muestra requiere unos 64 MB condensados o 128 MB cuadrados; el tiempo y espacio de los enlaces son cuadráticos. Ward y average usan distancia euclídea; Ward minimiza incrementos de dispersión y no se utiliza con una distancia incompatible. Se ajustó la representación a train completo y luego se muestrearon filas de esa misma geometría. No se extrapolan etiquetas jerárquicas a los eventos no muestreados.

| algoritmo | k | segundos | silhouette | davies_bouldin | calinski_harabasz | minimo | maximo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ward | 2 | 0.282052 | 0.597778 | 0.785535 | 3147 | 466 | 3534 |
| ward | 3 | 0.282052 | 0.291593 | 1.22836 | 2488.87 | 466 | 2271 |
| ward | 4 | 0.282052 | 0.297061 | 1.22211 | 2191.75 | 116 | 2271 |
| ward | 5 | 0.282052 | 0.312088 | 1.08263 | 2175.16 | 116 | 1681 |
| ward | 6 | 0.282052 | 0.316129 | 0.992759 | 2107.39 | 116 | 1681 |
| ward | 7 | 0.282052 | 0.33241 | 1.09291 | 2016.97 | 116 | 945 |
| ward | 8 | 0.282052 | 0.331914 | 1.0471 | 1963.33 | 17 | 945 |
| average | 2 | 0.265266 | 0.785401 | 0.316992 | 519.996 | 17 | 3983 |
| average | 3 | 0.265266 | 0.580242 | 0.67395 | 1946.35 | 17 | 3534 |
| average | 4 | 0.265266 | 0.484584 | 0.845683 | 1467.21 | 17 | 3534 |
| average | 5 | 0.265266 | 0.484584 | 0.87531 | 1108.41 | 4 | 3534 |
| average | 6 | 0.265266 | 0.48812 | 0.894846 | 995.079 | 4 | 3534 |
| average | 7 | 0.265266 | 0.486378 | 0.978 | 840.951 | 4 | 3534 |
| average | 8 | 0.265266 | 0.432012 | 1.02515 | 727.842 | 4 | 3534 |

El tiempo de cada enlace se repite por K: corresponde a un único árbol por método, no debe sumarse siete veces. Silhouette utiliza 2.000 eventos fijos dentro de la muestra jerárquica. DB y CH usan los 4.000. Average conserva su resultado desfavorable como segmentación general, aunque puede describir extremos; no se interpreta ese pequeño grupo como ataques. Ward K=2 se corta a altura 87.602528, entre las dos últimas fusiones. El dendrograma muestra 25 ramas terminales para legibilidad, no solo 25 observaciones.

## 5. Tamaños, perfiles y comparación

| algoritmo | cluster | failed_attempts_15min_mean | failed_attempts_1h_mean | time_since_previous_login_hours_median | has_previous_login_mean |
| --- | --- | --- | --- | --- | --- |
| kmeans_2 | 0 | 0 | 0.0152073 | 53.558 | 0.961255 |
| kmeans_2 | 1 | 1.57656 | 2.26273 | 0.0284672 | 1 |
| ward_2 | 0 | 0 | 0 | 50.1886 | 0.962083 |
| ward_2 | 1 | 1.40558 | 2.0794 | 0.0311979 | 1 |

KMeans separa un grupo sin fallos en los últimos 15 minutos y mediana de intervalo 53,56 horas, frente a actividad con fallos e intervalo mediano 0,02847 horas (1,71 minutos). Ward reproduce una estructura similar. Los nombres de clusters son identificadores arbitrarios; no ordenan gravedad.

Categorías más frecuentes (hasta tres por variable y cluster; distribuciones completas en CSV):

| algoritmo | cluster | variable | valor | eventos | porcentaje |
| --- | --- | --- | --- | --- | --- |
| kmeans_2 | 0 | Country | NO | 33808 | 81.8675 |
| kmeans_2 | 0 | Country | US | 1567 | 3.79456 |
| kmeans_2 | 0 | Country | GB | 1235 | 2.9906 |
| kmeans_2 | 0 | Device Type | desktop | 22438 | 54.3346 |
| kmeans_2 | 0 | Device Type | mobile | 16890 | 40.8998 |
| kmeans_2 | 0 | Device Type | tablet | 1925 | 4.66147 |
| kmeans_2 | 1 | Country | NO | 2724 | 54.3821 |
| kmeans_2 | 1 | Country | US | 734 | 14.6536 |
| kmeans_2 | 1 | Country | PL | 415 | 8.28509 |
| kmeans_2 | 1 | Device Type | mobile | 3730 | 74.466 |
| kmeans_2 | 1 | Device Type | desktop | 1143 | 22.8189 |
| kmeans_2 | 1 | Device Type | tablet | 136 | 2.71511 |
| ward_2 | 0 | Country | NO | 2924 | 82.7391 |
| ward_2 | 0 | Country | US | 136 | 3.84833 |
| ward_2 | 0 | Country | GB | 110 | 3.11262 |
| ward_2 | 0 | Device Type | desktop | 1940 | 54.8953 |
| ward_2 | 0 | Device Type | mobile | 1395 | 39.4737 |
| ward_2 | 0 | Device Type | tablet | 196 | 5.54612 |
| ward_2 | 1 | Country | NO | 227 | 48.7124 |
| ward_2 | 1 | Country | US | 81 | 17.382 |
| ward_2 | 1 | Country | PL | 39 | 8.3691 |
| ward_2 | 1 | Device Type | mobile | 359 | 77.0386 |
| ward_2 | 1 | Device Type | desktop | 95 | 20.3863 |
| ward_2 | 1 | Device Type | tablet | 12 | 2.57511 |

Los CSV `perfil_numerico_*` contienen count, media, DE, mínimo, mediana, máximo y cuartiles en unidades originales. Count excluye intervalos ausentes. `perfil_categorico_*` contiene todos los niveles de Device Type, Country e indicador de historial con conteos y porcentajes.

ARI entre KMeans completo y Ward muestral sobre los mismos 4.000 eventos: **0.928144**. Contingencia (filas KMeans, columnas Ward): `[[3534, 46], [0, 420]]`. Hay 46 asignaciones distintas tras alinear estos dos grupos; los algoritmos y poblaciones de ajuste difieren. La similitud no valida etiquetas ATO ni sustituye estabilidad frente al muestreo.

## 6. Evaluación externa posterior a congelación

| algoritmo | cluster | eventos | eventos_ato | eventos_no_ato | prevalencia | usuarios | usuarios_con_ato | porcentaje_eventos |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kmeans_2 | 0 | 41296 | 32 | 41264 | 0.000774893 | 1600 | 31 | 89.1826 |
| kmeans_2 | 1 | 5009 | 4 | 5005 | 0.000798563 | 941 | 4 | 10.8174 |
| ward_2 | 0 | 3534 | 1 | 3533 | 0.000282965 | 1264 | 1 | 88.35 |
| ward_2 | 1 | 466 | 0 | 466 | 0 | 317 | 0 | 11.65 |

Usuarios con ATO significa usuarios con al menos un evento ATO **dentro de ese cluster**. Un usuario puede tener eventos en ambos clusters: no se suman estos conteos como usuarios únicos. Hay 36 eventos ATO de 34 usuarios en train; la muestra jerárquica contiene solo un ATO. No ATO significa etiqueta negativa, no una garantía de actividad benigna.

Las prevalencias KMeans son 0,07749% y 0,07986%, prácticamente iguales descriptivamente. No hay evidencia aquí de una separación ATO útil. Esto no demuestra ausencia de cualquier señal no supervisada ni justifica buscar K con la etiqueta. La evaluación jerárquica externa es insuficiente para comparar enriquecimiento. No se calcularon accuracy, precision, recall ni F1 para clusters; ningún grupo se denomina malicioso.

## 7. Pruebas, arquitectura y límites

Se ejecutaron 9 pruebas y aprobaron 9: exclusión e invariancia ante target/IDs, transformaciones y finitud, reproducción exacta KMeans/Ward y muestreo, correspondencia de etiquetas/perfiles/evaluación externa, métricas OOF y confusiones de ambos protocolos, pares PNG/SVG a 300 DPI y consistencia de exportación supervisada. Los tests solo reajustan clustering para comprobar reproducción, no modelos supervisados. Comando: `python -B -m pytest -p no:cacheprovider -q fase04_clustering/tests`.

Clases con constructor: PreparadorDatos, ExperimentoKMeans y ExperimentoJerarquico. Responsabilidades separadas en datos, experimentos, evaluación interna, congelación, evaluación externa, estilo/visualizaciones, exportación e informes. Se aplica responsabilidad única y composición de transformadores; no se afirma implementar todos los principios SOLID mediante jerarquías innecesarias. Funciones y métodos snake_case; clases PascalCase. No se modificó código aprobado.

La muestra enriquecida, geografía sintética, correlación entre eventos de un usuario, imputación y representación euclídea limitan interpretación. Los grupos pueden capturar mecanismos de ingeniería de características. Los índices internos no miden detección ATO. No se estimaron intervalos de confianza ni estabilidad jerárquica entre múltiples muestras. No se midió pico RSS; los tamaños de memoria son estimaciones de matrices, no consumo máximo observado. El rango K=2–8 no explora toda estructura posible.

## 8. Reproducción y entregables

Versiones: `{"python": "3.12.7", "numpy": "2.3.4", "pandas": "2.3.3", "sklearn": "1.7.2", "scipy": "1.16.3"}`. Mantener orden de filas y versiones. Desde raíz, en un destino nuevo (los exportadores rechazan sobrescritura): ejecutar en orden `python -B -m fase04_clustering.ejecutar`, revisar índices sin y, `python -B -m fase04_clustering.congelar`, `python -B -m fase04_clustering.evaluacion_externa`, `python -B -m fase04_clustering.visualizaciones`, `python -B -m fase04_clustering.presentacion_supervisada`, pruebas y `python -B -m fase04_clustering.informes`. No volver a ejecutar sobre esta entrega ni borrar históricos para reproducirla.

Código y diseño: `fase04_clustering/`. Resultados: `fase04_clustering/resultados/`: candidatos CSV/NPZ (incluye todos los K y enlaces), auditoría de representación, selección congelada con hashes, etiquetas por evento, perfiles numéricos/categóricos, evaluación externa y comparación de particiones. `inventario_previo.json` registra históricos y `verificacion_integridad.json` sus comprobaciones y SHA-256 de nuevos entregables (excepto su propio hash).

- [fase04_clustering/resultados/graficas/dendrograma_ward.png](fase04_clustering/resultados/graficas/dendrograma_ward.png) · [SVG](fase04_clustering/resultados/graficas/dendrograma_ward.svg): Árbol Ward truncado y altura de corte para dos grupos.
- [fase04_clustering/resultados/graficas/estabilidad_kmeans.png](fase04_clustering/resultados/graficas/estabilidad_kmeans.png) · [SVG](fase04_clustering/resultados/graficas/estabilidad_kmeans.svg): ARI entre semillas; pérdida de estabilidad al aumentar K.
- [fase04_clustering/resultados/graficas/externa_kmeans_2.png](fase04_clustering/resultados/graficas/externa_kmeans_2.png) · [SVG](fase04_clustering/resultados/graficas/externa_kmeans_2.svg): Evaluación externa ATO después de congelar clusters.
- [fase04_clustering/resultados/graficas/externa_ward_2.png](fase04_clustering/resultados/graficas/externa_ward_2.png) · [SVG](fase04_clustering/resultados/graficas/externa_ward_2.svg): Evaluación externa ATO después de congelar clusters.
- [fase04_clustering/resultados/graficas/perfiles_kmeans_2.png](fase04_clustering/resultados/graficas/perfiles_kmeans_2.png) · [SVG](fase04_clustering/resultados/graficas/perfiles_kmeans_2.svg): Perfiles de fallos e intervalos en sus unidades originales.
- [fase04_clustering/resultados/graficas/perfiles_ward_2.png](fase04_clustering/resultados/graficas/perfiles_ward_2.png) · [SVG](fase04_clustering/resultados/graficas/perfiles_ward_2.svg): Perfiles de fallos e intervalos en sus unidades originales.
- [fase04_clustering/resultados/graficas/seleccion_interna.png](fase04_clustering/resultados/graficas/seleccion_interna.png) · [SVG](fase04_clustering/resultados/graficas/seleccion_interna.svg): Codo de inercia e índices internos para todos los candidatos; silhouette muestral, DB/CH poblacionales.

## 9. Conclusión

KMeans y Ward ofrecen un resumen exploratorio coherente de intensidad de fallos e intervalos, sin separación ATO demostrada. Se conservan para documentación descriptiva, no como clasificación ni selección de un detector. Test no se leyó ni utilizó; sus archivos solo se verificaron por metadatos. No hubo operaciones Git, instalaciones ni entrenamiento supervisado. Permanecen pendientes la selección supervisada definitiva y la evaluación final de test con autorización independiente.
