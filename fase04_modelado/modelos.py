from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier

NOMBRES = {
    'arbol_baseline': 'Arbol baseline', 'arbol_ponderado': 'Arbol ponderado',
    'gnb_baseline': 'GaussianNB baseline', 'gnb_ponderado': 'GaussianNB ponderado',
    'knn_baseline': 'KNN baseline', 'knn_ros': 'KNN + RandomOverSampler',
}


def crear_modelo(nombre):
    if nombre.startswith('arbol'):
        return 'arbol', DecisionTreeClassifier(random_state=42, class_weight='balanced' if nombre.endswith('ponderado') else None)
    if nombre.startswith('gnb'):
        return 'gaussian_nb', GaussianNB(var_smoothing=1e-9)
    if nombre in ['knn_baseline', 'knn_ros']:
        return 'distancias', KNeighborsClassifier(n_neighbors=5, weights='uniform', algorithm='brute', metric='euclidean', n_jobs=2)
    raise ValueError(nombre)
