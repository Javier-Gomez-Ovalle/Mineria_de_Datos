"""Figuras derivadas solo de predicciones OOF de train."""
from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR', str(Path('fase04_modelado/resultados_cv_usuario/cache_graficas').resolve()))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve
from .metricas import calcular_metricas, METRICAS
from .modelos import NOMBRES


def generar():
    r=Path('fase04_modelado/resultados_cv_usuario');g=r/'graficas'
    if g.exists():raise FileExistsError(g)
    p=pd.read_csv(r/'predicciones_oof.csv');f=pd.read_csv(r/'metricas_por_fold.csv');c=pd.read_csv(r/'comparacion_modelos.csv')
    for n in NOMBRES:
        a=p[p.modelo==n];m=calcular_metricas(a.y_true,a.score)
        for k in ['TP','FP','TN','FN',*METRICAS]:np.testing.assert_allclose(m[k],c.set_index('modelo').loc[n,k],rtol=1e-12,atol=1e-15)
    g.mkdir();plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    colors=plt.get_cmap('tab10').colors[:6];labels=list(NOMBRES.values())
    def guardar(fig,n):
        fig.savefig(g/f'{n}.png',dpi=180,bbox_inches='tight');fig.savefig(g/f'{n}.svg',bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(15,10),layout='constrained')
    for ax,m in zip(axes.flat,METRICAS):
        bars=ax.barh(labels,c[m],color=colors);ax.invert_yaxis();ax.bar_label(bars,fmt='%.5f',padding=4)
        ax.set_xlim(0,max(c[m].max()*1.3,.01));ax.set_title(m.replace('average_precision','Average Precision (PR-AUC)'));ax.set_xlabel('Valor OOF global')
    fig.suptitle('Comparacion de seis variantes | OOF train, umbral 0,5',fontsize=16);guardar(fig,'comparacion_metricas')
    for i,(n,label) in enumerate(NOMBRES.items()):
        row=c.set_index('modelo').loc[n];arr=np.array([[row.TN,row.FP],[row.FN,row.TP]],dtype=int)
        fig,ax=plt.subplots(figsize=(6,5),layout='constrained');ax.imshow(arr,cmap='Blues')
        for (a,b),v in np.ndenumerate(arr):ax.text(b,a,f'{[ ["TN","FP"],["FN","TP"] ][a][b]}\n{v:,}',ha='center',va='center',fontsize=17,color='white' if v>arr.max()/2 else 'black')
        ax.set(xticks=[0,1],yticks=[0,1],xticklabels=['No ATO','ATO'],yticklabels=['No ATO','ATO'],xlabel='Prediccion',ylabel='Etiqueta real',title=f'{label}\nMatriz OOF train, umbral 0,5');guardar(fig,f'confusion_{n}')
    fig,axes=plt.subplots(1,2,figsize=(15,6),layout='constrained')
    styles=['-','--','-',':','-.','--']
    for (n,label),color,style in zip(NOMBRES.items(),colors,styles):
        a=p[p.modelo==n];pr,re,_=precision_recall_curve(a.y_true,a.score);ap=c.set_index('modelo').loc[n,'average_precision']
        for ax in axes:ax.step(re,pr,where='post',label=f'{label}: AP={ap:.6f}',color=color,linestyle=style,linewidth=1.8)
    prevalence=p[p.modelo==next(iter(NOMBRES))].y_true.mean()
    for ax in axes:
        ax.axhline(prevalence,color='black',linestyle=':',label=f'Prevalencia train: {prevalence:.6f}');ax.set(xlabel='Recall',ylabel='Precision',xlim=(0,1),ylim=(0,1));ax.grid(alpha=.2)
    axes[0].set_title('Curvas Precision-Recall OOF');axes[1].set_title('Detalle de baja precision (escala log)');axes[1].set_yscale('log');axes[1].set_ylim(1e-5,1)
    axes[0].legend(fontsize=8);fig.suptitle('Average Precision, no area trapezoidal | curvas coincidentes pueden superponerse');guardar(fig,'curvas_precision_recall')
    fig,axes=plt.subplots(2,2,figsize=(15,10),layout='constrained')
    for ax,m in zip(axes.flat,METRICAS):
        for (n,label),color,style in zip(NOMBRES.items(),colors,styles):
            a=f[f.modelo==n];ax.plot(a.fold,a[m],marker='o',label=label,color=color,linestyle=style)
        ax.set(title=m,xlabel='Fold (positivos: 6, 7, 7, 8, 8)',ylabel='Valor',xticks=range(1,6));ax.grid(alpha=.2)
    handles,leg=axes[0,0].get_legend_handles_labels();fig.legend(handles,leg,loc='outside lower center',ncol=3);fig.suptitle('Estabilidad por fold | todos los resultados de validacion');guardar(fig,'estabilidad_folds')
    fig,axes=plt.subplots(1,2,figsize=(14,5),layout='constrained')
    for ax,m in zip(axes,['FP','FN']):
        bars=ax.barh(labels,c[m],color=colors);ax.invert_yaxis();ax.bar_label(bars,fmt='%d',padding=4);ax.set_xlim(0,c[m].max()*1.25);ax.set(title=f'{m} absolutos OOF',xlabel='Eventos')
    guardar(fig,'falsos_positivos_negativos')
    fig,axes=plt.subplots(2,2,figsize=(15,10),layout='constrained')
    for ax,m in zip(axes.flat,METRICAS):
        for i,(n,label) in enumerate(NOMBRES.items()):
            vals=f[f.modelo==n][m];mean=vals.mean();sd=vals.std(ddof=1)
            ax.errorbar(mean,i,xerr=sd,fmt='o',color=colors[i],capsize=4)
            ax.scatter(vals,np.full(len(vals),i)+np.linspace(-.12,.12,len(vals)),color=colors[i],alpha=.45,s=20)
            ax.text(max(mean+sd,vals.max())+.005,i,f'{mean:.4f} +/- {sd:.4f}',va='center',fontsize=8)
        ax.set_yticks(range(6),labels);ax.invert_yaxis();ax.set_title(m);ax.set_xlabel('Media +/- DE muestral; puntos = folds');ax.margins(x=.5)
    fig.suptitle('Variabilidad entre folds | barras no son intervalos de confianza');guardar(fig,'variabilidad_folds')
    print('Graficas generadas:',len(list(g.glob('*.png'))))


if __name__=='__main__':generar()
