import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold


def construir_folds(y, grupos):
    folds = list(StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42).split(np.zeros(len(y)), y, grupos))
    visitas = np.zeros(len(y), dtype=int)
    filas = []
    for numero, (a, b) in enumerate(folds, 1):
        if set(grupos.iloc[a]) & set(grupos.iloc[b]):
            raise ValueError('Usuarios compartidos')
        if set(y.iloc[a]) != {0, 1} or set(y.iloc[b]) != {0, 1}:
            raise ValueError(f'Fold {numero} sin ambas clases; revisar protocolo antes de entrenar')
        visitas[b] += 1
        row = {'fold': numero, 'usuarios_compartidos': 0}
        for etiqueta, indices in [('subtrain', a), ('validacion', b)]:
            row.update({f'{etiqueta}_eventos': len(indices), f'{etiqueta}_usuarios': grupos.iloc[indices].nunique(),
                        f'{etiqueta}_positivos': int(y.iloc[indices].sum()),
                        f'{etiqueta}_usuarios_positivos': grupos.iloc[indices][y.iloc[indices].eq(1)].nunique()})
        filas.append(row)
    if not (visitas == 1).all():
        raise ValueError('Cobertura de folds invalida')
    return folds, pd.DataFrame(filas)
