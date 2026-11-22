# Procedimiento de referencia congelado — Fase 4

Fecha: 2026-11-21. Identificador: referencia_arbol_ponderado_v1.
Estado: **protocolo congelado; umbral numérico y modelo final todavía NO calculados**. Test cerrado. Este documento no autoriza ejecución.

## 1. Población y entradas

Única entrada para selección y entrenamiento futuro: `dataset_train_fase04.csv`.
SHA-256: `98d4d4970ada7bf11ec2e76f89e93c46c76c3d097043020598638547f977e53f`.
46.305 eventos, 1.600 usuarios, 36 ATO, 46.269 negativos, 34 usuarios con ATO. Mantener todas las filas y su orden original. User ID como entero de 64 bits; nunca convertirlo a float.

Target: `Is Account Takeover`, validado binario no nulo y convertido a int8. Clave de trazabilidad: User ID + Login Timestamp + IP Address, sin nulos ni duplicados. Clave y target nunca entran a X.

Orden exacto de X:
1. failed_attempts_15min
2. failed_attempts_1h
3. time_since_previous_login_hours
4. has_previous_login
5. Device Type
6. Country

Aplicar `fase04_preparacion.seleccion.separar_datos`. Numéricas e indicador a float; rechazar infinitos, negativos, indicador fuera de 0/1 y ausencia de intervalo que no coincida con has_previous_login=0. Categóricas object; nulos, cadena vacía y "-" se normalizan a np.nan. No recodificar otras categorías.

## 2. Preprocesamiento

Usar `crear_preprocesador('arbol')` de `fase04_preparacion/transformaciones.py`, verificado por hash en la evidencia adjunta. Cada ajuste crea instancia nueva; ningún transformador ajustado histórico se reutiliza.

Orden de salida:
- Bloque num: las tres primeras entradas, SimpleImputer(strategy='median', keep_empty_features=True). Sin log1p ni escalado.
- Bloque bin: has_previous_login, passthrough.
- Bloque cat: Device Type, Country; SimpleImputer(strategy='constant', fill_value='Desconocido'), seguido de OneHotEncoder(categories='auto', drop=None, handle_unknown='ignore', sparse_output=False, dtype=float64, min_frequency=None, max_categories=None, feature_name_combiner='concat').
- ColumnTransformer(remainder='drop', verbose_feature_names_out=True, sparse_threshold=0.3, n_jobs=None, transformer_weights=None). Pipelines sin caché. Imputadores con missing_values=np.nan, copy=True, add_indicator=False; keep_empty_features=False en el categórico. Numérico fill_value=None. No se modifica la fábrica aprobada.

Ajustar medianas y vocabularios únicamente sobre cada subtrain. Transformar su validación sin fit. Las categorías nuevas se representan con ceros en su bloque One-Hot; no se aprende un vocabulario con validación/test. Si una numérica no tiene observaciones, detenerse como exige ajustar_train.

Full train contiene cuatro dispositivos y 54 países: se esperan 62 columnas (3+1+4+54). La lista nominal completa está en `fase04_modelado/referencia_congelada/evidencia_congelacion.json`, campo columnas_esperadas_full_train; se deriva de categorías observadas sin ajustar un transformador ahora. El modelo final deberá registrar get_feature_names_out y comprobar esta lista. **No imponer 62 columnas a folds internos**: el número depende de las categorías de su ajuste. Los ajustes históricos del árbol tuvieron entre 49 y 62 columnas.

## 3. Estimador y entorno

DecisionTreeClassifier, variante arbol_ponderado. Parámetros completos:
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

Sin sample_weight adicional, ROS, SMOTE, calibración, poda/búsqueda de hiperparámetros ni selección de familias. class_weight='balanced' calcula n_ajuste/(2*n_clase_ajuste) exclusivamente con y del ajuste correspondiente. El árbol no tiene n_jobs. Para predecir usar predict_proba, localizar la columna cuya classes_ sea 1 y comparar score >= umbral; no usar predict como sustituto de esa regla. Lotes de predicción de 512 eventos como implementación histórica; trabajar con el mismo orden y sin redondear scores.

Entorno verificado:
```json
{
  "python": "3.12.7",
  "numpy": "2.3.4",
  "pandas": "2.3.3",
  "sklearn": "1.7.2",
  "scipy": "1.16.3",
  "joblib": "1.5.2"
}
```
No cambiar versiones para la ejecución final sin revisar y versionar el protocolo antes de abrir test. No se instala nada ahora.

## 4. Umbral definitivo: regla congelada, valor pendiente

