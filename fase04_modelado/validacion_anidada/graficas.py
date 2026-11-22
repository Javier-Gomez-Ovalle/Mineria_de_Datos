"""Figuras de las seis variantes y selector sin ordenar por ganador externo."""
import os
from .auditoria import RAIZ,RESULTADOS,activar_guardia,guardar_json
os.environ['MPLCONFIGDIR']=str((RAIZ/'cache_graficas').resolve())
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from fase04_modelado.modelos import NOMBRES

ETIQUETAS=['Árbol baseline','Árbol ponderado','GaussianNB baseline','GaussianNB ponderado','KNN baseline','KNN + ROS','Selector conjunto']
ORDEN=list(NOMBRES)+['selector_conjunto'];COLORES=['#0072B2','#D55E00']
NOTA='OOF externas · 46.305 eventos · 36 ATO · 34 usuarios positivos | 5 folds; evaluación interna del procedimiento'

class ExportadorFiguras:
    def __init__(self):self.destino=RESULTADOS/'graficas';self.destino.mkdir();self.catalogo=[]
    def guardar(self,fig,nombre,descripcion):
        for ext in ['png','svg']:
            p=self.destino/f'{nombre}.{ext}'
            if p.exists():raise FileExistsError(p)
            fig.savefig(p,dpi=300,bbox_inches='tight')
        plt.close(fig);self.catalogo.append(dict(nombre=nombre,descripcion=descripcion,png=(self.destino/f'{nombre}.png').as_posix(),svg=(self.destino/f'{nombre}.svg').as_posix()))

