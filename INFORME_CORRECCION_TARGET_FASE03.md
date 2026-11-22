# Informe de corrección del target ATO de Fase 3

Fecha de intervención: 18 de noviembre de 2026 (America/Bogota).

La implementación modular fue extraída y verificada; se corrigió el transporte de la etiqueta durante la ingeniería de características y se generó `dataset_final_modelo_corregido.csv`. Sus 57.420 etiquetas coinciden individualmente con el RBA original. Las únicas diferencias respecto al enriquecido anterior son 90 etiquetas; las otras 34 columnas conservan incluso su representación en bytes.

Esta intervención termina en la recuperación del enriquecido. Los train/test preparados y el preprocesador anteriores permanecen intactos y no deben interpretarse como artefactos ya corregidos.

## A. Diagnóstico

### Causa y archivos involucrados

La versión autorizada de `fase03/pipeline.py` retiraba el target en la línea 79 mediante `pop`, ejecutaba las funciones de features y lo reincorporaba en la línea 88 desde una serie externa. Entretanto, `fase03/features.py:108` ordenaba los eventos por usuario y timestamp y ejecutaba `reset_index(drop=True)`.

Los índices numéricos reutilizados ya correspondían a otros eventos. La asignación conservaba la cantidad de positivos, pero cambiaba su asociación. Una prueba que comprobara únicamente ese conteo no detectaría el defecto.

El ZIP modular autorizado es la base de esta intervención. No se utilizó el monolito histórico como sustituto. La secuencia defectuosa explica exactamente las 90 discrepancias: 45 eventos originalmente negativos recibieron True y los 45 ATO originales recibieron False.

### Fuente de verdad y alcance

- Enriquecido original: `dataset_final_modelo_actualizado.csv`.
- Fuente de verdad: `[fuente externa]/rba_dataset.csv`.
- Clave de correspondencia: `User ID + Login Timestamp + IP Address`.
- El target no forma parte de esa clave.
- Se contrastaron también Device Type, Country, Region, City, ASN, Login Successful e Is Attack IP: cero diferencias en todos ellos.

Los resultados de este informe son comprobaciones ejecutadas en esta intervención. La inversión de permutación se utilizó únicamente como comprobación independiente; las etiquetas del archivo nuevo proceden de la unión uno a uno con el RBA.

## B. Extracción

- ZIP: `fase03_etapa1_modular_escalada_lista_para_test_y_train.zip`.
- SHA-256: `c44533f698b039911f02b1241b53e61800f67a753c2abbeae8ca86da181d8b0e`.
- Prefijo extraído: `fase03_etapa1_modular/fase03_refactor/`.
- Destino: `fase03_refactor/`.
- El destino no existía antes de la extracción.
- Se validó el CRC del ZIP y se verificó que ninguna ruta escapara del destino.
- Se crearon los archivos en modo exclusivo, sin sobrescribir archivos.
- Se extrajeron **25 archivos, incluidos los 23 Python**.
- Antes de modificar código se comprobó la igualdad SHA-256 de cada archivo con el miembro correspondiente del ZIP.
- El ZIP original permanece intacto.

La extracción conserva módulos, punto de entrada, pruebas, documentación, README de fixtures y copia legacy. La carpeta de fixtures no incluye los datasets de pruebas históricas.

### Archivos extraídos verificados

