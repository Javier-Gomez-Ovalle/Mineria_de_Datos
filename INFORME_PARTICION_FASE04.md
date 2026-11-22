# Informe de partición definitiva de train y test para Fase 4

Fecha: 18 de noviembre de 2026 (America/Bogota).

Se generaron dos conjuntos sin preprocesamiento ni sobremuestreo, a partir del enriquecido corregido y auditado. La separación conserva íntegramente los historiales de los usuarios: 1.600 usuarios en entrenamiento y 400 en prueba, sin usuarios compartidos.

## Origen y trazabilidad

Archivo: `dataset_final_modelo_corregido.csv`, en la raíz del repositorio.

SHA-256: `7cdf551319fa3de9f8b5805a59ee07a83d7f51fc9dc3cebe8a3cc9d74aa584ab`.

Contenido comprobado: 57.420 eventos, 35 columnas, 2.000 usuarios, 45 ATO y 43 usuarios con al menos un ATO. El target no tiene nulos y la clave `User ID + Login Timestamp + IP Address` es única.

No se volvió a consultar el RBA original ni se repitió su reconciliación.

## Estrategia

Se construyó una tabla de una fila por usuario, ordenada por User ID. Su etiqueta de estratificación es el máximo booleano de Is Account Takeover entre sus eventos: True si el usuario tiene al menos un ATO.

Se aplicó `sklearn.model_selection.train_test_split` a esa lista de usuarios, con `test_size=0.2`, `random_state=42` y `stratify=etiquetas_usuario`. Finalmente se filtró el enriquecido por pertenencia a cada conjunto de identificadores, manteniendo el orden relativo de sus eventos.

Es una partición estratificada de usuarios, no una partición aleatoria de filas. La proporción 80/20 se aplica a los 2.000 usuarios; la cantidad de eventos difiere ligeramente porque sus historiales tienen tamaños diferentes. Con 43 usuarios positivos, la asignación entera resultante es 34 para train y 9 para test.

Procedimiento reproducible en memoria:

```python
usuarios_ato = df.groupby("User ID", sort=True)["Is Account Takeover"].max()
usuarios_train, usuarios_test = train_test_split(
    usuarios_ato.index.to_numpy(),
    test_size=0.2,
    random_state=42,
    stratify=usuarios_ato.to_numpy(),
)
mascara_train = df["User ID"].isin(usuarios_train)
mascara_test = df["User ID"].isin(usuarios_test)
```

La ejecución utilizó el entorno existente de Python y scikit-learn, sin instalar paquetes ni modificar código de Fase 3. Para reproducibilidad entre entornos conviene conservar la versión utilizada de scikit-learn (1.7.2), además de la semilla y el orden de usuarios.

## Resultados

| Métrica | Train | Test | Total |
|---|---:|---:|---:|
| Eventos | 46.305 | 11.115 | 57.420 |
| Porcentaje de eventos | 80,6426 % | 19,3574 % | 100 % |
| Usuarios | 1.600 | 400 | 2.000 |
| Porcentaje de usuarios | 80 % | 20 % | 100 % |
| Usuarios con ATO | 34 | 9 | 43 |
| Porcentaje de los usuarios con ATO | 79,0698 % | 20,9302 % | 100 % |
| Usuarios sin ATO | 1.566 | 391 | 1.957 |
| Eventos ATO | 36 | 9 | 45 |
| Porcentaje de los eventos ATO | 80 % | 20 % | 100 % |
| Eventos negativos | 46.269 | 11.106 | 57.375 |
| Prevalencia de ATO por evento | 0,077745 % | 0,080972 % | 0,078370 % |
| Columnas | 35 | 35 | 35 |

Se conservaron User ID, Is Account Takeover y las otras 33 columnas. User ID se mantiene para trazabilidad; no se ha decidido ni ejecutado todavía la selección de predictores.

## Verificaciones ejecutadas

