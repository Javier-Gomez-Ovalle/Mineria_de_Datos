"""Descripción de train y errores históricos; no selecciona nuevas variables."""
import json
import numpy as np
import pandas as pd
from fase04_preparacion.seleccion import separar_datos,NUMERICAS
from .contratos import OUT,HIST,activar_guardia,csv_nuevo,json_nuevo,texto_nuevo,verificar_integridad

def tabla(df):
    def val(v):return f'{v:.6g}' if isinstance(v,(float,np.floating)) else str(v)
    return '| '+' | '.join(map(str,df.columns))+' |\n|'+'|'.join(['---']*len(df.columns))+'|\n'+'\n'.join('| '+' | '.join(val(v) for v in row)+' |' for row in df.itertuples(index=False,name=None))+'\n'

def main():
    activar_guardia();n=verificar_integridad();OUT.mkdir(exist_ok=False)
    df=pd.read_csv('dataset_train_fase04.csv');x,y,keys=separar_datos(df)
    parts=json.loads((HIST/'particiones.json').read_text(encoding='utf-8'))
    fold=np.zeros(len(df),int)
    for p in parts:fold[p['validacion']]=p['fold_externo']
    z=x.copy();z['y']=y;z['fold']=fold
    numeric=[];categorical=[]
    for f in range(6):
        part=z if f==0 else z[z.fold.eq(f)]
        for c in NUMERICAS+['has_previous_login']:
            for label,g in part.groupby('y'):
                a=g[c];numeric.append(dict(fold=f,predictor=c,y=int(label),n=len(a),nulos=int(a.isna().sum()),unicos=a.nunique(),min=a.min(),mediana=a.median(),media=a.mean(),p90=a.quantile(.9),p99=a.quantile(.99),max=a.max()))
        for c in ['Country','Device Type','has_previous_login']:
            for level,g in part.groupby(c,dropna=False):categorical.append(dict(fold=f,predictor=c,categoria=level,eventos=len(g),ATO=int(g.y.sum()),prevalencia=g.y.mean()))
    csv_nuevo(OUT/'distribuciones_numericas.csv',pd.DataFrame(numeric));csv_nuevo(OUT/'distribuciones_categoricas.csv',pd.DataFrame(categorical))
    corr=x.select_dtypes('number').corr(method='spearman');csv_nuevo(OUT/'correlaciones_spearman.csv',corr.reset_index())
    identical=z.groupby(list(x.columns),dropna=False).y.agg(['size','sum']).reset_index();mixed=identical[(identical['sum']>0)&(identical['sum']<identical['size'])]
    csv_nuevo(OUT/'perfiles_identicos_clases_mixtas.csv',mixed)
    users=pd.DataFrame({'User ID':df['User ID'],'y':y}).groupby('User ID').y.agg(['size','sum']).reset_index();csv_nuevo(OUT/'distribucion_usuarios_train.csv',users)
    old=pd.read_csv(HIST/'predicciones_externas.csv',float_precision='round_trip')
    global_old=pd.read_csv(HIST/'metricas_globales.csv');errors=[]
    allgroups=[(name,g) for name,g in old.groupby('modelo')]+[('selector_conjunto',old[old.selector])]
    for model,g in allgroups:
        g=g.sort_values('evento_id');np.testing.assert_array_equal(g.evento_id,np.arange(len(y)));np.testing.assert_array_equal(g.y_true,y)
        w=x.copy();w['User ID']=df['User ID'];w['y']=y.to_numpy();w['pred']=g.pred_aprendido.to_numpy();w['actividad_usuario']=w['User ID'].map(df['User ID'].value_counts());w['actividad_bin']=pd.cut(w.actividad_usuario,[0,10,30,100,np.inf]).astype(str)
        w['fallos_previos']=np.where(w.failed_attempts_1h>0,'si','no')
        for c in ['User ID','Country','Device Type','has_previous_login','actividad_bin','fallos_previos']:
            for level,v in w.groupby(c):
                tp=int(((v.y==1)&(v.pred==1)).sum());fp=int(((v.y==0)&(v.pred==1)).sum());fn=int(((v.y==1)&(v.pred==0)).sum());neg=int((v.y==0).sum())
                errors.append(dict(modelo=model,perfil=c,valor=str(level),eventos=len(v),ATO=int(v.y.sum()),TP=tp,FP=fp,FN=fn,FPR=fp/neg if neg else np.nan,recall=tp/int(v.y.sum()) if v.y.sum() else np.nan))
    e=pd.DataFrame(errors);csv_nuevo(OUT/'errores_historicos_por_perfil.csv',e)
    summary=dict(eventos=len(df),usuarios=len(users),ATO=int(y.sum()),usuarios_ATO=int((users['sum']>0).sum()),prevalencia=float(y.mean()),grupos_identicos_mixtos=len(mixed),ATO_en_grupos_mixtos=int(mixed['sum'].sum()),negativos_en_grupos_mixtos=int((mixed['size']-mixed['sum']).sum()),historicos_verificados=n)
    json_nuevo(OUT/'diagnostico.json',summary)
    top=e[(e.modelo=='selector_conjunto')&(e.perfil=='Country')].sort_values(['FN','FP'],ascending=False).head(10)
    text='''# Diagnóstico de capacidad predictiva — Fase 4

Fecha: 2026-11-21. Solo train. Diagnóstico producido antes de ejecutar el nuevo experimento.

## Auditoría y evidencia

Se inspeccionaron informes de corrección de target, preprocesamiento, Impossible Travel, CV1/CV2, clustering, selección y anidada; fábricas de modelos y transformadores, transporte de target y cálculo temporal. El manifiesto de entrega anidada coincide con sus archivos; el inventario nuevo conserva 406 archivos históricos permitidos. Test se excluye antes de hash/lectura; no se acredita su integridad mediante acceso al contenido. No se repitió reconciliación RBA ni pipelines históricos.

Fase 3 mantiene el target unido al evento y valida mediante User ID + timestamp + IP, detectando cambios de identidad/etiqueta. Rolling closed=left y shift(1) respaldan por inspección estática el uso de historial anterior. Los tests y reconciliación previos son evidencia histórica, no pruebas vueltas a ejecutar aquí. La disponibilidad real del historial en producción sigue siendo un contrato necesario; CV por usuario no demuestra generalización temporal.

La representación aprobada usa medianas locales y One-Hot; GaussianNB añade log1p y KNN log1p/StandardScaler. Árboles sin poda, GaussianNB var_smoothing=1e-9, KNN k=5 uniforme euclídeo. Ponderación/ROS se limitan al ajuste local. CV1 estratifica eventos agrupando usuarios; CV2 y anidada estratifican usuarios positivos. Semilla 42. CV1 tuvo usuarios positivos [9,8,1,8,8]; CV2/anidada [6,7,7,7,7], eventos [6,7,7,8,8]. La anidada registra 120 ajustes y 20 pruebas históricas aprobadas. No hay evidencia de discrepancia entre tabla anidada y resumen del encargo.

## Desbalance y predictores

'''+tabla(pd.DataFrame([summary]))+'''
32 usuarios tienen un ATO y dos tienen dos: 36 eventos no equivalen a 36 sujetos independientes. Un acierto mueve recall global 2,78 puntos porcentuales y el recall de un fold 12,5–16,7 puntos. La prevalencia es 0,07775%; un clasificador que nunca alerta tendría alta accuracy sin detectar ningún ATO.

Los contadores tienen medianas cero en ambas clases, máximos negativos 20/28 y positivos 3/3; su Spearman es 0,9051. La separación descriptiva numérica es débil y no monotónica. El intervalo anterior tiene 1.600 ausentes estructurales (primer evento), 44.608 valores distintos y cola hasta 8.757 horas; su cardinalidad permite sobreajuste. has_previous_login codifica precisamente esa ausencia, no una observación adicional independiente. Ocho positivos son primer login; 28 tienen historia. Los seis predictores no describen hábitos personalizados de país/dispositivo.

30 positivos usan desktop y seis mobile; 15 están en RO, cinco NO, cuatro IT. País tiene 54 categorías y dispositivo cuatro. Estas diferencias descriptivas pueden explicar parte del ranking, pero no prueban causalidad ni transferencia; categorías con pocos ATO generan estimaciones frágiles. Se exportan distribuciones por clase dentro de cada fold, incluidos ceros/ausentes/extremos, sin elegir variables ni umbrales a partir de ellas.

Cuatro vectores idénticos de seis entradas contienen ocho positivos y 621 negativos. Un predictor determinista basado solo en esas entradas asigna el mismo score a cada grupo. No es un límite superior de generalización ni demuestra imposibilidad universal: evidencia una limitación de representación para esos casos observados.

## Modelos y errores

'''+tabla(global_old[global_old.regla.eq('aprendido')][['modelo','TP','FP','FN','precision','recall','f1','average_precision']])+'''
La AP concatenada por variante no equivale a AP media por fold; el selector no tiene AP global. KNN ofrece ranking relativo interesante, pero pocos aciertos al decidir alertas. GaussianNB produce scores extremos y miles de falsas alarmas; ponderar tampoco resuelve esa limitación. El árbol ponderado mejora F1 agregado respecto a otros, pero no fue seleccionado de forma estable por el procedimiento interno. El clustering segmenta geometría de X; la similitud de prevalencias entre grupos no lo convierte en detector.

Perfil de errores del selector histórico por país (denominadores incluidos):

'''+tabla(top)+'''
El archivo errores_historicos_por_perfil.csv incluye todos los modelos y selector, usuarios, país, dispositivo, presencia de historia, tramos de actividad y fallos previos. Se incluyen eventos/ATO y FPR/recall por grupo para evitar confundir tamaño con concentración de riesgo. Identificadores se usan solo para auditoría, nunca como predictores. No se construyen reglas para memorizar los errores conocidos.

## Exclusiones y temporalidad

| Variables | Decisión y requisito pendiente |
|---|---|
| Login Successful / login_exitoso_normalizado | Resultado del intento actual: no disponible en el escenario preautenticación. Solo reconsiderable cambiando explícitamente el escenario. Fallos de intentos anteriores sí son historial. |
| Is Attack IP | Sin fecha de disponibilidad de inteligencia por evento; no se demuestra conocimiento contemporáneo. Mantener fuera. |
| Region / City / enriquecimiento IP | Geografía sintética y asociaciones no verificadas; enriquecimiento externo sin contrato temporal fiable. No reincorporar por asociación con y. |
| distance_previous_km / required_speed_kmh / impossible_travel | Cero mezcla ausencia de evaluación y normalidad; centroides incompletos y geografía no física. Informe previo: 5.662 evaluables, 40.643 no evaluables (39.043 centroides y 1.600 sin anterior), nueve alertas según regla existente. travel_evaluable corregiría representación, no fiabilidad. |
| Turnos, residencia, empleados | Atributos simulados sin evidencia observada/temporal por usuario. No inferir causalidad de relaciones artificiales. |

[La documentación primaria de RBA](https://github.com/das-group/rba-dataset) describe datos sintetizados y limitaciones geográficas. No se reabre el RBA original. Ninguna variable excluida reúne nueva evidencia suficiente para reintroducirla en esta intervención.

## Diagnóstico y oportunidad

No puede atribuirse causalmente el bajo rendimiento a un único factor: pocos positivos, solapamiento, representación limitada y supuestos de los modelos confluyen. El fracaso parcial de pesos/ROS contradice que solo baste equilibrar clases. No se demuestra que todo algoritmo posible vaya a fallar.

Se justifica un único contraste: bosque ponderado con búsqueda pequeña de regularización interna, para probar si promediar árboles reduce inestabilidad. No se justifica una batería abierta de algoritmos ni rescatar señales de semántica dudosa. Diseño y criterios congelados en PROPUESTA_EXPERIMENTOS_MEJORA_FASE04.md. El análisis repetido del mismo train aumenta el riesgo de adaptación; los resultados nuevos serán exploratorios y no una validación externa independiente.

## Archivos y limitaciones

Tablas completas en fase04_modelado/mejora_controlada/resultados/: diagnostico.json, distribuciones_numericas.csv, distribuciones_categoricas.csv (fold=0 global, 1–5 externo), correlaciones_spearman.csv, perfiles_identicos_clases_mixtas.csv, distribucion_usuarios_train.csv y errores_historicos_por_perfil.csv. No se afirma haber comprobado causalidad ni disponibilidad operacional por ejecutar tests. La auditoría de código es estática salvo los contratos explícitamente comprobados con datos y hashes.
'''
    texto_nuevo('INFORME_DIAGNOSTICO_CAPACIDAD_PREDICTIVA_FASE04.md',text)
    print(json.dumps(summary))

if __name__=='__main__':main()
