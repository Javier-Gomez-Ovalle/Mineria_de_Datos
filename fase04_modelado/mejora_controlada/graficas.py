"""Presentación de todos los resultados; AP heterogénea no se concatena."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve,average_precision_score
from .contratos import OUT,activar_guardia,json_nuevo
from .evaluar import grupos

LABELS={'arbol_baseline':'Árbol base','arbol_ponderado':'Árbol ponderado','gnb_baseline':'GNB base','gnb_ponderado':'GNB ponderado','knn_baseline':'KNN base','knn_ros':'KNN ROS','random_forest':'Random Forest','selector_historico':'Selector 6','selector_ampliado':'Selector 7'}

def main():
    activar_guardia();dest=OUT/'graficas';dest.mkdir(exist_ok=False);catalog=[]
    def save(fig,name,desc):
        fig.tight_layout();fig.savefig(dest/f'{name}.png',dpi=300);fig.savefig(dest/f'{name}.svg');plt.close(fig);catalog.append(dict(archivo=f'graficas/{name}.png',vector=f'graficas/{name}.svg',descripcion=desc))
    gm=pd.read_csv(OUT/'comparacion_global.csv');gm=gm[gm.regla.eq('aprendido')];fm=pd.read_csv(OUT/'metricas_por_fold.csv');fm=fm[fm.regla.eq('aprendido')]
    fig,axes=plt.subplots(2,2,figsize=(14,11))
    for ax,m in zip(axes.ravel(),['precision','recall','f1','f2']):
        bars=ax.barh([LABELS[n] for n in gm.modelo],gm[m]);ax.bar_label(bars,fmt='%.4f',padding=3,fontsize=8);ax.set_xlim(0,max(gm[m])*1.3);ax.set_title(m);ax.grid(axis='x',alpha=.2)
    fig.suptitle('Validación externa por usuarios · umbrales aprendidos internamente');save(fig,'comparacion_metricas','Precision, Recall, F1 y F2 de las siete variantes y dos selectores; sin accuracy.')
    fig,axes=plt.subplots(2,2,figsize=(15,11))
    for ax,m in zip(axes.ravel(),['precision','recall','f1','average_precision']):
        for i,n in enumerate(gm.modelo):
            v=fm[fm.modelo.eq(n)][m];ax.scatter(np.full(len(v),i),v,s=28);ax.errorbar(i,v.mean(),yerr=v.std(),fmt='k_',capsize=4)
        ax.set_xticks(range(len(gm)),[LABELS[n] for n in gm.modelo],rotation=45,ha='right');ax.set_title(m+' por fold; media ± DE');ax.grid(alpha=.2)
    save(fig,'estabilidad_folds','Cinco puntos por procedimiento; DE muestral. AP por fold, incluida la familia seleccionada en cada fold.')
    fig,axes=plt.subplots(1,2,figsize=(14,7))
    for ax,m in zip(axes,['FP','FN']):
        bars=ax.barh([LABELS[n] for n in gm.modelo],gm[m]);ax.bar_label(bars,padding=3);ax.set_xlim(0,max(gm[m])*1.25);ax.set_title(m+' absolutos');ax.grid(axis='x',alpha=.2)
    save(fig,'falsas_alarmas_omisiones','Cantidad absoluta de FP y FN, incluyendo GaussianNB sin ocultarlo.')
    for _,r in gm.iterrows():
        fig,ax=plt.subplots(figsize=(5.5,4.5));matrix=np.array([[r.TN,r.FP],[r.FN,r.TP]],int);ax.imshow(matrix,cmap='Blues')
        for (i,j),v in np.ndenumerate(matrix):ax.text(j,i,f'{v:,}',ha='center',va='center',fontsize=15,color='white' if v>matrix.max()/2 else 'black')
        ax.set_xticks([0,1],['No ATO','ATO']);ax.set_yticks([0,1],['No ATO','ATO']);ax.set_xlabel('Predicción');ax.set_ylabel('Etiqueta');ax.set_title(LABELS[r.modelo]+' · OOF externo');save(fig,'confusion_'+r.modelo,'Matriz absoluta de '+LABELS[r.modelo]+'.')
    allgroups=grupos();fig,axes=plt.subplots(2,3,figsize=(16,10));axes=axes.ravel()
    for f,ax in zip(range(1,6),axes):
        for name,g in allgroups:
            if name.startswith('selector'):continue
            v=g[g.fold_externo.eq(f)];p,r,_=precision_recall_curve(v.y_true,v.score);ap=average_precision_score(v.y_true,v.score);ax.step(r,p,where='post',label=f'{LABELS[name]} AP={ap:.4f}',alpha=.8)
        ax.set_title(f'Fold externo {f}');ax.set_xlabel('Recall');ax.set_ylabel('Precision');ax.set_ylim(0,1.02);ax.legend(fontsize=6);ax.grid(alpha=.2)
    axes[-1].axis('off');axes[-1].text(0,.8,'PR calculada dentro de cada fold.\nNo se mezclan familias del selector.\nGNB base y ponderado pueden solaparse.\nAP global no equivale a AP media.',va='top')
    save(fig,'pr_por_fold','Curvas Precision–Recall y AP de las siete variantes en cada fold externo; sin concatenar familias.')
    fig,ax=plt.subplots(figsize=(12,5));rf=fm[fm.modelo.eq('random_forest')];ax.plot(rf.fold,rf.TP,'o-',label='ATO detectados');ax.plot(rf.fold,rf.FN,'o-',label='ATO omitidos');ax.plot(rf.fold,rf.FP,'o-',label='Falsas alarmas')
    for m in ['TP','FN','FP']:
        for f,v in zip(rf.fold,rf[m]):ax.annotate(str(v),(f,v),textcoords='offset points',xytext=(3,5))
    ax.set_xlabel('Fold externo');ax.set_ylabel('Eventos');ax.set_title('Transferencia del bosque · decisiones congeladas');ax.legend();ax.grid(alpha=.2);save(fig,'bosque_por_fold','Detectados, omitidos y falsas alarmas del bosque por fold.')
    json_nuevo(OUT/'catalogo_graficas.json',catalog)

if __name__=='__main__':main()