| Comprobación | Resultado |
|---|---|
| Archivos de destino inexistentes antes de escribir | Verificado |
| Escritura sin sobrescritura | Modo exclusivo xb para CSV y x para informe |
| Intersección de usuarios | 0 |
| Unión de usuarios | Exactamente los 2.000 usuarios originales |
| Unión de eventos | Exactamente los 57.420 registros originales |
| Eventos asignados simultáneamente a ambos conjuntos | 0 |
| Eventos no asignados | 0 |
| Cada usuario íntegro dentro de un solo conjunto | Sí |
| Claves de evento duplicadas dentro de las salidas | 0 |
| Duplicados de eventos introducidos | 0 |
| Nulos en el target | 0 |
| Suma de positivos de ambos conjuntos | 45 |
| Suma de usuarios con ATO de ambos conjuntos | 43 |
| Columnas y su orden | Las 35 originales, en idéntico orden |
| Valores, tipos inferidos y nulos de cada subconjunto | Idénticos al origen |
| Orden relativo de los eventos de cada salida | Conservado |
| Repetición con semilla 42 | Mismos usuarios, filas y bytes serializados |
| Relectura de ambos archivos escritos | Verificada |
| Origen y archivos preexistentes | Hashes preservados |

Las máscaras de pertenencia se comprobaron como mutuamente excluyentes y exhaustivas. La concatenación de los subconjuntos, restaurando sus índices de origen, se comparó exactamente con el DataFrame original.

Para evitar cambios en la representación de fechas, números o nulos, se conservaron los registros CSV originales byte por byte y se distribuyeron entre archivos según esas máscaras. Se comprobó que la cantidad de líneas físicas correspondiera a los registros esperados. Cada salida se analizó en memoria y, después de escribirla, se releyó y se contrastó con su subconjunto mediante `pd.testing.assert_frame_equal(..., check_exact=True)`.

Se repitió la partición con la misma semilla antes de escribir, comprobando igualdad de las listas de usuarios y de la serialización completa de ambas salidas.

## Archivos generados y huellas

Todos se encuentran en:

``

| Archivo | Tamaño en bytes | SHA-256 |
|---|---:|---|
| `dataset_train_fase04.csv` | 13218803 | `98d4d4970ada7bf11ec2e76f89e93c46c76c3d097043020598638547f977e53f` |
| `dataset_test_fase04.csv` | 3180834 | `90c50ab404c3fcef6cc33e59387aec4ac405f41200e6aa61c0f8bf1db43c72fa` |

El tercer entregable es este informe, `INFORME_PARTICION_FASE04.md`. Su hash se comunica en la entrega final, fuera del propio archivo.

## Limitaciones estadísticas

Solo existen 43 usuarios positivos y 45 eventos ATO. Train dispone de 34 usuarios positivos y 36 ATO; test dispone de 9 usuarios positivos y 9 ATO. Un acierto o error en test modifica el recall de la clase positiva en 1/9, aproximadamente 11,11 puntos porcentuales.

La estratificación preserva aproximadamente la distribución de usuarios con ATO, pero no garantiza proporciones idénticas de eventos ni equilibrio entre clases. El desbalance permanece intencionalmente en ambos conjuntos.

Los eventos de un mismo usuario están relacionados; no deben interpretarse como observaciones totalmente independientes. La separación por usuario evita que su historial aparezca en ambos conjuntos, pero no constituye una evaluación temporal de eventos futuros.

Esta muestra enriquecida no representa necesariamente la prevalencia de ATO en producción. Las métricas futuras deberán acompañarse de conteos absolutos y reconocer la incertidumbre derivada del número reducido de positivos.

La semilla se fijó antes de evaluar modelos. No se buscaron semillas alternativas según resultados predictivos.

## Estado y cierre

No se modificaron los datasets históricos, el enriquecido corregido, el preprocesador existente, el ZIP original ni los módulos de Fase 3. Se verificaron hashes de los archivos preexistentes fuera de los metadatos internos de Git.

No se ejecutaron operaciones Git, pipelines, ajustes de imputadores, codificadores o escaladores, sobremuestreo ni entrenamiento. No se crearon archivos adicionales a los tres entregables autorizados.

La tarea termina con los CSV particionados y verificados. La preparación de predictores y el modelado quedan fuera de esta intervención.