| Ruta relativa a fase03_refactor | SHA-256 al extraer |
|---|---|
| `Automatizar_empaquetado.py` | `4410920426f945dc60751517ec863e0f6747fcd275e4c22e3c451540f2c390c4` |
| `docs/FASE_03_INFORME_TECNICO.md` | `a56b7f1fb75e61d4df85cf29a9c5baf4cd93e9d8ad67c772bc2c299784d607af` |
| `fase03/config.py` | `81b543886643f7ba980d429b6f655101235b18799e8f0d705f5a9ad1e161c6ea` |
| `fase03/diagnostico.py` | `4bcd72a1b1ad624b88a2f45daab1bdfb03e7d38d9213d05f1e210fb63be6a866` |
| `fase03/empleados.py` | `9c658276749b4582d65ca9b3a35f3b7f1641a2ff44f05ba92639850ca4f0808e` |
| `fase03/exportacion.py` | `2395ef904ba4b8f064dc76648f801a8200ad4a9a696091a5887d12e590d23816` |
| `fase03/features.py` | `0f5c2a52df8c27ec0b57d6afaf1e69beab8ef11a294123e8846c1af5ac3d2263` |
| `fase03/ip_resolver.py` | `bd3e038d02489248cf640ce0a76165fb959e150e9ec6e99ca997dccf2cbdb1a1` |
| `fase03/ip_utils.py` | `825dd5f257f84536eba2a175c633acb40d5b66602b748d93e7f0dfbb40490a12` |
| `fase03/muestreo.py` | `65e2d47ee3b3e634f8ec1e4f233c29b64c094295466ecd80fe709447332ec027` |
| `fase03/pipeline.py` | `e25ca3b8194e3c8f52540146551d51e8b9a0243271386f02a6fe591790f3ea6c` |
| `fase03/preprocessing.py` | `317c67deadf05cad660c345db30e35fc9243ebe76fa28a18911990d6b5ac5dc0` |
| `fase03/rba_reader.py` | `c6f202e5c5ed3adaf4957fc5dfc1c04c8f97464e1c30c1297acdb1c392913a77` |
| `fase03/resampling.py` | `c28686390f13f7272d266481ad9e01b7e01ff7da85a6083c09def308ca5635ff` |
| `fase03/split.py` | `18b8afea32a49a858f0a1dbacae06bcad3b7bcd523148c2c127a618e778a91fb` |
| `fase03/timestamp_utils.py` | `86a729e466b842846d2e7e56cabb925dabf9146998d10a5a75e92a74044b7aa6` |
| `fase03/validacion.py` | `9a1a0fe55cf06f06fdbc400bfd24e76beba1e79f3dcceeefbb723d918963b687` |
| `fase03/__init__.py` | `71bce4fbc6f1f1a7e5ec67286a33ddef3e48e32e2419fc9c2caa1c0719b3f17f` |
| `main.py` | `156950b664d093c94b9de195420b5074449cd37e37ffba030f24191602088cd3` |
| `tests/comparar_pipelines_colab.py` | `19c7c0e8b6c5898220525a57e86dcfbf03ab283eb4afad1bbb83e9f83b464555` |
| `tests/conftest.py` | `54ac1091abd01fc6c711a46d9aad1b50db2341fa7877ef850d7a7fd202a630c2` |
| `tests/fixtures/README.md` | `cb63cc0d36be07dd7eb602a5f4ff8f67f2bd5c5702addec933a32b61f79d31f3` |
| `tests/legacy/fase03_pipeline_v4.py` | `a4447dc9528a63dfe38a4290121759daa268119ba2491270e1bf6eece5a594cd` |
| `tests/test_fase03.py` | `5709f594e949692eba29c77ca977bcb522f942d809429ae5e21fa8fde87170a6` |
| `tests/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

## C. Código corregido

### Cambios sobre los archivos extraídos

| Archivo | Cambio |
|---|---|
| `fase03/pipeline.py` | Conserva el target como columna durante las features. Captura y verifica la asociación antes/después por clave de evento. Elimina pop y reasignación por índice. |
| `fase03/features.py` | Actualiza exclusivamente el docstring que describía la antigua retirada del target. No cambia las fórmulas, umbrales ni transformaciones. |

Los otros **23 archivos extraídos** siguen siendo idénticos al ZIP.

### Archivos de código y pruebas añadidos

| Archivo | Responsabilidad |
|---|---|
| `fase03/asociacion_target.py` | Captura la referencia por clave y valida columnas, claves únicas/no nulas, etiquetas, número de filas, identidad y asociación evento-target. |
| `fase03/reconciliacion_target.py` | Lectura del RBA por bloques, reconciliación exacta y preparación de bytes del CSV corregido sin recalcular features. No escribe archivos por sí mismo. |
| `tests/test_correccion_target.py` | Regresión del defecto e invariantes de asociación; prueba el bloque real de features del orquestador. |
| `tests/test_reconciliacion_target.py` | Contratos de reconciliación y conservación exacta de los campos ajenos al target. |

La solución respeta snake_case, PascalCase y la distribución modular. No añade paquetes. Las funciones nuevas no mantienen DataFrames como estado global.

### Asociación estable y prevención de fuga

La etiqueta viaja dentro del mismo DataFrame que su evento. La comprobación usa la clave de negocio, no posiciones o índices de pandas. El timestamp se canoniza en una copia de referencia, con la utilidad existente, para admitir su conversión Unix/texto a datetime. No se modifica el DataFrame de entrada al construir esa referencia.

Se rechazan claves nulas, vacías o duplicadas, pérdida de la columna target, valores inválidos, cambios en el número de filas, sustitución de eventos y cambios de etiquetas incluso cuando el número de positivos permanece igual.

El target ya no está físicamente ausente durante las features. Las funciones actuales no lo leen para calcular características; la prueba metamórfica verifica que invertir las etiquetas no cambia ninguna otra columna. La exclusión del target de X permanece en el preprocesamiento existente, que no se ejecutó en esta intervención.

### Firmas del código nuevo o modificado

| Archivo | SHA-256 final |
|---|---|
| `fase03/pipeline.py` | `ab1193664c706d1bc23ab550db41fa2b5b087b48ef923783b6945d93698862ba` |
| `fase03/features.py` | `91e9e101b3831ac92d80ffb757086d87fa2e3faa9fed323f78682e0729037f75` |
| `fase03/asociacion_target.py` | `4b633c92ca0723ec7b416c19b067531be1837ee66689b544e49d0a01235e67d6` |
| `fase03/reconciliacion_target.py` | `bf09cb6e7cb1340374deeca4af4e976ea5f016320c3039abc73c1944a6721744` |
| `tests/test_correccion_target.py` | `2b4b248efa2995ef6c363c430605d9362d73634f55f9d1681bb2e03bc6ac7788` |
| `tests/test_reconciliacion_target.py` | `a94d29b25b5442553129004e11f0216db0d61463604790c854941dc5b6a2e6dc` |

## D. Reconciliación

### Procedimiento ejecutado

1. Lectura por bloques de 250.000 filas, con columnas seleccionadas.
2. Retención exclusiva de los eventos de los 2.000 usuarios del enriquecido.
3. Registro de la posición original de lectura para la comprobación independiente de la permutación.
4. Validación de claves en ambos conjuntos y unión externa con `validate="one_to_one"`.
5. Rechazo de eventos ausentes/adicionales y discrepancias en atributos.
6. Recuperación del target original y restitución del orden de filas del enriquecido.
7. Comparación individual con la hipótesis de inversión de la permutación.

| Comprobación | Resultado |
|---|---:|
| Eventos examinados en cada pasada completa | 31.269.264 |
| Eventos retenidos de los usuarios seleccionados | 57.420 |
| Usuarios seleccionados | 2.000 |
| Correspondencias únicas | 57.420 |
| Claves duplicadas en ambos conjuntos reconciliados | 0 |
| Eventos ausentes | 0 |
| Eventos adicionales | 0 |
| Correspondencias ambiguas | 0 |
| Discrepancias en atributos compartidos | 0 |
| Etiquetas discrepantes antes | 90 |
| Etiquetas coincidentes antes | 57.330 |
| Positivos originales | 45 |
| Negativos originales | 57.375 |
| Usuarios con ATO originales | 43 |
| Errores de la inversión respecto al original | 0 |

### Matriz anterior

Las filas representan el target original y las columnas el del enriquecido anterior. No son métricas de un clasificador.

| Original | Anterior negativo | Anterior positivo |
|---|---:|---:|
| Negativo | 57.330 | 45 |
| Positivo | 45 | 0 |

### Matriz posterior

| Original | Corregido negativo | Corregido positivo |
|---|---:|---:|
| Negativo | 57.375 | 0 |
| Positivo | 0 | 45 |

### Coste e incidencia de ejecución

La ejecución que produjo el archivo completó la lectura en **112.26 segundos**, utilizando 126 bloques. La lectura, validaciones, escritura y relectura verificadora ocuparon **114.35 segundos**. El máximo de RSS observado en los puntos de progreso de esa lectura fue **286806016 bytes**, aproximadamente 286.81 MB; no es una medición continua del pico de todo el proceso.

**Se realizaron dos pasadas completas en esta intervención.** El primer intento llegó a las validaciones de reconciliación y del CSV en memoria, pero se interrumpió antes de escribir al comprobar los archivos originales protegidos: la transmisión de un nombre con acentos desde PowerShell a Python lo convirtió en una ruta inválida y produjo OSError. Ningún artefacto de salida se había escrito. Al terminar el proceso se perdió la correspondencia en RAM.

Se corrigió la transmisión usando JSON con escapes Unicode y se adelantó la comprobación de todas las rutas protegidas al inicio. La segunda pasada fue necesaria para recuperar nuevamente las etiquetas de la fuente de verdad. No se sustituyó la reconciliación por una corrección basada solo en la permutación.

En conjunto se examinaron 62.538.528 filas contando la repetición, sobre un archivo de 9.052.907.531 bytes: aproximadamente 18,11 GB de contenido secuencial entre ambas pasadas. Esta cifra no mide tráfico de red ni caché de Drive. No se copió el RBA ni se calculó su hash completo. Su tamaño y mtime no cambiaron durante la lectura satisfactoria.

## E. Dataset corregido

- Ruta: `dataset_final_modelo_corregido.csv`.
- Tamaño: **16399088 bytes**.
- Forma: **57.420 filas × 35 columnas**.
- Positivos: **45**; negativos: **57.375**.
- Usuarios: **2.000**, de los cuales **43** tienen ATO.
- SHA-256: `7cdf551319fa3de9f8b5805a59ee07a83d7f51fc9dc3cebe8a3cc9d74aa584ab`.

El original preservado tiene SHA-256 `cc916ccbb6cdbdb70fb434b552dd0130fe5b4e8ab7667b81930d72b6b2f148c7`.

### Evidencia de integridad

El escritor sustituye únicamente el último campo booleano de cada registro. Conserva la cabecera, el orden de filas/columnas, los prefijos de cada registro, las representaciones numéricas, comillas, nulos, caracteres y saltos de línea. Se comprobó previamente que este CSV no contiene registros multilínea y que el target es la última columna; otros formatos se rechazan explícitamente.

Antes de escribir se releyeron los bytes candidatos con pandas y se ejecutó `assert_frame_equal(..., check_exact=True)` sobre las 34 columnas distintas del target. También se compararon los dtypes inferidos y la máscara de nulos. Se verificó que el target candidato coincidiera con las 57.420 etiquetas recuperadas del original, en el mismo orden.

El archivo se creó en modo exclusivo (`xb`) y después se volvió a leer: sus bytes coinciden exactamente con los validados y sus etiquetas coinciden con la serie original recuperada.

| Condición de cierre | Resultado |
|---|---|
| Misma cantidad de filas y columnas | Cumplida |
| Mismos usuarios y registros | Cumplida |
| Mismo orden de filas y columnas | Cumplida |
| Filas perdidas o duplicadas | 0 |
| Diferencias en las otras 34 columnas | 0 |
| Bytes ajenos al target preservados | Sí |
| Nulos preservados | Sí |
| Dtypes inferidos preservados | Sí |
| Etiquetas diferentes frente al enriquecido anterior | Exactamente 90 |
| Etiquetas diferentes frente al RBA original | 0 |
| Características derivadas recalculadas | Ninguna |

### Huellas por columna no target

Además de la comparación exacta y la conservación de bytes, se registran las huellas de los valores e índices de cada columna. Se calculan con SHA-256 sobre los bytes devueltos por `pd.util.hash_pandas_object(serie, index=True)` en pandas 2.3.3. Estas huellas dependen de la representación/versión; la igualdad no se fundamenta únicamente en ellas.

| Columna | Huella |
|---|---|
| `User ID` | `084e96df9b314c15b7cce614835fa07e26cd6de9c98107a217dad8af1ccc2030` |
| `IP Address` | `e48b069c6944a4942a9585a04f39b6453895cc88f53b69f32b955b1a4a626655` |
| `Login Timestamp` | `c50234f8f9513dc8a4b095cf51a619dcba99a1a753da8619997b711e5a68d7a9` |
| `Login Successful` | `23d497a65e5fbbe2567a77fa25a850b10137beade65e2f0bc231cb649605a8d5` |
| `login_exitoso_normalizado` | `23d497a65e5fbbe2567a77fa25a850b10137beade65e2f0bc231cb649605a8d5` |
| `Device Type` | `eb2a7b00314e66fdae00a0b4016166ed6e38d399054beaf3278172822a3628a1` |
| `Is Attack IP` | `0cd31fd6be9769f455270257c8d4332e0d323fac0ea663d4008991c60802a6f6` |
| `Country` | `806a760c9e44c1fefbf98c3ec47f725eb7258a23573ce1c9b87e42c8cbdb0410` |
| `Region` | `d9c8ae610d59a96024def38a06c9a9a832c4530ae5c8b1b8169ff524867bbf85` |
| `City` | `46b640e6b52e17f0b76165d2085da07146d0bacc72e468ae1caf625ffc62f9e5` |
| `ASN` | `a986541b4cd0a1aba0e496461bea2eefc70010998027226a2df00fa148e137b8` |
| `ip_country_code` | `3fd8ac9a52d1c75164e9a812cfcbcc94ae741ece548501aab5abba281984bcd8` |
| `ip_country_name` | `c02ac0cfb6d1f5afe7153ef150d6ec8120a9609d6bc20be01303e0aedc246354` |
| `ip_asn` | `3bcfc9fdd5a75737609b41f1981395c9cdf0e615a069ab1c2faa9ed085dff6bd` |
| `ip_as_name` | `6b1659bbc90dc1082ed762b7b978a0b18dcd89ce95504c076a5a6af4540cd938` |
| `ip_as_domain` | `b86421d8410c41df841107124deb72935d9dbaef7fe1bad9f9ef6f20f0a22888` |
| `Nombre_Completo` | `62c07c91012a3fe37d795798de00b8e2586a68fa35d56595aa70fe18624e7638` |
| `Rol_Hospitalario` | `76fc5ba56de782d9a97e3650c13687e62ad0ca6629c22c3973371f12444111ca` |
| `Pais_Residencia` | `467eb7f742cd0eb20712478e3f02beee668f131b56e9611e75f746acfd094e26` |
| `Ciudad_Base` | `a02fe644fd29bbe43ff1087df5db2276384455f6a346f3691fda6f6a6d21e902` |
| `Turno_Asignado` | `407eaea716beb99877c84e414987ecef334557b362a2e775950f35f43c0ac23c` |
| `Estado_Cuenta` | `2a459acb01a35c7adf8b9ede1d9ed4ae8d3fdb2a0bc4a29fdae7e59fa8838074` |
| `Fecha_Ingreso` | `a19edf366f931dc5873dfde98f32d5f2531b18823f7ab181715b8b69d36cca59` |
| `failed_attempts_15min` | `762f5fcf3d27c1315e5f1e4a04c70c21d9ea2c70a519da3ae3ce6d9b58b2023b` |
| `failed_attempts_1h` | `8ba7bb6fbd9aa9d8cffff7c5264fc75d2d73781440e9a56400ea6b2e926f29c4` |
| `has_previous_login` | `95d13fa79e7769193cedb3cef10b1ac9625794e5b478d9b1a3b946e54af8346f` |
| `previous_login_timestamp` | `62716064dbb3e5ceed4bf6b4e976266abf543ef82a4f649822567216b440fc34` |
| `time_since_previous_login_hours` | `649ef1bf6a70d75ab53e3f7d77af846df8d06eec2192863d0a936acd5d8dc3b2` |
| `distance_previous_km` | `d6d315f1e34f3b4c27e82a891ec8c4c7257b1d8ebfec5408287cc67dfedb96f0` |
| `required_speed_kmh` | `ac0e9931dde44b4234910e1eeb048b315370303475bd7a2655c3e53e5375d31a` |
| `impossible_travel` | `3dee00e0e807835b4c825dd7c6e490cb7da4850d33df4c98ee65214033cdfe5c` |
| `is_outside_shift` | `c3f91742e7837f1834199b742571d426a2ae409df0328f36c312cf83a072ca5b` |
| `country_mismatch` | `c56449921fab6f9c021dafcf3ef700f4954e0cbe0832b8871bc3fc4487109e57` |
| `inactive_account_success` | `3a4bc25c4bea91772f02ffdb30ca5b5dab4cdcfa08be45ff9862cceda8932af9` |

## F. Pruebas

### Ejecución y resultados

Desde `fase03_refactor/`:

```powershell
python -B -m pytest -p no:cacheprovider -q tests/test_correccion_target.py tests/test_reconciliacion_target.py
```

Resultado final: **31 pruebas aprobadas, 0 fallidas, 0 omitidas en esta selección**, en 3,54 segundos. Antes de incorporar las pruebas de reconciliación se ejecutaron las 20 de asociación, también aprobadas; no se suman como pruebas distintas al total final.

Se analizó sintácticamente la totalidad de los **27 archivos Python** presentes tras los añadidos, sin errores. No se generaron cachés de Python ni de pytest en el proyecto.

### Cobertura de las pruebas específicas

- Reproduce el pop, ordenamiento, reset_index y reasignación del código original; conserva el conteo positivo y demuestra que la guarda rechaza la asociación errónea.
- Ejecuta el bloque corregido real de features del orquestador y comprueba la etiqueta por identificador único de evento.
- Acepta reordenamientos y reinicios de índices, incluso si los índices originales se repiten.
- Rechaza pérdida de etiquetas, filas eliminadas o añadidas, duplicados y sustituciones de eventos con igual número de filas.
- Rechaza targets nulos o inválidos, claves nulas y columnas duplicadas.
- Verifica la conversión de timestamps Unix a datetime sin perder la asociación.
- Comprueba que cambiar las etiquetas no modifica las features.
- Comprueba que las guardas no mutan el DataFrame de entrada.
- Rechaza coincidencias ambiguas, eventos ausentes/adicionales y discrepancias en atributos originales.
- Verifica que la serialización conserve precisión textual, comillas, acentos, nulos y saltos de línea.
- Rechaza número incorrecto de etiquetas y CSV multilínea.
- Conserva el CSV idéntico cuando no hay etiquetas que cambiar.

El test de integración aislada obtiene mediante AST el bloque de features de `PipelineFase03.ejecutar` y ejecuta ese bloque con las funciones reales. Evita importar los servicios de lectura/generación y ejecutar el pipeline completo. No es una prueba end-to-end de Fase 3.

### Límites de ejecución

No se ejecutó la suite histórica completa: contiene ejecuciones del pipeline, preparación, sobremuestreo y escrituras fuera de este alcance. Tampoco se instalaron sus dependencias ausentes, como Faker en el intérprete del proyecto. Las 31 pruebas específicas y la reconciliación completa son las verificaciones efectivamente ejecutadas; no se atribuye aprobación a pruebas no ejecutadas.

Entorno utilizado: Python 3.12.7, pandas 2.3.3, NumPy 2.3.4, scikit-learn 1.7.2, pytest 9.1.1. No se deserializó `preprocessor.joblib`, no se ajustó ningún preprocesador y no se entrenó ningún modelo.

## G. Estado del proyecto

### Archivos creados y modificados

- Carpeta nueva `fase03_refactor/`: 25 archivos extraídos y cuatro añadidos, 29 archivos en total.
- Dentro de la extracción se modificaron únicamente `fase03/pipeline.py` y el docstring de `fase03/features.py`.
- Nuevos módulos: `fase03/asociacion_target.py`, `fase03/reconciliacion_target.py`.
- Nuevas pruebas: `tests/test_correccion_target.py`, `tests/test_reconciliacion_target.py`.
- Nuevo CSV: `dataset_final_modelo_corregido.csv`.
- Nuevo informe: `INFORME_CORRECCION_TARGET_FASE03.md`.

Se preservaron los 15 archivos preexistentes del repositorio inspeccionados (excluyendo metadatos internos de Git), verificando sus hashes antes y después de generar el CSV. La documentación histórica extraída se conserva; este informe documenta la corrección sin sobrescribirla.

| Archivo preexistente | SHA-256 preservado |
|---|---|
| `.gitignore` | `ca05615cce6a90316cf5d04477ae1ab6da3276a0de743cbf12fd953ff71dc624` |
| `dataset_final_modelo_actualizado.csv` | `cc916ccbb6cdbdb70fb434b552dd0130fe5b4e8ab7667b81930d72b6b2f148c7` |
| `dataset_test_prepared.csv` | `be82f93cf4399174ea21d68c913d9161635d9d653c7d79167137058c68a0b233` |
| `dataset_train_prepared.csv` | `d2f1225d9bc6e63134c963ed0eb4b68ca015b894b1af636974c8990e214dbe38` |
| `eda_20261025_171310.zip` | `0f323c16ae30a52caccd4ed5510a9d45cb99d0266773e86b1258f16c2e6fc2ea` |
| `empleados.csv` | `c0eee01a06161fede87d27672b67931db8ac26c5dc4c35761f7871284ade96aa` |
| `Fase 1  2 y 3 MINERIA DE DATOS.pdf` | `ca5b3afb514ce49f3b3b4021e4c94af34ef3546157329dc041b4f455e641031c` |
| `Fase-1-y-2-MINERIA-DE-DATOS.pdf` | `f9b6afbddc24c16d33c8b82cc3865e9a9eadc5efb617baec6005a8e49209365c` |
| `fase03_etapa1_modular_escalada_lista_para_test_y_train.zip` | `c44533f698b039911f02b1241b53e61800f67a753c2abbeae8ca86da181d8b0e` |
| `Informe parcial EDA.docx` | `bad2cf2a2cce87cbd06a9f3fc5ea9d3ae172dfeabd4202870ce71ca720498a66` |
| `Pitch Minería de Datos — Detección de Account Takeover (CRISP-DM).pptx` | `7d98efc3adf481a510b996f7a402126d3018b89458d7db14d6c8c83d93660af9` |
| `preprocessor.joblib` | `dfb32bfe38e0309a14bdd5211c6248600f664a99aed37c4e81c2be7c371d07ea` |
| `rba_2000_users.csv` | `c21d3e8593b5666ffabf153d58f40bb4c797738ad7e1d3cdc3a587bfd5328db3` |
| `README.md` | `87409d1d1fc65c0365097efef5cdc3bffb160cef682fdd5d702bd795a7f4a468` |
| `.vscode\settings.json` | `b3f38d5469db454a51c0c705ae9160a4e133df1f23c19f7086cce7169a544aa9` |

### Git

La rama permanece en `fase04-modelado`, que era la rama activa al comenzar. No se cambió de rama, no se hizo stage, commit ni push y no se modificó el remoto. Antes de esta intervención el estado era limpio. Los entregables nuevos quedan sin seguimiento:

```text
?? INFORME_CORRECCION_TARGET_FASE03.md
?? dataset_final_modelo_corregido.csv
?? fase03_refactor/
```

No hay cambios en archivos ya versionados; las modificaciones de código descritas son respecto a los miembros originales del ZIP, dentro de una carpeta nueva.

### Cierre y siguiente autorización

Las etapas autorizadas de extracción, corrección del mecanismo y reconstrucción del enriquecido quedan completadas. Las verificaciones reproducen las 90 discrepancias y acreditan cero discrepancias después de corregir.

Se conserva el contenido original de train, test y preprocessor. No se generó una partición nueva, no se aplicó sobremuestreo, no se ejecutaron clasificadores ni clustering y no se inició Fase 4. La revisión del enriquecido corregido y la preparación posterior requieren una autorización independiente.

La validación certifica correspondencia con este RBA y preservación de las features existentes; no acredita la veracidad externa de las etiquetas del RBA ni vuelve a validar científicamente las características derivadas.
