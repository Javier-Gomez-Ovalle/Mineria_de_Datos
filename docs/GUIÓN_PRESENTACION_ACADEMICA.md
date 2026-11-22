# Guion de presentación académica — Fase 5

Estado: contenido inicial para revisión; no PPTX generado. Fecha: 22 de noviembre de 2026.
Requisito definitivo: **12 diapositivas, 540 segundos (9 minutos), máximo 10 minutos**. No habrá diapositivas de respaldo en el PPT principal. El frontend amplía evidencia; no reemplaza la sustentación. Este requisito sustituye la secuencia extensa de la planificación anterior, que se conserva como documento histórico.

Las cifras de evaluación final proceden de su informe cerrado, nunca de una nueva lectura del dataset test. Las cifras mostradas abajo se redondean para exposición; el catálogo conserva la precisión original. AP significa Average Precision, no accuracy. Precision/Recall/F1/AP y silhouette son adimensionales; los conteos se expresan en eventos. Las duraciones conservan la unidad especificada por cada variable: time_since_previous_login_hours utiliza horas; los tiempos de cómputo y de exposición indicados en segundos conservan esa unidad.

## Distribución narrativa y relación con el frontend

| Diapositiva | Sección frontend propuesta | Segundos | Fuente principal exacta |
|---|---|---:|---|
| 1. Portada | Proyecto | 15 | Fase-1-y-2-MINERIA-DE-DATOS.pdf, portada; README.md |
| 2. Contexto y problema | Problema, justificación y alcance | 35 | Fase-1-y-2-MINERIA-DE-DATOS.pdf, páginas 4–6, §§2.1–2.2 |
| 3. Objetivos | Objetivos originales desplegables | 50 | Fase-1-y-2-MINERIA-DE-DATOS.pdf, página 7, §§2.3–2.4 |
| 4. Metodología | CRISP-DM, datos, preparación y protocolos | 55 | INFORME_FINAL_FASE04_CRISP_DM.md; INFORME_PREPROCESAMIENTO_FASE04.md |
| 5. Despliegue | Estado del proyecto | 20 | README.md; docs/PLAN_FRONTEND_FASE05.md; frontend/README.md |
| 6. Árbol de decisión | Supervisados → árbol, CV1/CV2/anidada | 45 | fase04_modelado/resultados_cv_usuario/comparacion_modelos.csv, filas arbol_baseline/arbol_ponderado |
| 7. Naive Bayes | Supervisados → GaussianNB | 40 | Mismo CSV, filas gnb_baseline/gnb_ponderado |
| 8. KNN | Supervisados → KNN y ROS | 40 | Mismo CSV, filas knn_baseline/knn_ros |
| 9. K-Means | No supervisados → KMeans | 40 | fase04_clustering/resultados/candidatos.csv, algoritmo kmeans; INFORME_CLUSTERING_FASE04.md |
| 10. Jerárquico | No supervisados → Ward; Average como contraste exploratorio | 40 | fase04_clustering/resultados/candidatos.csv, algoritmos ward/average; INFORME_CLUSTERING_FASE04.md |
| 11. Modelo de referencia seleccionado: resultados y limitaciones | Comparación, RF, selección y evaluación cerrada | 90 | INFORME_DECISION_MODELO_FASE04.md; fase04_modelado/evaluacion_final_test_20261122/INFORME_EVALUACION_FINAL_TEST_FASE04.md |
| 12. Regresión e interpolación | Métodos numéricos, sensibilidad separada | 70 | fase04_metodos_numericos/resultados/resultados.json; fase04_metodos_numericos/revision_complementaria/resultados_sensibilidad.json |
| **Total** | | **540** | |

La tabla es un mapa editorial, no pantallas ya implementadas. Las tablas de todas las variantes y protocolos quedan disponibles en el catálogo, aun cuando una diapositiva solo pueda mostrar dos figuras.

## 1. Portada — 15 s

**Mensaje:** detección académica de Account Takeover con minería de datos.
**Contenido:** título, CRISP-DM y contexto hospitalario simulado. Autores, institución, asignatura y fecha de sustentación deben confirmarse antes del PPT; no se inventan.
**Fuente:** portada del PDF original y README.md para nombre del proyecto.
**Visual:** título y un diagrama mínimo «datos → evidencia → límites».
**Explicación oral:** el PowerPoint presenta el trabajo; la aplicación permitirá consultar evidencia detallada. No es un sistema hospitalario en producción.

