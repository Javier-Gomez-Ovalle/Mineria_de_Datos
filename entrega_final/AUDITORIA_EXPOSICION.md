# Auditoría final de exposición: no aprobada todavía

Fecha: 22 de noviembre de 2026. Referencia inicial: main `23e2320`. Se inspeccionaron metadatos del árbol y sus tres commits alcanzables (`17e2c72`, `babe98d`, `23e2320`), cabeceras CSV no protegidas, los seis CSV identificados y coincidencias de sus identificadores en archivos de texto versionados no protegidos. No se imprimen registros ni identificadores en este informe. Los nombres que contienen test se excluyeron de la lectura; no se abrió, copió, procesó, hasheó ni evaluó el dataset test o sus predicciones.

## Hallazgos y medida segura

| Archivo | Filas / bytes | Contenido y riesgo | Ubicación inicial / acción |
|---|---:|---|---|
| `dataset_train_fase04.csv` | 46.305 / 13.218.803 | Eventos individuales de 1.600 usuarios; identificador, IP, timestamps, nombre simulado, rol, residencia, actividad y target. Alta vinculabilidad dentro del conjunto. | Presente en los tres commits; retirar del árbol actual, conservar local. |
| `empleados.csv` | 2.000 / 188.583 | Identificador, nombre simulado, rol, residencia, turno, estado y fecha. Vincula atributos de empleado con eventos. | Igual. |
| `fase04_modelado/mejora_controlada/resultados/distribucion_usuarios_train.csv` | 1.600 / 42.241 | Identificador y conteos de eventos/ATO por usuario. | Igual. |
| `fase04_modelado/mejora_controlada/resultados/metricas_por_usuario.csv` | 14.400 / 677.226 | Identificador, conteos y errores por usuario/modelo. | Igual. |
| `fase04_modelado/resultados_cv_usuario/asignacion_usuarios.csv` | 1.600 / 48.684 | Identificador, estrato ATO, fold y actividad por usuario. | Igual. |
| `fase04_modelado/mejora_controlada/resultados/errores_historicos_por_perfil.csv` | 11.655 / 682.586 | Columna genérica `valor`: contiene identificadores en 11.200 filas cuyo perfil es `User ID`. También contiene otros perfiles agregados; se retira completo para no modificar resultados históricos. | Igual. |

Antes de la retirada, los seis respondieron HTTP HEAD 200 en raw público/main. Ninguno está en el árbol de `gh-pages`; no forman parte de las 15 descargas agregadas. Se utilizó `git rm --cached` exclusivamente con esas seis rutas y se añadieron exclusiones explícitas a `.gitignore`. Los originales permanecen en sus rutas locales; su tamaño y SHA-256 se registraron y comprobaron antes/después en `AUDITORIA_EXPOSICION.json`. No fue necesario duplicarlos ni hacer un respaldo general que pudiera copiar material protegido.

### Naturaleza de los datos

La documentación existente `docs/PROCEDENCIA_Y_LICENCIAS.md` declara RBA sintetizado a partir de comportamiento real y empleados generados con Faker. IPinfo es un catálogo de redes reales aplicado a eventos sintéticos. Por tanto, la presencia de nombre/IP/ID no demuestra identidad personal real ni una filtración de datos clínicos. La retirada responde al alcance vigente de publicación agregada y a la vinculación individual que conservan estas tablas. No revoca licencias abiertas previamente concedidas ni elimina copias de terceros. Esta auditoría no certifica la anonimización ni vuelve a acreditar versiones/licencias originales.

## Historial y alcance

Al comienzo no había rutas de main presentes exclusivamente en commits antiguos: las seis estaban también en HEAD. Tras la retirada quedan en commits históricos. Los tres commits iniciales siguen alcanzables; un commit de borrado no purga sus blobs. La rama local `fase04-modelado` no aparece entre las ramas/tags anunciadas por `git ls-remote`: el remoto anuncia main y gh-pages, sin tags. No se infiere que esos commits locales nunca hayan sido publicados o que no existan referencias ocultas, cachés o forks.

