# Resultados conservados de selección del umbral

Umbral: **0.9976439543869569**. Regla score >= umbral. F1 exacto 4/23 = 0.17391304347826086. Precisión 0.14285714285714285; recall 0.2222222222222222.

| Real / predicción | No ATO | ATO |
|---|---:|---:|
| No ATO | 46221 | 48 |
| ATO | 28 | 8 |

13 candidatos evaluados; tabla completa en candidatos_umbral.csv. ?nico umbral con F1 máximo: [0.9976439543869569]. Se aplic? la regla congelada: F1 por evento sobre OOF concatenadas, fracciones exactas, desempate cercanía a 0.5 y después mayor. No se usaron umbrales históricos externos.

OOF: predicciones_oof.csv, SHA-256 28a1d200f65cb72229b34cd41cb888f3698e785eb680229e944cd5f537c73a57. Registro numérico: umbral_definitivo.json, SHA-256 e5327bd50594edd9d1c67e5076bd53f101c9194b068911e8faf16567f7109095.

Distribución de probabilidades, fold 0 = OOF concatenadas:
```
 fold     n  unicos  ceros  unos  count     mean      std  min  1%  25%  50%  75%  90%      99%  max
    0 46305      11  45833    40  46305 0.009012 0.088930    0   0    0    0    0    0 0.860755    1
    1 16361       5  16330    24  16361 0.001894 0.043471    0   0    0    0    0    0 0.000000    1
    2 14522       5  14301    12  14522 0.013327 0.107337    0   0    0    0    0    0 0.860755    1
    3 15422       5  15202     4  15422 0.012502 0.103968    0   0    0    0    0    0 0.871124    1
```

Todos los valores exactos y frecuencias por clase/fold en valores_probabilidades_oof.csv. Trazabilidad de eventos en predicciones_oof.csv y particiones.json; decisiones en decisiones_oof.csv. Métricas por fold en metricas_por_fold_umbral_seleccionado.csv.

Las probabilidades OOF proceden de tres modelos distintos, sin escala calibrada común garantizada. El umbral se seleccion? utilizando estas etiquetas OOF: su F1 y las métricas por fold al umbral elegido NO son estimaciones independientes del rendimiento. El ajuste final con todo train puede producir otra distribución de scores; no se garantiza transferencia del umbral. AP concatenada OOF 0.02478258099105275 tampoco equivale a AP media por fold y no intervino en la selección.

La selección quedó guardada antes del ajuste final. La ejecución se detuvo por un error posterior al escribir la auditoría final; modelo y preprocesador no se serializaron. No se ha evaluado test.
