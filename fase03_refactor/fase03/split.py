"""
split.py
========
Split TRAIN/TEST por User ID (Etapa 2). Función de módulo, sin estado.

POR QUÉ POR USUARIO Y NO POR FILA
Un usuario tiene muchos eventos con comportamiento correlacionado. Un split
por fila pondría eventos del mismo usuario en TRAIN y en TEST (leakage).
Aquí cada usuario cae COMPLETO en un solo conjunto.

ESTRATIFICACIÓN
Se estratifica por el flag "usuario con al menos un ATO", para que ambos
conjuntos reciban positivos. Si el diseño no garantiza positivos en ambos
conjuntos, el proceso SE DETIENE con error. NO se duplican positivos en TEST.
"""
from sklearn.model_selection import train_test_split

from .preprocessing import COLUMNA_ID_USUARIO, COLUMNA_TARGET, normalizar_target


def _resumir_conjunto(df_parte):
    y = normalizar_target(df_parte[COLUMNA_TARGET])
    ato_por_usuario = y.groupby(df_parte[COLUMNA_ID_USUARIO]).max()
    n_eventos = len(df_parte)
    n_ato_eventos = int(y.sum())
    return {
        "usuarios": int(df_parte[COLUMNA_ID_USUARIO].nunique()),
        "eventos": int(n_eventos),
        "ato_usuarios": int(ato_por_usuario.sum()),
        "ato_eventos": n_ato_eventos,
        "prevalencia_pct": 100.0 * n_ato_eventos / n_eventos if n_eventos else 0.0,
    }


def dividir_train_test_por_usuario(df, config):
    """Devuelve (df_train, df_test, info). Lanza error si hay solapamiento de
    usuarios, si hay menos de 2 usuarios ATO, o si TRAIN/TEST quedan sin
    ningún evento ATO."""
    print("=" * 60)
    print("[ETAPA 2] Split TRAIN/TEST por User ID")
    print("=" * 60)

    for col in (COLUMNA_ID_USUARIO, COLUMNA_TARGET):
        if col not in df.columns:
            raise KeyError(f"Falta la columna obligatoria '{col}' para el split.")

    y_evento = normalizar_target(df[COLUMNA_TARGET])
    ato_por_usuario = y_evento.groupby(df[COLUMNA_ID_USUARIO]).max()
    usuarios = ato_por_usuario.index.to_numpy()
    etiquetas = ato_por_usuario.to_numpy()

    n_ato = int(etiquetas.sum())
    n_no_ato = int(len(etiquetas) - n_ato)
    if n_ato < 2 or n_no_ato < 2:
        raise ValueError(
            f"Split imposible con garantías: usuarios ATO={n_ato}, usuarios "
            f"no-ATO={n_no_ato}. Se necesitan >=2 de cada tipo para tener "
            "positivos en TRAIN y TEST. NO se duplican positivos en TEST; "
            "revisa la estrategia de muestreo."
        )

    usuarios_train, usuarios_test = train_test_split(
        usuarios,
        test_size=config.TEST_SIZE,
        random_state=config.RANDOM_STATE,
        stratify=etiquetas,
    )
    set_train = set(usuarios_train.tolist())
    set_test = set(usuarios_test.tolist())
    solapamiento = set_train & set_test
    if solapamiento:
        raise RuntimeError(
            f"LEAKAGE: {len(solapamiento)} usuarios aparecen en TRAIN y TEST."
        )

    mascara_train = df[COLUMNA_ID_USUARIO].isin(set_train)
    df_train = df.loc[mascara_train].reset_index(drop=True)
    df_test = df.loc[~mascara_train].reset_index(drop=True)

    info = {
        "train": _resumir_conjunto(df_train),
        "test": _resumir_conjunto(df_test),
        "solapamiento_usuarios": len(solapamiento),
    }
    for nombre in ("train", "test"):
        if info[nombre]["ato_eventos"] < 1:
            raise ValueError(
                f"El conjunto {nombre.upper()} quedó sin ningún evento ATO. "
                "Se detiene: NO se corrige duplicando positivos."
            )

    for nombre in ("train", "test"):
        r = info[nombre]
        print(f"  {nombre.upper():5s} usuarios={r['usuarios']:,} eventos={r['eventos']:,} "
              f"ATO usuarios={r['ato_usuarios']:,} ATO eventos={r['ato_eventos']:,} "
              f"prevalencia={r['prevalencia_pct']:.4f}%")
    print("  Solapamiento de usuarios TRAIN/TEST: 0")
    print("  [OK] Split por User ID completado.\n")
    return df_train, df_test, info