## 2. Contexto y planteamiento del problema — 35 s

**Mensaje:** una credencial válida no garantiza que quien inicia sesión sea su titular.
**Contenido:** caso de hospital de alta complejidad con turnos 24/7; distinguir actividad legítima inusual de abuso de credenciales. Justificación: priorizar detección sin saturar con falsas alarmas. Alcance: experimentación académica con eventos sintéticos; no pacientes reales ni incidentes comprobados del hospital.
**Fuente:** Fase-1-y-2-MINERIA-DE-DATOS.pdf, páginas 4–6, §§2.1 y 2.2; docs/PROCEDENCIA_Y_LICENCIAS.md, RBA/IPinfo.
**Visual:** esquema de dos accesos con credenciales válidas, titular/suplantación. No usar mapas o identidades individuales del dataset.
**Explicación oral:** RBA sintetiza comportamiento de autenticación; IPinfo es un catálogo de redes reales aplicado a esos eventos, no otra fuente de logins sintéticos. La geografía enriquecida no acredita viajes reales.

## 3. Objetivo general y objetivos específicos — 50 s

**Mensaje:** contrastar la intención original con la evidencia obtenida, sin reescribir los objetivos después del experimento.
**Fuente exacta:** Fase-1-y-2-MINERIA-DE-DATOS.pdf, página física 7, §§2.3–2.4; también aparecen en Fase 1  2 y 3 MINERIA DE DATOS.pdf, página 8.
**Contenido original completo para notas y consulta frontend:**

> Desarrollar un modelo predictivo basado en minería de datos para identificar inicios de sesión sospechosos en el hospital, ayudando a detectar de forma automática cuándo un atacante externo está intentando suplantar la identidad de un empleado.

1. Fusionar tres fuentes de datos independientes: el registro histórico de autenticaciones (RBA Dataset), el catálogo de geolocalización IP-País (IPinfo) y el maestro sintético de personal hospitalario en un único archivo de trabajo en Python utilizando la librería Pandas.

2. Crear variables de comportamiento basadas en ciberseguridad, como el número de intentos fallidos para detectar “fuerza bruta” y la ubicación geográfica para detectar "viajes imposibles".

3. Entrenar un algoritmo de Árbol de Decisión que sea fácil de entender y graficar, permitiendo explicar de manera clara y visual por qué el sistema clasifica un acceso como normal o como ataque.

4. Evaluar el rendimiento del modelo utilizando métricas específicas para datos desbalanceados, esto con el fin de garantizar una alta efectividad en la detección de amenazas reales sin ir a saturar el sistema con falsas alarmas.

**Visual:** objetivo general y cuatro extractos literales breves, claramente indicados como extractos: «Fusionar tres fuentes de datos independientes…», «Crear variables de comportamiento basadas en ciberseguridad…», «Entrenar un algoritmo de Árbol de Decisión…», «Evaluar el rendimiento del modelo utilizando métricas específicas para datos desbalanceados…». El texto completo permanece en notas de esta misma diapositiva y en el frontend, no en una diapositiva extra.
**Explicación oral:** «garantizar una alta efectividad» es el propósito formulado originalmente, no un logro demostrado. Impossible Travel se construyó, pero se excluyó como predictor final por sus limitaciones. Los objetivos no se sustituyen por recomendaciones posteriores.
**Normalización documental:** solo espacios/saltos de línea y unión de IP-País; no se cambia su significado.

## 4. Metodología: proceso CRISP-DM y conclusiones — 55 s

