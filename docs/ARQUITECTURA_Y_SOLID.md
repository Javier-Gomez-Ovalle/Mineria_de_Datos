# Arquitectura real y principios SOLID

## Flujo y límites

`ConfiguracionPipeline` aporta rutas y parámetros. `PipelineFase03` coordina `AnalizadorRBA`, la estrategia de muestreo, `GeneradorEmpleados`, `ResolutorIPinfo`, las funciones de features y exportación. `asociacion_target.py` y `reconciliacion_target.py` protegen la identidad de los eventos. En Fase 4, `seleccion.py` define seis entradas, `transformaciones.py` construye el preprocesador, `modelos.py` crea estimadores, y los motores de CV gestionan ajustes y OOF. Métricas, gráficas e informes están separados. Los artefactos congelados son salidas, no configuración para volver a buscar modelos.

| Principio y significado | Evidencia concreta | Problema evitado y alcance |
|---|---|---|
| **S ? responsabilidad única:** una unidad tiene un motivo de cambio definido | `fase03/rba_reader.py:AnalizadorRBA`, `empleados.py:GeneradorEmpleados`, `ip_resolver.py:ResolutorIPinfo`; `fase04_preparacion/seleccion.py:seleccionar_predictores` | Cambiar el origen de datos no exige reescribir las métricas. Aplicación clara en módulos; los orquestadores todavía agrupan varias tareas operativas. |
| **O ? abierto a extensión, cerrado a modificación** | `fase03/muestreo.py:EstrategiaMuestreo` declara `seleccionar`; `MuestreoAleatorioSimple` y `MuestreoEstratificadoPorTarget` lo implementan | Otra estrategia puede inyectarse sin cambiar el flujo del pipeline. Parcial: `fase04_modelado/modelos.py:crear_modelo` usa condicionales y se modifica al agregar familias. |
| **L ? sustitución conservando contrato** | Ambas estrategias heredan `EstrategiaMuestreo` y retornan `ResultadoMuestreo` | El pipeline consume `resultado_muestreo.usuarios`. La estrategia por target necesita conteos ATO, mientras la aleatoria puede ignorarlos: no se afirma sustitución universal con argumentos incompletos. La firma común no demuestra por sí sola LSP; harían falta pruebas compartidas de precondiciones y postcondiciones. |
| **I ? interfaces pequeñas por consumidor** | `EstrategiaMuestreo` tiene solo `seleccionar`; `ajustar_train(preprocesador, x_train)` no pide etiquetas o test | El consumidor no depende de métodos ajenos a su tarea. Aplicación concreta y limitada; funciones pequeñas no constituyen automáticamente prueba de ISP en toda la arquitectura. |
| **D ? depender de abstracciones** | `PipelineFase03.__init__(config, estrategia_muestreo)` recibe una estrategia y llama `seleccionar` | Permite cambiar muestreo sin acoplar la orquestación a una implementación. Parcial: `AnalizadorRBA`, `GeneradorEmpleados` y `ResolutorIPinfo` se instancian directamente; no hay inyección general de todos los servicios. |

Ejemplo existente: el constructor conserva `self.estrategia_muestreo`; `ejecutar()` llama `self.estrategia_muestreo.seleccionar(contador_usuarios, contador_eventos_ato)`. La abstracción deriva de `ABC`, usa `@abstractmethod` y retorna una dataclass con `usuarios` y `origen`.

En Fase 4, `AjustadorVariante.predecir(x_ajuste, y_ajuste, x_validacion)` no recibe el target de validación: fabrica un preprocesador nuevo, ajusta con subtrain y transforma validación. Es una separación metodológica comprobable, no una interfaz nueva creada para esta publicación.

## Deuda reconocida

Se conservó el comportamiento del código sin refactorizaciones. Se corrigió únicamente el comentario desactualizado de muestreo.py sobre la retirada física del target. El pipeline conserva la etiqueta asociada al evento. Las fábricas condicionales y dependencias concretas descritas arriba siguen siendo límites reales de SOLID.