def main():
    activar_guardia();plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.titlesize':13,'figure.titlesize':15,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
    e=ExportadorFiguras();g=pd.read_csv(RESULTADOS/'metricas_globales.csv',float_precision='round_trip');f=pd.read_csv(RESULTADOS/'metricas_por_fold.csv',float_precision='round_trip');s=pd.read_csv(RESULTADOS/'selecciones.csv',float_precision='round_trip');pos=np.arange(7)
    fig,axes=plt.subplots(1,3,figsize=(18,7),layout='constrained')
    for ax,m in zip(axes,['precision','recall','f1']):
        for j,regla in enumerate(['aprendido','fijo_05']):
            v=g[g.regla.eq(regla)].set_index('modelo').loc[ORDEN,m];b=ax.barh(pos+(j-.5)*.35,v,height=.35,color=COLORES[j],label=regla);ax.bar_label(b,fmt='%.4f',padding=3,fontsize=10)
        ax.set(yticks=pos,yticklabels=ETIQUETAS,title=m,xlabel='Métrica global por evento',xlim=(0,max(g[m].max()*1.3,.01)));ax.invert_yaxis();ax.legend()
    fig.suptitle('Umbral aprendido dentro de cada entrenamiento externo frente a 0,5\n'+NOTA);e.guardar(fig,'01_metricas_globales','Precision, recall y F1. Selector a 0,5 usa las mismas variantes seleccionadas con umbral aprendido.')
    for nombre,etiqueta in zip(ORDEN,ETIQUETAS):
        fig,axes=plt.subplots(1,2,figsize=(11,5.5),layout='constrained')
        for ax,regla in zip(axes,['aprendido','fijo_05']):
            q=g[g.modelo.eq(nombre)&g.regla.eq(regla)].iloc[0];cm=np.array([[q.TN,q.FP],[q.FN,q.TP]],int);ax.imshow(cm,cmap='Blues',vmin=0,vmax=46305)
            for (i,j),v in np.ndenumerate(cm):ax.text(j,i,f'{[["TN","FP"],["FN","TP"]][i][j]}\n{v:,}',ha='center',va='center',fontsize=17,color='white' if v>23152 else 'black')
            ax.set(xticks=[0,1],yticks=[0,1],xticklabels=['No ATO','ATO'],yticklabels=['No ATO','ATO'],xlabel='Predicción',ylabel='Etiqueta real',title=regla)
        fig.suptitle(f'{etiqueta} · matrices absolutas\n46.305 eventos, 36 ATO | Ninguna variante omitida');e.guardar(fig,f'02_confusion_{nombre}','Confusiones absolutas: umbral aprendido y referencia; filas reales, columnas predichas.')
    fig,axes=plt.subplots(3,2,figsize=(14,12),layout='constrained')
    for ax,(nombre,etiqueta) in zip(axes.flat,zip(NOMBRES,ETIQUETAS)):
        q=s[s.modelo.eq(nombre)].sort_values('fold_externo');ax.plot(q.fold_externo,q.umbral,'o-',color=COLORES[0]);ax.axhline(.5,color=COLORES[1],linestyle='--',label='Referencia 0,5')
        for row in q.itertuples():ax.annotate(f'{row.umbral:.6g}',(row.fold_externo,row.umbral),xytext=(0,8),textcoords='offset points',ha='center',fontsize=10)
        ax.set(title=etiqueta,xlabel='Fold externo',ylabel='Umbral elegido internamente',xticks=range(1,6),ylim=(-.04,1.14));ax.grid(alpha=.2);ax.legend(fontsize=9)
    fig.suptitle('Estabilidad de umbrales · elegidos sin etiquetas externas\n0 representa política de alertar a todos; precisión completa en CSV');e.guardar(fig,'03_umbrales','Umbrales de las seis variantes por fold. Diferencias pequeñas en árboles no implican decisiones similares.')
    fig,axes=plt.subplots(1,2,figsize=(15,6),layout='constrained');elegidos=s[s.selector];counts=elegidos.modelo.value_counts().reindex(NOMBRES,fill_value=0);b=axes[0].barh(ETIQUETAS[:6],counts,color=COLORES[0]);axes[0].bar_label(b,padding=4);axes[0].set(xlim=(0,5.5),xlabel='Folds (de cinco)',title='Variante elegida internamente');axes[0].invert_yaxis()
    for j,regla in enumerate(['aprendido','fijo_05']):
        q=f[f.modelo.eq('selector_conjunto')&f.regla.eq(regla)].sort_values('fold_externo');axes[1].plot(q.fold_externo,q.f1,'o-',label=regla,color=COLORES[j])
    axes[1].set(xlabel='Fold externo',ylabel='F1 externo',title='Selector: desempeño por fold',xticks=range(1,6),ylim=(0,.2));axes[1].legend();fig.suptitle('Selector conjunto · no es un modelo fijo\n'+NOTA);e.guardar(fig,'04_selector','Frecuencia de selección interna y F1 externo; no selecciona retrospectivamente un ganador.')
    fig,axes=plt.subplots(2,2,figsize=(16,11),layout='constrained')
    for ax,m in zip(axes.flat,['precision','recall','f1','average_precision']):
        for j,regla in enumerate(['aprendido','fijo_05']):
            for i,n in enumerate(ORDEN):
                v=f.loc[f.modelo.eq(n)&f.regla.eq(regla),m];ax.scatter(v,np.full(len(v),i+(j-.5)*.25),color=COLORES[j],s=26,alpha=.7,label=regla if i==0 else None);ax.scatter(v.mean(),i+(j-.5)*.25,color=COLORES[j],marker='D',s=38)
        ax.set(yticks=range(7),yticklabels=ETIQUETAS,xlabel='Métrica por fold',title=m.replace('average_precision','AP por fold · no AP global selector'));ax.set_xlim(left=0);ax.invert_yaxis();ax.legend()
    fig.suptitle('Variabilidad: puntos = folds; rombos = media no ponderada\n'+NOTA+'\nLa dispersión y DE no son intervalos de confianza. AP no depende del umbral.');e.guardar(fig,'05_variabilidad','Cinco métricas por variante, regla y selector. AP del selector conserva su significado local por fold.')
    fig,axes=plt.subplots(1,3,figsize=(18,7),layout='constrained')
    for ax,m,titulo in zip(axes,['usuarios_ato_detectados','usuarios_ato_omitidos','usuarios_sin_ato_con_alerta'],['Usuarios ATO detectados','Usuarios ATO omitidos','Usuarios sin ATO con alertas']):
        for j,regla in enumerate(['aprendido','fijo_05']):
            v=g[g.regla.eq(regla)].set_index('modelo').loc[ORDEN,m];b=ax.barh(pos+(j-.5)*.35,v,height=.35,color=COLORES[j],label=regla);ax.bar_label(b,fmt='%d',padding=3)
        ax.set(yticks=pos,yticklabels=ETIQUETAS,title=titulo,xlabel='Usuarios',xlim=(0,max(g[m].max()*1.25,1)));ax.invert_yaxis();ax.legend()
    fig.suptitle('Métricas complementarias por usuario\n34 usuarios ATO · detección exige al menos un evento ATO alertado');e.guardar(fig,'06_usuarios','Usuarios positivos detectados/omitidos y usuarios completamente negativos con alertas; no confundir con eventos.')
    fig,axes=plt.subplots(1,3,figsize=(18,7),layout='constrained')
    for ax,m in zip(axes,['TP','FP','FN']):
        for j,regla in enumerate(['aprendido','fijo_05']):
            v=g[g.regla.eq(regla)].set_index('modelo').loc[ORDEN,m];b=ax.barh(pos+(j-.5)*.35,v,height=.35,color=COLORES[j],label=regla);ax.bar_label(b,fmt='%d',padding=3)
        ax.set(yticks=pos,yticklabels=ETIQUETAS,title=m,xlabel='Eventos',xlim=(0,max(g[m].max()*1.25,1)));ax.invert_yaxis();ax.legend()
    fig.suptitle('Detecciones, falsas alarmas y omisiones · escalas propias explícitas\n'+NOTA);e.guardar(fig,'07_conteos','TP/FP/FN por variante y selector, sin ocultar falsas alarmas de GaussianNB.')
    guardar_json(RESULTADOS/'catalogo_graficas.json',e.catalogo)

if __name__=='__main__':main()
