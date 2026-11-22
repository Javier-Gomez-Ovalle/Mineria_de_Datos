# Informe del procedimiento de referencia — Fase 4

Fecha: 2026-11-21. Se documenta una referencia académica; no se entrena ni evalúa un modelo.

## Dictamen y justificación

El procedimiento está suficientemente definido para solicitar autorización de **ejecución futura**. Modelo: árbol de decisión ponderado fijo; umbral: selección interna estratificada por usuario. No se solicita al usuario elegir un número de umbral ni completar parámetros.

La elección está expresamente indicada por el encargo: mayor F1 agregado de la variante arbol_ponderado en la validación anidada exploratoria. Se recalcularon desde sus predicciones guardadas TP=5, FP=54, TN=46.215, FN=31, Precision=0,08474576, Recall=0,13888889 y F1=0,10526316. Detectó cinco de 34 usuarios ATO, omitió 29 y generó FP en 33 usuarios. Estos resultados no acreditan un detector satisfactorio.

Es una **elección retrospectiva de referencia**, no una victoria de selección anidada: el selector histórico eligió otras familias en cuatro folds y tuvo resultados distintos. La autorización metodológica actual permite fijar esta familia como referencia, manteniendo explícito ese sesgo. No se reescribe el historial que concluía falta de ganador robusto.

## Inspección y coherencia

Se revisaron informes CV1, CV2, selección supervisada, validación anidada, diagnóstico y decisión tras Random Forest; fábricas de modelos y preprocesamiento, selección de columnas, particiones, selección de umbral y auditorías de ajustes. Se verificó el manifiesto de la mejora controlada y se inventariaron 501 archivos históricos permitidos, excluyendo test de hash/lectura.

Veinte auditorías del árbol ponderado (15 internas y cinco externas) tienen exactamente los parámetros de la fábrica actual, class_weight local y ausencia de ROS. Los cinco umbrales históricos se reprodujeron exactamente, incluidos empates y fracciones F1, usando únicamente OOF internas existentes. Se comprobó correspondencia de las 46.305 predicciones externas con índices, claves y etiquetas de train y se recalcularon sus métricas.

No se encontraron contradicciones materiales de parámetros o conteos. Las recomendaciones históricas cambiaron con protocolo/evidencia: CV1 resaltaba árbol baseline, selección exploratoria resaltaba ranking KNN, y anidada/mejora no recomendaron ganador. Eso no es inconsistencia del código. El nuevo árbol fijo es una decisión académica posterior, que no altera esas conclusiones.

La cifra 62 describe el vocabulario full train, no cada fold: las auditorías muestran 49–62 columnas para árboles. No reutilizar el vocabulario completo en validación interna para forzar dimensiones.

## Configuración completa y datos

La especificación normativa es [PROCEDIMIENTO_REFERENCIA_CONGELADO_FASE04.md](PROCEDIMIENTO_REFERENCIA_CONGELADO_FASE04.md). Incluye todos los parámetros del estimador, versiones, normalización de entradas, orden de las seis columnas, imputación, vocabulario local, desempates y protocolo futuro. Evidencia técnica y 62 nombres esperados en `fase04_modelado/referencia_congelada/evidencia_congelacion.json`.

Train autorizado: `dataset_train_fase04.csv`, SHA-256 `98d4d4970ada7bf11ec2e76f89e93c46c76c3d097043020598638547f977e53f`. Se verificaron 46.305 eventos, 1.600 usuarios, 36 ATO y 34 usuarios positivos. No se consultó test para obtener o verificar ninguna cifra.

X: failed_attempts_15min, failed_attempts_1h, time_since_previous_login_hours, has_previous_login, Device Type y Country. Target Is Account Takeover separado, trazabilidad por User ID/timestamp/IP.

El árbol usa mediana en las tres numéricas, indicador intacto y One-Hot denso sobre categóricas imputadas con Desconocido; categorías desconocidas ignoradas. No log1p ni StandardScaler para esta representación. Aprender todo exclusivamente del ajuste correspondiente. La creación de instancias sin fit para recuperar parámetros no constituye entrenamiento.

## Exclusiones que permanecen

