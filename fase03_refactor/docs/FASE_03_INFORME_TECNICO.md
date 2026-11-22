# Fase 03 — Informe Técnico (CRISP-DM: Data Preparation)

**Proyecto:** Desarrollo de un modelo predictivo para la detección de anomalías de autenticación mediante la metodología CRISP-DM en el sector salud.
**Etapa de este informe:** Etapa 1 — Refactor arquitectónico sin cambios metodológicos.

---

## 1. Objetivo de esta etapa

Migrar `fase03_pipeline_v4.py` (script monolítico, ~1.550 líneas, validado funcionalmente) hacia una arquitectura modular mantenible, **sin alterar ningún resultado ya obtenido**: mismos usuarios seleccionados, mismo `empleados.csv`, misma resolución IP, mismas features, mismas validaciones. El objetivo de Etapa 1 es exclusivamente arquitectónico — el problema metodológico del muestreo (0 positivos en la muestra) se resuelve en la Etapa 2, después de ejecutar el diagnóstico pendiente sobre los usuarios con `Is Account Takeover = True`.

## 2. Fuentes de datos

Sin cambios respecto al README maestro: RBA Dataset (sintético, ~33M+ eventos), catálogo IPinfo (rangos IP → país/ASN), maestro de empleados 100% sintético anclado a `User ID` reales del RBA. Ver `README_FASE_03_CRISP_DM_53_FASES.md` para el detalle completo — este informe no lo duplica.

## 3. Naturaleza sintética de los datos

El RBA, IPinfo (uso real de un catálogo público, pero el enriquecimiento resultante se usa dentro de una simulación) y `empleados.csv` se tratan como material exclusivamente académico. Ninguna afirmación de este pipeline debe interpretarse como descripción de un hospital, empleado o paciente real.

## 4. Arquitectura del pipeline

```
fase03/
├── config.py            # ConfiguracionPipeline (dataclass) + constantes de dominio
├── ip_utils.py           # clasificar_ip, diagnosticar_ipv4_ipv6 (funciones puras)
├── timestamp_utils.py    # inferir_unidad_timestamp, convertir_login_timestamp (funciones puras)
├── rba_reader.py         # AnalizadorRBA (clase: 1ª y 2ª pasada por chunks)
├── muestreo.py           # EstrategiaMuestreo (ABC), ResultadoMuestreo,
│                         #   MuestreoAleatorioSimple, MuestreoEstratificadoPorTarget (pendiente)
├── empleados.py          # GeneradorEmpleados (clase)
├── ip_resolver.py        # ResolutorIPinfo (clase; incluye el fix de dtype de merge_asof)
├── features.py           # Funciones: temporales, impossible travel, turnos, negocio
├── validacion.py         # validar_calidad_bloqueante (función)
├── diagnostico.py        # generar_metricas_diagnosticas, imprimir_checklist_final (funciones)
├── exportacion.py        # exportar_dataset_final (función)
└── pipeline.py           # PipelineFase03 (clase orquestadora)

main.py                   # punto de entrada ejecutable

tests/
├── conftest.py            # fixtures compartidos, skip automático si faltan datos reales
├── legacy/fase03_pipeline_v4.py   # copia del monolito, usada como oráculo de comparación
├── fixtures/               # (vacío en este entregable — instrucciones en README.md)
└── test_fase03.py           # 4 capas de regresión + smoke test

docs/
└── FASE_03_INFORME_TECNICO.md   # este documento
```

## 5. Responsabilidad de cada módulo

| Módulo | Responsabilidad | Entrada | Salida |
|---|---|---|---|
| `config.py` | Configuración reproducible + constantes de dominio | — | `ConfiguracionPipeline`, diccionarios de constantes |
| `ip_utils.py` | Clasificar/convertir direcciones IP | IP como string | `(int, versión)` |
| `timestamp_utils.py` | Convertir `Login Timestamp` de forma defensiva | Serie numérica/texto | Serie `datetime64` |
| `rba_reader.py` | Leer el RBA por chunks (33M+ filas) | Ruta del RBA | `Counter` de eventos por usuario; DataFrame de historial |
| `muestreo.py` | Decidir QUÉ usuarios entran al pipeline | `Counter` | `ResultadoMuestreo` (usuarios + origen) |
| `empleados.py` | Generar maestro sintético de empleados | Lista de `User ID` | DataFrame de empleados |
| `ip_resolver.py` | Enriquecer IPs vía IPinfo (`merge_asof`) | DataFrame de logs | DataFrame enriquecido + diagnóstico |
| `features.py` | Ingeniería de características | DataFrame integrado (sin target) | DataFrame con features |
| `validacion.py` | Validaciones bloqueantes | DataFrame final | Excepción o `True` |
| `diagnostico.py` | Métricas descriptivas + checklist | DataFrame final | `dict` de métricas, impresión en consola |
| `exportacion.py` | Selección de columnas + escritura CSV | DataFrame integrado | DataFrame final, archivo CSV |
| `pipeline.py` | Orquestar las 8 etapas | `ConfiguracionPipeline`, `EstrategiaMuestreo` | DataFrame final |

