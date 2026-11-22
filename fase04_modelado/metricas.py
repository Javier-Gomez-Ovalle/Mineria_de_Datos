import numpy as np
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score, average_precision_score

METRICAS = ['precision', 'recall', 'f1', 'average_precision']


def calcular_metricas(y, score):
    score = np.asarray(score)
    if not np.isfinite(score).all() or ((score < 0) | (score > 1)).any():
        raise ValueError('Probabilidades invalidas')
    pred = (score >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {'TP': int(tp), 'FP': int(fp), 'TN': int(tn), 'FN': int(fn),
            'precision': precision_score(y, pred, zero_division=0),
            'recall': recall_score(y, pred, zero_division=0),
            'f1': f1_score(y, pred, zero_division=0),
            'average_precision': average_precision_score(y, score),
            'sin_predicciones_positivas': bool(pred.sum() == 0)}
