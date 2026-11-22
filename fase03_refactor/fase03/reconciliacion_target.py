"""Reconciliación acotada contra RBA y preparación de un CSV sin alterar features.

No ejecuta Fase 3, no ajusta modelos ni escribe archivos. El llamador decide
cuándo persistir los bytes, una vez satisfechas todas las validaciones.
"""
import hashlib
import io
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .asociacion_target import CLAVE_EVENTO
from .preprocessing import COLUMNA_TARGET, normalizar_target


ATRIBUTOS_ORIGINALES = [
    "Device Type", "Country", "Region", "City", "ASN",
    "Login Successful", "Is Attack IP",
]


def leer_original_seleccionado(ruta, usuarios, chunksize=250_000, progreso=None):
    """Una pasada completa, reteniendo solo los usuarios solicitados."""
    ruta = Path(ruta)
    estado_inicial = ruta.stat()
    inicio = time.perf_counter()
    columnas = ["index"] + CLAVE_EVENTO + ATRIBUTOS_ORIGINALES + [COLUMNA_TARGET]
    tipos = {c: str for c in columnas}
    tipos.update({"User ID": "int64", "index": "int64"})
    fragmentos = []
    filas = retenidas = bloques = 0
    fecha_previa = None
    orden_temporal = True
    with ruta.open("rb") as archivo:
        lector = pd.read_csv(archivo, usecols=columnas, dtype=tipos,
                             keep_default_na=False, chunksize=chunksize)
        for bloque in lector:
            fechas = bloque["Login Timestamp"]
            orden_temporal = (orden_temporal and fechas.is_monotonic_increasing
                              and (fecha_previa is None or fecha_previa <= fechas.iloc[0]))
            fecha_previa = fechas.iloc[-1]
            mascara = bloque["User ID"].isin(usuarios)
            seleccionado = bloque.loc[mascara].copy()
            seleccionado["_fila_original"] = np.flatnonzero(mascara.to_numpy()) + filas
            fragmentos.append(seleccionado)
            filas += len(bloque)
            retenidas += len(seleccionado)
            bloques += 1
            if progreso is not None and (bloques == 1 or bloques % 5 == 0):
                progreso({"bloques": bloques, "filas_examinadas": filas,
                          "retenidas": retenidas, "bytes_leidos": archivo.tell(),
                          "segundos": round(time.perf_counter() - inicio, 2)})
    estado_final = ruta.stat()
    if (estado_inicial.st_size, estado_inicial.st_mtime_ns) != (estado_final.st_size, estado_final.st_mtime_ns):
        raise ValueError("El RBA cambió durante la consulta; se detiene la reconciliación.")
    datos = pd.concat(fragmentos, ignore_index=True) if fragmentos else pd.DataFrame(columns=columnas + ["_fila_original"])
    return datos, {"filas_examinadas": filas, "bloques": bloques,
                   "bytes_rba": estado_inicial.st_size, "filas_retenidas": retenidas,
                   "orden_temporal_original": bool(orden_temporal),
                   "segundos_lectura": round(time.perf_counter() - inicio, 2),
                   "rba_tamano_y_mtime_preservados": True}


def reconciliar_eventos(enriquecido, original):
    """Devuelve etiquetas originales en el orden enriquecido y evidencia individual."""
    columnas = CLAVE_EVENTO + ATRIBUTOS_ORIGINALES + [COLUMNA_TARGET]
    for nombre, datos in [("enriquecido", enriquecido), ("original", original)]:
        faltantes = set(columnas) - set(datos.columns)
        if faltantes or not datos.columns.is_unique:
            raise ValueError(f"Esquema inválido en {nombre}: {faltantes}")
        if datos[CLAVE_EVENTO].isna().any().any():
            raise ValueError(f"Clave nula en {nombre}")
        if any(datos[c].astype(str).str.strip().eq("").any() for c in CLAVE_EVENTO):
            raise ValueError(f"Clave vacía en {nombre}")
        if datos.duplicated(CLAVE_EVENTO).any():
            raise ValueError(f"Clave duplicada en {nombre}: correspondencia ambigua")
        normalizar_target(datos[COLUMNA_TARGET])
    izquierda = enriquecido[columnas].reset_index(drop=True).copy()
    izquierda["_fila_enriquecida"] = np.arange(len(izquierda))
    derecha = original[columnas + ["_fila_original"]]
    cruce = izquierda.merge(derecha, on=CLAVE_EVENTO, how="outer", validate="one_to_one",
                            suffixes=("_enriquecido", "_original"), indicator=True)
    ausentes = int(cruce["_merge"].eq("left_only").sum())
    adicionales = int(cruce["_merge"].eq("right_only").sum())
    if ausentes or adicionales:
        raise ValueError(f"Correspondencia incompleta: ausentes={ausentes}, adicionales={adicionales}")
    cruce = cruce.sort_values("_fila_enriquecida").reset_index(drop=True)
    diferencias = {c: int(cruce[c + "_enriquecido"].ne(cruce[c + "_original"]).sum())
                   for c in ATRIBUTOS_ORIGINALES}
    if any(diferencias.values()):
        raise ValueError(f"Discrepancias en atributos originales: {diferencias}")
    verdadero = normalizar_target(cruce[COLUMNA_TARGET + "_original"]).astype(bool)
    anterior = normalizar_target(cruce[COLUMNA_TARGET + "_enriquecido"]).astype(bool)
    orden = cruce.sort_values("_fila_original")["_fila_enriquecida"].to_numpy(dtype=int)
    inversion = np.empty(len(cruce), dtype=bool)
    inversion[orden] = anterior.to_numpy()
    matriz = {"original_0_anterior_0": int((~verdadero & ~anterior).sum()),
              "original_0_anterior_1": int((~verdadero & anterior).sum()),
              "original_1_anterior_0": int((verdadero & ~anterior).sum()),
              "original_1_anterior_1": int((verdadero & anterior).sum())}
    evidencia = {"eventos": len(cruce), "correspondencias_unicas": len(cruce),
                 "ausentes": ausentes, "adicionales": adicionales, "ambiguos": 0,
                 "diferencias_atributos": diferencias, "matriz_antes": matriz,
                 "discrepancias_antes": int(verdadero.ne(anterior).sum()),
                 "positivos": int(verdadero.sum()), "negativos": int((~verdadero).sum()),
                 "usuarios_ato": int(cruce.loc[verdadero, "User ID"].nunique()),
                 "errores_inversion": int(np.count_nonzero(inversion != verdadero.to_numpy()))}
    return verdadero.rename(COLUMNA_TARGET), evidencia