El rastreo de identificadores conocidos en CSV/JSON/Markdown/código/texto no protegido reveló el sexto archivo. Las columnas de conteos agregados como `usuarios` o `usuarios_con_ato` no son por sí mismas identificadores. No se abrió contenido test ni se deserializaron modelos o archivos binarios para certificar una ausencia universal de información individual. La conclusión se limita al alcance documentado, no a todos los objetos posibles de GitHub.

## Consecuencias para reproducción y despliegue

- La aplicación, el catálogo, los 15 CSV agregados, las 58 figuras, el PPTX y `gh-pages` permanecen sin cambios.
- No se modifican métricas, código de Fase 3, modelos, umbral, preprocesador, manifiestos ni informes académicos históricos.
- El trabajo local conserva los archivos en las rutas que esperan los scripts. Una nueva copia de main ya no podrá reproducir entrenamientos ni auditorías por usuario sin obtener los insumos mediante un canal privado autorizado. No se ejecutaron esos procesos.
- Las menciones a los archivos en informes/inventarios históricos se conservan por trazabilidad: describen la entrega anterior, no disponibilidad pública actual. Este documento es el aviso vigente. El código fuente no se elimina ni se modifica para ocultar dependencias.
- Un colaborador que actualice su checkout puede perder sus copias rastreadas al aplicar el commit de retirada: debe respaldarlas privadamente antes de hacer pull. Los originales de este equipo están preservados. No usar force-add ni volver a incorporar ramas antiguas.

## Cierre pendiente: estrategia recomendada, no ejecutada

Retirar del árbol reduce la distribución por defecto, pero no satisface una exigencia de inaccesibilidad histórica. Recomiendo una limpieza dirigida de las seis rutas en una copia de trabajo aislada del historial público de main, con preservación separada de gh-pages. No ejecutar un filtro global sobre todo este repositorio local: contiene otras ramas y material fuera del alcance.

Antes de autorizar esa operación:

1. Resguardar los seis originales y el historial académico en almacenamiento privado con control de acceso. El respaldo no debe incorporar ni leer el test/predicciones; verificar primero la lista de objetos por metadatos. Conservar el manifiesto de integridad actual.
2. Congelar temporalmente cambios, inventariar ramas/tags/PR/forks y documentar el mapa de commits que cambiará. Preparar y revisar la copia filtrada sin publicar todavía.
3. Comparar los árboles: únicamente deben desaparecer las seis rutas; métricas, modelos, figuras y presentación deben permanecer idénticos. Comprobar enlaces que usen SHA y referencias de manifiestos sin modificarlos silenciosamente.
4. Autorizar explícitamente el reemplazo remoto de main con las protecciones apropiadas y coordinación de colaboradores. Preservar gh-pages y comprobar después la aplicación. Evitar merges de clones antiguos que reintroduzcan los objetos.
5. Verificar las URLs antiguas por commit. Evaluar referencias/cachés y solicitar a GitHub la retirada cuando sea aplicable. GitHub advierte que la reescritura no elimina copias externas y que Support no retira datos no sensibles: dada la procedencia sintética, no se puede garantizar una purga asistida.

Alternativa si no se acepta reescritura: migrar la fuente a un repositorio limpio y restringir o retirar la disponibilidad del original, después de evaluar consecuencias sobre Pages y URLs. Crear un repositorio nuevo mientras el anterior permanece público no resuelve la exposición. No se cambió visibilidad, no se eliminó ningún repositorio, no hubo force push, reset ni rebase.

Referencia técnica: [GitHub — Removing sensitive data from a repository](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).

## Verificación posterior

Pendiente de registrar tras publicar la retirada. El dictamen seguirá siendo **no aprobado** mientras las versiones históricas permanezcan accesibles sin una decisión expresa que acepte su publicación sintética.
