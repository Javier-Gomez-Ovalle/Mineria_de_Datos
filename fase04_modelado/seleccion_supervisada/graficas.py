"""Presentación uniforme derivada únicamente de resultados existentes."""
import os
from .auditoria import RAIZ,FUENTES,NOMBRES,activar_guardia,guardar_json
os.environ['MPLCONFIGDIR']=str((RAIZ/'cache_graficas').resolve())
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve

COLORES=['#0072B2','#D55E00','#009E73','#CC79A7','#B8860B','#56B4E9']
METRICAS=['precision','recall','f1','average_precision']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.titlesize':13,'figure.titlesize':16,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
NOTA='OOF train: 46.305 eventos · 36 ATO · 34 usuarios positivos | Exploratorio, sin estimación independiente'

class ExportadorFiguras:
    def __init__(self):self.carpeta=RAIZ/'graficas';self.carpeta.mkdir();self.catalogo=[]

    def guardar(self,fig,nombre,descripcion):
        for extension in ('png','svg'):
            ruta=self.carpeta/f'{nombre}.{extension}'
            if ruta.exists():raise FileExistsError(ruta)
            fig.savefig(ruta,dpi=300,bbox_inches='tight')
        plt.close(fig);self.catalogo.append(dict(nombre=nombre,descripcion=descripcion,png=(self.carpeta/f'{nombre}.png').as_posix(),svg=(self.carpeta/f'{nombre}.svg').as_posix()))

