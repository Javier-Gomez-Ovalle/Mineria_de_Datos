"""Figuras internas y externas claramente separadas."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram
from sklearn.metrics import adjusted_rand_score
from .estilo import plt,COLORES,guardar
from .exportacion import guardar_json

def main():
    r=Path('fase04_clustering/resultados');g=r/'graficas';c=pd.read_csv(r/'candidatos.csv');a=np.load(r/'candidatos.npz')
    fig,axes=plt.subplots(2,2,figsize=(13,10),layout='constrained')
    for ax,metrica,titulo in zip(axes.flat,['inercia','silhouette','davies_bouldin','calinski_harabasz'],['Inercia (menor al aumentar K)','Silhouette · muestra fija de 2.000','Davies–Bouldin · menor es mejor','Calinski–Harabasz · mayor es mejor']):
        for color,(nombre,tabla) in zip(COLORES,c.groupby('algoritmo',sort=False)):
            if tabla[metrica].notna().any():ax.plot(tabla.k,tabla[metrica],'o-',label=nombre,color=color)
        ax.set(title=titulo,xlabel='Número de clusters K',ylabel='Índice',xticks=range(2,9));ax.set_ylim(bottom=0);ax.grid(alpha=.2);ax.legend()
    fig.suptitle('Candidatos sin target | KMeans: 46.305; jerárquico: 4.000 eventos\nCH e inercia dependen de la población; no comparar sus magnitudes entre muestras')
    guardar(fig,g,'seleccion_interna')
    fig,ax=plt.subplots(figsize=(10,5),layout='constrained');t=c[c.algoritmo.eq('kmeans')]
    ax.plot(t.k,t.ari_min,'o-',label='ARI mínimo',color=COLORES[0]);ax.plot(t.k,t.ari_media,'s--',label='ARI medio',color=COLORES[1]);ax.set(xlabel='K',ylabel='Adjusted Rand Index entre semillas',ylim=(0,1.05),title='Estabilidad KMeans · semillas 42, 43 y 44');ax.legend();guardar(fig,g,'estabilidad_kmeans')
    corte=json.loads((r/'seleccion_congelada.json').read_text(encoding='utf-8'))['corte_ward']
    fig,ax=plt.subplots(figsize=(14,6),layout='constrained');dendrogram(a['enlace_ward'],truncate_mode='lastp',p=25,show_leaf_counts=True,ax=ax,color_threshold=corte)
    ax.axhline(corte,color='black',linestyle='--',label=f'Corte K=2: altura {corte:.2f}');ax.set(title='Ward · dendrograma truncado a 25 ramas',xlabel='Ramas terminales (paréntesis: eventos agrupados)',ylabel='Altura de enlace Ward');ax.legend();guardar(fig,g,'dendrograma_ward')
    for n in ('kmeans_2','ward_2'):
        t=pd.read_csv(r/f'evaluacion_externa_{n}.csv')
        fig,axes=plt.subplots(1,3,figsize=(15,5),layout='constrained')
        for ax,col,titulo in zip(axes,['eventos_no_ato','eventos_ato','prevalencia'],['Eventos no ATO','Eventos ATO','Prevalencia ATO (%)']):
            vals=t[col]*(100 if col=='prevalencia' else 1);b=ax.bar(t.cluster.astype(int).astype(str),vals,color=COLORES[:2]);ax.bar_label(b,fmt='%.3f' if col=='prevalencia' else '%.0f',padding=4);ax.set(xlabel='Cluster',ylabel=titulo,title=titulo);ax.set_ylim(0,max(vals.max()*1.2,.01))
        fig.suptitle(f'{n} · evaluación externa posterior a congelación\nConteos en escalas separadas; agrupaciones descriptivas, no clases de ataque');guardar(fig,g,f'externa_{n}')
        p=pd.read_csv(r/f'perfil_numerico_{n}.csv');cols=['failed_attempts_15min_mean','failed_attempts_1h_mean','time_since_previous_login_hours_median']
        fig,axes=plt.subplots(1,3,figsize=(15,5),layout='constrained')
        for ax,col,titulo in zip(axes,cols,['Fallos en 15 min · media','Fallos en 1 h · media','Intervalo previo · mediana (h)']):
            b=ax.bar(p.cluster.astype(str),p[col],color=COLORES[:2]);ax.bar_label(b,fmt='%.3f',padding=4);ax.set(title=titulo,xlabel='Cluster');ax.set_ylim(0,max(p[col].max()*1.2,.01))
        fig.suptitle(f'Perfiles originales sin estandarizar | {n}');guardar(fig,g,f'perfiles_{n}')
    km=a['kmeans_2'][a['indices_muestra']];ward=a['ward_2'];ari=adjusted_rand_score(km,ward)
    guardar_json(r/'comparacion_particiones.json',dict(ari=ari,eventos_comunes=len(km),contingencia=pd.crosstab(km,ward).to_numpy().tolist()))

if __name__=='__main__':main()