Aplicar `construir_particiones(y, usuarios, n_splits=3)` de `fase04_modelado/validacion_anidada/particiones.py` **a todo train autorizado**, cuando se autorice ejecutarlo:
- Una fila por User ID, groupby(sort=True); estrato=max(target) por usuario.
- StratifiedKFold(n_splits=3, shuffle=True, random_state=42) sobre esa tabla.
- Expandir usuarios a posiciones de eventos originales, orden ascendente de posiciones.
- Ningún usuario compartido; ambos labels en cada ajuste/validación; cada usuario y evento exactamente una vez en validación.
- Ajustar tres árboles y tres preprocesadores locales. Generar una única probabilidad OOF por evento para arbol_ponderado. Conservar índices, claves, folds, y_true y score con precisión float64 suficiente (CSV %.17g y lectura round_trip).

Pasar exclusivamente estas OOF nuevas de train a `seleccionar_umbral` de `fase04_modelado/validacion_anidada/seleccion_umbral.py`.
Candidatos: np.unique(concatenación de scores OOF, 0.0, 0.5, np.nextafter(1.0,np.inf)=1.0000000000000002).
Predicción positiva si score >= t.
Maximizar **F1 por evento sobre las OOF concatenadas**, Fraction(2*TP, 2*TP+FP+FN), sin redondear ni promediar F1 por fold.
Empates exactos: menor abs(t-0.5); después mayor t. No colapsar candidatos con predicciones equivalentes.
t=0 permite alertar todos; t>1 permite ninguno. Mantener estas políticas aunque el resultado sea desfavorable.

No optimizar F2/recall/AP en sustitución de F1, no calibrar, no usar y externa, no promediar ni votar los cinco umbrales históricos. 0.5 solo es candidato y punto de desempate, no valor final impuesto. No reutilizar como umbral definitivo la selección exploratoria CV1/CV2 ni los umbrales por fold. No ejecutar ahora la nueva partición/selección ni obtener su valor.

## 5. Secuencia futura, sujeta a autorización

1. Verificar hashes/versiones/contratos de train y fuentes congeladas.
2. Ejecutar únicamente la selección interna de tres folds descrita, sin búsqueda adicional.
3. Guardar OOF, tabla de candidatos, decisión/empates y umbral numérico. Congelar su hash antes de acceder a test.
4. Crear un preprocesador nuevo y ajustar en todo train; transformar train y ajustar un único árbol con parámetros congelados y pesos locales full train. Este será el cuarto ajuste, tras los tres internos.
5. Guardar modelo, transformador, esquema, clases, umbral, versiones, hashes y log en una carpeta final nueva; validar serialización con datos de train. No sobrescribir artefactos históricos.
6. **Solo con autorización expresa para evaluación final**, abrir test una vez. Transformar con el preprocesador final sin fit y evaluar ese único modelo/umbral. Validar esquema, claves, labels y separación de usuarios como controles bloqueantes, no como selección de datos. Conservar todos los eventos; si falla un contrato, detenerse sin reparar silenciosamente.
7. Persistir score, predicción, target y claves; TP/FP/TN/FN, Precision, Recall, F1, F2, especificidad, FPR, AP, PR, falsas alarmas y métricas por usuario. Definir usuario ATO detectado solo si se alerta correctamente al menos un ATO suyo. Incluir usuarios sin ATO con alerta. No presentar accuracy como criterio principal.
8. Reportar resultados una vez sin ajustar nada a su vista. AP test corresponde a un único estimador y se distingue de AP OOF concatenada y media por fold históricas. No comparar nuevos candidatos en test.

## 6. Inmutabilidad y alcance

Después de abrir test no cambiar datos, predictores, exclusiones, imputación/OHE, familia, parámetros, semilla, estratificación, objetivo, desempates ni umbral. No descartar casos, ajustar clases, elegir otra métrica para redefinir éxito ni volver a seleccionar un modelo. Un fallo técnico exige documentar la incidencia; no autoriza búsqueda o una segunda evaluación oportunista.

La elección fija del árbol responde a la decisión académica del usuario basada retrospectivamente en F1 agregado. No es el selector conjunto histórico: elimina su búsqueda entre familias. La extensión de la regla interna de tres folds a todo train queda definida aquí para el ajuste final futuro; todavía no ha sido ejecutada. Los resultados históricos no son una estimación independiente libre de sesgo de esta elección retrospectiva.

No se afirma ganador ni detector satisfactorio. Solo 36 ATO/34 usuarios positivos, solapamiento de entradas y alta inestabilidad. Test no garantiza precisión estadística por estar reservado. No existe criterio operativo de aceptación; F1 es referencia académica. Fase 4 no está terminada.

