"""
timestamp_utils.py
===================
Conversión defensiva de 'Login Timestamp' (entero Unix de 64 bits con
unidad no especificada por la documentación oficial del RBA Dataset).
Funciones puras, sin estado compartido -> permanecen como funciones de
módulo, no como clase.
"""
import pandas as pd


def inferir_unidad_timestamp(serie_numerica):
    """
    Infiere la unidad de un timestamp Unix de 64 bits a partir del
    orden de magnitud de los valores (NO se asume 's' a ciegas, porque
    la documentación oficial del RBA Dataset confirma que la columna es
    un entero de 64 bits pero no especifica la unidad).

    Heurística estándar por número de dígitos de la parte entera:
        ~10 dígitos -> segundos       (hasta el año ~2286)
        ~13 dígitos -> milisegundos
        ~16 dígitos -> microsegundos
        ~19 dígitos -> nanosegundos

    Devuelve (unidad, mediana_de_magnitud) para que quede trazable en
    los logs qué se detectó y por qué.
    """
    valores_validos = pd.to_numeric(serie_numerica, errors="coerce").dropna()
    if valores_validos.empty:
        return "s", None

    mediana = valores_validos.abs().median()
    orden_magnitud = len(str(int(mediana))) if mediana > 0 else 1

    if orden_magnitud <= 10:
        unidad = "s"
    elif orden_magnitud <= 13:
        unidad = "ms"
    elif orden_magnitud <= 16:
        unidad = "us"
    else:
        unidad = "ns"

    return unidad, mediana


def convertir_login_timestamp(serie_original, ventana_fechas_conocida=None):
    """
    Convierte 'Login Timestamp' a datetime64[ns] de forma DEFENSIVA:

    1) Caso esperado (documentación oficial): la columna es un ENTERO
       de 64 bits. Se infiere la unidad real (segundos/ms/us/ns) por
       orden de magnitud — nunca se asume 'unit=s' sin verificar.
    2) Salvaguarda: si la mayoría de los valores NO son numéricos
       (columna en texto, p. ej. por un mirror de Kaggle distinto), se
       cambia de estrategia y se parsea como texto de fecha/hora en vez
       de fallar o corromper silenciosamente todos los deltas de tiempo.

    Adicionalmente se ejecuta una verificación de cordura (no
    bloqueante) contra la ventana de recolección conocida del dataset
    original, para detectar si la unidad inferida produjo fechas
    absurdas.
    """
    numerico = pd.to_numeric(serie_original, errors="coerce")

    no_nulos_original = serie_original.notna()
    total_no_nulos = int(no_nulos_original.sum())
    if total_no_nulos == 0:
        proporcion_numerica = 0.0
    else:
        convertidos_ok = (numerico.notna() & no_nulos_original).sum()
        proporcion_numerica = convertidos_ok / total_no_nulos

    if proporcion_numerica >= 0.95:
        unidad, mediana = inferir_unidad_timestamp(serie_original)
        print(f"  'Login Timestamp' detectado como ENTERO (Unix epoch de 64 bits). "
              f"Unidad inferida: '{unidad}' (mediana de magnitud: {mediana}).")
        convertido = pd.to_datetime(numerico, unit=unidad, errors="coerce")
    else:
        print("  [ATENCIÓN] 'Login Timestamp' NO parece numérico en este archivo "
              "(contradice la especificación oficial del RBA Dataset, que lo "
              "define como entero de 64 bits). Se intentará parsear como texto "
              "de fecha/hora en su lugar.")
        convertido = pd.to_datetime(serie_original, errors="coerce")

    fecha_min = convertido.min()
    fecha_max = convertido.max()
    print(f"  Rango de fechas resultante: {fecha_min} -> {fecha_max}")

    if ventana_fechas_conocida and pd.notna(fecha_min) and pd.notna(fecha_max):
        limite_inf = pd.Timestamp(ventana_fechas_conocida[0])
        limite_sup = pd.Timestamp(ventana_fechas_conocida[1])
        fuera_de_ventana = (fecha_min < limite_inf) or (fecha_max > limite_sup)
        if fuera_de_ventana:
            print(
                "  [ATENCIÓN] El rango de fechas resultante cae FUERA de la "
                f"ventana de recolección conocida del RBA Dataset "
                f"({ventana_fechas_conocida[0]} a {ventana_fechas_conocida[1]}). "
                "Esto puede indicar que la unidad inferida es incorrecta. "
                "Verifica manualmente una muestra de valores crudos de "
                "'Login Timestamp' antes de confiar en los resultados."
            )
        else:
            print("  [OK] El rango de fechas resultante es consistente con la "
                  "ventana de recolección conocida del dataset.")

    n_no_convertibles = int(convertido.isna().sum() - serie_original.isna().sum())
    if n_no_convertibles > 0:
        print(f"  [ATENCIÓN] {n_no_convertibles:,} valores de 'Login Timestamp' "
              "no se pudieron convertir y quedaron como NaT.")

    return convertido
