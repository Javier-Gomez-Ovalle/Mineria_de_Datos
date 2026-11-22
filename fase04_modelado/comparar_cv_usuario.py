"""Comparacion descriptiva de dos protocolos; no selecciona umbrales."""
from pathlib import Path
import json
import hashlib
import os
os.environ.setdefault('MPLCONFIGDIR',str(Path('fase04_modelado/resultados_cv_usuario/cache_graficas').resolve()))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .metricas import METRICAS
from .modelos import NOMBRES


def ejecutar():
    r=Path('fase04_modelado/resultados_cv_usuario');old=Path('fase04_modelado/resultados')
    prev=pd.read_csv(old/'comparacion_modelos.csv').set_index('modelo');new=pd.read_csv(r/'comparacion_modelos.csv').set_index('modelo')
    rows=[]
    medidas=['TP','FP','TN','FN',*METRICAS,*[m+s for m in METRICAS for s in ['_media_folds','_sd_folds']], 'entrenamiento_s','prediccion_s']
    for nombre in NOMBRES:
        for m in medidas:
            row={'modelo':nombre,'metrica':m,'cv_evento':prev.loc[nombre,m],'cv_usuario':new.loc[nombre,m], 'diferencia_usuario_menos_evento':new.loc[nombre,m]-prev.loc[nombre,m]}
            if m in METRICAS:
                row['rango_cv_evento']=prev[m].rank(method='min',ascending=False)[nombre]
                row['rango_cv_usuario']=new[m].rank(method='min',ascending=False)[nombre]
            rows.append(row)
    pd.DataFrame(rows).to_csv(r/'comparacion_protocolos.csv',index=False,mode='x')
    dist=[]
    for nombre,base in [('cv_evento',old),('cv_usuario',r)]:
        f=pd.read_csv(base/'distribucion_folds.csv');f.insert(0,'protocolo',nombre)
        for parte in ['subtrain','validacion']:
            f[f'{parte}_negativos']=f[f'{parte}_eventos']-f[f'{parte}_positivos']
            f[f'{parte}_usuarios_negativos']=f[f'{parte}_usuarios']-f[f'{parte}_usuarios_positivos']
        dist.append(f)
    pd.concat(dist,ignore_index=True).to_csv(r/'comparacion_distribucion_folds.csv',index=False,mode='x')
    o=pd.read_csv(r/'predicciones_oof.csv');a=o[o.modelo=='arbol_baseline']
    users=a.groupby('User ID',sort=True).agg(usuario_con_ato=('y_true','max'),fold_validacion=('fold','first'),eventos=('evento_id','size'),eventos_ato=('y_true','sum')).reset_index()
    users.to_csv(r/'asignacion_usuarios.csv',index=False,mode='x')
    f=pd.read_csv(r/'distribucion_folds.csv')
    assert len(users)==1600 and users.usuario_con_ato.sum()==34 and users.eventos.sum()==46305
    protocolo={'splitter':'StratifiedKFold','unidad':'usuarios','estrato':'max(Is Account Takeover) por User ID','orden_usuarios':'User ID ascendente, groupby(sort=True)', 'n_splits':5,'shuffle':True,'random_state':42,'expansion':'todos los eventos del usuario, conservando orden original de train','semillas_ensayadas':[42], 'test_leido':False,'reentrenamiento_final':False,'validacion_usuarios_positivos':f.validacion_usuarios_positivos.tolist(),'validacion_eventos_positivos':f.validacion_positivos.tolist(),'referencia_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [old/'comparacion_modelos.csv',old/'distribucion_folds.csv',old/'metricas_por_fold.csv']}}
    with (r/'protocolo_cv_usuario.json').open('x',encoding='utf-8') as h:json.dump(protocolo,h,indent=2)
    labels=list(NOMBRES.values());fig,axes=plt.subplots(2,2,figsize=(15,10),layout='constrained')
    for ax,m in zip(axes.flat,METRICAS):
        yy=np.arange(6);a=ax.barh(yy-.17,prev.loc[list(NOMBRES),m],height=.32,label='CV1: estrato por evento',color='#577590');b=ax.barh(yy+.17,new.loc[list(NOMBRES),m],height=.32,label='CV2: estrato por usuario',color='#c06c38')
        ax.set_yticks(yy,labels);ax.invert_yaxis();ax.bar_label(a,fmt='%.5f',padding=3,fontsize=8);ax.bar_label(b,fmt='%.5f',padding=3,fontsize=8)
        ax.set_title(m);ax.set_xlim(0,max(prev[m].max(),new[m].max())*1.32);ax.set_xlabel('Metrica OOF global')
    fig.suptitle('Sensibilidad al protocolo de folds | mismos modelos y umbral 0,5');fig.legend(*axes[0,0].get_legend_handles_labels(),loc='outside lower center',ncol=2)
    for ext in ['png','svg']:fig.savefig(r/'graficas'/f'comparacion_protocolos.{ext}',dpi=180,bbox_inches='tight')
    plt.close(fig)
    print(new[['TP','FP','TN','FN',*METRICAS,*[m+'_sd_folds' for m in METRICAS]]].to_string())


if __name__=='__main__':ejecutar()
