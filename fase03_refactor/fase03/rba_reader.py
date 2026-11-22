"""
rba_reader.py
=============
Lectura del RBA Dataset (~33M+ filas / ~9 GB) mediante procesamiento
por chunks, en dos pasadas independientes (README, secciones 7-9,
45-46).

  1) primera_pasada(): recorre el archivo COMPLETO una sola vez para
     contar eventos por usuario (Counter) y diagnosticar IPv4/IPv6 a
     nivel global. Nunca carga el archivo completo en memoria.
  2) segunda_pasada(usuarios_seleccionados): recorre el archivo de
     nuevo, filtrando por isin() para retener únicamente el historial
     completo de los usuarios ya seleccionados.

POR QUÉ ES UNA CLASE (justificación real, no nominal)
------------------------------------------------------
Ambos métodos comparten la misma configuración (ruta del RBA, tamaños
de chunk, columnas obligatorias) a través de DOS invocaciones
secuenciales sobre el mismo objeto durante una sola corrida del
pipeline. Es genuinamente distinto de envolver una función de un solo
método en una clase (lo cual SÍ evitamos en features.py/validacion.py
tras la revisión crítica) — aquí hay estado compartido real entre
llamadas.

REGLA DE MEMORIA (obligatoria tras la revisión crítica)
--------------------------------------------------------
Esta clase NUNCA almacena el Counter ni los DataFrames grandes como
atributos de self. Solo self.config (liviano) vive en la instancia.
El Counter (puede tener millones de claves) y los DataFrames (pueden
pesar varios GB) se devuelven como valores de retorno; liberarlos con
del + gc.collect() sigue siendo responsabilidad del orquestador
(PipelineFase03), exactamente en los mismos puntos donde ya se
liberaban en fase03_pipeline_v4.py.
"""
import time
from collections import Counter

import pandas as pd

from .ip_utils import clasificar_ip, diagnosticar_ipv4_ipv6

def _mascara_evento_ato(serie):
    """Máscara booleana de eventos con Is Account Takeover == True.
    Acepta bool nativo o texto 'True'/'False'. Devuelve (mascara, n_no_reconocidos);
    un valor no reconocido cuenta como NO-ATO y se reporta, nunca se asume True."""
    if serie.dtype == bool:
        return serie, 0
    texto = serie.astype(str).str.strip().str.lower()
    n_no_reconocidos = int((~texto.isin(["true", "false"])).sum())
    return texto.eq("true"), n_no_reconocidos