**Mensaje:** trazabilidad y separación por usuario preceden a cualquier comparación.
**Contenido:** comprensión del negocio/datos → preparación → modelado → evaluación → despliegue académico en preparación. Integración RBA/IPinfo/personal sintético, corrección de 90 etiquetas y conjunto corregido de 57.420 eventos, 2.000 usuarios y 45 ATO. Train: 46.305 eventos, 1.600 usuarios, 36 ATO y 34 usuarios positivos. Partición por usuario 80/20, semilla 42.
Seis predictores: failed_attempts_15min, failed_attempts_1h (conteos), time_since_previous_login_hours (h), has_previous_login (0/1), Device Type y Country (categorías). Identificadores, target, geografía Impossible Travel y atributos aleatorios del personal no son predictores finales.
CV1 estratifica eventos con grupos; CV2 estratifica usuarios ATO/no ATO; anidada aprende umbral/configuración dentro del subtrain. Imputación/OHE y transformaciones se ajustan dentro de folds; ROS solo en subtrain. No reutilizar la matriz de todo train para validar.
**Fuentes:** INFORME_CORRECCION_TARGET_FASE03.md; INFORME_PARTICION_FASE04.md; INFORME_PREPROCESAMIENTO_FASE04.md; INFORME_REVISION_IMPOSSIBLE_TRAVEL_FASE04.md; INFORME_SEGUNDA_VALIDACION_FASE04.md; INFORME_FINAL_FASE04_CRISP_DM.md; docs/PROCEDENCIA_Y_LICENCIAS.md.
**Visual:** un flujo CRISP-DM con pequeñas etiquetas de datos, predictores y protocolos.
**Explicación oral:** el aprendizaje fue metodológico: corregir asociación del target y evitar fuga no garantiza una señal predictiva fuerte. No afirmar que todas las fases equivalen a despliegue productivo.

## 5. Despliegue del proyecto — 20 s

**Mensaje:** código publicado y aplicación pública son estados distintos.
**Contenido:** repositorio GitHub https://github.com/Javier-Gomez-Ovalle/Mineria_de_Datos; referencia remota main observada 17e2c72051092217aaea972fa08a8220207fa4d8. Frontend: base Vite/TypeScript local, sin despliegue público. Backend/base de datos no implementados en esta etapa.
**Fuentes:** README.md; frontend/package.json; frontend/README.md; comprobación de referencia remota de esta revisión, registrada en docs/REPORTE_ETAPA_INICIAL_FASE05.md.
**Visual:** dos estados «Repositorio publicado» / «Aplicación pendiente», no un enlace público inventado.
**Explicación oral:** actualizar el estado al elaborar el PPT solo si existe evidencia de despliegue real; la compilación local no lo demuestra.

## 6. Árbol de decisión — 45 s

**Mensaje:** reglas interpretables no implican detección suficiente.
**Contenido:** árbol divide por condiciones; ponderar penaliza más la clase minoritaria. CV2 a 0,5: baseline Precision 0,046875; Recall 0,083333; F1 0,060000; AP 0,008862. Ponderado: Precision 0,013158; Recall 0,250000; F1 0,025000; AP 0,015817. No atribuir estas métricas al modelo final con umbral aprendido.
**Fuentes:** fase04_modelado/resultados_cv_usuario/comparacion_modelos.csv; metricas_por_fold.csv en esa carpeta; INFORME_SEGUNDA_VALIDACION_FASE04.md.
**Máximo dos figuras:** fase04_modelado/resultados_cv_usuario/graficas/confusion_arbol_baseline.png y confusion_arbol_ponderado.png. Matrices de eventos absolutos, ejes clase real/predicha.
**Explicación oral:** ponderar incrementa detecciones y falsas alarmas. Explicar cómo funciona una regla sin inventar una ruta del árbol final ni presentar importancia como causalidad. CV1/anidada y variabilidad se consultan en frontend.

## 7. Naive Bayes — 40 s

**Mensaje:** alto recall aislado puede ser inutilizable por falsas alarmas.
**Contenido:** GaussianNB combina distribuciones gaussianas con independencia condicional aproximada; supuestos discutibles para dummies y ventanas relacionadas. En CV2 ambas variantes: Recall 0,861111; Precision 0,000850; F1 0,001698; AP 0,000840. No ocultar la coincidencia de resultados.
**Fuentes:** fase04_modelado/resultados_cv_usuario/comparacion_modelos.csv y metricas_por_fold.csv; INFORME_PREPROCESAMIENTO_FASE04.md, representaciones.
**Máximo dos figuras:** fase04_modelado/resultados_cv_usuario/graficas/confusion_gnb_baseline.png y confusion_gnb_ponderado.png.
**Explicación oral:** detectar la mayoría a costa de decenas de miles de falsas alertas no constituye éxito operativo. log1p no garantiza normalidad ni independencia.