def main():
    activar_guardia();e=ExportadorFiguras();r=RAIZ/'resultados';t=pd.read_csv(r/'umbrales_globales.csv',float_precision='round_trip');f=pd.read_csv(r/'umbrales_por_fold.csv',float_precision='round_trip');h=pd.read_csv(r/'historicos_globales.csv',float_precision='round_trip')
    fig,axes=plt.subplots(2,2,figsize=(16,11),layout='constrained');pos=np.arange(6)
    for ax,m in zip(axes.flat,METRICAS):
        for j,protocolo in enumerate(FUENTES):
            v=h[h.protocolo.eq(protocolo)].set_index('modelo').loc[list(NOMBRES),m]
            b=ax.barh(pos+(j-.5)*.35,v,height=.35,label=protocolo,color=COLORES[j]);ax.bar_label(b,fmt='%.4f',padding=3,fontsize=10)
        ax.set(yticks=pos,yticklabels=list(NOMBRES.values()),xlabel='Métrica OOF global',title=m.replace('average_precision','Average Precision'),xlim=(0,max(h[m].max()*1.35,.01)));ax.invert_yaxis();ax.legend()
    fig.suptitle('Comparación CV1/CV2 · umbral histórico 0,5\n'+NOTA);e.guardar(fig,'01_comparacion_protocolos','Métricas de todas las variantes a 0,5. Cambia la partición, no el algoritmo.')
    for protocolo,carpeta in FUENTES.items():
        o=pd.read_csv(carpeta/'predicciones_oof.csv')
        fig,axes=plt.subplots(1,2,figsize=(16,7),layout='constrained')
        for (nombre,titulo),color,estilo in zip(NOMBRES.items(),COLORES,['-','--','-',':','-.','--']):
            q=o[o.modelo.eq(nombre)];p,re,_=precision_recall_curve(q.y_true,q.score);ap=h[h.modelo.eq(nombre)&h.protocolo.eq(protocolo)].average_precision.iloc[0]
            for ax in axes:ax.step(re,p,where='post',color=color,linestyle=estilo,label=f'{titulo}: AP={ap:.6f}')
        for ax in axes:
            ax.axhline(36/46305,color='black',linestyle=':',label='Prevalencia 36/46.305 = 0,07775%');ax.set(xlim=(0,1),ylim=(0,1.02),xlabel='Recall',ylabel='Precision');ax.grid(alpha=.2)
        axes[1].set_yscale('log');axes[1].set_ylim(1e-5,1.02);axes[0].set_title('Escala lineal completa');axes[1].set_title('Detalle: precision en escala logarítmica');axes[1].legend(fontsize=9,loc='upper right')
        fig.suptitle(f'{protocolo} · Precision–Recall | GaussianNB baseline y ponderado coinciden\n'+NOTA);e.guardar(fig,f'02_pr_{protocolo}','AP y prevalencia. AP global concatena escalas de cinco estimadores no necesariamente calibradas; detalle log explícito.')
    for numero,(nombre,titulo) in enumerate(NOMBRES.items(),1):
        fig,axes=plt.subplots(2,2,figsize=(15,11),layout='constrained')
        for j,protocolo in enumerate(FUENTES):
            q=t[t.modelo.eq(nombre)&t.protocolo.eq(protocolo)&t.umbral.le(1)].sort_values('umbral');color=COLORES[j]
            for ax,cols in [(axes[0,0],['precision','recall']),(axes[0,1],['TP','FN']),(axes[1,0],['FP']),(axes[1,1],['porcentaje_alertas'])]:
                for z,col in enumerate(cols):ax.step(q.umbral,q[col],where='pre',color=color,linestyle='-' if z==0 else '--',label=f'{protocolo}: {col}');ax.scatter(q.umbral,q[col],s=15,color=color)
                ax.set(xlabel='Umbral t · alerta si score ≥ t',xlim=(0,1));ax.set_ylim(bottom=0);ax.grid(alpha=.2);ax.legend(fontsize=10)
            ref=q[q.umbral.eq(.4)].iloc[0];axes[0,1].text(.98,.92-j*.09,f'{protocolo} t=0,4: TP={int(ref.TP)}, FN={int(ref.FN)}',transform=axes[0,1].transAxes,ha='right',fontsize=10,color=color)
        for ax,tit,ylabel in zip(axes.flat,['Precision y recall','Detecciones y omisiones','Falsas alarmas','Carga de alertas'],['Proporción','Eventos','Eventos FP','Porcentaje de eventos (%)']):ax.set(title=tit,ylabel=ylabel)
        fig.suptitle(f'{titulo} · sensibilidad al umbral\n{NOTA}\nPuntos: umbrales evaluados; escalones, no interpolación. t>1: cero alertas.');e.guardar(fig,f'03_umbrales_{nombre}','Precision/recall, TP/FN, FP y porcentaje de alertas por umbral y protocolo. Estados exactos y sus métricas en CSV.')
        for protocolo in FUENTES:
            fig,axes=plt.subplots(1,3,figsize=(15,5.5),layout='constrained')
            for ax,umbral in zip(axes,[.2,.4,.5]):
                q=t[t.modelo.eq(nombre)&t.protocolo.eq(protocolo)&t.umbral.eq(umbral)].iloc[0];cm=np.array([[q.TN,q.FP],[q.FN,q.TP]],int);ax.imshow(cm,cmap='Blues',vmin=0,vmax=46305)
                for (i,j),v in np.ndenumerate(cm):ax.text(j,i,f'{[["TN","FP"],["FN","TP"]][i][j]}\n{v:,}',ha='center',va='center',fontsize=15,color='white' if v>23152 else 'black')
                ax.set(xticks=[0,1],yticks=[0,1],xticklabels=['No ATO','ATO'],yticklabels=['No ATO','ATO'],xlabel='Predicción',ylabel='Real',title=f'Umbral {umbral:g}')
            fig.suptitle(f'{protocolo} · {titulo} · confusiones absolutas\n'+NOTA);e.guardar(fig,f'04_confusiones_{protocolo}_{nombre}','Matrices a 0,2 / 0,4 / 0,5. No omite variantes desfavorables; resto de umbrales en tabla completa.')
    fig,axes=plt.subplots(2,2,figsize=(16,11),layout='constrained')
    for ax,m in zip(axes.flat,METRICAS):
        for j,protocolo in enumerate(FUENTES):
            q=f[f.protocolo.eq(protocolo)&f.umbral.eq(.5)];media=q.groupby('modelo')[m].mean().reindex(NOMBRES);de=q.groupby('modelo')[m].std().reindex(NOMBRES)
            # DE se informa numéricamente; puntos individuales evitan interpretar barras como IC.
            for i,n in enumerate(NOMBRES):
                vals=q.loc[q.modelo.eq(n),m];ax.scatter(vals,np.full(len(vals),i+(j-.5)*.25),s=27,color=COLORES[j],alpha=.6,label=protocolo if i==0 else None)
                ax.scatter(media[n],i+(j-.5)*.25,marker='D',s=38,color=COLORES[j])
        ax.set(yticks=range(6),yticklabels=list(NOMBRES.values()),xlabel='Métrica de fold',title=m.replace('average_precision','Average Precision'));ax.set_xlim(left=0);ax.invert_yaxis();ax.legend()
    fig.suptitle('Variabilidad a 0,5 · puntos: folds; rombos: medias\n'+NOTA+'\nCinco folds dependientes; dispersión y DE no son intervalos de confianza.');e.guardar(fig,'05_variabilidad_folds','Cinco valores por variante y protocolo. Medias y DE a todos los umbrales disponibles en resumen_folds.csv.')
    fig,axes=plt.subplots(1,2,figsize=(16,7),layout='constrained')
    for ax,protocolo in zip(axes,FUENTES):
        for (nombre,titulo),color in zip(NOMBRES.items(),COLORES):
            q=t[t.modelo.eq(nombre)&t.protocolo.eq(protocolo)].drop_duplicates(['TP','FP']);ax.scatter(q.FP,q.TP,label=titulo,color=color,s=35,alpha=.8)
        ax.set(xlabel='Falsas alarmas FP (escala symlog; incluye cero)',ylabel='ATO detectados TP',title=protocolo,ylim=(0,38));ax.set_xscale('symlog',linthresh=10);ax.set_xlim(left=0);ax.grid(alpha=.2)
    axes[1].legend(fontsize=9);fig.suptitle('Detecciones frente a falsas alarmas · todos los estados observados\n'+NOTA);e.guardar(fig,'06_compromisos_tp_fp','Puntos exploratorios sin coste FP/FN supuesto. Frontera Pareto identificada en CSV, no implica ganador.')
    filas=[]
    for nombre,titulo in NOMBRES.items():
        for protocolo in FUENTES:
            q=t[t.modelo.eq(nombre)&t.protocolo.eq(protocolo)&t.umbral.eq(.4)].iloc[0];filas.append([titulo,protocolo,int(q.TP),int(q.FP),int(q.FN),f'{q.precision:.4f}',f'{q.recall:.4f}',f'{q.porcentaje_alertas:.3f}%'])
    fig,ax=plt.subplots(figsize=(16,8),layout='constrained');ax.axis('off');tab=ax.table(cellText=filas,colLabels=['Variante','CV','TP','FP','FN','Precision','Recall','Alertas %'],loc='center',colWidths=[.30,.07,.07,.10,.07,.12,.12,.12]);tab.auto_set_font_size(False);tab.set_fontsize(11);tab.scale(1,1.9)
    fig.suptitle('Tabla de compromisos · referencia común t=0,4 (no selección validada)\n'+NOTA);e.guardar(fig,'07_tabla_compromisos','Comparación legible de conteos y tasas a referencia 0,4; no ordena variantes por una sola métrica.')
    guardar_json(RAIZ/'catalogo_graficas.json',e.catalogo)

if __name__=='__main__':main()
