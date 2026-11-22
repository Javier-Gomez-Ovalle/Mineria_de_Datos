"""ATO solo después de verificar la congelación; nunca retorna parámetros."""
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
from fase04_preparacion.seleccion import TARGET,CLAVE,NUMERICAS,CATEGORICAS
from .datos import PreparadorDatos
from .exportacion import guardar_csv

def resumir_externo(tabla):
    return tabla.groupby('cluster').apply(lambda g:pd.Series(dict(eventos=len(g),eventos_ato=int(g[TARGET].sum()),eventos_no_ato=int((1-g[TARGET]).sum()),prevalencia=float(g[TARGET].mean()),usuarios=g['User ID'].nunique(),usuarios_con_ato=g.loc[g[TARGET].eq(1),'User ID'].nunique())),include_groups=False).reset_index()

def main():
    r=Path('fase04_clustering/resultados');congelada=json.loads((r/'seleccion_congelada.json').read_text(encoding='utf-8'))
    for n,v in congelada['seleccion'].items():assert hashlib.sha256((r/f'etiquetas_{n}.csv').read_bytes()).hexdigest()==v['sha256']
    d=PreparadorDatos().cargar()
    # Primer acceso a y en el flujo de clustering, con decisiones ya inmutables.
    y=pd.read_csv(d.origen,usecols=[TARGET])[TARGET]
    assert y.notna().all() and y.isin([True,False,0,1]).all()
    for n in congelada['seleccion']:
        t=pd.read_csv(r/f'etiquetas_{n}.csv');indices=t.evento_id.to_numpy()
        pd.testing.assert_frame_equal(t[CLAVE],d.claves.iloc[indices][CLAVE].reset_index(drop=True))
        t[TARGET]=y.iloc[indices].astype(int).to_numpy()
        guardar_csv(r/f'evaluacion_externa_{n}.csv',resumir_externo(t))
        p=d.x.iloc[indices].copy();p['cluster']=t.cluster.to_numpy()
        num=p.groupby('cluster')[NUMERICAS+['has_previous_login']].agg(['count','mean','std','min','median','max',lambda s:s.quantile(.25),lambda s:s.quantile(.75)])
        num.columns=['_'.join(c).replace('<lambda_0>','q25').replace('<lambda_1>','q75') for c in num.columns]
        guardar_csv(r/f'perfil_numerico_{n}.csv',num.reset_index())
        filas=[]
        for cluster,g in p.groupby('cluster'):
            for columna in CATEGORICAS+['has_previous_login']:
                for valor,cantidad in g[columna].fillna('Desconocido').value_counts().items():filas.append(dict(cluster=cluster,variable=columna,valor=valor,eventos=cantidad,porcentaje=100*cantidad/len(g)))
        guardar_csv(r/f'perfil_categorico_{n}.csv',pd.DataFrame(filas))

if __name__=='__main__':main()
