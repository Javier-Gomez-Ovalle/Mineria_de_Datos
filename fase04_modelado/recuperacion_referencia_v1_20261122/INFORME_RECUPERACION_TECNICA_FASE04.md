# Recuperación técnica del modelo de referencia — Fase 4

Fecha: 2026-11-22. Procedimiento referencia_arbol_ponderado_v1. **Recuperación completada; modelo serializado y verificado, test cerrado.**

## Incidencia y solución

El archivo original auditoria_modelo_final.json termina en `"hojas_observadas":`. Ese campo se obtiene de model.get_n_leaves(), que devuelve <class 'numpy.int64'> en este entorno. Se confirmó el TypeError de json.dumps con ese escalar tras el único ajuste final. El error no se produjo en las OOF ni en la selección de umbral. Se conserva intacto el JSON parcial y su traceback en fase04_modelado/ejecucion_referencia_v1/.

La nueva función json_native convierte explícitamente enteros NumPy a int, booleanos a bool, flotantes NumPy finitos exactamente representables a float y arrays/estructuras anidadas recursivamente. Rechaza NaN, infinitos, complejos, tipos no soportados, claves no string y flotantes que perderían precisión. No sustituye inválidos por cero/null/texto. json.dumps usa allow_nan=False y valida la cadena completa antes de abrir el destino exclusivo, evitando archivos parciales ante errores de conversión. 13 casos de conversión/rechazo aprobados (7 válidos y 6 inválidos), sin ajustes de prueba.

## Integridad y configuración

Se verificaron todos los archivos del manifiesto fallido, incluidos OOF, candidatos, particiones, umbral, resultados y auditoría parcial. Se verificaron fuentes congeladas, versiones exactas, contratos y SHA de train `98d4d4970ada7bf11ec2e76f89e93c46c76c3d097043020598638547f977e53f`. 526 archivos históricos permitidos permanecen iguales por hash/tamaño/mtime; test se excluyó antes de inspeccionar metadatos o contenido.

Train: 46.305 eventos, 1.600 usuarios, 36 ATO y 34 usuarios positivos. Seis predictores aprobados, mediana local, binaria intacta y One-Hot aprobado; sin escalado, log1p ni ROS. **Un ajuste final del preprocesador y un ajuste final del árbol**; cero folds y cero selecciones nuevas. No se ejecutaron otros modelos ni se cambiaron parámetros.

```json
{
  "ccp_alpha": 0.0,
  "class_weight": "balanced",
  "criterion": "gini",
  "max_depth": null,
  "max_features": null,
  "max_leaf_nodes": null,
  "min_impurity_decrease": 0.0,
  "min_samples_leaf": 1,
  "min_samples_split": 2,
  "min_weight_fraction_leaf": 0.0,
  "monotonic_cst": null,
  "random_state": 42,
  "splitter": "best"
}
```

Versiones:
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

El árbol recuperado tiene profundidad 49 y 184 hojas. Estos son resultados del ajuste, no hiperparámetros nuevos. No existe artefacto del ajuste perdido con el que comparar bit a bit: reproducibilidad respaldada por fuentes/datos/semilla/versiones idénticos. No se afirma una comparación imposible con el modelo anterior en memoria.

## Umbral conservado

Umbral exacto **0.9976439543869569**, regla score >= umbral. Registro copiado byte a byte, SHA-256 `e5327bd50594edd9d1c67e5076bd53f101c9194b068911e8faf16567f7109095`. Se conservan F1 OOF de selección 0.17391304347826086, TP=8, FP=48, TN=46.221 y FN=28. No se recalcularon umbral ni métricas OOF.

El F1 se optimizó en OOF de tres estimadores distintos y no estima independientemente rendimiento final. El ajuste con todo train puede cambiar la escala de scores; transferir el umbral no garantiza calibración/equivalencia con OOF. La prueba de recarga compara el mismo modelo antes/después de guardar, no demuestra transferencia o generalización.

## Artefactos y recarga

| Artefacto | SHA-256 |
|---|---|
| modelo_final.joblib | d23a2a0f93d64682931608829a030e9615be43990e4ae43d99262b5a9254ff5e |
| preprocesador_final.joblib | 01fbfd1f162dda4c7e31946da3e4cc19e87d9badfac235d662345369096168c6 |
| umbral_definitivo.json | e5327bd50594edd9d1c67e5076bd53f101c9194b068911e8faf16567f7109095 |

Ambos joblib existen y tienen tamaño positivo. Se recargaron, verificando parámetros, clases [0,1] y los 62 nombres de columnas esperados. Sobre **todos los 46.305 eventos de train**, las matrices, probabilidades y decisiones coinciden exactamente. Tolerancia rtol=0, atol=0; diferencia máxima=0.0. No se calcularon métricas de rendimiento sobre esos scores de resustitución.

Evidencia: auditoria_modelo_final.json, evidencia_recarga.json, esquema_final.json, verificaciones.json, pruebas_conversion.json, inventario_previo.json y registro_ejecucion.json. MANIFIESTO_MODELO_FINAL.json registra parámetros, versiones, umbral y hashes; su recarga se comprueba antes de declarar completada esta recuperación. El manifiesto no se incluye en su propio hash.

## Estado final

Sin incidencias nuevas ni desviaciones. No se sobrescribió ningún archivo previo; implementación y salidas nuevas en fase04_modelado/recuperacion_referencia_v1_20261122/. Sin instalaciones ni operaciones Git. Test no se abrió, leyó, inspeccionó, procesó, hasheó ni evaluó.

**Detención tras verificación.** La evaluación final exige autorización posterior e independiente. Fase 4 continúa abierta; esto no acredita un detector satisfactorio ni ganador definitivo.
