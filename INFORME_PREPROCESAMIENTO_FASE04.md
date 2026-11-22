# Fase 4: seleccion y preprocesamiento

Fecha: 2026-11-18. Preparacion academica; no se entrenaron modelos ni se calcularon metricas predictivas.

## Resultado

Se fijaron seis predictores antes de transformar test. Se generaron tres representaciones de **62 columnas**, cada una con **46.305 filas de train y 11.115 de test**. Se mantienen 36 y 9 positivos respectivamente, en vectores y separados. No hay usuarios compartidos; se conserva el orden de los eventos y la trazabilidad por clave natural.

Los artefactos estan en `artefactos_preprocesamiento_fase04/`. Las matrices X son NPY float64, sin identificadores ni target. Los vectores y son NPY int8. Los CSV de trazabilidad conservan User ID como entero de 64 bits, timestamp, IP y fila_matriz (indice base cero). No convertir User ID a float al unir datos.

## Evidencia y escenario

Se inspeccionaron `fase03_refactor/fase03/features.py`, `pipeline.py`, `empleados.py` y el informe tecnico modular, ademas de `INFORME_EDA.md` dentro de `eda_20261025_171310.zip`, sin extraerlo ni ejecutar Fase 3.

El EDA usa hashes y etiquetas historicos, 44 usuarios positivos y datos sobremuestreados. Sus cruces con el target NO fundamentan esta seleccion. El informe tecnico modular tambien contiene descripciones antiguas de la retirada/reincorporacion del target; el codigo corregido es la referencia efectiva.

Escenario conservador adoptado: puntuar el intento antes de conocer su resultado, con el historial anterior del mismo usuario disponible. No se presume una zona horaria local ni una fecha de disponibilidad de fuentes externas. Seleccion conceptual y perfil de train; no se usaron resultados predictivos ni asociaciones de test con y.

