"""Redibuja OOF históricos: no importa ni ajusta modelos supervisados."""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve
from fase04_modelado.metricas import calcular_metricas,METRICAS
from .estilo import plt,COLORES,guardar
from .exportacion import guardar_csv

NOMBRES={'arbol_baseline':'Árbol baseline','arbol_ponderado':'Árbol ponderado','gnb_baseline':'GaussianNB baseline','gnb_ponderado':'GaussianNB ponderado','knn_baseline':'KNN baseline','knn_ros':'KNN + RandomOverSampler'}

def main():
    destino=Path('fase04_modelado/resultados_presentacion_supervisado');destino.mkdir()
    consolidadas=[]
    for protocolo,carpeta in [('CV1','resultados'),('CV2','resultados_cv_usuario')]:
        r=Path('fase04_modelado')/carpeta;g=destino/protocolo
        oof=pd.read_csv(r/'predicciones_oof.csv');c=pd.read_csv(r/'comparacion_modelos.csv').set_index('modelo').loc[list(NOMBRES)].reset_index();f=pd.read_csv(r/'metricas_por_fold.csv')
        for nombre in NOMBRES:
            p=oof[oof.modelo.eq(nombre)];m=calcular_metricas(p.y_true,p.score)
            for metrica in ['TP','FP','TN','FN',*METRICAS]:np.testing.assert_allclose(m[metrica],c.set_index('modelo').loc[nombre,metrica],rtol=1e-12,atol=1e-15)
        c['protocolo']=protocolo;consolidadas.append(c)
        fig,axes=plt.subplots(2,2,figsize=(15,10),layout='constrained')
        for ax,m in zip(axes.flat,METRICAS):
            b=ax.barh(list(NOMBRES.values()),c[m],color=COLORES);ax.bar_label(b,fmt='%.5f',padding=3);ax.invert_yaxis();ax.set(title=m.replace('average_precision','Average Precision'),xlabel='Métrica OOF global',xlim=(0,max(c[m].max()*1.35,.01)))
        fig.suptitle(f'{protocolo} · comparación OOF train | umbral 0,5');guardar(fig,g,'metricas_oof')
        for nombre,titulo in NOMBRES.items():
            v=c.set_index('modelo').loc[nombre];cm=np.array([[v.TN,v.FP],[v.FN,v.TP]],dtype=int)
            fig,ax=plt.subplots(figsize=(6,5),layout='constrained');ax.imshow(cm,cmap='Blues')
            for (i,j),valor in np.ndenumerate(cm):ax.text(j,i,f'{[["TN","FP"],["FN","TP"]][i][j]}\n{valor:,}',ha='center',va='center',fontsize=18,color='white' if valor>cm.max()/2 else 'black')
            ax.set(xticks=[0,1],yticks=[0,1],xticklabels=['No ATO','ATO'],yticklabels=['No ATO','ATO'],xlabel='Predicción',ylabel='Etiqueta real',title=f'{protocolo} · {titulo}\nConteos OOF absolutos · umbral 0,5');guardar(fig,g,f'confusion_{nombre}')
        fig,ax=plt.subplots(figsize=(12,7),layout='constrained')
        for (nombre,titulo),color,estilo in zip(NOMBRES.items(),COLORES,['-','--','-',':','-.','--']):
            p=oof[oof.modelo.eq(nombre)];precision,recall,_=precision_recall_curve(p.y_true,p.score);ap=c.set_index('modelo').loc[nombre,'average_precision'];ax.step(recall,precision,where='post',color=color,linestyle=estilo,label=f'{titulo} · AP={ap:.6f}')
        prevalencia=p.y_true.mean();ax.axhline(prevalencia,color='black',linestyle=':',label=f'Prevalencia={prevalencia:.6f}');ax.set(xlim=(0,1),ylim=(0,1.02),xlabel='Recall',ylabel='Precision',title=f'{protocolo} · curvas Precision–Recall OOF\nGaussianNB baseline y ponderado se superponen');ax.legend(loc='upper left',bbox_to_anchor=(1.01,1));guardar(fig,g,'curvas_pr')
        fig,axes=plt.subplots(2,2,figsize=(15,10),layout='constrained')
        for ax,m in zip(axes.flat,METRICAS):
            for (nombre,titulo),color in zip(NOMBRES.items(),COLORES):
                t=f[f.modelo.eq(nombre)];ax.plot(t.fold,t[m],'o-',label=titulo,color=color,alpha=.85)
            ax.set(title=m.replace('average_precision','Average Precision'),xlabel='Fold',ylabel='Métrica por fold',xticks=sorted(f.fold.unique()));ax.set_ylim(bottom=0);ax.grid(alpha=.2)
        axes[0,0].legend(fontsize=9);fig.suptitle(f'{protocolo} · estabilidad por fold (subtrain solapados)');guardar(fig,g,'estabilidad_folds')
        fig,axes=plt.subplots(2,2,figsize=(15,10),layout='constrained')
        for ax,m in zip(axes.flat,METRICAS):
            vals=[f.loc[f.modelo.eq(n),m].to_numpy() for n in NOMBRES];ax.boxplot(vals,orientation='horizontal',tick_labels=list(NOMBRES.values()),showmeans=True)
            for i,v in enumerate(vals):ax.scatter(v,np.full(len(v),i+1),s=20,color=COLORES[i])
            ax.set(title=m.replace('average_precision','Average Precision'),xlabel='Valores de cinco folds');ax.set_xlim(left=0)
        fig.suptitle(f'{protocolo} · variabilidad | puntos: folds; triángulo: media\nCajas y desviaciones no son intervalos de confianza');guardar(fig,g,'variabilidad_folds')
        fig,axes=plt.subplots(1,2,figsize=(15,6),layout='constrained')
        for ax,m in zip(axes,['FP','FN']):
            b=ax.barh(list(NOMBRES.values()),c[m],color=COLORES);ax.bar_label(b,fmt='%d',padding=3);ax.invert_yaxis();ax.set(title=m,xlabel='Eventos OOF',xlim=(0,max(c[m].max()*1.25,1)))
        fig.suptitle(f'{protocolo} · falsas alarmas y omisiones | escalas explícitas');guardar(fig,g,'fp_fn')
    todo=pd.concat(consolidadas);guardar_csv(destino/'metricas_verificadas.csv',todo)
    fig,axes=plt.subplots(2,2,figsize=(15,10),layout='constrained');pos=np.arange(6)
    for ax,m in zip(axes.flat,METRICAS):
        for j,(nombre,t) in enumerate(todo.groupby('protocolo',sort=False)):
            b=ax.barh(pos+(j-.5)*.35,t[m],height=.35,label=nombre,color=COLORES[j]);ax.bar_label(b,fmt='%.4f',padding=3,fontsize=9)
        ax.set(yticks=pos,yticklabels=list(NOMBRES.values()),xlabel='Métrica OOF global',title=m.replace('average_precision','Average Precision'),xlim=(0,max(todo[m].max()*1.35,.01)));ax.invert_yaxis();ax.legend()
    fig.suptitle('Cambio de protocolo CV1 → CV2 | mismos modelos y datos\nDiferencias de partición, no mejora del algoritmo');guardar(fig,destino,'comparacion_protocolos')

if __name__=='__main__':main()
