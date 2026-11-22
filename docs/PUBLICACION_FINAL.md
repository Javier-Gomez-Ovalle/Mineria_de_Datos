# Publicación oficial y alcance de la entrega

Fecha: 22 de noviembre de 2026. Repositorio oficial: https://github.com/Javier-Gomez-Ovalle/Mineria_de_Datos . Rama principal: main. El directorio de staging fue una fuente de integración, no otro repositorio oficial.

## Selección

Se conservan módulos, pruebas, informes finales y evidencia diferenciada de CV1, CV2, validación anidada, clustering, selección, recuperación y evaluación final. Resultados preliminares se identifican por protocolo y no sustituyen la evaluación final. No se alteraron métricas, scores ni predicciones.

Datos distribuidos: dataset_train_fase04.csv y empleados.csv. Se omiten test y sus predicciones individuales, datos completos con eventos reservados, preparados antiguos, ZIP redundantes, preprocesador obsoleto, cachés y archivos privados. Los originales RBA/IPinfo se obtienen desde sus fuentes documentadas; no se inventan enlaces de Drive. Ver PROCEDENCIA_Y_LICENCIAS.md.

El inventario público contiene únicamente rutas relativas y hashes de archivos incluidos. No es un inventario del computador. La selección mediante lista explícita de .gitignore impide incorporar accidentalmente los archivos históricos que siguen almacenados localmente. Para agregar un archivo futuro debe añadirse conscientemente a esa lista.

## Integridad y duplicados justificados

Modelo: d23a2a0f93d64682931608829a030e9615be43990e4ae43d99262b5a9254ff5e

Preprocesador: 01fbfd1f162dda4c7e31946da3e4cc19e87d9badfac235d662345369096168c6

Registro del umbral: e5327bd50594edd9d1c67e5076bd53f101c9194b068911e8faf16567f7109095

Umbral: 0.9976439543869569. Se utiliza la referencia de 64 caracteres confirmada por el responsable; no se modificó el preprocesador.

Se conservan dos duplicados exactos por contrato: umbral_definitivo.json en ejecución y recuperación, exigido por su trazabilidad congelada; referencias_cv1_cv2.csv e historicos_globales.csv, consumidos en las rutas de dos informes y registrados en manifiestos. No hay datasets o informes duplicados sin esta justificación. Los __init__.py vacíos son marcadores de paquetes.

## Documentación y estado histórico

Se corrigieron caracteres dañados, enlaces y rutas personales en documentos no congelados. Las métricas permanecen iguales. Se corrigió el comentario obsoleto de muestreo.py que decía retirar físicamente el target. No cambió el cálculo. El manifiesto recuperado conserva su estado histórico SIN_EVALUAR_TEST: la evaluación posterior está documentada separadamente. El informe final de Fase 4 es la síntesis vigente; el README de estado anterior queda fuera de la publicación.

Los manifiestos y evidencias congelados no se reescriben para ocultar insumos ausentes. Sus referencias describen la ejecución histórica, no prometen que esta entrega distribuya todos esos insumos. No ejecutar pipelines ni evaluación final para revisar la publicación.

## Git

La publicación usa una nueva raíz, sin padres históricos. Se conserva el remoto original. El historial anterior se mantiene localmente con respaldo; el respaldo de objetos usa enlaces físicos para no leer ni duplicar el contenido del test. Los cambios de referencias remotas se hacen con lease sobre el commit observado. La ausencia de ramas o etiquetas que alcancen la historia antigua no garantiza la eliminación inmediata de cachés, forks o enlaces a commits retenidos por GitHub.

## Límites

No se acredita la edición exacta de IPinfo ni la versión histórica de Faker. El código propio se publica autorizado, sin licencia explícita elegida. No se declara MIT. Modelo académico de baja sensibilidad; no apto para presentar como detector productivo. La publicación temporal no impide que terceros conserven copias.
