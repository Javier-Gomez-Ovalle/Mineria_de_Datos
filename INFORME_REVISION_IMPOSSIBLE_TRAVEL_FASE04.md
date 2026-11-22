# Revisión técnica de Impossible Travel — Fase 4

Fecha: 2026-11-18. Alcance: inspección de código y análisis descriptivo exclusivamente de train, sin target, entrenamiento ni cambios en artefactos existentes.

## Diagnóstico y recomendación

**Existe un problema de representación corregible:** `impossible_travel=0` mezcla imposibilidad de evaluar con ausencia de alerta. Es defendible construir un indicador explícito de evaluabilidad y conservar una alerta nullable. Sin embargo, **corregir la representación no valida la interpretación física de la señal**. La geografía es sintética, el diccionario es incompleto y cada país se reduce a un único punto.

Recomendación: mantener estas variables fuera del preprocesamiento principal actual. Conservar la propuesta de representación para una futura rama experimental, versionada y expresamente descrita como heurística sobre geografía sintética. No se demuestra que carezcan de señal predictiva; tampoco se ha demostrado que aporten señal útil. La baja cobertura por sí sola no justifica descartarlas definitivamente.

No se incorpora todavía `travel_evaluable` a X: describe principalmente la cobertura del diccionario, no la normalidad del usuario. Esta revisión crea únicamente este informe.

## 1. Fuentes inspeccionadas y alcance