## 6. Clases existentes y por qué (criterio aplicado tras la revisión crítica)

Se mantienen como clase **solo** donde hay estado compartido genuino entre múltiples métodos, o donde se necesita sustituibilidad (inyección de dependencia):

- **`ConfiguracionPipeline`** — contenedor de datos (`@dataclass`), constructor con valores por defecto sobreescribibles.
- **`AnalizadorRBA`** — dos métodos (`primera_pasada`, `segunda_pasada`) que comparten `self.config` (ruta, chunksize) entre invocaciones secuenciales del mismo objeto.
- **`EstrategiaMuestreo`** (ABC) + **`MuestreoAleatorioSimple`** + **`MuestreoEstratificadoPorTarget`** — el punto real de OCP/DIP del proyecto (ver sección 8).
- **`GeneradorEmpleados`** — agrupa distribuciones ponderadas + estado de generadores aleatorios (Faker + numpy) + validación de integridad post-generación.
- **`ResolutorIPinfo`** — lógica multi-paso no trivial (clasificación, construcción de rangos, `merge_asof`, validación de rango), autocontenida.
- **`PipelineFase03`** — orquestador con inyección de dependencia real.

## 7. Funciones existentes y por qué

`features.py`, `validacion.py`, `diagnostico.py`, `exportacion.py` se mantienen como **funciones de módulo**, no clases: cada una tiene un solo método público, sin estado propio más allá de `config`, y — en el caso específico de `features.py` — un **orden fijo y no intercambiable** entre ellas (`crear_feature_turnos` depende de que `crear_features_temporales` ya haya convertido `Login Timestamp` a datetime; `crear_feature_impossible_travel` depende de `previous_country` y `time_since_previous_login_hours`, creadas por `crear_features_temporales`). Envolverlas en clases habría sido cumplimiento cosmético del requisito del profesor, no una necesidad arquitectónica — esto quedó señalado explícitamente en la revisión crítica previa a esta implementación.

## 8. Dónde se aplican realmente SRP, OCP y DIP

- **SRP** (transversal): cada módulo tiene una sola razón para cambiar. Un cambio en la regla de `country_mismatch` solo toca `features.py`; un cambio en la resolución IP solo toca `ip_resolver.py`.
- **OCP**: `PipelineFase03` depende de `EstrategiaMuestreo` (abstracción). Cuando se implemente `MuestreoEstratificadoPorTarget` en la Etapa 2, **no se modificará ni una línea de `PipelineFase03`** — solo se inyectará una instancia distinta.
- **DIP**: `PipelineFase03.__init__(self, config, estrategia_muestreo)` recibe la estrategia ya construida desde afuera, nunca la instancia internamente.

**No se afirma aplicación de ISP ni LSP** — no existen múltiples interfaces cliente-específicas que segregar, ni jerarquías de sustitución más allá de la única interfaz `EstrategiaMuestreo`. Forzar esos principios sería nominal, no real.

## 9. Decisiones metodológicas tomadas (Etapa 1)

Ninguna decisión metodológica nueva. Se preserva exactamente: `MIN_EVENTOS_USUARIO=15`, `N_USUARIOS=2000`, `RANDOM_STATE=42`, `FAKER_SEED=42`, `UMBRAL_VELOCIDAD_KMH=800.0`, `VENTANA_MAX_HORAS=12.0`, selección aleatoria simple (`MuestreoAleatorioSimple`, sin cambios respecto a `seleccionar_usuarios()` del monolito).

## 10. Cómo se evita target leakage (barrera estructural, no solo disciplina)

