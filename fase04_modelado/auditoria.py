import numpy as np
from fase04_preparacion.seleccion import PREDICTORES, NUMERICAS, CATEGORICAS


def auditar_preprocesador(prep, x):
    if list(x) != PREDICTORES or list(prep.feature_names_in_) != PREDICTORES:
        raise ValueError('Predictores no aprobados')
    num = prep.named_transformers_['num']
    esperado = x[NUMERICAS].median().to_numpy()
    np.testing.assert_allclose(num.named_steps['imputar'].statistics_, esperado)
    cat = prep.named_transformers_['cat'].named_steps['onehot']
    for c, categorias in zip(CATEGORICAS, cat.categories_):
        assert set(categorias) == set(x[c].fillna('Desconocido'))
    assert cat.handle_unknown == 'ignore'
    if 'escalar' in num.named_steps:
        valores = np.log1p(x[NUMERICAS].fillna(x[NUMERICAS].median()).to_numpy())
        np.testing.assert_allclose(num.named_steps['escalar'].mean_, valores.mean(axis=0))
        np.testing.assert_allclose(num.named_steps['escalar'].var_, valores.var(axis=0))
        assert num.named_steps['escalar'].n_samples_seen_ == len(x)
    return {'filas_ajuste': len(x), 'medianas': esperado.tolist(),
            'categorias': {c: a.tolist() for c, a in zip(CATEGORICAS,cat.categories_)},
            'columnas': prep.get_feature_names_out().tolist(), 'controles': 'OK'}


def verificar_oof(oof, y, claves, nombres):
    for n in nombres:
        parte = oof[oof.modelo == n].sort_values('evento_id')
        np.testing.assert_array_equal(parte.evento_id, np.arange(len(y)))
        np.testing.assert_array_equal(parte.y_true, y)
        for c in claves:
            np.testing.assert_array_equal(parte[c].to_numpy(), claves[c].to_numpy())
        assert not parte.evento_id.duplicated().any()
        np.testing.assert_array_equal(parte.y_pred, (parte.score >= .5).astype(int))