## 8. KNN — 40 s

**Mensaje:** ranking y clasificación al umbral elegido son propiedades diferentes.
**Contenido:** voto de vecinos tras escalado; ROS solo en subtrain. CV2 baseline: TP 0, F1 0 y AP 0,043163; ROS: Precision 0,048077, Recall 0,138889, F1 0,071429, AP 0,012462.
**Fuentes:** fase04_modelado/resultados_cv_usuario/comparacion_modelos.csv y metricas_por_fold.csv; INFORME_SEGUNDA_VALIDACION_FASE04.md.
**Máximo dos figuras:** fase04_modelado/resultados_cv_usuario/graficas/confusion_knn_baseline.png y confusion_knn_ros.png.
**Explicación oral:** AP mayor no garantiza aciertos a 0,5. La interpretación depende de cercanía en el espacio transformado, no de una explicación causal. No mostrar observaciones individuales como vecinos.

## 9. K-Means — 40 s

**Mensaje:** segmentación geométrica no equivale a separar ataques.
**Contenido:** agrupa por cercanía a centroides, sin target. K=2; 41.296/5.009 eventos; silhouette 0,606043. Prevalencias ATO descriptivas 32/41.296 y 4/5.009, similares. K se eligió por índices internos/estabilidad, no por ATO.
**Fuentes:** INFORME_CLUSTERING_FASE04.md; fase04_clustering/resultados/candidatos.csv, kmeans k=2; evaluacion_externa_kmeans_2.csv; seleccion_congelada.json.
**Máximo dos figuras:** fase04_clustering/resultados/graficas/seleccion_interna.png y perfiles_kmeans_2.png. Indicar silhouette/DB/CH adimensionales y unidades de cada predictor del perfil.
**Explicación oral:** interpretar perfiles de actividad y tamaño, no etiquetar un cluster como atacante. Índices internos no son Precision/Recall.

## 10. Clustering jerárquico — 40 s

**Mensaje:** Ward muestra una estructura exploratoria sobre una muestra, no un detector.
**Contenido:** fusiones jerárquicas; Ward minimiza incremento de dispersión. Submuestra de 4.000 eventos por coste; K=2, grupos 3.534/466; silhouette 0,597778. Como contraste exclusivamente exploratorio, Average K=2 da silhouette 0,785401 pero grupos extremos 3.983/17. Estos resultados corresponden a Average, no a Ward; Ward es el procedimiento protagonista de esta diapositiva y de sus dos figuras.
**Fuentes:** INFORME_CLUSTERING_FASE04.md; fase04_clustering/resultados/candidatos.csv y evaluacion_externa_ward_2.csv.
**Máximo dos figuras:** fase04_clustering/resultados/graficas/dendrograma_ward.png y perfiles_ward_2.png. Dendrograma: distancia de enlace en espacio transformado; 25 ramas terminales por legibilidad, no 25 observaciones.
**Explicación oral:** no comparar conteos con KMeans como si ambas poblaciones fueran idénticas; tampoco presentar silhouette mayor como evidencia de detección ATO.

## 11. Modelo de referencia seleccionado: resultados y limitaciones — 90 s

