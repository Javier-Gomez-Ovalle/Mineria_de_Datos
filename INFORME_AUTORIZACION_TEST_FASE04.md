# Informe previo a autorización de test — Fase 4

Fecha: 2026-11-21. **Este informe NO concede autorización y NO acredita una evaluación ejecutada.**

## Resultado

El procedimiento de referencia está definido para solicitar autorización: arbol_ponderado fijo, preprocesamiento aprobado y selección del umbral con tres folds internos por usuario en train. El umbral numérico y el modelo final siguen pendientes. No debe abrirse test hasta autorizar la ejecución y congelar los artefactos resultantes.

## Verificaciones realizadas en esta intervención

| Verificación | Evidencia / resultado |
|---|---|
| Informes CV1/CV2/selección/anidada/diagnóstico/RF | Inspeccionados; diferencias explicadas por protocolo/evidencia, sin contradicción material de parámetros. |
| Train | SHA-256 98d4d4970ada7bf11ec2e76f89e93c46c76c3d097043020598638547f977e53f; 46.305 eventos, 1.600 usuarios, 36 ATO y 34 usuarios positivos; clave única y target válido. |
| Parámetros del árbol | Fábrica sin fit y 20 auditorías históricas coinciden en todos los parámetros. |
| Umbrales históricos | Cinco decisiones reproducidas exactamente desde OOF internas guardadas, sin ajustes nuevos. |
| Predicciones externas históricas | 46.305 eventos alineados por índice, clave y target; métricas recalculadas 5 TP, 54 FP, 46.215 TN, 31 FN. |
| Preprocesamiento | Inspección de fábrica; orden y reglas locales documentados; 62 columnas esperadas full train derivadas sin fit, dimensiones históricas 49–62. |
| Entorno | Versiones y parámetros efectivos registrados en evidencia JSON; sin instalaciones. |
| Integridad previa | 501 archivos permitidos inventariados con SHA-256/tamaño/mtime; manifiesto anterior de mejora verificado. |
| Integridad final | Se verificará contra ese inventario al emitir manifiesto de esta entrega: única modificación autorizada es adenda README, con prefijo anterior intacto. |
| Test | No abierto, leído, inspeccionado, procesado, evaluado ni hasheado. Excluido del inventario antes de stat/hash; guardia activa en análisis. |
| Entrenamiento | Cero fit de modelos o transformadores; no se ejecutó selección nueva ni modelo final. |
| Git / dependencias | Ninguna operación Git ni instalación. |

Estas son comprobaciones ejecutadas mediante assertions y recálculo sobre artefactos existentes. No se ejecutó pytest en esta tarea porque las suites históricas contienen ajustes sintéticos; no se cuentan sus resultados previos como pruebas nuevas. Cinco reproducciones de umbral y 20 auditorías revisadas no significan 25 nuevos entrenamientos.

## Integridad y alcance de evidencia

`fase04_modelado/referencia_congelada/inventario_previo.json` conserva hashes/tamaño/mtime de los 501 archivos permitidos antes de crear entregables. `evidencia_congelacion.json` registra parámetros, versiones, columnas y resultados de comprobación. `manifiesto_entrega.json` registra la verificación final y hashes de nuevos documentos.

README puede cambiar únicamente por la adenda autorizada. Su prefijo anterior se verificará byte a byte contra el hash original. Los otros 500 históricos deben coincidir íntegramente. Los archivos test quedan fuera de esta certificación criptográfica: no se afirma haberlos hasheado para demostrar que se preservaron. No se accedió al RBA original.

No se ejecutaron funciones fit ni entrenamiento en esta intervención. Se comprobará que no aparecieron archivos .joblib/.pkl/.npy u otros artefactos de modelo entre las nuevas salidas; es evidencia del trabajo realizado, no una auditoría del equipo completo fuera del repositorio.

## Riesgos que acompañan la autorización

- La elección de familia es retrospectiva por F1 exploratorio, autorizada como referencia; no implica ganador definitivo.
- Detectar cinco y omitir 31 ATO es una limitación importante, aunque F1 supere a otras variantes.
- Solo 34 usuarios positivos y solapamiento de entradas hacen frágil la estimación; la estabilidad observada es limitada.
- No existe tolerancia operativa de FP ni coste definido para omisiones; no se certifica aptitud productiva.
- La nueva selección interna sobre todo train todavía no se ejecutó y su umbral no puede anticiparse.
- Test permanece reservado para una evaluación única, sin escoger posteriormente otro modelo o umbral.

## Secuencia que requerirá autorización

Autorizar explícitamente tres ajustes internos del árbol fijo para elegir umbral con la regla congelada, un ajuste final en todo train, persistencia/verificación de artefactos y, por separado o de manera explícita en la misma autorización, la evaluación única sobre test **después de congelar umbral y artefactos**. No abrir test antes de ese punto. Si la autorización solo cubre entrenamiento, detenerse antes de test.

La especificación no requiere decisiones técnicas adicionales para ejecutarse; sí requiere autorización. Si un hash, versión o contrato falla, detenerse y documentar la incidencia. No corregir o reemplazar silenciosamente datos, configuración o umbral. No se declara cerrada Fase 4.

