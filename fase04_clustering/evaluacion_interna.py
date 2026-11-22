"""Métricas internas sin acceso a etiquetas ATO."""
import numpy as np
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

def evaluar(matriz, etiquetas):
    indices = np.random.default_rng(42).choice(len(matriz), min(2000,len(matriz)), replace=False)
    tamanos = np.unique(etiquetas, return_counts=True)[1]
    return dict(silhouette=silhouette_score(matriz[indices], etiquetas[indices]),
                davies_bouldin=davies_bouldin_score(matriz,etiquetas),
                calinski_harabasz=calinski_harabasz_score(matriz,etiquetas),
                minimo=int(tamanos.min()), maximo=int(tamanos.max()), tamanos=tamanos.tolist())