La [documentacion oficial del dataset RBA](https://github.com/das-group/rba-dataset) define Login Successful como resultado del intento e Is Attack IP como pertenencia a datos de atacantes conocidos. No establece una fecha de disponibilidad por evento para esa segunda bandera. No se demuestra fuga ni utilidad por esa definicion: se excluye por incertidumbre temporal. Login Successful seria admisible en otro escenario, posterior al intento, previa validacion de su contrato temporal.

La misma fuente describe geografia e IP sintetizadas y advierte que ciudades/regiones no conservan las relaciones reales originales. Esto limita la interpretacion geografica, no impide estudiar contexto nominal sintetico. Country se conserva como contexto de acceso, sin interpretarlo como ubicacion real del hospital ni como medida de distancia.

## Inventario de las 35 variables

Nulos y cardinalidades corresponden exclusivamente a train. Un nulo no equivale a cero. Las columnas excluidas no se imputan ni codifican.

| Variable | Funcion/tipo | Nulos train | Decision y fundamento |
|---|---|---:|---|
| User ID | Identificador | 0 | Trazabilidad, fuera de X; conservar grupos para validacion futura |
| IP Address | Identificador de red | 0 | Trazabilidad, fuera de X; 13.643 valores y direcciones sintetizadas |
| Login Timestamp | Temporal | 0 | Trazabilidad; no codificar fecha absoluta ni asumir hora local |
| Login Successful | Resultado binario actual | 0 | Excluir en escenario previo al resultado |
| login_exitoso_normalizado | Resultado binario redundante | 0 | Excluir por el mismo motivo; duplicaria Login Successful |
| Device Type | Nominal/contexto | 0 | Incluir; cuatro categorias, tipo de dispositivo del intento |
| Is Attack IP | Bandera externa | 0 | Excluir; disponibilidad historica no acreditada, no fuga demostrada |
| Country | Nominal/geografia | 0 | Incluir; 54 categorias, contexto del intento; limitacion sintetica |
| Region | Nominal/geografia | 14 | Excluir; 238 valores y 14.374 guiones, geografia sintetizada |
| City | Nominal/geografia | 3 | Excluir; 1.235 valores y 14.132 guiones, granularidad no fiable |
| ASN | Identificador nominal de red | 0 | Excluir del baseline; 426 valores, redundancia con contexto geografico y ASNs artificiales; nunca magnitud continua |
| ip_country_code | Nominal/enriquecimiento | 10.101 | Excluir; redundancia y catalogo sin vigencia historica acreditada |
| ip_country_name | Nominal/redundante | 10.101 | Excluir; equivalente descriptivo del codigo |
| ip_asn | Identificador nominal/enriquecimiento | 11.196 | Excluir; fuente externa sin contrato temporal |
| ip_as_name | Nominal/redundante | 11.196 | Excluir; identidad del proveedor enriquecido |
| ip_as_domain | Identificador/redundante | 11.212 | Excluir; identidad del proveedor enriquecido |
| Nombre_Completo | Identificador sintetico | 0 | Excluir; sin informacion conductual real |
| Rol_Hospitalario | Nominal sintetica | 0 | Excluir; asignacion aleatoria, no observacion del usuario |
| Pais_Residencia | Nominal sintetica | 0 | Excluir; asignacion aleatoria |
| Ciudad_Base | Nominal sintetica | 0 | Excluir; depende del pais inventado |
| Turno_Asignado | Nominal sintetica | 0 | Excluir; no representa horario real |
| Estado_Cuenta | Nominal sintetica | 0 | Excluir; no representa estado historico de la cuenta |
| Fecha_Ingreso | Temporal sintetica | 0 | Excluir; se genera respecto a fecha de ejecucion, no al evento |
| failed_attempts_15min | Conteo retrospectivo | 0 | Incluir; actividad fallida reciente |
| failed_attempts_1h | Conteo retrospectivo | 0 | Incluir; persistencia en ventana mas larga, redundancia parcial con 15 min |
| has_previous_login | Binaria/historial | 0 | Incluir; distingue ausencia estructural del intervalo |
| previous_login_timestamp | Temporal/redundante | 1.600 | Excluir de X; se usa solo para validar linaje temporal |
| time_since_previous_login_hours | Numerica/temporal | 1.600 | Incluir; mediana train y bandera de historial existente |
| distance_previous_km | Numerica/geografia derivada | 40.643 | Excluir; 87,77% ausente, centroides y geografia sintetica |
| required_speed_kmh | Numerica/geografia derivada | 40.643 | Excluir; cobertura baja y derivacion de distancia/tiempo |
| impossible_travel | Binaria derivada/redundante | 0 | Excluir; cero mezcla no evaluable y evaluado sin alerta |
| is_outside_shift | Binaria sintetica derivada | 0 | Excluir; depende de turno inventado y hora sin validacion local |
| country_mismatch | Binaria sintetica derivada | 10.101 | Excluir; residencia inventada y catalogo externo |
| inactive_account_success | Binaria sintetica/resultado | 0 | Excluir; estado inventado y resultado actual |
| Is Account Takeover | Target | 0 | Solo y; nunca entra en transformadores |

ASN e indicadores de red podrian estudiarse en un experimento futuro dentro de train. Su exclusion actual es una decision conservadora de alcance, no evidencia de ausencia de poder predictivo. No se anadieron nuevas variables de IP/hora ni se recalcularon las caracteristicas de Fase 3.

## Ausencias y transformaciones

Las medianas aprendidas son 0 para ambos conteos y 31,357389166666664 horas para el intervalo. Los conteos no tienen ausencias en train; cero es su mediana observada, no un reemplazo universal. Los primeros 1.600 eventos de usuario carecen de intervalo. Se verifica que esta ausencia coincide exactamente con has_previous_login=0. Por ello no se agrega un segundo indicador identico. Inconsistencias, infinitos y magnitudes negativas producen error.

Las categoricas pasan por imputacion constante `Desconocido` y `OneHotEncoder(handle_unknown="ignore", sparse_output=False)`. Se normalizan guion/cadena vacia a ausente. `unknown` de Device Type se conserva como categoria observada. No hay ausencias en las dos categoricas seleccionadas de train: Desconocido no produce una columna aprendida en esta corrida. Una ausencia futura sin categoria aprendida, igual que una categoria nueva, produce ceros en ese bloque; no se aprende de test.

Se conservan todos los eventos y extremos. No se aplica clipping, PCA, RobustScaler, ordinal encoding ni sobremuestreo.

## One-Hot Encoding

- Device Type (4): `desktop`, `mobile`, `tablet`, `unknown`.
- Country (54): `AR, AT, AU, BD, BF, BG, BR, CA, CH, CL, CZ, DE, DK, DO, ES, FR, GB, GE, GR, GT, HK, HU, ID, IL, IN, IR, IT, JP, KE, KR, KW, KY, LV, MY, MZ, NG, NL, NO, NZ, PH, PL, PY, QA, RO, RU, SD, SG, SI, SK, TH, TR, UA, US, VE`.

Resultado: 58 columnas One-Hot + 3 numericas + 1 binaria = **62**. El orden exacto figura en `manifiesto_fase04.json` y `get_feature_names_out()` de cada preprocesador.

Como comprobacion posterior a fijar la seleccion, test contiene 53 filas con pais no visto en train y cero tipos de dispositivo nuevos. No se ampliaron categorias ni se cambiaron decisiones por este resultado. El bloque Country de esas filas se codifica a ceros.

## Representaciones por familia

| Representacion | Uso posterior | Numericas | Binaria y One-Hot |
|---|---|---|---|
| arbol | Arbol de decision | Mediana, sin escalado | 0/1 |
| gaussian_nb | Gaussian Naive Bayes | Mediana y log1p | 0/1 |
| distancias | KNN, K-means, jerarquico | Mediana, log1p y StandardScaler | 0/1, sin estandarizar categorias raras |

log1p comprime colas: en train el intervalo alcanza 8.757,14 horas y los conteos maximos son 20 y 28. No garantiza normalidad ni independencia. GaussianNB es un baseline aproximado: las dummies no son gaussianas y las dos ventanas estan relacionadas. Un Naive Bayes mixto seria una alternativa futura; no se usa MultinomialNB para magnitudes que no representan frecuencias de terminos ni se binarizan indiscriminadamente las continuas.

La media de las tres numericas despues de imputar y aplicar log1p es `[0.0908341877289412, 0.11957190210910196, 3.3902727008493043]`; sus escalas StandardScaler son `[0.2943750426173906, 0.36066816772488103, 2.425124205574646]`. Todos estos parametros proceden de train.

KNN y clustering comparten una geometria inicial justificada por escalas, no por etiquetas. Mantener dummies en 0/1 evita amplificar automaticamente paises raros; aun asi, la ponderacion relativa entre bloques y la redundancia de ventanas requieren validacion solo en train. K-means sobre mezclas numericas y categoricas codificadas tiene centroides fraccionarios; no representa por si mismo grupos de fraude. El jerarquico sobre 46.305 filas puede requerir memoria cuadratica (una matriz densa float64 completa ronda 17,2 GB); no se construyo esa matriz.

Las X no supervisadas son exactamente `X_*_distancias_fase04.npy`. No se entrenaron grupos, no se les entregaron etiquetas y no se decidieron distancias o hiperparametros a partir de y. Los y separados quedan disponibles solo para la etapa supervisada o una evaluacion externa posterior claramente delimitada.

## Arquitectura y prevencion de fuga

- `seleccion.py`: contrato de columnas, validacion, separacion X/y/claves. Una lista positiva excluye todas las demas columnas.
- `transformaciones.py`: fabricas de ColumnTransformer/Pipeline y API de ajuste que acepta solo X_train. Cada llamada fabrica un estado independiente.
- `ejecutar.py`: orquestacion, escritura exclusiva, relectura, hashes y manifiesto. Rechaza una carpeta de salida existente.
- `tests/test_preparacion.py`: pruebas unitarias adversariales e integracion con los archivos generados.

El ajuste recibe solo train. Test pasa exclusivamente por transform. Se compara la huella del preprocesador antes/despues de transformar test. La ejecucion repite el ajuste con train y compara matrices exactas para comprobar determinismo. No se ajusta ningun estimador predictivo.

Fase 3 usa rolling retrospectivo `closed='left'` por usuario y shift(1). Ademas de la inspeccion estatica, se verifico en ambos conjuntos que previous_login_timestamp corresponde al evento anterior del mismo usuario, es estrictamente anterior y produce el intervalo exportado. No se reejecutaron ventanas ni se consulto el RBA. El historial anterior de usuarios de test se considera disponible secuencialmente: esto no es evaluacion de primer acceso sin historial. La disponibilidad operativa de los resultados anteriores sigue siendo un supuesto a validar en despliegue.

**Validacion cruzada futura:** NO usar las matrices ya ajustadas con todo train como entrada de validacion cruzada para estimar rendimiento. En cada fold debe instanciarse `crear_preprocesador`, ajustarse exclusivamente con el subtrain y transformar su validacion. Usar grupos User ID (preferiblemente estratificacion por usuario con ATO), mantener usuarios enteros y reservar test para la evaluacion final. Estos artefactos corresponden al ajuste final sobre todo el train autorizado, no a folds preprocesados.

## Desbalance: diseno para la etapa posterior

Primero comparar baselines sin remuestreo. Para arbol, evaluar pesos de clase dentro de validacion agrupada; para GaussianNB, pesos muestrales si se justifica; KNN no ofrece class_weight equivalente. RandomOverSampler seria una alternativa solo dentro del subtrain de cada fold, despues del ajuste del preprocesamiento y antes del modelo. No crear copias antes de separar grupos, no remuestrear validacion/test ni clusters. No se aplico ninguna de estas estrategias ni se instalaron dependencias.

## Pruebas y verificacion

Comando desde la raiz:

```text
python -B -m pytest -p no:cacheprovider -q fase04_preparacion/tests/test_preparacion.py
```

Resultado final: **11 passed in 2.22s**, sin warnings ni skips. Antes de generar artefactos, la prueba de integracion se omitia explicitamente; la corrida final la incluye.

Se verifican independencia de target/identificadores, categorias nuevas no aprendidas, medianas y medias aprendidas solo con train aun ante test extremo, imputacion, ausencia de NaN/infinito, orden de filas, serializacion/relectura, claves y etiquetas alineadas, bloqueo de sobrescritura y entradas invalidas. La generacion verifico tambien reproduccion exacta de matrices y que transformar test no modifica estado. Estos controles demuestran el comportamiento ejercitado; no prueban eficacia predictiva ni eliminan incertidumbres de procedencia del dataset.

## Artefactos, uso y reproducibilidad

En `artefactos_preprocesamiento_fase04/`:

- `X_train_{arbol,gaussian_nb,distancias}_fase04.npy` y sus tres equivalentes `X_test_*`.
- `preprocesador_{arbol,gaussian_nb,distancias}_fase04.joblib`: solo transformadores ajustados.
- `y_train_fase04.npy`, `y_test_fase04.npy`.
- `trazabilidad_train_fase04.csv`, `trazabilidad_test_fase04.csv`.
- `manifiesto_fase04.json`: columnas, categorias, estadisticas de train, versiones, comprobaciones y SHA-256 de los otros 13 artefactos.

```python
import numpy as np
import joblib
X_train = np.load('artefactos_preprocesamiento_fase04/X_train_distancias_fase04.npy', allow_pickle=False)
y_train = np.load('artefactos_preprocesamiento_fase04/y_train_fase04.npy', allow_pickle=False)
prep = joblib.load('artefactos_preprocesamiento_fase04/preprocesador_distancias_fase04.joblib')
```

Para reproducir en otra carpeta nueva, desde la raiz, llamar `ejecutar(salida=Path('otra_carpeta_nueva'))`. El comando `python -B -m fase04_preparacion.ejecutar` usa la carpeta predeterminada y ahora rechazara sobrescribirla. Usar el entorno compatible; no cargar joblib de fuentes no confiables.

Versiones: Python 3.12.7, pandas 2.3.3, NumPy 2.3.4, SciPy 1.16.3, scikit-learn 1.7.2, joblib 1.5.2. Ninguna transformacion emplea aleatoriedad; se conserva la particion de semilla 42.

SHA-256 de entrada:

```text
dataset_train_fase04.csv
98d4d4970ada7bf11ec2e76f89e93c46c76c3d097043020598638547f977e53f
dataset_test_fase04.csv
90c50ab404c3fcef6cc33e59387aec4ac405f41200e6aa61c0f8bf1db43c72fa
dataset_final_modelo_corregido.csv (solo integridad, sin nueva reconciliacion)
7cdf551319fa3de9f8b5805a59ee07a83d7f51fc9dc3cebe8a3cc9d74aa584ab
```

## Limitaciones y cierre

Solo 34 usuarios positivos en train y 9 en test; 36/9 eventos ATO. Un caso cambia el recall de test 11,11 puntos porcentuales. Las filas de cada usuario estan relacionadas. La muestra enriquecida no estima prevalencia poblacional y el conjunto sintetico no valida aplicacion clinica ni productiva. La particion por usuario no garantiza generalizacion temporal a fechas futuras. No se eligieron variables por rendimiento: no se afirma que estos seis predictores sean optimos ni que la geografia aporte capacidad discriminante real.

No se modificaron Fase 3, datasets originales, particiones definitivas, ZIP ni preprocesador historico. No se ejecuto Git, entrenamiento, metricas, clustering ni sobremuestreo. La tarea se detiene con artefactos preparados y verificados.
