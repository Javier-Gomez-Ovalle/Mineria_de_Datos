"""Extiende las particiones anidadas congeladas con una familia; 65 ajustes."""
import json,time,platform
from fractions import Fraction
import numpy as np
import pandas as pd
import sklearn,psutil
from fase04_preparacion.seleccion import separar_datos
from fase04_modelado.modelos import NOMBRES
from .contratos import *
from .ajuste import predecir,crear_bosque

def main():
    activar_guardia();verificar_integridad();t=time.perf_counter()
    df=pd.read_csv('dataset_train_fase04.csv');x,y,keys=separar_datos(df);users=keys['User ID']
    train_hash=sha('dataset_train_fase04.csv');oldconfig=json.loads((HIST/'configuracion_congelada.json').read_text(encoding='utf-8'));assert train_hash==oldconfig['train_sha256']
    parts=json.loads((HIST/'particiones.json').read_text(encoding='utf-8'));verificar_particiones(parts,users,len(y))
    config=dict(fecha='2026-11-21',train_sha256=train_hash,propuesta_sha256=sha('PROPUESTA_EXPERIMENTOS_MEJORA_FASE04.md'),particiones_sha256=sha(HIST/'particiones.json'),configuraciones=[crear_bosque(c).get_params() for c in CONFIGS],predictores=list(x),criterio='F1 OOF interno; desempates umbral distancia .5 y mayor; configuracion orden fijo',selector_orden=list(NOMBRES)+['random_forest'],ajustes_previstos=65,versiones=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,sklearn=sklearn.__version__))
    json_nuevo(OUT/'configuracion_congelada.json',config);audits=[];external=[];rss=[]
    for p in parts:
        fold=p['fold_externo'];a=p['ajuste'];b=p['validacion'];decisions=[];inner_records=[]
        old=json.loads((HIST/f'decisiones_congeladas_{fold}.json').read_text(encoding='utf-8'));assert sha(HIST/f'oof_internas_{fold}.csv')==old['oof_sha256']
        old_oof=pd.read_csv(HIST/f'oof_internas_{fold}.csv',float_precision='round_trip')
        for name,g in old_oof.groupby('modelo'):
            g=g.sort_values('evento_id');assert set(g.evento_id)==set(a) and g.evento_id.is_unique
            np.testing.assert_array_equal(g.y_true,y.iloc[g.evento_id]);np.testing.assert_array_equal(g.usuario,users.iloc[g.evento_id])
            d,_=seleccionar(g.y_true,g.score);assert d['umbral']==old['decisiones'][name]['umbral']
        for ci,c in enumerate(CONFIGS):
            scores=pd.Series(np.nan,index=a);coverage=pd.Series(0,index=a)
            for ii,q in enumerate(p['internas'],1):
                aa=q['ajuste'];bb=q['validacion'];s,audit=predecir(x.iloc[aa],y.iloc[aa],x.iloc[bb],c)
                scores.loc[bb]=s;coverage.loc[bb]+=1
                audit.update(fold_externo=fold,fold_interno=ii,configuracion=ci,nivel='interno');audits.append(audit)
                inner_records.append(pd.DataFrame(dict(evento_id=bb,usuario=users.iloc[bb].to_numpy(),y_true=y.iloc[bb].to_numpy(),score=s,fold_externo=fold,fold_interno=ii,configuracion=ci)))
            assert coverage.eq(1).all() and scores.notna().all()
            d,table=seleccionar(y.iloc[a],scores.loc[a]);d['configuracion']=ci;decisions.append(d)
            csv_nuevo(OUT/f'umbrales_internos_{fold}_{ci}.csv',table)
            print(f'Externo {fold}/5 configuracion {ci+1}/4: F1 interno {d["f1"]:.6f}, umbral {d["umbral"]:.8g}',flush=True)
        best=max(range(4),key=lambda i:fraccion(decisions[i]));d=decisions[best]
        names=list(NOMBRES);values=[Fraction(old['decisiones'][n]['f1_numerador'],old['decisiones'][n]['f1_denominador']) for n in names]+[fraccion(d)]
        joint=(names+['random_forest'])[max(range(7),key=lambda i:values[i])]
        csv_nuevo(OUT/f'oof_internas_{fold}.csv',pd.concat(inner_records,ignore_index=True))
        frozen=dict(fold_externo=fold,configuraciones=decisions,elegida=best,umbral=d['umbral'],selector_ampliado=joint,oof_sha256=sha(OUT/f'oof_internas_{fold}.csv'),historico_decisiones_sha256=sha(HIST/f'decisiones_congeladas_{fold}.json'))
        path=OUT/f'decision_congelada_{fold}.json';json_nuevo(path,frozen);freeze_hash=sha(path)
        s,audit=predecir(x.iloc[a],y.iloc[a],x.iloc[b],CONFIGS[best]);audit.update(fold_externo=fold,fold_interno=0,configuracion=best,nivel='externo');audits.append(audit)
        assert sha(path)==freeze_hash
        rec=keys.iloc[b].copy();rec.insert(0,'evento_id',b);rec['fold_externo']=fold;rec['modelo']='random_forest';rec['score']=s;rec['umbral']=d['umbral'];rec['pred_aprendido']=(s>=d['umbral']).astype(int);rec['pred_05']=(s>=.5).astype(int);rec['configuracion']=best
        external.append(rec);rss.append(psutil.Process().memory_info().rss)
    out=pd.concat(external,ignore_index=True);assert len(out)==len(y) and out.evento_id.is_unique
    # Solo después de congelar y predecir los cinco externos se incorporan etiquetas de evaluación.
    out['y_true']=y.iloc[out.evento_id].to_numpy();csv_nuevo(OUT/'predicciones_externas_rf.csv',out)
    json_nuevo(OUT/'auditoria_ajustes.json',audits)
    json_nuevo(OUT/'ejecucion.json',dict(ajustes=len(audits),segundos=time.perf_counter()-t,rss_muestreado_bytes=rss,historicos_verificados=verificar_integridad(),test_leido=False,modelo_final_entrenado=False))
    print('Completados 65 ajustes; test cerrado.',flush=True)

if __name__=='__main__':main()
