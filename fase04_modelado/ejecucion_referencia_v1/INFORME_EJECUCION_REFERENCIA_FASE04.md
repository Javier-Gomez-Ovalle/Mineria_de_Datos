# Ejecución de referencia: detenida por incidencia

Fecha: 2026-11-21. Procedimiento referencia_arbol_ponderado_v1. Estado: INCOMPLETO; no apto todavía para evaluación final.

Se ejecutaron los tres ajustes internos y el ajuste final en todo train. La escritura de auditoria_modelo_final.json fall? con TypeError: Object of type int64 is not JSON serializable. El traceback se conserva en INCIDENCIA_EJECUCION.txt. El archivo de auditoría quedó parcialmente escrito y no es un JSON válido; no se repar? ni sobrescribi?.

El fallo ocurri? después de model.fit y de comprobar parámetros finales y 62 columnas, pero antes de serializar modelo/preprocesador. El proceso termin?: el modelo en memoria no se conserva. No existen modelo_final.joblib ni preprocesador_final.joblib; no hay hashes de esos artefactos. No se completaron pruebas de recarga o igualdad de predicciones serializadas. No se presenta el ajuste como entrega final congelada.

## Configuración y etapas completadas

SHA train: 98d4d4970ada7bf11ec2e76f89e93c46c76c3d097043020598638547f977e53f. 46.305 eventos, 1.600 usuarios, 36 ATO y 34 usuarios positivos. Se mantuvieron los seis predictores, mediana local, indicador intacto y One-Hot local. Sin log1p, escalado, ROS, comparaciones entre algoritmos ni cambios de parámetros.

Parámetros efectivos verificados antes y después del fit final:
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
Versiones verificadas:
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

Tres folds estratificados por usuario, seed 42. Separación comprobada, particiones reconstruidas dos veces, una OOF por evento y un fold por usuario. Ajustes locales auditados en auditoria_folds.json. Las OOF conservaron exactamente probabilidades y claves al recargar CSV. La decisión de umbral se reprodujo dos veces sobre esas OOF sin nuevos ajustes.

Distribución de folds:
```
 fold_externo  fold_interno  usuarios_compartidos  ajuste_eventos  ajuste_usuarios  ajuste_ato  ajuste_negativos  ajuste_usuarios_ato  validacion_eventos  validacion_usuarios  validacion_ato  validacion_negativos  validacion_usuarios_ato
            0             1                     0           29944             1066          24             29920                   22               16361                  534              12                 16349                       12
            0             2                     0           31783             1067          25             31758                   23               14522                  533              11                 14511                       11
            0             3                     0           30883             1067          23             30860                   23               15422                  533              13                 15409                       11
```

Umbral conservado: 0.9976439543869569; TP=8, FP=48, TN=46221, FN=28; F1 OOF de selección=0.17391304347826086. No es una estimación independiente del rendimiento final. El modelo final usa todo train y no se garantiza equivalencia de sus probabilidades con las de tres estimadores OOF. No se calibr? ni se alter? el umbral.

## Integridad, restricciones y parada

Antes del ajuste se verificaron hashes congelados, versiones, contratos y parámetros. Después de la incidencia se verificaron los 507 archivos históricos permitidos contra inventario_previo.json: SHA-256, tamaño y mtime intactos. No se ejecut? pytest. Las verificaciones completadas no sustituyen las comprobaciones de serialización pendientes.

Test no fue leído, inspeccionado, procesado, hasheado ni evaluado. No se ejecut? Git ni se instalaron dependencias. No se modificaron históricos. única incidencia: serialización JSON de la auditoría final; no se aplic? corrección ni se reanud? entrenamiento.

Para continuar se requiere autorización de recuperación: corregir explícitamente la conversión de escalares de la auditoría en una implementación/destino nuevos, conservar las OOF/decisión existentes verificadas y repetir solo el ajuste final que se perdi? en memoria, seguido de serialización y comprobaciones pendientes. No se autoriza implícitamente esa recuperación ni abrir test. Fase 4 sigue abierta.