- `fase03_refactor/fase03/features.py`: orden temporal, Haversine, distancia, velocidad y alerta.
- `fase03_refactor/fase03/config.py`: 18 puntos geográficos; umbral 800 km/h y ventana de 12 horas.
- `fase03_refactor/fase03/pipeline.py` y `asociacion_target.py`: secuencia de cálculo y conservación de la asociación evento-target.
- `fase04_preparacion/seleccion.py`, `transformaciones.py`, `ejecutar.py`: lista de predictores, ajuste exclusivo con train y exportación.
- `INFORME_PREPROCESAMIENTO_FASE04.md`: exclusiones y justificación anterior.
- [Documentación oficial del RBA](https://github.com/das-group/rba-dataset), consultada el 2026-11-18.

Se leyó `dataset_train_fase04.csv` con `usecols` limitado a diez campos de identidad, país, tiempo y viaje. **Is Account Takeover no se cargó en el análisis.** No se analizaron test ni el conjunto completo, ni se leyó el RBA original. Para integridad se calculan hashes de archivos, sin utilizar sus valores como observaciones.

Train contiene 46.305 eventos de 1.600 usuarios. SHA-256:

`98d4d4970ada7bf11ec2e76f89e93c46c76c3d097043020598638547f977e53f`

## 2. Funcionamiento actual exacto

### Evento anterior

`crear_features_temporales` ordena por User ID y Login Timestamp, reinicia el índice y aplica `groupby(User ID).shift(1)` a timestamp y Country. El anterior es **el intento inmediatamente anterior**, sea exitoso o fallido; no necesariamente la última sesión autenticada. Esto impide interpretar automáticamente los dos extremos como viajes realizados por la misma persona.

El intervalo es `(timestamp_actual - timestamp_anterior).total_seconds() / 3600`. `has_previous_login` indica presencia del timestamp anterior. `previous_country` no se exportó al CSV, pero puede reconstruirse en memoria desde Country y el historial completo del usuario. Esta revisión lo reconstruyó únicamente para atribuir causas y contrastar cálculos.

### Distancia

Se buscan Country actual y previous_country en `CENTROIDES_GEOGRAFICOS`. Si falta alguna entrada, sus coordenadas son NaN. Haversine usa radio terrestre de 6.371 km:

`a = sin²(Δlat/2) + cos(lat_anterior) cos(lat_actual) sin²(Δlon/2)`

`distancia = 6371 × 2 × arcsin(sqrt(a))`

Ángulos convertidos a radianes. Si cualquier coordenada es NaN, la distancia es NaN. Sin historial se fuerza NaN. No usa ip_country_code, IPinfo, ciudades ni coordenadas observadas del dispositivo. Dos eventos del mismo país cubierto producen distancia cero aunque en realidad pudieran estar separados por miles de kilómetros.

El diccionario fija puntos representativos; el código no calcula centroides geométricos ni documenta su precisión o procedencia. No corresponde tratarlos como posiciones observadas de cada login.

### Velocidad y alerta

Se calcula `required_speed_kmh = distance_previous_km / time_since_previous_login_hours` solamente si la distancia no es NaN y el intervalo es no nulo y estrictamente positivo. Sin historial se fuerza NaN.

La alerta empieza en cero para todas las filas. Pasa a uno si simultáneamente:

1. Existe historial y distancia/intervalo calculables.
2. `required_speed_kmh > 800.0`.
3. `time_since_previous_login_hours < 12.0`.

Por tanto, **800 exactos no activan alerta y 12 horas exactas tampoco**. Es una regla de velocidad más una restricción temporal, no un umbral aislado. La comparación y las unidades implementan correctamente esa regla. No hay evidencia aquí para afirmar que 800 sea el umbral óptimo o físicamente calibrado para este dataset.

Un cero puede significar: sin anterior; país desconocido; punto geográfico ausente; intervalo no válido; velocidad menor o igual a 800; o intervalo fuera de la ventana, incluso con velocidad superior a 800. No significa necesariamente desplazamiento normal, ni ausencia de ATO.

## 3. Cobertura y causas en train

Evaluable significa calculable para velocidad, sin imponer todavía la ventana de alerta de 12 horas. Causas mutuamente excluyentes por prioridad: sin anterior → país desconocido → falta de punto → tiempo inválido → evaluable. País desconocido incluye nulo, vacío o marcador explícito; un código conocido sin entrada en el diccionario se clasifica aparte.

| Estado | Eventos | % de train |
|---|---:|---:|
| Evaluable | 5.662 | 12,2276 % |
| No evaluable, total | 40.643 | 87,7724 % |
| Sin login anterior | 1.600 | 3,4554 % |
| País actual/anterior desconocido, teniendo anterior | 0 | 0 % |
| Falta de punto geográfico, con países disponibles e historial | 39.043 | 84,3170 % |
| Intervalo nulo/no finito, teniendo anterior y puntos | 0 | 0 % |
| Intervalo cero/negativo, teniendo anterior y puntos | 0 | 0 % |

Los 1.600 países anteriores nulos de los primeros eventos se atribuyen a ausencia de historial, no se cuentan otra vez como país desconocido. No hay países actuales desconocidos según el criterio anterior.

De los 39.043 eventos sin puntos: 38.663 carecen de ambas entradas, 190 solo de la actual y 190 solo de la anterior. El diccionario contiene 18 países y omite `NO`. Noruega aparece en **36.532 eventos actuales** de train. Otras ausencias frecuentes son PL (1.218), UA (609), RO (329) y CZ (249). Estos conteos por país actual incluyen primeros eventos y no deben sumarse como si fueran la partición causal anterior.

**Corrección del porcentaje contextual:** el porcentaje comprobado es 40.643 / 46.305 = 87,7724 %. El 70,8 % se aproxima a 40.643 / 57.420 = 70,7819 %, que mezcla el numerador de train con el total global. Esa es una posible explicación del dato citado, no una procedencia demostrada. Esta revisión no estima de nuevo la cobertura global porque el análisis está limitado a train.

## 4. Distribución de magnitudes calculables

Estadísticas sobre los 5.662 eventos calculables, sin imputación:

| Estadística | Distancia (km) | Velocidad (km/h) |
|---|---:|---:|
| Mínimo | 0 | 0 |
| Percentil 25 | 0 | 0 |
| Mediana | 0 | 0 |
| Percentil 75 | 0 | 0 |
| Percentil 95 | 0 | 0 |
| Percentil 99 | 0 | 0 |
| Media | 21,7810 | 50,5199 |
| Desviación estándar muestral | 402,2544 | 2.598,7733 |
| Máximo | 8.724,7395 | 175.310,9592 |

Hay 5.633 distancias cero (99,4878 % de los calculables) y solo 29 positivas. Existen ocho valores distintos de distancia y treinta de velocidad. En los 29 desplazamientos positivos, distancia mínima/mediana/máxima = 734,0189 / 931,5694 / 8.724,7395 km; velocidad mínima/mediana/máxima = 0,2696 / 51,1897 / 175.310,9592 km/h. No se eliminaron extremos.

| Resultado entre calculables | Eventos |
|---|---:|
| Velocidad menor o igual a 800 | 5.653 |
| Velocidad estrictamente mayor que 800 | 9 |
| Mayor que 800 y dentro de ventana menor que 12 horas | 9 |
| Mayor que 800 pero fuera de ventana | 0 |
| Calculables fuera de ventana de 12 horas, cualquier velocidad | 2.718 |

Las nueve alertas son el 0,0194 % de train y el 0,1590 % de los calculables. Son alertas heurísticas, no nueve ATO comprobados: no se consultaron etiquetas. Los 46.296 ceros originales se descomponen exactamente en 40.643 no evaluables y 5.653 evaluables sin alerta.

## 5. Verificaciones realizadas y límites de la evidencia

En memoria se comprobaron los 46.305 registros, sin ejecutar el pipeline:

- El timestamp anterior coincide con shift(1) del mismo usuario y es estrictamente menor al actual cuando existe. No se encontraron empates temporales con el anterior en train.
- El indicador de historial coincide con la presencia del timestamp anterior.
- El intervalo exportado coincide con la diferencia temporal.
- Haversine reconstruida desde Country anterior/actual y el diccionario existente coincide con la distancia exportada, incluyendo NaN.
- Distancia / intervalo coincide con velocidad exportada, incluyendo NaN.
- La regla estricta de 800 km/h y 12 horas coincide con todas las etiquetas `impossible_travel` exportadas.

Distancia y velocidad se contrastaron con tolerancias rtol=1e-10 y atol=1e-8; la alerta se comparó exactamente. No se recalcularon ni guardaron columnas del dataset; los cálculos auxiliares sirven únicamente de contraste.

Por inspección estática, el cálculo no usa target ni eventos posteriores. Pipeline mantiene el target unido al evento y valida identidad/etiqueta mediante clave User ID + Login Timestamp + IP Address antes y después de ingeniería. Esa validación de asociación no certifica fiabilidad geográfica. No se volvió a auditar ni usar el target en esta revisión.

La causalidad temporal del cálculo se sustenta en shift(1) y los timestamps contrastados. No demuestra que en una operación real Country llegara al sistema con latencia cero, ni que el catálogo representara ubicaciones históricas. Para despliegue haría falta ese contrato de disponibilidad. En un futuro caso con timestamps empatados, se necesita una política explícita: no asumir que el orden arbitrario de filas establece causalidad.

## 6. Representación alternativa propuesta, no implementada

Separar validez de distancia, evaluabilidad de velocidad y ventana de la regla:

```text
distance_valid = existe_anterior AND países_disponibles
                 AND ambos_puntos_finitos_validos
                 AND distancia_finita_no_negativa

travel_evaluable = distance_valid AND intervalo_finito_positivo
                   AND velocidad_finita_no_negativa

travel_in_window = travel_evaluable AND intervalo < 12

impossible_travel_nullable = NA, si travel_evaluable = 0
                            int(velocidad > 800 AND intervalo < 12), en otro caso
```

Mantener `distance_previous_km` como NaN si la distancia no es válida y `required_speed_kmh` como NaN cuando no se puede evaluar velocidad. Una distancia podría ser válida con tiempo inválido; no debe borrarse solo por ello. En train actual ambas coberturas coinciden, pero no es una garantía general.

Para evitar cambiar silenciosamente la regla histórica, no sustituir su alerta por `velocidad > 800` a secas. Si se necesita ese indicador puro, llamarlo `speed_over_800_nullable` y mantener separada la ventana de 12 horas. Fuera de ventana una alerta cero significa “no satisface la regla”, no normalidad.

Guardar para auditoría una causa principal, con prioridad documentada, y banderas de causas concurrentes cuando proceda: sin_anterior, pais_actual_desconocido, pais_anterior_desconocido, punto_actual_ausente, punto_anterior_ausente, tiempo_invalido, coordenadas_invalidas. No inventar que toda ausencia procede de un país desconocido.

Una categórica alternativa puede representar `no_evaluable`, `evaluable_fuera_ventana`, `evaluable_en_ventana_sin_alerta`, `alerta`. Si se seleccionara como predictor nominal, usar OneHotEncoder ajustado exclusivamente en train. Para diagnósticos conviene conservar aparte el motivo de no evaluabilidad. No es necesario introducir todas las codificaciones redundantes simultáneamente.

En modelos que exigen números completos, imputación de magnitudes solo con train y bandera explícita de evaluabilidad. Aquí la mediana válida es cero: imputar por mediana sin bandera volvería a confundir ausente con cero observado. Incluso con bandera, la geometría de KNN/clustering puede quedar dominada por cobertura; no hay una imputación que recupere la información geográfica que falta. No imputar la alerta desconocida como “no alerta” sin conservar su estado.

## 7. Riesgos metodológicos y alternativas

La documentación oficial indica que países, IP y timestamps fueron sintetizados; los países se asignaron por valor de característica y las ciudades/regiones no conservan las relaciones originales. Esto limita la interpretación de distancias como viajes reales. [Fuente oficial](https://github.com/das-group/rba-dataset#data-creation).

Inferencias de esta revisión: la magnitud física puede reflejar el procedimiento de síntesis, puntos representativos y cambios de IP, en lugar de movilidad. Además, login anterior y actual podrían pertenecer a actores distintos; VPN/proxies también impiden identificar inequívocamente el lugar de la persona. Una velocidad extrema no demuestra desplazamiento físico ni compromiso de cuenta.

Ampliar el diccionario, especialmente con Noruega, aumentaría cobertura computacional, pero no restauraría geografía real. No se añadieron entradas ni se escogieron países según el target. Cualquier ampliación futura debe versionar fuente, cobertura y cálculo, evitando mezclar distancias calculadas con catálogos diferentes.

Como alternativa conductual futura, `country_changed` nullable puede comparar Country con el país del intento anterior cuando ambos existen. No requiere centroides, distancia ni umbral de velocidad y mide cambio de contexto nominal, no viaje físico. Requiere revisión y pruebas propias; no se generó ni se incorporó ahora.

## 8. Pruebas necesarias antes de una incorporación futura

1. Casos unitarios independientes para primer evento, país actual/anterior nulo, código sin punto, coordenadas no finitas y fuera de rango, intervalo nulo/cero/negativo; comprobar razones diferenciadas.
2. Casos de distancia cero válida y positiva; distancia conservada con tiempo inválido; alerta NA para no evaluable.
3. Límites 800 exactos, inmediatamente por debajo/encima; 12 horas exactas y alrededor del límite. Preservar la regla histórica estricta.
4. Control numérico de Haversine (puntos idénticos, separados, cercanos a antípodas); acotar a [0,1] el argumento auxiliar por errores de redondeo si se implementa una nueva versión. El código actual no lo acota; no produjo discrepancias en train.
5. Invariancia de prefijos: añadir eventos futuros no cambia eventos anteriores; aislamiento entre usuarios; política de empates temporales y filas desordenadas.
6. Cambiar o eliminar el target no modifica ninguna característica. Validar claves, orden y cantidades al incorporar resultados.
7. Contrastar estado evaluable/alerta con los valores existentes donde son válidos; verificar que ningún NA se convierta semánticamente en normalidad.
8. Ajustar imputación, One-Hot y escalado solo en subtrain de cada fold; transformar validación/test sin refit. Casos de categorías nuevas y fold sin valores válidos deben tener una política explícita, nunca una mediana inventada.
9. Comprobar hashes, versionado, relectura y bloqueo de sobrescritura de artefactos históricos. Luego, si se autoriza modelado, evaluar la rama por usuarios dentro de train, manteniendo test reservado; esa evaluación no se ejecuta aquí.

## 9. Decisión final

**Sí puede repararse la representación de no evaluabilidad sin usar el target ni información futura. No basta para justificar incluir las magnitudes físicas en el baseline actual.** Se mantiene su exclusión del preprocesamiento principal y se recomienda una rama experimental explícita antes de reconsiderarla. La propuesta conserva 800 km/h y 12 horas, no modifica datasets ni preprocesadores y no afirma poder predictivo.

Esta revisión no cambia código ni artefactos anteriores. Solo se crea `INFORME_REVISION_IMPOSSIBLE_TRAVEL_FASE04.md`. No se entrenaron modelos, no se calcularon asociaciones con y, no hubo sobremuestreo ni operaciones Git.