`PipelineFase03.ejecutar()` retira físicamente `Is Account Takeover` del DataFrame (`df.pop(...)`) inmediatamente después de la resolución IP y **antes** de invocar cualquier función de `features.py`. Mientras la columna no exista en el DataFrame, es estructuralmente imposible que una feature la use — no depende de que nadie recuerde la regla. La columna se reincorpora únicamente antes de validar/exportar. Esto se verifica empíricamente con `test_capa_d_no_leakage_barajar_target_no_cambia_ninguna_feature` (baraja el target y confirma que ninguna feature cambia) y `test_capa_d_features_py_no_menciona_is_account_takeover` (garantía estructural adicional: el string ni siquiera aparece en el código fuente de `features.py`).

## 11. Cómo se controla el consumo de memoria

Ninguna clase almacena DataFrames grandes ni el `Counter` de millones de claves como atributo `self` — solo `config` (liviano) vive en las instancias. Los objetos voluminosos son variables locales de `PipelineFase03.ejecutar()`, liberadas con `del` + `gc.collect()` exactamente en los mismos puntos donde ya se liberaban en el monolito (después de seleccionar usuarios, y después del merge RBA+empleados). El procesamiento por chunks (`CHUNKSIZE_PASADA_1=500_000`, `CHUNKSIZE_PASADA_2=250_000`) se conserva sin cambios en `AnalizadorRBA`.

## 12. Limitaciones del dataset sintético

Sin cambios respecto al README maestro (Sección 49): RBA sintético, empleados 100% sintéticos, IPinfo sin coordenadas (centroides representativos), IPv6 no resuelto en esta fase, `impossible_travel` es heurística con umbral configurable, propósito exclusivamente académico.

## 13. Reproducibilidad

`RANDOM_STATE=42` y `FAKER_SEED=42` viven en `ConfiguracionPipeline` y se pasan sin cambios a `np.random.default_rng()` y `Faker.seed()`. Verificado empíricamente por `test_capa_b_empleados_reproducible_mismos_seeds` (misma configuración + mismos usuarios → mismo `empleados.csv`, columna por columna).

## 14. Pruebas realizadas

| Capa | Prueba | Requiere datos reales | Resultado en este entorno |
|---|---|---|---|
| A | Equivalencia end-to-end vs. monolito | Sí (`rba_2000_users.csv` + IPinfo) | **Omitida** (archivos no disponibles aquí) |
| B | Reproducibilidad de `empleados.csv` (seeds) | No | **Pasó** |
| B | Equivalencia de `empleados.csv` vs. monolito | Sí | **Omitida** |
| C | `Pais_Residencia` es ISO2 | No | **Pasó** |
| C | Centroides usan ISO2, no nombres en español | No | **Pasó** |
| C | `country_mismatch` ISO2 vs. ISO2, NaN si falta info | No | **Pasó** |
| C | `has_previous_login` + NaN forzado en impossible travel | No | **Pasó** |
| C | `calcular_rolling_retrospectivo` con un solo usuario (edge case pandas≥3.0) | No | **Pasó** |
| C | Fix de dtype de `merge_asof` (RBA con IPv6 vs. IPinfo puro IPv4) | No | **Pasó** |
| D | Barajar el target no cambia ninguna feature | No | **Pasó** |
| D | `features.py` no menciona el target en su código fuente | No | **Pasó** |
| — | Smoke test: pipeline completo end-to-end (datos sintéticos) | No | **Pasó** |

**10 de 12 pruebas pasaron; 2 se omitieron explícitamente por falta de archivos reales — no se simuló ni se forzó su paso.** Para activarlas: ver `tests/fixtures/README.md`.

## 15. Cómo verificar equivalencia con el pipeline anterior (instrucciones para Javier)

```bash
# 1. Copiar los archivos reales generados en tu corrida de Colab:
cp /ruta/a/tu/rba_2000_users.csv tests/fixtures/
cp /ruta/a/tu/country_asn.csv tests/fixtures/

# 2. Ejecutar la suite completa (ahora las 12 pruebas deberían correr, no solo 10):
cd fase03_refactor
python3 -m pytest tests/ -v
```

Si `test_capa_a_equivalencia_end_to_end_contra_monolito` pasa, el refactor es funcionalmente transparente: el mismo `rba_2000_users.csv` produce el mismo `dataset_final_modelo.csv` con el pipeline monolítico y con la arquitectura modular.
