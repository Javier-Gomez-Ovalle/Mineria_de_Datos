"""Estimadores exploratorios independientes de la evaluación externa."""
from time import perf_counter
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from scipy.cluster.hierarchy import linkage, cut_tree
from .evaluacion_interna import evaluar

class ExperimentoKMeans:
    def __init__(self, matriz):
        self.matriz = matriz
        self.etiquetas = {}

    def ejecutar(self):
        filas=[]
        for k in range(2,9):
            inicio=perf_counter(); modelos=[]
            for semilla in (42,43,44):
                modelos.append(KMeans(n_clusters=k,init='k-means++',n_init=10,max_iter=300,random_state=semilla,algorithm='lloyd').fit(self.matriz))
            m=modelos[0];self.etiquetas[k]=m.labels_
            estabilidad=[adjusted_rand_score(modelos[a].labels_,modelos[b].labels_) for a,b in ((0,1),(0,2),(1,2))]
            filas.append(dict(algoritmo='kmeans',k=k,inercia=m.inertia_,iteraciones=m.n_iter_,segundos=perf_counter()-inicio,ari_min=min(estabilidad),ari_media=np.mean(estabilidad),**evaluar(self.matriz,m.labels_)))
            print('KMeans',k,flush=True)
        return filas

class ExperimentoJerarquico:
    def __init__(self, matriz, muestra=4000):
        self.indices=np.sort(np.random.default_rng(42).choice(len(matriz),muestra,replace=False))
        self.matriz=matriz[self.indices]
        self.enlaces={};self.etiquetas={}

    def ejecutar(self):
        filas=[]
        for metodo in ('ward','average'):
            inicio=perf_counter(); z=linkage(self.matriz,method=metodo,metric='euclidean');duracion=perf_counter()-inicio
            self.enlaces[metodo]=z
            for k in range(2,9):
                etiquetas=cut_tree(z,n_clusters=k).ravel();self.etiquetas[metodo,k]=etiquetas
                filas.append(dict(algoritmo=metodo,k=k,segundos=duracion,**evaluar(self.matriz,etiquetas)))
            print('Jerarquico',metodo,flush=True)
        return filas