**Mensaje:** árbol ponderado como procedimiento de referencia; no superioridad universal ni aptitud productiva.
**Contenido y comparación en tabla pequeña:**
- Reglas aprendidas/anidada externa: árbol ponderado TP 5, FP 54, FN 31, Precision 0,084746, Recall 0,138889, F1 0,105263. Es un equilibrio retrospectivo, no prueba independiente de victoria.
- GaussianNB ponderado: 31 aciertos y 38.839 FP; KNN baseline: 6 aciertos y 122 FP. Random Forest, extensión controlada: 4 aciertos, 158 FP y 32 FN; AP global 0,06021, mayor ranking relativo sin mejor equilibrio. No equiparar ranking con utilidad.
- Selección del umbral de referencia: 0,9976439543869569. F1 OOF usado para seleccionarlo: 0,173913; no estimación independiente. Scores OOF de tres árboles, transferencia al ajuste completo no garantizada.
- Evaluación final documentada: TP 1 / FP 12 / TN 11.094 / FN 8; Precision 0,076923; Recall 0,111111; F1 0,090909; AP 0,009267. Nueve ATO de nueve usuarios: gran incertidumbre, ocho omitidos.
**Fuentes exactas:** INFORME_DECISION_MODELO_FASE04.md; INFORME_DIAGNOSTICO_CAPACIDAD_PREDICTIVA_FASE04.md; fase04_modelado/mejora_controlada/resultados/comparacion_global.csv; fase04_modelado/recuperacion_referencia_v1_20261122/MANIFIESTO_MODELO_FINAL.json; fase04_modelado/evaluacion_final_test_20261122/INFORME_EVALUACION_FINAL_TEST_FASE04.md.
**Visual:** tabla comparativa de reglas aprendidas + matriz final transcrita de conteos documentados. No mezclar test de un modelo con CV de otros en un ranking.
**Explicación oral:** separar selección, estimación externa y evaluación cerrada. Pocos positivos, inestabilidad, datos sintéticos y geografía no fiable limitan generalización. Conclusión: trazabilidad reproducible lograda, detección insuficiente. Mejoras futuras son recomendaciones, no resultados. Ningún otro algoritmo se evalúa ahora sobre test.

## 12. Regresión lineal e interpolación de Lagrange — 70 s

**Mensaje:** dos ejercicios descriptivos distintos, sin causalidad ni extrapolación.
**Composición:** dos columnas, exactamente dos gráficas:
- fase04_metodos_numericos/resultados/graficas/regresion_lineal.png. Principal intacta: 5.662 pares, 5.633 en (0,0), x distancia (km), y velocidad (km/h). y = 2,6411940341 x − 7,0079848329. R² = 0,167134; r = 0,408821; RMSE = 2.371,4696 km/h. Pendiente en h⁻¹, intercepto en km/h. MSE = 5.623.867,9851 (km/h)² puede quedar en notas.
- fase04_metodos_numericos/resultados/graficas/interpolacion_lagrange.png. P(x) = −646,473854098942 + 0,778670072678091 x − 0,000088839509545728 x². x en km, P(x) en km/h; coeficientes dimensionales correspondientes. Intervalo cerrado [931,5694204688522; 7.821,982499064356] km. Tres nodos, error máximo en nodos 1,33×10⁻¹³ km/h; no extrapolar.
**Fuentes:** fase04_metodos_numericos/resultados/resultados.json, regresion/interpolacion/auditoria; INFORME_REGRESION_INTERPOLACION_FASE04.md en esa carpeta; fase04_metodos_numericos/revision_complementaria/INFORME_REVISION_COMPLEMENTARIA.md y resultados_sensibilidad.json.
**Explicación oral:** x/y comparten una relación de construcción velocidad=distancia/tiempo; asociación no implica causalidad. Los ceros dominan la regresión. Sensibilidad separada de 29 distancias positivas: pendiente 3,067009, intercepto −3.179,051793 km/h, r 0,323548, R² 0,104684, MSE 1.093.684.287,980527 (km/h)², RMSE 33.070,897901 km/h. Diagnóstico, nunca reemplazo del ajuste principal.
Los nodos históricos corresponden a cuartiles de distancias distintas y mediana inferior de velocidad dentro de cada nivel; la revisión anterior verificó registros reales, intervalo y rechazo de extrapolación. Esta etapa verifica documentación, no vuelve a abrir train. El polinomio interpola esos nodos, no demuestra capacidad predictiva general.
La figura complementaria de ceros/extremos se ofrece como referencia en frontend, no como tercera gráfica en esta diapositiva.

## Criterios antes de producir el PPTX

Validar esta narrativa, metadatos de portada y legibilidad con las figuras a tamaño real. Los títulos y ejes deben incluir unidades; tablas de clasificación en escala 0–1, matrices en eventos. No reutilizar indiscriminadamente el PowerPoint histórico: contiene cifras de fases preliminares. No añadir diapositivas. El catálogo no distribuye figuras todavía ni observaciones individuales; las rutas anteriores son referencias para la futura composición autorizada. Ningún test dataset fue leído ni se calculó su hash en esta etapa.
