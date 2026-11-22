# Detección académica de Account Takeover (ATO)

> **Aviso de distribución (22/11/2026):** train, empleados y cuatro tablas con identificadores se retiran del árbol público actual; se conservan localmente. Sus versiones históricas aún requieren resolución. Antes de actualizar una copia que los tenga rastreados, resguárdalos privadamente. El frontend y los resultados agregados no cambian. Consulta la [auditoría de exposición y sus límites](entrega_final/AUDITORIA_EXPOSICION.md); las referencias históricas a estos archivos no garantizan su disponibilidad en una copia nueva.

Proyecto de minería de datos con CRISP-DM para estudiar accesos a cuentas comprometidas. Su objetivo general es comparar métodos supervisados y explorar agrupaciones sobre eventos sintetizados. Los objetivos específicos son corregir la asociación evento–etiqueta, separar usuarios, prevenir fuga, comparar variantes y documentar una referencia evaluada una sola vez. No es un detector validado para producción.

## Metodología y resultados

Fase 3 integra RBA, atributos de empleados generados y catálogo IPinfo; la reconciliación corrigió 90 etiquetas. Fase 4 selecciona seis predictores, separa usuarios, ajusta preprocesamiento dentro de folds y compara Árbol de Decisión, GaussianNB y KNN con variantes. KMeans y clustering jerárquico son exploratorios, no clasificadores. Una extensión controlada incluye Random Forest ponderado. Se preservan CV1, CV2, validación anidada y resultados desfavorables.

La referencia es un Árbol ponderado, semilla 42, con umbral **0.9976439543869569**. Su F1 OOF usado para seleccionar el umbral fue **0.17391304347826086**, no una estimación independiente. El informe histórico de test registra TP=1, FP=12, TN=11094, FN=8; Precision=0.076923, Recall=0.111111 y F1=0.090909. Estas cifras se transcriben, no se recalculan. Solo nueve ATO en test y datos sintéticos limitan las conclusiones.

## Navegación

| Ruta | Contenido |
|---|---|
| `fase03_refactor/` | Extracción, enriquecimiento, asociación del target y pruebas |
| `fase04_preparacion/` | Selección explícita y transformadores |
| `fase04_modelado/` | Comparaciones, validaciones, resultados, gráficas y referencia |
| `fase04_clustering/` | KMeans y Ward; resultados exploratorios |
| `docs/` | Arquitectura, licencias, metodología y reproducción |
| `data/README.md` | Inventario y límites de distribución |
| `dataset_train_fase04.csv`, `empleados.csv` | Datos autorizados; se mantienen en raíz por contratos del código |
| `INFORME_FINAL_FASE04_CRISP_DM.md` | Síntesis académica y enlaces a tablas/gráficas |

El modelo se conserva en `fase04_modelado/recuperacion_referencia_v1_20261122/`, sin duplicarlo ni cambiar sus manifiestos. Los informes raíz también mantienen su ubicación para conservar enlaces. No se crearon carpetas vacías `modelos/` o `resultados/`.

## Uso seguro

Python **3.12.7**, NumPy, pandas, scikit-learn, SciPy y joblib; imbalanced-learn y matplotlib para el código experimental.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -B tools/verificar_publicacion.py
python -B -m pytest -p no:cacheprovider -q tests/test_publicacion.py
```

La verificación carga los artefactos pero no entrena, predice ni abre datasets. Para código de Fase 3, Faker es opcional y su versión histórica no está acreditada. No ejecutar pipelines ni evaluación final para revisar esta entrega. Los experimentos se conservan para inspección y reproducción futura en una copia de trabajo, no para sobrescribir evidencia.

## Documentación

- [Arquitectura y SOLID](docs/ARQUITECTURA_Y_SOLID.md)
- [Metodología y resultados](docs/METODOLOGIA_Y_RESULTADOS.md)
- [Procedencia y licencias](docs/PROCEDENCIA_Y_LICENCIAS.md)
- [Reproducción y límites](docs/REPRODUCCION.md)
- [Decisiones de selección](docs/PUBLICACION_FINAL.md)
- [Comparación de algoritmos](INFORME_COMPARATIVO_ALGORITMOS_FASE04.md)

RBA: [Kaggle](https://www.kaggle.com/datasets/dasgroup/rba-dataset), CC BY 4.0. IPinfo: [Kaggle](https://www.kaggle.com/datasets/ipinfo/ipinfo-country-asn), CC BY-SA 4.0; edición local sin identificación completa. No se atribuye una licencia única al proyecto. El test no se distribuye y no debe reabrirse. La disponibilidad pública temporal no limita las copias que terceros puedan conservar.