def preparar_csv_corregido(contenido, etiquetas):
    """Cambia solo el último campo booleano; conserva los demás bytes del CSV.

Este escritor deliberadamente rechaza CSV con registros multilínea o target
en otra posición. No aplica un ciclo genérico read_csv/to_csv que redondee
floats, reformatee fechas, altere nulos o cambie los saltos de línea.
"""
    anterior = pd.read_csv(io.BytesIO(contenido))
    etiquetas = normalizar_target(pd.Series(etiquetas).reset_index(drop=True)).astype(bool)
    if len(anterior) != len(etiquetas) or anterior.columns[-1] != COLUMNA_TARGET:
        raise ValueError("Dimensiones o posición del target incompatibles.")
    lineas = contenido.splitlines(keepends=True)
    if len(lineas) != len(anterior) + 1:
        raise ValueError("CSV multilínea: no se modifica sin un escritor específico.")
    salida = [lineas[0]]
    cambios = 0
    for linea, etiqueta in zip(lineas[1:], etiquetas):
        cuerpo = linea.rstrip(b"\r\n")
        fin = linea[len(cuerpo):]
        prefijo, token = cuerpo.rsplit(b",", 1)
        if token not in (b"True", b"False"):
            raise ValueError("Representación del target inesperada; no se modifica.")
        nuevo_token = b"True" if etiqueta else b"False"
        cambios += token != nuevo_token
        salida.append(prefijo + b"," + nuevo_token + fin)
    resultado = b"".join(salida)
    corregido = pd.read_csv(io.BytesIO(resultado))
    pd.testing.assert_frame_equal(anterior.drop(columns=COLUMNA_TARGET),
                                  corregido.drop(columns=COLUMNA_TARGET), check_exact=True)
    if not corregido.dtypes.equals(anterior.dtypes):
        raise ValueError("Cambió algún dtype inferido del CSV.")
    if not corregido[COLUMNA_TARGET].reset_index(drop=True).equals(etiquetas):
        raise ValueError("Las etiquetas serializadas no coinciden con el RBA original.")
    for vieja, nueva in zip(lineas, resultado.splitlines(keepends=True)):
        if vieja.rsplit(b",", 1)[0] != nueva.rsplit(b",", 1)[0]:
            raise ValueError("Se modificaron bytes ajenos al target.")
    hashes_columnas = {
        col: hashlib.sha256(pd.util.hash_pandas_object(corregido[col], index=True).to_numpy().tobytes()).hexdigest()
        for col in corregido.columns if col != COLUMNA_TARGET
    }
    return resultado, {"filas": len(corregido), "columnas": len(corregido.columns),
                       "etiquetas_modificadas": int(cambios), "diferencias_features": 0,
                       "discrepancias_despues": 0, "dtypes_preservados": True,
                       "bytes_no_target_preservados": True,
                       "nulos_preservados": bool(anterior.isna().equals(corregido.isna())),
                       "sha256_anterior": hashlib.sha256(contenido).hexdigest(),
                       "sha256_corregido": hashlib.sha256(resultado).hexdigest(),
                       "tamano_corregido": len(resultado), "hashes_columnas_no_target": hashes_columnas}