| Grupo | Motivo vigente |
|---|---|
| User ID, timestamp e IP | Trazabilidad/agrupación; no memorizar identidades. |
| Login Successful y login_exitoso_normalizado actuales | Resultado no disponible en detección preautenticación; los fallos anteriores sí integran el historial. |
| Is Attack IP | Disponibilidad temporal de inteligencia no establecida. |
| Region, City, enriquecimiento IP | Semántica geográfica sintética y enriquecimiento sin contrato temporal validado. |
| distance_previous_km, required_speed_kmh, impossible_travel | Evaluabilidad incompleta, ceros ambiguos y coordenadas no fiables como desplazamiento físico. |
| Turnos, residencia y empleados | Atributos simulados sin evidencia conductual real suficiente. |

No se agregan características ni se recalculan existentes. La disponibilidad futura de historial pasado sigue siendo un supuesto del escenario.

## Selección del umbral y ejecución pendiente

Se conserva el procedimiento histórico: tres folds de usuarios estratificados por presencia de ATO, shuffle=True y random_state=42; cada preprocesador y árbol se ajusta solo en el subtrain. El umbral se elegirá por F1 exacto sobre OOF internas concatenadas por evento, candidatos scores únicos más 0, 0,5 y siguiente float sobre 1; empate por cercanía a 0,5 y luego mayor.

La aplicación futura se hará sobre todo train autorizado y con una sola familia fija. No hay bucle externo adicional ni nueva competición de familias. No se usan métricas externas para modificar parámetros o desempatar. Los valores históricos siguientes son evidencia de reproducción, **no candidatos manuales para el umbral definitivo**:

| Fold externo histórico | Umbral aprendido dentro de su subtrain |
|---|---:|
| 1 | 0.9975534930682306 |
| 2 | 0.9976028261418118 |
| 3 | 1 |
| 4 | 0.9978844270323213 |
| 5 | 0.999263291450088 |

El umbral definitivo queda pendiente de ejecutar la regla congelada con autorización. No se infiere su valor de estos cinco umbrales. La dimensión final y medianas se verificarán tras el ajuste autorizado, sin cambios silenciosos.

Tras obtener el umbral se ajustarán un nuevo preprocesador y árbol sobre todo train, se serializarán y se congelarán hashes/esquema/decisión. Solo después, y con autorización expresa, se ejecutará una evaluación única de test. El protocolo incluye métricas por evento y usuario, matriz/PR/AP, trazabilidad y detención ante incumplimientos. No habrá modificación del umbral tras ver test. Ninguno de estos pasos se ejecutó ahora.

## Limitaciones y riesgos

36 positivos no permiten estimar rendimiento con precisión; 34 usuarios son la unidad positiva independiente aproximada, no 36 eventos independientes. Ocho ATO comparten las seis entradas con 621 negativos. F1 agregado histórico favorece al árbol ponderado, pero omite 31/36 ATO; umbrales cercanos a uno e inestabilidad entre folds advierten transferencia frágil. Random Forest no resolvió el problema.

F1 es criterio académico, no coste operacional. No existe presupuesto de falsas alarmas ni garantía de utilidad en producción. La selección de familia mira resultados externos exploratorios ya conocidos: test intacto aporta una evaluación posterior reservada, pero no borra el sesgo de selección de los resultados históricos. No se establecerá un umbral arbitrario para declarar éxito después de ver test.

La ausencia de contradicciones documentales y las verificaciones de implementación no prueban generalización ni causalidad. No se demuestra imposibilidad universal de detectar ATO.

## Entrega y estado

Se crean este informe, la especificación congelada, el informe de autorización y evidencia de hashes/verificaciones. README recibe exclusivamente una adenda para reflejar la referencia, conservando íntegro su contenido anterior y conclusiones. No se modifica código ni artefactos de entrenamiento. Cero ajustes nuevos; cero evaluaciones test; ninguna operación Git; ninguna dependencia instalada.

Pendiente: autorización explícita de ejecución del procedimiento y de evaluación final. La configuración está definida; el valor numérico del umbral y los artefactos ajustados todavía no existen. **Fase 4 sigue abierta.**

