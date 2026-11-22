# Reproducción y revisión segura

Ejecutar desde la raíz de esta copia, con Python 3.12.7. Crear un entorno virtual e instalar `requirements-dev.txt` para revisión; `requirements-inference.txt` basta para cargar los artefactos. Esta preparación no instaló paquetes. Faker no está instalado en el entorno observado y su versión histórica no está fijada. `requirements-fase03-optional.txt` lo declara, pero no garantiza reproducir empleados bit a bit.

## Comprobaciones disponibles, sin entrenar

```powershell
python -B tools/verificar_publicacion.py
python -B -m pytest -p no:cacheprovider -q tests/test_publicacion.py
Push-Location fase03_refactor
python -B -m pytest -p no:cacheprovider -q tests/test_correccion_target.py tests/test_reconciliacion_target.py
Pop-Location
```

Las dos pruebas de Fase 3 usan ejemplos sintéticos en memoria para comprobar asociación y reconciliación; no recorren el RBA original. No ejecutar la suite histórica completa: algunas pruebas requieren datos omitidos y otras realizan ajustes de estimadores.

## Carga de referencia sin inferencia

```python
from pathlib import Path
import joblib
base = Path('fase04_modelado/recuperacion_referencia_v1_20261122')
modelo = joblib.load(base / 'modelo_final.joblib')
preprocesador = joblib.load(base / 'preprocesador_final.joblib')
```

Cargar únicamente estos artefactos propios verificados: joblib no es un formato seguro para archivos desconocidos. La normalización de entradas está en `fase04_preparacion.seleccion.seleccionar_predictores`; no eliminarla en una integración futura. La regla congelada usa probabilidad de clase 1 >= 0.9976439543869569. Esta entrega no realiza inferencias.

## Datos y reproducción completa

Train y empleados permanecen en raíz para respetar rutas existentes y hashes. Los originales están documentados por sus enlaces oficiales, no por enlaces inventados de Drive. Fase 3 recibe `ConfiguracionPipeline(RBA_PATH=..., IPINFO_PATH=..., OUT_RBA_2000=..., OUT_EMPLEADOS=..., OUT_DATASET_FINAL=...)`; configurar siempre salidas nuevas en una copia experimental. La versión local IPinfo y Faker no están suficientemente identificadas para prometer reproducción exacta desde cero.

No se distribuyen test, dataset corregido completo ni subconjunto RBA que contiene sus eventos. Por tanto, esta entrega permite revisar código, evidencia, cargar el modelo y ejecutar comprobaciones limitadas, no repetir la evaluación final. Solicitar autorización separada para distribución de esos datos. No reconstruir test por diferencia ni usar fuentes originales para eludir esta restricción.

## Procedimientos congelados

No ejecutar `ejecutar.py`, motores de entrenamiento, `recuperar.py`, scripts de preparación ni `evaluar_una_vez.py`: pueden escribir resultados, entrenar o acceder al test. Se incluyen como evidencia de implementación. No modificar umbral, modelos, manifiestos ni salidas históricas. Para experimentos nuevos haría falta otro alcance y directorio independiente.

El exportador XLSX histórico dependía de `@oai/artifact-tool` instalado en una ruta temporal del equipo; se omitió esa herramienta no portable y se conserva el XLSX ya generado. CSV y código de análisis son la evidencia accesible sin esa dependencia.

Los manifiestos originales pueden enumerar archivos omitidos y contener rutas absolutas históricas. No se alteraron para aparentar una reproducción completa. `docs/INVENTARIO_PUBLICACION.json` describe la distribución efectiva; `docs/VERIFICACION_PUBLICACION.json` registra las comprobaciones nuevas. Enlaces documentales a insumos excluidos se listan como límites, no como archivos disponibles.