class AnalizadorRBA:
    def __init__(self, config):
        self.config = config

    def _validar_columnas(self):
        """Valida el encabezado REAL del CSV (nrows=0) antes de leer
        nada. Método privado: no forma parte del contrato público de
        la clase, solo lo usa primera_pasada() como paso previo."""
        config = self.config
        print("  Validando encabezado real del archivo RBA...")
        encabezado_real = set(pd.read_csv(config.RBA_PATH, nrows=0).columns)
        faltantes = [c for c in config.COLUMNAS_RBA_OBLIGATORIAS if c not in encabezado_real]

        if faltantes:
            raise ValueError(
                "ERROR DE VALIDACIÓN DE ENCABEZADO — el archivo RBA no contiene "
                f"las columnas obligatorias: {faltantes}.\n"
                f"Columnas encontradas en el archivo: {sorted(encabezado_real)}\n"
                "El pipeline NO renombra columnas de forma silenciosa."
            )

        print(f"  Encabezado validado: las {len(config.COLUMNAS_RBA_OBLIGATORIAS)} "
              "columnas obligatorias están presentes.\n")
        return True

    def primera_pasada(self):
        """Primera pasada COMPLETA sobre el RBA por chunks. Devuelve
        (contador_usuarios, contador_eventos_ato, diagnostico_global):
          - contador_usuarios: eventos totales por usuario (todos los usuarios).
          - contador_eventos_ato: eventos Is Account Takeover=True por usuario
            (solo usuarios con >=1 ATO; del orden de cientos de claves).
        La columna del target se lee en ESTA MISMA pasada: cero pasadas extra.
        Solo se usa para MUESTREAR (qué usuarios entran), nunca para features."""
        config = self.config
        print("=" * 60)
        print("[2/8] Analizando dataset RBA (primera pasada, por chunks)...")
        print("=" * 60)

        self._validar_columnas()

        contador_usuarios = Counter()
        contador_eventos_ato = Counter()
        n_ato_no_reconocidos = 0
        acumulador_global = {"total": 0, "ipv4": 0, "ipv6": 0, "invalidas": 0}

        t0 = time.time()
        n_chunks = 0

        reader = pd.read_csv(
            config.RBA_PATH,
            usecols=["User ID", "IP Address", "Is Account Takeover"],
            chunksize=config.CHUNKSIZE_PASADA_1,
            dtype={"User ID": "int64"},
        )

        for chunk in reader:
            n_chunks += 1
            contador_usuarios.update(chunk["User ID"].values)

            mascara_ato, n_no_rec = _mascara_evento_ato(chunk["Is Account Takeover"])
            n_ato_no_reconocidos += n_no_rec
            contador_eventos_ato.update(chunk.loc[mascara_ato, "User ID"].values)

            versiones = chunk["IP Address"].apply(lambda x: clasificar_ip(x)[1])
            acumulador_global["total"] += len(versiones)
            acumulador_global["ipv4"] += int((versiones == 4).sum())
            acumulador_global["ipv6"] += int((versiones == 6).sum())
            acumulador_global["invalidas"] += int(versiones.isna().sum())

            if n_chunks % 5 == 0:
                print(f"    ... {n_chunks} chunks procesados "
                      f"({acumulador_global['total']:,} filas acumuladas)")

        duracion = time.time() - t0
        total = acumulador_global["total"]

        diagnostico_global = {
            "poblacion": "RBA GLOBAL (33M+)",
            "total_ips": total,
            "total_ipv4": acumulador_global["ipv4"],
            "total_ipv6": acumulador_global["ipv6"],
            "total_invalidas": acumulador_global["invalidas"],
            "pct_ipv4": 100 * acumulador_global["ipv4"] / total if total else 0.0,
            "pct_ipv6": 100 * acumulador_global["ipv6"] / total if total else 0.0,
            "pct_invalidas": 100 * acumulador_global["invalidas"] / total if total else 0.0,
        }

        print(f"\n  Chunks procesados: {n_chunks}")
        print(f"  Usuarios únicos detectados: {len(contador_usuarios):,}")
        print(f"  [ATO] Eventos Is Account Takeover=True: "
              f"{sum(contador_eventos_ato.values()):,}")
        print(f"  [ATO] Usuarios distintos con >=1 evento ATO: "
              f"{len(contador_eventos_ato):,}")
        if n_ato_no_reconocidos:
            print(f"  [ATENCIÓN] {n_ato_no_reconocidos:,} valores de "
                  "'Is Account Takeover' no reconocidos (contados como NO-ATO).")
        print(f"  [POBLACIÓN GLOBAL] IPv4: {diagnostico_global['total_ipv4']:,} "
              f"({diagnostico_global['pct_ipv4']:.2f}%)")
        print(f"  [POBLACIÓN GLOBAL] IPv6: {diagnostico_global['total_ipv6']:,} "
              f"({diagnostico_global['pct_ipv6']:.2f}%)")
        print(f"  [POBLACIÓN GLOBAL] Inválidas: {diagnostico_global['total_invalidas']:,} "
              f"({diagnostico_global['pct_invalidas']:.2f}%)")
        print(f"  Tiempo primera pasada: {duracion:.1f}s\n")

        return contador_usuarios, contador_eventos_ato, diagnostico_global

    def segunda_pasada(self, usuarios_seleccionados):
        """Segunda pasada por chunks: aísla TODO el historial de los
        usuarios seleccionados (no son N_USUARIOS filas, README
        Sección 8)."""
        config = self.config
        print("=" * 60)
        print("[4/8] Extrayendo historial completo de los usuarios seleccionados...")
        print("=" * 60)

        set_usuarios = set(usuarios_seleccionados)
        columnas = config.COLUMNAS_RBA_OBLIGATORIAS

        fragmentos = []
        n_chunks = 0
        t0 = time.time()

        reader = pd.read_csv(
            config.RBA_PATH,
            usecols=columnas,
            chunksize=config.CHUNKSIZE_PASADA_2,
            dtype={"User ID": "int64"},
        )

        for chunk in reader:
            n_chunks += 1
            filtrado = chunk[chunk["User ID"].isin(set_usuarios)]
            if not filtrado.empty:
                fragmentos.append(filtrado)

            if n_chunks % 5 == 0:
                filas_acum = sum(len(f) for f in fragmentos)
                print(f"    ... {n_chunks} chunks leídos, "
                      f"{filas_acum:,} filas retenidas hasta ahora")

        if not fragmentos:
            raise RuntimeError(
                "ERROR CRÍTICO: la segunda pasada no encontró NINGÚN registro "
                "para los usuarios seleccionados. Revisa integridad del archivo."
            )

        df_2000 = pd.concat(fragmentos, ignore_index=True)
        del fragmentos
        duracion = time.time() - t0

        diagnostico_subconjunto = diagnosticar_ipv4_ipv6(
            df_2000["IP Address"], etiqueta_poblacion="SUBCONJUNTO usuarios seleccionados"
        )

        df_2000.to_csv(config.OUT_RBA_2000, index=False)

        print(f"\n  Filas totales extraídas: {len(df_2000):,}")
        print(f"  Usuarios distintos en el resultado: "
              f"{df_2000['User ID'].nunique():,}")
        print(f"  [SUBCONJUNTO] IPv4: {diagnostico_subconjunto['total_ipv4']:,} "
              f"({diagnostico_subconjunto['pct_ipv4']:.2f}%)")
        print(f"  [SUBCONJUNTO] IPv6: {diagnostico_subconjunto['total_ipv6']:,} "
              f"({diagnostico_subconjunto['pct_ipv6']:.2f}%)")
        print(f"  Archivo generado: {config.OUT_RBA_2000}")
        print(f"  Tiempo segunda pasada: {duracion:.1f}s\n")

        return df_2000, diagnostico_subconjunto
