# ============================================================================
# FASE 03 — PREPARACIÓN DE DATOS (CRISP-DM)
# Proyecto: Detección predictiva de accesos anómalos
#           Hospital Clínico Privado de Alta Complejidad
# Autor: Javier — 8vo semestre
# Entorno objetivo: Google Colab (RAM ≈ 12 GB)
#
# VERSIÓN 4 — Refactor controlado sobre la Versión 3.
# La Versión 3 ya resolvía correctamente:
#   - Lectura por chunks de los 33M+ registros del RBA (memoria).
#   - Inferencia defensiva de la unidad del 'Login Timestamp' (entero de
#     64 bits: segundos / ms / us / ns, según orden de magnitud).
#   - Resolución de rangos IP mediante pd.merge_asof (binary search).
# Esta Versión 4 preserva TODO lo anterior intacto y corrige dos
# inconsistencias semánticas reales detectadas en auditoría ("Spanglish"):
#
#   BUG #1 — CENTROIDES_GEOGRAFICOS usaba llaves en español
#            ("Colombia", "México"...) pero se consultaba contra
#            df["Country"], que en el RBA YA viene en formato ISO2
#            ("CO", "US"...). El lookup fallaba silenciosamente para
#            casi todos los registros -> impossible_travel subestimado.
#            CORRECCIÓN: las llaves de CENTROIDES_GEOGRAFICOS ahora son
#            códigos ISO2, alineados con el formato real de 'Country'.
#
#   BUG #2 — country_mismatch comparaba Pais_Residencia (nombre en
#            español, ej. "España") contra ip_country_name (nombre en
#            inglés de IPinfo, ej. "Spain"). Coincidía por accidente en
#            pocos países y fallaba sistemáticamente en el resto.
#            CORRECCIÓN: Pais_Residencia ahora se genera directamente
#            como código ISO2 y se compara contra ip_country_code
#            (el campo 'country' de 2 letras que IPinfo entrega nativo),
#            ambos normalizados a mayúsculas.
#
# Además se agrega, por requerimiento explícito de la Sección 3.7 / 31:
#   - Variable binaria 'has_previous_login' (0 = primer evento del
#     usuario, 1 = existe historial previo), independiente de que
#     distance_previous_km / required_speed_kmh puedan ya ser NaN por
#     otras razones (país sin centroide, IP no resuelta, etc).
#
# ----------------------------------------------------------------------------
# NOTA METODOLÓGICA (léase antes de ejecutar):
# Este script NO entrena ningún modelo. NO contiene train_test_split(),
# SMOTE, oversampling/undersampling, ni .fit() de ningún clasificador.
# Eso pertenece a la Fase 04 y está fuera del alcance de este archivo.
#
# Las coordenadas en CENTROIDES_GEOGRAFICOS son coordenadas reales de
# referencia (capitales/ciudades conocidas) usadas como "centroides
# representativos" para aproximar Impossible Travel — NUNCA como la
# ubicación GPS real de ningún usuario (Secciones 27, 33).
#
# Fuente del país para Impossible Travel: 'Country' ORIGINAL del RBA
# (ISO2 nativo, no requiere conversión). IPinfo se usa solo como
# enriquecimiento de IP y para 'country_mismatch' (Sección 36).
# ----------------------------------------------------------------------------

import gc
import time
import random
import ipaddress
from collections import Counter

import numpy as np
import pandas as pd
from faker import Faker

# ============================================================================
# [1/8] CONFIGURACIÓN DEL ENTORNO
# ============================================================================

def configurar_entorno():
    """Centraliza TODAS las constantes reproducibles del pipeline."""
    print("=" * 60)
    print("[1/8] Configurando entorno...")
    print("=" * 60)

    config = {
        "RBA_PATH": "/content/rba_dataset.csv",
        "IPINFO_PATH": "/content/country_asn.csv",
        "OUT_RBA_2000": "/content/rba_2000_users.csv",
        "OUT_EMPLEADOS": "/content/empleados.csv",
        "OUT_DATASET_FINAL": "/content/dataset_final_modelo.csv",

        "RANDOM_STATE": 42,
        "FAKER_SEED": 42,

        "MIN_EVENTOS_USUARIO": 15,
        "N_USUARIOS": 2000,

        "CHUNKSIZE_PASADA_1": 500_000,
        "CHUNKSIZE_PASADA_2": 250_000,

        "COLUMNAS_RBA_OBLIGATORIAS": [
            "User ID",
            "IP Address",
            "Login Timestamp",
            "Login Successful",
            "Device Type",
            "Is Attack IP",
            "Is Account Takeover",
            "Country",
            "Region",
            "City",
            "ASN",
            "Round-Trip Time [ms]",
        ],

        "VENTANA_CORTA": "15min",
        "VENTANA_LARGA": "1h",

        "UMBRAL_VELOCIDAD_KMH": 800.0,
        "VENTANA_MAX_HORAS": 12.0,

        "PESO_ASISTENCIAL_HOSPITALARIO": 0.80,
        "PROB_CUENTA_ACTIVA": 0.93,

        # Ventana de recolección real del RBA Dataset, según su
        # documentación oficial (das-group/rba-dataset). Se usa
        # únicamente como verificación de cordura no bloqueante sobre
        # la unidad inferida del timestamp.
        "VENTANA_FECHAS_RBA_CONOCIDA": ("2019-01-01", "2022-12-31"),

        # Set de códigos ISO2 reconocidos por el pipeline (empleados +
        # centroides). Se usa solo para diagnóstico informativo, NUNCA
        # para inventar o corregir países no reconocidos.
        "ISO2_RECONOCIDOS": {
            "CO", "MX", "ES", "AR", "PE", "CL", "US", "EC",
            "BR", "VE", "DE", "FR", "GB", "CA", "CN", "IN", "RU", "JP",
        },
    }

    print(f"  RANDOM_STATE            = {config['RANDOM_STATE']}")
    print(f"  MIN_EVENTOS_USUARIO      = {config['MIN_EVENTOS_USUARIO']}")
    print(f"  N_USUARIOS               = {config['N_USUARIOS']}")
    print(f"  UMBRAL_VELOCIDAD_KMH     = {config['UMBRAL_VELOCIDAD_KMH']}")
    print(f"  VENTANA_MAX_HORAS        = {config['VENTANA_MAX_HORAS']}")
    print("  Entorno configurado correctamente.\n")

    return config


def validar_columnas_rba(path, columnas_obligatorias):
    """Valida el encabezado REAL del CSV (nrows=0) antes de leer nada."""
    print("  Validando encabezado real del archivo RBA...")
    encabezado_real = set(pd.read_csv(path, nrows=0).columns)
    faltantes = [c for c in columnas_obligatorias if c not in encabezado_real]

    if faltantes:
        raise ValueError(
            "ERROR DE VALIDACIÓN DE ENCABEZADO — el archivo RBA no contiene "
            f"las columnas obligatorias: {faltantes}.\n"
            f"Columnas encontradas en el archivo: {sorted(encabezado_real)}\n"
            "El pipeline NO renombra columnas de forma silenciosa."
        )

    print(f"  Encabezado validado: las {len(columnas_obligatorias)} "
          "columnas obligatorias están presentes.\n")
    return True


# ============================================================================
# UTILIDAD COMPARTIDA: CLASIFICACIÓN / CONVERSIÓN DE IP
# ============================================================================

def clasificar_ip(ip_str):
    """Clasifica una IP y, si es IPv4 válida, la convierte a entero.
    version=4 -> IPv4 (ip_int válido). version=6 -> IPv6 (no se resuelve
    en Fase 03). version=None -> inválida/nula. Nunca lanza excepción."""
    if pd.isna(ip_str):
        return (np.nan, None)
    try:
        ip_obj = ipaddress.ip_address(str(ip_str).strip())
        if isinstance(ip_obj, ipaddress.IPv4Address):
            return (int(ip_obj), 4)
        else:
            return (np.nan, 6)
    except ValueError:
        return (np.nan, None)


def diagnosticar_ipv4_ipv6(serie_ips, etiqueta_poblacion):
    """Diagnóstico IPv4/IPv6/inválidas para CUALQUIER población de IPs,
    etiquetado explícitamente para que el checklist nunca mezcle
    poblaciones distintas sin identificarlas."""
    versiones = serie_ips.apply(lambda x: clasificar_ip(x)[1])
    total = len(versiones)
    total_ipv4 = int((versiones == 4).sum())
    total_ipv6 = int((versiones == 6).sum())
    total_invalidas = int(versiones.isna().sum())

    return {
        "poblacion": etiqueta_poblacion,
        "total_ips": total,
        "total_ipv4": total_ipv4,
        "total_ipv6": total_ipv6,
        "total_invalidas": total_invalidas,
        "pct_ipv4": 100 * total_ipv4 / total if total else 0.0,
        "pct_ipv6": 100 * total_ipv6 / total if total else 0.0,
        "pct_invalidas": 100 * total_invalidas / total if total else 0.0,
    }


# ============================================================================
# UTILIDAD: CONVERSIÓN SEGURA DE 'Login Timestamp' (heredada de V3, intacta)
# ============================================================================

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

    # IMPORTANTE: la proporción "es numérico" se mide SOLO sobre los
    # valores que ya eran no-nulos en el ORIGINAL. Medirla sobre la
    # serie completa confundiría nulos legítimos (NaN reales del
    # dataset) con fallos de conversión, y dispararía el fallback de
    # texto incluso cuando la columna sí es un entero válido.
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

    # --- Verificación de cordura (no bloqueante) ---
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


# ============================================================================
# [2/8] PRIMERA PASADA — CONTEO DE FRECUENCIA + DIAGNÓSTICO GLOBAL IPv4/IPv6
# ============================================================================

def analizar_dataset_rba(config):
    """Primera pasada COMPLETA sobre el RBA (33M+ filas) por chunks."""
    print("=" * 60)
    print("[2/8] Analizando dataset RBA (primera pasada, por chunks)...")
    print("=" * 60)

    validar_columnas_rba(config["RBA_PATH"], config["COLUMNAS_RBA_OBLIGATORIAS"])

    contador_usuarios = Counter()
    acumulador_global = {"total": 0, "ipv4": 0, "ipv6": 0, "invalidas": 0}

    t0 = time.time()
    n_chunks = 0

    reader = pd.read_csv(
        config["RBA_PATH"],
        usecols=["User ID", "IP Address"],
        chunksize=config["CHUNKSIZE_PASADA_1"],
        dtype={"User ID": "int64"},
    )

    for chunk in reader:
        n_chunks += 1
        contador_usuarios.update(chunk["User ID"].values)

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
    print(f"  [POBLACIÓN GLOBAL] IPv4: {diagnostico_global['total_ipv4']:,} "
          f"({diagnostico_global['pct_ipv4']:.2f}%)")
    print(f"  [POBLACIÓN GLOBAL] IPv6: {diagnostico_global['total_ipv6']:,} "
          f"({diagnostico_global['pct_ipv6']:.2f}%)")
    print(f"  [POBLACIÓN GLOBAL] Inválidas: {diagnostico_global['total_invalidas']:,} "
          f"({diagnostico_global['pct_invalidas']:.2f}%)")
    print(f"  Tiempo primera pasada: {duracion:.1f}s\n")

    return contador_usuarios, diagnostico_global


# ============================================================================
# [3/8] SELECCIÓN REPRODUCIBLE DE 2.000 USUARIOS
# ============================================================================

def seleccionar_usuarios(contador_usuarios, config):
    """Selección ALEATORIA, REPRODUCIBLE, SIN REEMPLAZO de N_USUARIOS."""
    print("=" * 60)
    print("[3/8] Seleccionando 2.000 usuarios (muestra reproducible)...")
    print("=" * 60)

    poblacion_elegible = [
        uid for uid, freq in contador_usuarios.items()
        if freq >= config["MIN_EVENTOS_USUARIO"]
    ]
    poblacion_elegible.sort()

    print(f"  Usuarios con >= {config['MIN_EVENTOS_USUARIO']} eventos: "
          f"{len(poblacion_elegible):,}")

    if len(poblacion_elegible) < config["N_USUARIOS"]:
        raise ValueError(
            "La población elegible es menor que N_USUARIOS. "
            "Revisa MIN_EVENTOS_USUARIO o el archivo de origen."
        )

    rng = np.random.default_rng(config["RANDOM_STATE"])
    usuarios_seleccionados = rng.choice(
        poblacion_elegible, size=config["N_USUARIOS"], replace=False
    )
    usuarios_seleccionados = sorted(int(u) for u in usuarios_seleccionados)

    if len(set(usuarios_seleccionados)) != config["N_USUARIOS"]:
        raise RuntimeError(
            "ERROR CRÍTICO: la selección de usuarios no produjo exactamente "
            f"{config['N_USUARIOS']} usuarios únicos. Selección abortada."
        )
    for uid in usuarios_seleccionados:
        if contador_usuarios[uid] < config["MIN_EVENTOS_USUARIO"]:
            raise RuntimeError(
                f"ERROR CRÍTICO: el usuario {uid} fue seleccionado pero no "
                f"cumple MIN_EVENTOS_USUARIO. Selección abortada."
            )

    print(f"  Usuarios seleccionados: {len(usuarios_seleccionados):,} "
          f"(RANDOM_STATE={config['RANDOM_STATE']})")
    print("  [OK] Verificado: exactamente N_USUARIOS únicos, todos con "
          "el mínimo de eventos requerido.\n")

    return usuarios_seleccionados


# ============================================================================
# [4/8] SEGUNDA PASADA — EXTRACCIÓN DEL HISTORIAL COMPLETO
# ============================================================================

def extraer_historial_usuarios(usuarios_seleccionados, config):
    """Segunda pasada por chunks: aísla TODO el historial de los 2.000
    usuarios seleccionados (no son 2.000 filas, Sección 8)."""
    print("=" * 60)
    print("[4/8] Extrayendo historial completo de los 2.000 usuarios...")
    print("=" * 60)

    set_usuarios = set(usuarios_seleccionados)
    columnas = config["COLUMNAS_RBA_OBLIGATORIAS"]

    fragmentos = []
    n_chunks = 0
    t0 = time.time()

    reader = pd.read_csv(
        config["RBA_PATH"],
        usecols=columnas,
        chunksize=config["CHUNKSIZE_PASADA_2"],
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
    del fragmentos  # libera la lista de fragmentos intermedios cuanto antes
    duracion = time.time() - t0

    diagnostico_subconjunto = diagnosticar_ipv4_ipv6(
        df_2000["IP Address"], etiqueta_poblacion="SUBCONJUNTO 2.000 usuarios"
    )

    df_2000.to_csv(config["OUT_RBA_2000"], index=False)

    print(f"\n  Filas totales extraídas: {len(df_2000):,}")
    print(f"  Usuarios distintos en el resultado: "
          f"{df_2000['User ID'].nunique():,}")
    print(f"  [SUBCONJUNTO] IPv4: {diagnostico_subconjunto['total_ipv4']:,} "
          f"({diagnostico_subconjunto['pct_ipv4']:.2f}%)")
    print(f"  [SUBCONJUNTO] IPv6: {diagnostico_subconjunto['total_ipv6']:,} "
          f"({diagnostico_subconjunto['pct_ipv6']:.2f}%)")
    print(f"  Archivo generado: {config['OUT_RBA_2000']}")
    print(f"  Tiempo segunda pasada: {duracion:.1f}s\n")

    return df_2000, diagnostico_subconjunto


# ============================================================================
# [5/8] MAESTRO SINTÉTICO DE EMPLEADOS (empleados.csv)
# ----------------------------------------------------------------------------
# CORRECCIÓN V4 (Bug #2 / Sección 3.5): Pais_Residencia se genera
# DIRECTAMENTE como código ISO2 canónico (CO, MX, ES...), no como nombre
# en español. Esto es una decisión deliberada por instrucción explícita:
# se sacrifica la columna paralela "nombre legible en español" (que el
# otro README sugería conservar para trazabilidad) a cambio de tener una
# única representación canónica que se puede comparar sin fricción
# contra ip_country_code (IPinfo) y contra 'Country' del RBA.
# ============================================================================

ROLES_ASISTENCIALES = {
    "Médico Especialista": 0.18,
    "Médico General": 0.14,
    "Enfermero/a": 0.28,
    "Auxiliar de Enfermería": 0.20,
    "Farmacéutico/a": 0.10,
    "Personal de Laboratorio": 0.10,
}

ROLES_NO_ASISTENCIALES = {
    "Administrativo - Facturación": 0.30,
    "Administrativo - RRHH": 0.20,
    "Personal de TI / Soporte": 0.30,
    "Directivo / Gerencia": 0.20,
}

TURNOS = {
    "Diurno": 0.35,          # 06:00 - 14:00
    "Tarde": 0.25,           # 14:00 - 22:00
    "Nocturno": 0.25,        # 22:00 - 06:00 (cruza medianoche)
    "Administrativo": 0.15,  # 08:00 - 17:00
}

VENTANAS_TURNO = {
    "Diurno": (6, 14),
    "Tarde": (14, 22),
    "Nocturno": (22, 6),
    "Administrativo": (8, 17),
}

# Mismas ponderaciones de la V3 (Sección 17), solo que ahora la llave es
# el código ISO2 canónico en lugar del nombre en español.
PAISES_RESIDENCIA_PESOS = {
    "CO": 0.72,  # Colombia
    "MX": 0.06,  # México
    "ES": 0.05,  # España
    "AR": 0.04,  # Argentina
    "PE": 0.04,  # Perú
    "CL": 0.03,  # Chile
    "US": 0.03,  # Estados Unidos
    "EC": 0.03,  # Ecuador
}

# Mismas ciudades de la V3, ahora indexadas por ISO2. La coherencia
# Pais_Residencia <-> Ciudad_Base se sigue validando explícitamente
# más abajo (no se relaja esa validación).
CIUDADES_POR_PAIS = {
    "CO": ["Bogotá", "Medellín", "Cali", "Barranquilla", "Ibagué", "Bucaramanga"],
    "MX": ["Ciudad de México", "Guadalajara", "Monterrey", "Puebla"],
    "ES": ["Madrid", "Barcelona", "Valencia", "Sevilla"],
    "AR": ["Buenos Aires", "Córdoba", "Rosario"],
    "PE": ["Lima", "Arequipa", "Cusco"],
    "CL": ["Santiago", "Valparaíso", "Concepción"],
    "US": ["Miami", "Houston", "Los Ángeles"],
    "EC": ["Quito", "Guayaquil", "Cuenca"],
}


def _construir_lista_ponderada(pesos_dict):
    etiquetas = list(pesos_dict.keys())
    pesos = np.array(list(pesos_dict.values()), dtype=float)
    pesos = pesos / pesos.sum()
    return etiquetas, pesos


def generar_empleados(usuarios_seleccionados, config):
    """Genera empleados.csv con EXACTAMENTE los 2.000 User ID reales del
    RBA. Atributos 100% sintéticos (Faker, seed=42). Ciudad_Base
    coherente con Pais_Residencia.

    CAMBIO V4: 'Pais_Residencia' ahora almacena el código ISO2
    canónico (ej. 'CO') en vez del nombre en español (ej. 'Colombia').
    Esto es lo que permite comparaciones geográficas sin fricción en
    'country_mismatch' más adelante.
    """
    print("=" * 60)
    print("[5/8] Generando maestro sintético de empleados...")
    print("=" * 60)

    Faker.seed(config["FAKER_SEED"])
    fake = Faker()
    rng = np.random.default_rng(config["RANDOM_STATE"])
    rng_python = random.Random(config["RANDOM_STATE"])

    peso_asistencial = config["PESO_ASISTENCIAL_HOSPITALARIO"]
    peso_no_asistencial = 1.0 - peso_asistencial

    roles_etiquetas = list(ROLES_ASISTENCIALES.keys()) + list(ROLES_NO_ASISTENCIALES.keys())
    roles_pesos = np.array(
        [w * peso_asistencial for w in ROLES_ASISTENCIALES.values()] +
        [w * peso_no_asistencial for w in ROLES_NO_ASISTENCIALES.values()]
    )
    roles_pesos = roles_pesos / roles_pesos.sum()

    turnos_etiquetas, turnos_pesos = _construir_lista_ponderada(TURNOS)
    paises_etiquetas, paises_pesos = _construir_lista_ponderada(PAISES_RESIDENCIA_PESOS)

    n = len(usuarios_seleccionados)

    roles_asignados = rng.choice(roles_etiquetas, size=n, p=roles_pesos)
    turnos_asignados = rng.choice(turnos_etiquetas, size=n, p=turnos_pesos)
    paises_asignados = rng.choice(paises_etiquetas, size=n, p=paises_pesos)
    estados_cuenta = rng.choice(
        ["Activo", "Inactivo"], size=n,
        p=[config["PROB_CUENTA_ACTIVA"], 1 - config["PROB_CUENTA_ACTIVA"]],
    )

    registros = []
    for i, uid in enumerate(usuarios_seleccionados):
        pais_iso2 = paises_asignados[i]
        ciudades_del_pais = CIUDADES_POR_PAIS.get(pais_iso2, ["Ciudad no catalogada"])
        ciudad = rng_python.choice(ciudades_del_pais)

        registros.append({
            "User ID": uid,
            "Nombre_Completo": fake.name(),
            "Rol_Hospitalario": roles_asignados[i],
            "Pais_Residencia": pais_iso2,  # <- ISO2 canónico (CAMBIO V4)
            "Ciudad_Base": ciudad,
            "Turno_Asignado": turnos_asignados[i],
            "Estado_Cuenta": estados_cuenta[i],
            "Fecha_Ingreso": fake.date_between(start_date="-10y", end_date="-1y"),
        })

    df_empleados = pd.DataFrame(registros)

    if set(df_empleados["User ID"]) != set(usuarios_seleccionados):
        raise RuntimeError(
            "ERROR CRÍTICO DE INTEGRIDAD REFERENCIAL: los User ID de "
            "empleados.csv no coinciden 100% con los usuarios extraídos "
            "del RBA."
        )
    if len(df_empleados) != config["N_USUARIOS"]:
        raise RuntimeError(
            f"ERROR CRÍTICO: empleados.csv tiene {len(df_empleados)} filas, "
            f"se esperaban exactamente {config['N_USUARIOS']}."
        )
    if not pd.api.types.is_integer_dtype(df_empleados["User ID"]):
        raise RuntimeError(
            "El dtype de 'User ID' en empleados.csv debe ser entero (int64)."
        )

    incoherentes = df_empleados.apply(
        lambda r: r["Ciudad_Base"] not in CIUDADES_POR_PAIS.get(r["Pais_Residencia"], []),
        axis=1,
    ).sum()
    if incoherentes > 0:
        raise RuntimeError(
            f"ERROR CRÍTICO: {incoherentes} empleados tienen Ciudad_Base "
            "incoherente con su Pais_Residencia."
        )

    # Diagnóstico informativo (NO bloqueante): confirma que los códigos
    # ISO2 generados están dentro del set reconocido por el pipeline.
    iso2_no_reconocidos = set(df_empleados["Pais_Residencia"].unique()) - config["ISO2_RECONOCIDOS"]
    if iso2_no_reconocidos:
        print(f"  [ATENCIÓN] Códigos ISO2 generados fuera del set reconocido: "
              f"{iso2_no_reconocidos}. Revisa PAISES_RESIDENCIA_PESOS.")
    else:
        print("  [OK] Todos los códigos ISO2 de 'Pais_Residencia' están dentro "
              "del set reconocido por el pipeline.")

    df_empleados.to_csv(config["OUT_EMPLEADOS"], index=False)

    print(f"  Empleados generados: {len(df_empleados):,}")
    print("  [OK] Integridad referencial (User ID): 100% verificado")
    print("  [OK] Coherencia Pais_Residencia (ISO2) / Ciudad_Base: 100% verificado")
    print("  Distribución de roles (asistencial vs. no asistencial):")
    print(df_empleados["Rol_Hospitalario"].value_counts(normalize=True)
          .mul(100).round(1).to_string())
    print(f"  Archivo generado: {config['OUT_EMPLEADOS']}\n")

    return df_empleados


# ============================================================================
# [6/8] RESOLUCIÓN DE RANGOS IP (IPinfo + merge_asof) — SOLO ENRIQUECIMIENTO
# ============================================================================

def resolver_ips(df_logs, config):
    """
    Enriquece cada IP con datos de IPinfo. Enriquecimiento ADICIONAL,
    NUNCA sustituye 'Country'/'Region'/'City' originales del RBA. Las
    columnas nuevas llevan prefijo 'ip_'.

    'ip_country_code' es el código ISO2 nativo de 2 letras que entrega
    IPinfo en su columna 'country' — esta es la columna que se usará
    para 'country_mismatch' (Sección 3.9 / 36), NO 'ip_country_name'.

    NOTA DE MEMORIA (heredada de V3): esta función MUTA `df_logs`
    directamente (sin `.copy()` inicial), porque es el único objeto
    vivo que viaja por el orquestador `main()`.
    """
    print("=" * 60)
    print("[6/8] Resolviendo rangos IP mediante IPinfo (solo enriquecimiento)...")
    print("=" * 60)

    clasificacion = df_logs["IP Address"].apply(clasificar_ip)
    df_logs["ip_int"] = clasificacion.apply(lambda t: t[0])
    df_logs["ip_version"] = clasificacion.apply(lambda t: t[1])
    del clasificacion

    total_ips = len(df_logs)
    total_ipv4 = int((df_logs["ip_version"] == 4).sum())
    total_ipv6 = int((df_logs["ip_version"] == 6).sum())
    total_invalidas = int(df_logs["ip_version"].isna().sum())

    df_ipinfo = pd.read_csv(config["IPINFO_PATH"])

    columnas_ipinfo_esperadas = {"start_ip", "end_ip", "country", "country_name",
                                  "asn", "as_name", "as_domain"}
    faltantes_ipinfo = columnas_ipinfo_esperadas - set(df_ipinfo.columns)
    if faltantes_ipinfo:
        raise ValueError(
            f"ERROR: el archivo IPinfo no contiene las columnas esperadas: "
            f"{faltantes_ipinfo}"
        )

    start_clas = df_ipinfo["start_ip"].apply(clasificar_ip)
    end_clas = df_ipinfo["end_ip"].apply(clasificar_ip)
    df_ipinfo["start_ip_int"] = start_clas.apply(lambda t: t[0])
    df_ipinfo["start_version"] = start_clas.apply(lambda t: t[1])
    df_ipinfo["end_ip_int"] = end_clas.apply(lambda t: t[0])
    del start_clas, end_clas

    df_ipinfo_v4 = df_ipinfo[df_ipinfo["start_version"] == 4].copy()
    # (Este .copy() SÍ se conserva: aísla el subconjunto IPv4 del resto
    # del catálogo IPinfo completo, que se descarta a continuación —
    # es un ahorro de memoria, no un gasto, porque libera df_ipinfo.)
    del df_ipinfo

    df_ipinfo_v4 = df_ipinfo_v4.dropna(subset=["start_ip_int", "end_ip_int"])
    df_ipinfo_v4 = df_ipinfo_v4.sort_values("start_ip_int").reset_index(drop=True)

    # CORRECCIÓN (bug de dtype en merge_asof): tras el dropna() de la
    # línea anterior, start_ip_int/end_ip_int YA NO contienen NaN en
    # este subconjunto. Sin embargo, el dtype de la columna pudo haber
    # quedado como float64 desde su creación en df_ipinfo completo (si
    # existía algún NaN en OTRAS filas del catálogo original, p. ej.
    # entradas IPv6). Se fuerza int64 explícitamente, ahora que la
    # ausencia de NaN en este subconjunto está garantizada.
    df_ipinfo_v4["start_ip_int"] = df_ipinfo_v4["start_ip_int"].astype("int64")
    df_ipinfo_v4["end_ip_int"] = df_ipinfo_v4["end_ip_int"].astype("int64")

    print(f"  Rangos IPv4 disponibles en IPinfo: {len(df_ipinfo_v4):,}")

    ips_unicas = (
        df_logs.loc[df_logs["ip_version"] == 4, ["ip_int"]]
        .drop_duplicates()
        .sort_values("ip_int")
        .reset_index(drop=True)
    )

    # CORRECCIÓN (bug de dtype en merge_asof): 'ip_int' llega aquí ya
    # filtrado a df_logs["ip_version"] == 4, lo que garantiza que en
    # ESTE subconjunto no existe ningún NaN (clasificar_ip solo devuelve
    # NaN cuando version != 4). Sin embargo, el dtype de la columna
    # pudo haber quedado como float64 desde su creación sobre el
    # DataFrame completo (33M+ filas), donde sí existen IPs IPv6 o
    # inválidas que fuerzan ese upcasting a nivel de columna. Se fuerza
    # int64 explícitamente, ahora que la ausencia de NaN está
    # garantizada en este subconjunto específico.
    ips_unicas["ip_int"] = ips_unicas["ip_int"].astype("int64")
    print(f"  IPs IPv4 únicas a resolver: {len(ips_unicas):,}")

    # 'country' (ISO2 nativo de IPinfo) -> 'ip_country_code'
    # 'country_name' (nombre en inglés) -> 'ip_country_name' (se
    #  conserva solo para lectura humana / auditoría, NUNCA para
    #  comparaciones geográficas — ese es justamente el Bug #2).
    columnas_geo_ipinfo = {
        "country": "ip_country_code",
        "country_name": "ip_country_name",
        "asn": "ip_asn",
        "as_name": "ip_as_name",
        "as_domain": "ip_as_domain",
    }
    df_ipinfo_v4 = df_ipinfo_v4.rename(columns=columnas_geo_ipinfo)
    columnas_geo_final = list(columnas_geo_ipinfo.values())

    resuelto = pd.merge_asof(
        ips_unicas,
        df_ipinfo_v4[["start_ip_int", "end_ip_int"] + columnas_geo_final],
        left_on="ip_int",
        right_on="start_ip_int",
        direction="backward",
    )
    del df_ipinfo_v4

    dentro_de_rango = resuelto["ip_int"] <= resuelto["end_ip_int"]
    for col in columnas_geo_final:
        resuelto.loc[~dentro_de_rango, col] = np.nan

    ipv4_unicas_resueltas = int(dentro_de_rango.sum())
    ipv4_unicas_no_resueltas = len(resuelto) - ipv4_unicas_resueltas

    resuelto_final = resuelto[["ip_int"] + columnas_geo_final].drop_duplicates(subset="ip_int")
    del resuelto
    df_logs = df_logs.merge(resuelto_final, on="ip_int", how="left")
    del resuelto_final

    # Normalización de mayúsculas del código ISO2 nativo. IPinfo ya lo
    # entrega en mayúsculas, pero se fuerza explícitamente para no
    # depender de un supuesto silencioso al comparar en country_mismatch.
    df_logs["ip_country_code"] = df_logs["ip_country_code"].str.upper()

    pct_resolucion = (
        100 * ipv4_unicas_resueltas / len(ips_unicas) if len(ips_unicas) else 0.0
    )

    diagnostico_resolucion = {
        "total_ips": total_ips,
        "total_ipv4": total_ipv4,
        "total_ipv6": total_ipv6,
        "total_invalidas": total_invalidas,
        "ipv4_unicas_resueltas": ipv4_unicas_resueltas,
        "ipv4_unicas_no_resueltas": ipv4_unicas_no_resueltas,
        "pct_resolucion_ipv4": pct_resolucion,
    }

    print(f"  IPs IPv4 únicas resueltas: {ipv4_unicas_resueltas:,} / "
          f"{len(ips_unicas):,} ({pct_resolucion:.2f}%)")
    print("  (No se asume 100% de resolución; se mide realmente)")
    print("  Columnas de IPinfo agregadas con prefijo 'ip_' (no sustituyen "
          "'Country'/'Region'/'City'/'ASN' originales del RBA)")
    print("  'ip_country_code' (ISO2, normalizado a mayúsculas) es la columna "
          "que se usará en country_mismatch — 'ip_country_name' se conserva "
          "solo para lectura humana.\n")

    return df_logs, diagnostico_resolucion


# ============================================================================
# [7/8] INGENIERÍA DE CARACTERÍSTICAS
# ============================================================================

VALORES_LOGIN_EXITOSO = {"true", "1", "1.0", "yes", "y", "t", "success", "successful"}
VALORES_LOGIN_FALLIDO = {"false", "0", "0.0", "no", "n", "f", "fail", "failed", "failure"}


def normalizar_login_successful(serie):
    """Conversión DEFENSIVA de 'Login Successful': reconoce booleanos
    nativos, texto ('True'/'False'/'yes'/'no', etc.) y 0/1. Un valor
    ambiguo se marca NaN — NUNCA se asume como éxito o fracaso.
    (Sin cambios respecto a V3: esta función ya conservaba la
    incertidumbre correctamente.)"""
    def _clasificar(valor):
        if pd.isna(valor):
            return np.nan
        if isinstance(valor, (bool, np.bool_)):
            return bool(valor)
        if isinstance(valor, (int, float, np.integer, np.floating)):
            if valor == 1:
                return True
            if valor == 0:
                return False
            return np.nan
        texto = str(valor).strip().lower()
        if texto in VALORES_LOGIN_EXITOSO:
            return True
        if texto in VALORES_LOGIN_FALLIDO:
            return False
        return np.nan

    valores_originales_unicos = serie.value_counts(dropna=False)
    print("  Valores originales detectados en 'Login Successful':")
    print(valores_originales_unicos.to_string())

    normalizado = serie.apply(_clasificar)
    n_desconocidos = int(normalizado.isna().sum() - serie.isna().sum())

    if n_desconocidos > 0:
        print(f"  [ATENCIÓN] {n_desconocidos:,} valores de 'Login Successful' "
              "no pudieron interpretarse de forma segura y se marcaron como "
              "NaN (política explícita: NO se asumen como éxito ni como "
              "fracaso).")
    else:
        print("  [OK] Todos los valores de 'Login Successful' se "
              "interpretaron correctamente.")

    return normalizado, n_desconocidos


def calcular_rolling_retrospectivo(df, columna_valor, ventana):
    """Ventana móvil retrospectiva (closed='left') POR USUARIO, con
    alineación EXPLÍCITA de índice (no depende del orden interno de
    groupby).

    ROBUSTEZ V4: se itera manualmente sobre los grupos y se concatena
    con pd.concat(), en vez de usar groupby().apply(). Esto evita un
    edge case real detectado en auditoría: en pandas >= 3.0,
    groupby().apply() puede devolver un DataFrame de una sola fila
    (en vez de concatenar las Series por grupo) cuando el DataFrame
    contiene EXACTAMENTE UN grupo. Con los 2.000 usuarios reales del
    pipeline esto nunca ocurre, pero la función no debería depender
    implícitamente de "haber más de un usuario" para ser correcta.
    """
    partes = []
    for _, grupo in df.groupby("User ID", sort=False):
        serie_temporal = grupo.set_index("Login Timestamp")[columna_valor]
        resultado = serie_temporal.rolling(ventana, closed="left").sum()
        resultado.index = grupo.index
        partes.append(resultado)

    resultados = pd.concat(partes) if partes else pd.Series(dtype=float)
    return resultados.reindex(df.index)


def crear_features_temporales(df, config):
    """
    Construye failed_attempts_15min/1h, previous_login_timestamp,
    previous_ip, previous_country (basado en 'Country' ORIGINAL del
    RBA), time_since_previous_login_hours y — NUEVO EN V4 —
    has_previous_login.

    CAMBIO V4: se agrega 'has_previous_login' (0/1) de forma explícita,
    independiente de cualquier otro cálculo. Esto es lo que la Sección
    3.7/31 exige: el missing semántico del primer evento debe quedar
    marcado con una variable propia, no inferido implícitamente a
    partir de otros NaN.
    """
    print("=" * 60)
    print("[7/8] Creando features de ingeniería (fuerza bruta, temporales)...")
    print("=" * 60)

    print("  Convirtiendo 'Login Timestamp' (entero Unix de 64 bits)...")
    df["Login Timestamp"] = convertir_login_timestamp(
        df["Login Timestamp"], config.get("VENTANA_FECHAS_RBA_CONOCIDA")
    )
    df = df.sort_values(["User ID", "Login Timestamp"]).reset_index(drop=True)

    print("\n  Normalizando 'Login Successful'...")
    login_normalizado, n_desconocidos = normalizar_login_successful(df["Login Successful"])
    df["login_exitoso_normalizado"] = login_normalizado

    # Máscara de FALLOS EXPLÍCITOS únicamente. Un valor desconocido
    # (NaN) no debe contar como fallo ni como éxito dentro de la
    # ventana de fuerza bruta — por eso se compara explícitamente
    # contra False, nunca se hace fillna(False) antes de esto.
    mascara_fallo_explicito = df["login_exitoso_normalizado"] == False  # noqa: E712
    df["is_failed"] = mascara_fallo_explicito.astype(int)

    df["failed_attempts_15min"] = calcular_rolling_retrospectivo(
        df, "is_failed", config["VENTANA_CORTA"]
    ).fillna(0)
    df["failed_attempts_1h"] = calcular_rolling_retrospectivo(
        df, "is_failed", config["VENTANA_LARGA"]
    ).fillna(0)

    grp = df.groupby("User ID")
    df["previous_login_timestamp"] = grp["Login Timestamp"].shift(1)
    df["previous_ip"] = grp["IP Address"].shift(1)
    df["previous_country"] = grp["Country"].shift(1)
    del grp

    # --- NUEVO EN V4: has_previous_login explícito ---
    df["has_previous_login"] = df["previous_login_timestamp"].notna().astype(int)

    delta = df["Login Timestamp"] - df["previous_login_timestamp"]
    df["time_since_previous_login_hours"] = delta.dt.total_seconds() / 3600.0
    del delta

    print(f"\n  failed_attempts_15min -> media: "
          f"{df['failed_attempts_15min'].mean():.3f}")
    print(f"  failed_attempts_1h    -> media: "
          f"{df['failed_attempts_1h'].mean():.3f}")
    print(f"  has_previous_login = 0 (primer evento por usuario): "
          f"{int((df['has_previous_login'] == 0).sum()):,}")
    print(f"  has_previous_login = 1 (con historial previo): "
          f"{int((df['has_previous_login'] == 1).sum()):,}")
    print(f"  Valores de Login Successful no interpretables: {n_desconocidos:,}\n")

    return df, n_desconocidos


# CORRECCIÓN V4 (Bug #1 / Sección 3.5): llaves en ISO2, alineadas con
# el formato NATIVO de df["Country"] en el RBA (ya es ISO2, no nombre).
# Antes las llaves eran nombres en español ("Colombia") y el lookup
# fallaba silenciosamente para casi todo el dataset.
CENTROIDES_GEOGRAFICOS = {
    "CO": (4.7110, -74.0721),    # Colombia
    "MX": (19.4326, -99.1332),   # México
    "ES": (40.4168, -3.7038),    # España
    "AR": (-34.6037, -58.3816),  # Argentina
    "PE": (-12.0464, -77.0428),  # Perú
    "CL": (-33.4489, -70.6693),  # Chile
    "US": (38.8951, -77.0364),   # Estados Unidos
    "EC": (-0.1807, -78.4678),   # Ecuador
    "BR": (-15.7939, -47.8828),  # Brasil
    "VE": (10.4806, -66.9036),   # Venezuela
    "DE": (52.5200, 13.4050),    # Alemania
    "FR": (48.8566, 2.3522),     # Francia
    "GB": (51.5074, -0.1278),    # Reino Unido
    "CA": (45.4215, -75.6972),   # Canadá
    "CN": (39.9042, 116.4074),   # China
    "IN": (28.6139, 77.2090),    # India
    "RU": (55.7558, 37.6173),    # Rusia
    "JP": (35.6762, 139.6503),   # Japón
}


def _distancia_haversine(lat1, lon1, lat2, lon2):
    """Distancia aproximada (km) entre dos puntos, fórmula de Haversine."""
    if any(pd.isna(v) for v in [lat1, lon1, lat2, lon2]):
        return np.nan
    R = 6371.0
    lat1_r, lon1_r, lat2_r, lon2_r = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c


def crear_feature_impossible_travel(df, config):
    """
    Impossible Travel sobre 'Country' ORIGINAL del RBA (actual y
    anterior) -> centroide representativo. Cobertura real del
    diccionario medida y devuelta.

    CAMBIO V4: además de la corrección de llaves ISO2 en
    CENTROIDES_GEOGRAFICOS (Bug #1), se agrega una máscara explícita
    que fuerza distance_previous_km / required_speed_kmh a NaN cuando
    has_previous_login == 0 — esto ya ocurría "por consecuencia"
    (previous_country era NaN), pero ahora queda garantizado "por
    regla", que es más auditable y a prueba de refactors futuros.
    """
    print("  Calculando Impossible Travel (Haversine + centroides ISO2 sobre "
          "'Country' original del RBA)...")

    def _lat(pais_iso2):
        return CENTROIDES_GEOGRAFICOS.get(pais_iso2, (np.nan, np.nan))[0]

    def _lon(pais_iso2):
        return CENTROIDES_GEOGRAFICOS.get(pais_iso2, (np.nan, np.nan))[1]

    df["_lat_actual"] = df["Country"].apply(_lat)
    df["_lon_actual"] = df["Country"].apply(_lon)
    df["_lat_previa"] = df["previous_country"].apply(_lat)
    df["_lon_previa"] = df["previous_country"].apply(_lon)

    df["distance_previous_km"] = df.apply(
        lambda r: _distancia_haversine(
            r["_lat_previa"], r["_lon_previa"], r["_lat_actual"], r["_lon_actual"]
        ),
        axis=1,
    )

    tiempo_valido = (
        df["time_since_previous_login_hours"].notna()
        & (df["time_since_previous_login_hours"] > 0)
    )
    distancia_valida = df["distance_previous_km"].notna()
    mascara_calculable = tiempo_valido & distancia_valida

    df["required_speed_kmh"] = np.nan
    df.loc[mascara_calculable, "required_speed_kmh"] = (
        df.loc[mascara_calculable, "distance_previous_km"]
        / df.loc[mascara_calculable, "time_since_previous_login_hours"]
    )

    # --- REGLA EXPLÍCITA V4 (Sección 31): sin historial, sin métrica ---
    # Aunque mascara_calculable ya excluye el primer evento en la
    # práctica, se refuerza aquí de forma explícita usando
    # has_previous_login para que la regla no dependa implícitamente
    # de otros cálculos si el pipeline cambia en el futuro.
    sin_historial = df["has_previous_login"] == 0
    df.loc[sin_historial, "distance_previous_km"] = np.nan
    df.loc[sin_historial, "required_speed_kmh"] = np.nan

    df["impossible_travel"] = 0
    condicion_anomalia = (
        mascara_calculable
        & (~sin_historial)
        & (df["required_speed_kmh"] > config["UMBRAL_VELOCIDAD_KMH"])
        & (df["time_since_previous_login_hours"] < config["VENTANA_MAX_HORAS"])
    )
    df.loc[condicion_anomalia, "impossible_travel"] = 1

    paises_relevantes = pd.concat(
        [df["Country"], df["previous_country"]]
    ).dropna().unique()
    paises_con_centroide = [p for p in paises_relevantes if p in CENTROIDES_GEOGRAFICOS]
    pct_cobertura_paises = (
        100 * len(paises_con_centroide) / len(paises_relevantes)
        if len(paises_relevantes) else 0.0
    )

    con_historial = df["has_previous_login"] == 1
    if con_historial.sum() > 0:
        ambos_con_centroide = (
            df.loc[con_historial, "Country"].isin(CENTROIDES_GEOGRAFICOS)
            & df.loc[con_historial, "previous_country"].isin(CENTROIDES_GEOGRAFICOS)
        )
        pct_cobertura_registros = 100 * ambos_con_centroide.sum() / con_historial.sum()
    else:
        pct_cobertura_registros = 0.0

    diagnostico_centroides = {
        "paises_relevantes_total": len(paises_relevantes),
        "paises_con_centroide": len(paises_con_centroide),
        "pct_cobertura_paises_distintos": pct_cobertura_paises,
        "pct_cobertura_registros_con_historial": pct_cobertura_registros,
    }

    df = df.drop(columns=["_lat_actual", "_lon_actual", "_lat_previa", "_lon_previa"])

    print(f"    Cobertura de centroides (países distintos, ISO2): "
          f"{len(paises_con_centroide)}/{len(paises_relevantes)} "
          f"({pct_cobertura_paises:.2f}%)")
    print(f"    Cobertura de centroides (registros con historial previo): "
          f"{pct_cobertura_registros:.2f}%")
    print(f"    impossible_travel = 1 -> {int(df['impossible_travel'].sum()):,} registros")
    print(f"    (heurística: velocidad > {config['UMBRAL_VELOCIDAD_KMH']} km/h "
          f"Y ventana < {config['VENTANA_MAX_HORAS']}h)\n")

    return df, diagnostico_centroides


def crear_feature_turnos(df):
    """is_outside_shift, respetando turnos que cruzan medianoche.
    Sin cambios respecto a V3."""
    print("  Calculando is_outside_shift (respetando turnos nocturnos)...")

    def _fuera_de_turno(hora, turno):
        if turno not in VENTANAS_TURNO or pd.isna(hora):
            return np.nan
        inicio, fin = VENTANAS_TURNO[turno]
        if inicio < fin:
            dentro = inicio <= hora < fin
        else:
            dentro = hora >= inicio or hora < fin
        return 0 if dentro else 1

    df["_hora_login"] = df["Login Timestamp"].dt.hour
    df["is_outside_shift"] = df.apply(
        lambda r: _fuera_de_turno(r["_hora_login"], r.get("Turno_Asignado", np.nan)),
        axis=1,
    )
    df = df.drop(columns=["_hora_login"])

    print(f"    Registros fuera de turno: "
          f"{int(df['is_outside_shift'].fillna(0).sum()):,}\n")
    return df


def crear_features_negocio(df):
    """
    country_mismatch e inactive_account_success.

    CORRECCIÓN V4 (Bug #2 / Sección 3.9, 36): country_mismatch ahora
    compara 'Pais_Residencia' (ISO2, generado directamente así en
    generar_empleados) contra 'ip_country_code' (ISO2 nativo de
    IPinfo), ambos normalizados a mayúsculas por seguridad. Antes se
    comparaba 'Pais_Residencia' (nombre en español) contra
    'ip_country_name' (nombre en inglés de IPinfo) — comparación que
    fallaba sistemáticamente salvo coincidencia accidental.

    Si la IP no fue resuelta (ip_country_code es NaN), el resultado
    debe ser NaN, NUNCA 0 ni 1 (Sección 31: ausencia de información no
    es lo mismo que "no hay mismatch").
    """
    print("  Calculando country_mismatch e inactive_account_success...")

    if "ip_country_code" not in df.columns:
        raise RuntimeError(
            "ERROR: 'ip_country_code' no está disponible; country_mismatch "
            "requiere el código ISO2 resuelto por IPinfo (Sección 36)."
        )

    pais_residencia_iso2 = df["Pais_Residencia"].astype("string").str.upper()
    ip_country_code_iso2 = df["ip_country_code"].astype("string").str.upper()

    ambos_conocidos = pais_residencia_iso2.notna() & ip_country_code_iso2.notna()
    df["country_mismatch"] = np.nan
    df.loc[ambos_conocidos, "country_mismatch"] = (
        pais_residencia_iso2[ambos_conocidos] != ip_country_code_iso2[ambos_conocidos]
    ).astype(int)

    df["inactive_account_success"] = (
        (df["Estado_Cuenta"] == "Inactivo")
        & (df["login_exitoso_normalizado"] == True)  # noqa: E712
    ).astype(int)

    n_no_resuelto = int((~ambos_conocidos).sum())
    print(f"    country_mismatch = 1 -> "
          f"{int(df['country_mismatch'].fillna(0).sum()):,} registros")
    print(f"    country_mismatch = NaN (IP no resuelta u otro dato faltante): "
          f"{n_no_resuelto:,} registros")
    print(f"    inactive_account_success = 1 -> "
          f"{int(df['inactive_account_success'].sum()):,} registros\n")

    return df


# ============================================================================
# [8/8] VALIDACIÓN BLOQUEANTE, DIAGNÓSTICO Y EXPORTACIÓN FINAL
# ============================================================================

def validar_calidad_bloqueante(df, usuarios_seleccionados, config):
    """Validaciones CRÍTICAS que DETIENEN la ejecución si fallan."""
    print("=" * 60)
    print("[8/8] Ejecutando validaciones BLOQUEANTES...")
    print("=" * 60)

    errores = []

    if len(set(usuarios_seleccionados)) != config["N_USUARIOS"]:
        errores.append(
            f"Se esperaban {config['N_USUARIOS']} usuarios únicos, "
            f"hay {len(set(usuarios_seleccionados))}."
        )

    usuarios_en_df = set(df["User ID"].unique())
    faltan_en_df = set(usuarios_seleccionados) - usuarios_en_df
    if faltan_en_df:
        errores.append(
            f"{len(faltan_en_df)} usuarios seleccionados no aparecen en el "
            "dataset integrado final (integridad referencial < 100%)."
        )

    conteo_final = df["User ID"].value_counts()
    insuficientes = conteo_final[conteo_final < config["MIN_EVENTOS_USUARIO"]]
    if len(insuficientes) > 0:
        errores.append(
            f"{len(insuficientes)} usuarios tienen menos de "
            f"{config['MIN_EVENTOS_USUARIO']} eventos en el dataset final."
        )

    if not pd.api.types.is_datetime64_any_dtype(df["Login Timestamp"]):
        errores.append("'Login Timestamp' no quedó convertido a datetime64.")

    orden_correcto = df.groupby("User ID")["Login Timestamp"].apply(
        lambda s: s.is_monotonic_increasing
    ).all()
    if not orden_correcto:
        errores.append(
            "El dataset no está correctamente ordenado por "
            "['User ID', 'Login Timestamp'] ascendente en todos los grupos."
        )

    columnas_obligatorias_salida = [
        "User ID", "Login Timestamp", "Is Account Takeover",
        "failed_attempts_15min", "failed_attempts_1h",
        "has_previous_login",
        "impossible_travel", "is_outside_shift",
        "country_mismatch", "inactive_account_success",
    ]
    faltantes_salida = [c for c in columnas_obligatorias_salida if c not in df.columns]
    if faltantes_salida:
        errores.append(f"Faltan columnas obligatorias de salida: {faltantes_salida}")

    if "Is Account Takeover" not in df.columns:
        errores.append("'Is Account Takeover' (Ground Truth) no está presente.")
    elif df["Is Account Takeover"].isna().all():
        errores.append("'Is Account Takeover' está completamente vacío.")

    # Verificación adicional (heredada de V3): si la conversión de
    # timestamp produjo un rango de fechas absurdo, no se exporta.
    fecha_min = df["Login Timestamp"].min()
    fecha_max = df["Login Timestamp"].max()
    if pd.notna(fecha_min) and fecha_min.year < 1990:
        errores.append(
            f"'Login Timestamp' produjo fechas implausibles (mínimo: "
            f"{fecha_min}). Esto sugiere que la unidad del timestamp se "
            "infirió incorrectamente. Revisa 'convertir_login_timestamp'."
        )

    # NUEVO EN V4 (informativo, no bloqueante): coherencia has_previous_login
    # vs distance_previous_km / required_speed_kmh. Si has_previous_login==0
    # pero alguna de las dos métricas NO es NaN, es un error de regla, no
    # un simple missing esperado -> aquí SÍ debe bloquear, porque violaría
    # la Sección 31 directamente.
    if "has_previous_login" in df.columns:
        primer_evento = df["has_previous_login"] == 0
        fuga_distancia = primer_evento & df["distance_previous_km"].notna()
        fuga_velocidad = primer_evento & df["required_speed_kmh"].notna()
        if fuga_distancia.any() or fuga_velocidad.any():
            errores.append(
                "Se encontraron valores NO nulos de 'distance_previous_km' o "
                "'required_speed_kmh' en registros con has_previous_login=0 "
                "(primer evento del usuario). Esto viola la Sección 31: la "
                "ausencia de historial debe producir NaN semántico, nunca "
                "un valor calculado."
            )

    # NUEVO EN V4 (informativo, no bloqueante): country_mismatch debe ser
    # NaN exactamente donde falte información, no 0 por defecto.
    if "country_mismatch" in df.columns and "ip_country_code" in df.columns:
        ip_no_resuelta = df["ip_country_code"].isna()
        mismatch_deberia_ser_nan_pero_no_lo_es = (
            ip_no_resuelta & df["country_mismatch"].notna()
        )
        if mismatch_deberia_ser_nan_pero_no_lo_es.any():
            errores.append(
                "'country_mismatch' tiene valores no nulos en registros donde "
                "'ip_country_code' es NaN (IP no resuelta). Esto viola la "
                "Sección 31/36: sin país de IP conocido, el mismatch debe "
                "ser NaN."
            )

    if errores:
        mensaje = (
            "VALIDACIÓN BLOQUEANTE FALLIDA — el dataset final NO se exportará.\n"
            "Errores encontrados:\n" + "\n".join(f"  - {e}" for e in errores)
        )
        raise RuntimeError(mensaje)

    print("  [OK] Todas las validaciones bloqueantes pasaron correctamente.\n")
    return True


def generar_metricas_diagnosticas(df, usuarios_seleccionados, diagnostico_global,
                                   diagnostico_subconjunto, diagnostico_resolucion,
                                   diagnostico_centroides, n_login_desconocidos,
                                   config):
    """Recolecta TODAS las métricas informativas para el checklist final."""
    metricas = {
        "n_usuarios_seleccionados": len(usuarios_seleccionados),
        "diagnostico_global": diagnostico_global,
        "diagnostico_subconjunto": diagnostico_subconjunto,
        "diagnostico_resolucion": diagnostico_resolucion,
        "diagnostico_centroides": diagnostico_centroides,
        "n_login_desconocidos": n_login_desconocidos,
    }

    usuarios_en_df = set(df["User ID"].unique())
    metricas["pct_integridad_referencial"] = (
        100 * len(usuarios_en_df & set(usuarios_seleccionados)) / len(usuarios_seleccionados)
        if usuarios_seleccionados else 0.0
    )

    metricas["orden_temporal_correcto"] = bool(
        df.groupby("User ID")["Login Timestamp"]
        .apply(lambda s: s.is_monotonic_increasing).all()
    )
    metricas["timestamp_es_datetime"] = pd.api.types.is_datetime64_any_dtype(
        df["Login Timestamp"]
    )
    metricas["rango_fechas_login"] = (
        str(df["Login Timestamp"].min()), str(df["Login Timestamp"].max())
    )

    conteo_gt = df["Is Account Takeover"].value_counts(dropna=False)
    metricas["ground_truth_counts"] = conteo_gt.to_dict()
    metricas["ground_truth_pct"] = (100 * conteo_gt / conteo_gt.sum()).round(2).to_dict()

    metricas["impossible_travel_total"] = int(df["impossible_travel"].sum())
    metricas["fuera_de_turno_total"] = int(df["is_outside_shift"].fillna(0).sum())
    metricas["inactive_success_total"] = int(df["inactive_account_success"].sum())

    metricas["has_previous_login_0"] = int((df["has_previous_login"] == 0).sum())
    metricas["has_previous_login_1"] = int((df["has_previous_login"] == 1).sum())

    metricas["country_mismatch_1"] = int(df["country_mismatch"].fillna(0).sum())
    metricas["country_mismatch_nan"] = int(df["country_mismatch"].isna().sum())

    # Diagnóstico ISO2: cuántos Pais_Residencia distintos hay y si están
    # dentro del set reconocido (informativo).
    paises_residencia_unicos = set(df["Pais_Residencia"].dropna().unique())
    metricas["paises_residencia_no_reconocidos"] = sorted(
        paises_residencia_unicos - config["ISO2_RECONOCIDOS"]
    )

    columnas_clave = [
        "ip_country_code", "ip_country_name", "distance_previous_km",
        "required_speed_kmh", "previous_login_timestamp",
        "login_exitoso_normalizado",
    ]
    metricas["nulos_columnas_clave"] = {
        c: int(df[c].isna().sum()) for c in columnas_clave if c in df.columns
    }

    print("  Resumen de métricas de calidad calculadas:")
    print(f"    Integridad referencial: {metricas['pct_integridad_referencial']:.2f}%")
    print(f"    Orden temporal correcto: {metricas['orden_temporal_correcto']}")
    print(f"    Rango de fechas de login: {metricas['rango_fechas_login']}")
    print(f"    Distribución Ground Truth: {metricas['ground_truth_counts']}")
    print(f"    has_previous_login=0 / =1: {metricas['has_previous_login_0']:,} / "
          f"{metricas['has_previous_login_1']:,}")
    print(f"    country_mismatch=1 / NaN: {metricas['country_mismatch_1']:,} / "
          f"{metricas['country_mismatch_nan']:,}")
    print(f"    Nulos en columnas clave: {metricas['nulos_columnas_clave']}\n")

    return metricas


def exportar_dataset_final(df, config):
    """Exporta dataset_final_modelo.csv. 'Is Account Takeover' queda
    como ÚLTIMA columna, sin modificaciones."""
    columnas_finales = [
        "User ID", "IP Address", "Login Timestamp", "Login Successful",
        "login_exitoso_normalizado",
        "Device Type", "Is Attack IP",
        "Country", "Region", "City", "ASN",
        "ip_country_code", "ip_country_name", "ip_asn", "ip_as_name", "ip_as_domain",
        "Nombre_Completo", "Rol_Hospitalario", "Pais_Residencia",
        "Ciudad_Base", "Turno_Asignado", "Estado_Cuenta", "Fecha_Ingreso",
        "failed_attempts_15min", "failed_attempts_1h",
        "has_previous_login",
        "previous_login_timestamp", "time_since_previous_login_hours",
        "distance_previous_km", "required_speed_kmh", "impossible_travel",
        "is_outside_shift", "country_mismatch", "inactive_account_success",
        "Is Account Takeover",
    ]
    columnas_presentes = [c for c in columnas_finales if c in df.columns]
    # Selección de columnas (no requiere .copy() adicional: ya produce
    # un DataFrame nuevo e independiente)
    df_final = df[columnas_presentes]

    df_final.to_csv(config["OUT_DATASET_FINAL"], index=False)
    return df_final


def imprimir_checklist_final(df_final, metricas, config):
    """Checklist final con TODAS las métricas calculadas en tiempo real."""
    diag_sub = metricas["diagnostico_subconjunto"]
    diag_global = metricas["diagnostico_global"]
    diag_res = metricas["diagnostico_resolucion"]
    diag_cent = metricas["diagnostico_centroides"]
    gt_counts = metricas["ground_truth_counts"]
    gt_pct = metricas["ground_truth_pct"]

    print("=" * 60)
    print("CHECKLIST FINAL — FASE 03 CRISP-DM (Versión 4)")
    print("=" * 60)
    print()
    print(f"[OK] Usuarios seleccionados: {metricas['n_usuarios_seleccionados']}")
    print(f"[OK] Historial mínimo por usuario: >= {config['MIN_EVENTOS_USUARIO']} eventos")
    print(f"[OK] Integridad referencial User ID: "
          f"{metricas['pct_integridad_referencial']:.2f}%")
    print()
    print(f"[INFO] Total registros procesados para los 2000 usuarios: "
          f"{len(df_final):,}")
    print()
    print(f"[INFO] Rango de fechas de 'Login Timestamp': "
          f"{metricas['rango_fechas_login'][0]} -> {metricas['rango_fechas_login'][1]}")
    print()
    print(f"[INFO] --- Diagnóstico IP: SUBCONJUNTO de 2.000 usuarios ---")
    print(f"[INFO] IPv4: {diag_sub['total_ipv4']:,} ({diag_sub['pct_ipv4']:.2f}%)")
    print(f"[INFO] IPv6: {diag_sub['total_ipv6']:,} ({diag_sub['pct_ipv6']:.2f}%)")
    print(f"[INFO] IP inválidas/nulas: {diag_sub['total_invalidas']:,} "
          f"({diag_sub['pct_invalidas']:.2f}%)")
    print()
    print(f"[INFO] --- Diagnóstico IP: RBA GLOBAL (33M+), solo referencia ---")
    print(f"[INFO] IPv4: {diag_global['total_ipv4']:,} ({diag_global['pct_ipv4']:.2f}%)")
    print(f"[INFO] IPv6: {diag_global['total_ipv6']:,} ({diag_global['pct_ipv6']:.2f}%)")
    print(f"[INFO] IP inválidas/nulas: {diag_global['total_invalidas']:,} "
          f"({diag_global['pct_invalidas']:.2f}%)")
    print()
    print(f"[INFO] IPs IPv4 resueltas mediante IPinfo: "
          f"{diag_res['ipv4_unicas_resueltas']:,}")
    print(f"[INFO] IPs IPv4 no resueltas: {diag_res['ipv4_unicas_no_resueltas']:,}")
    print(f"[INFO] Porcentaje de resolución IPv4: "
          f"{diag_res['pct_resolucion_ipv4']:.2f}%")
    print()
    print(f"[INFO] Cobertura centroides ISO2 (países distintos): "
          f"{diag_cent['pct_cobertura_paises_distintos']:.2f}% "
          f"({diag_cent['paises_con_centroide']}/{diag_cent['paises_relevantes_total']})")
    print(f"[INFO] Cobertura centroides (registros con historial previo): "
          f"{diag_cent['pct_cobertura_registros_con_historial']:.2f}%")
    print()
    print(f"[INFO] has_previous_login = 0 (primer evento): "
          f"{metricas['has_previous_login_0']:,}")
    print(f"[INFO] has_previous_login = 1 (con historial): "
          f"{metricas['has_previous_login_1']:,}")
    print()
    print(f"[INFO] impossible_travel = 1: {metricas['impossible_travel_total']:,}")
    print(f"[INFO] registros fuera de turno: {metricas['fuera_de_turno_total']:,}")
    print(f"[INFO] cuentas inactivas con login exitoso: "
          f"{metricas['inactive_success_total']:,}")
    print(f"[INFO] valores de 'Login Successful' no interpretables: "
          f"{metricas['n_login_desconocidos']:,}")
    print()
    print(f"[INFO] country_mismatch = 1: {metricas['country_mismatch_1']:,}")
    print(f"[INFO] country_mismatch = NaN (IP no resuelta): "
          f"{metricas['country_mismatch_nan']:,}")
    if metricas["paises_residencia_no_reconocidos"]:
        print(f"[ATENCIÓN] Códigos ISO2 en Pais_Residencia fuera del set "
              f"reconocido: {metricas['paises_residencia_no_reconocidos']}")
    else:
        print("[OK] Todos los códigos ISO2 de Pais_Residencia están dentro "
              "del set reconocido.")
    print()
    print(f"[INFO] Nulos en columnas clave: {metricas['nulos_columnas_clave']}")
    print()
    print(f"[INFO] Orden temporal correcto: {metricas['orden_temporal_correcto']}")
    print(f"[INFO] Timestamp es datetime: {metricas['timestamp_es_datetime']}")
    print()
    print("[INFO] Distribución Ground Truth:")
    for valor, conteo in gt_counts.items():
        print(f"       Is Account Takeover = {valor}: {conteo:,} "
              f"({gt_pct.get(valor, 0):.2f}%)")
    print()
    print("[INFO] Dataset final:")
    print(f"       Filas: {len(df_final):,}")
    print(f"       Columnas: {df_final.shape[1]}")
    print()
    print("[OK] No se ejecutó entrenamiento de Machine Learning.")
    print("[OK] No se ejecutó SMOTE ni balanceo de clases.")
    print("[OK] No se realizó train_test_split.")
    print("[OK] No se realizaron predicciones.")
    print("[OK] 'Is Account Takeover' no fue utilizada para construir ninguna feature.")
    print("[OK] Fase 03 (Versión 4) finalizada.")
    print()
    print("Archivo generado:")
    print(config["OUT_DATASET_FINAL"])
    print()
    print("=" * 60)


# ============================================================================
# ORQUESTADOR PRINCIPAL (misma arquitectura de la V3, Sección 45/46)
# ============================================================================

def main():
    config = configurar_entorno()

    contador_usuarios, diagnostico_global = analizar_dataset_rba(config)
    usuarios_seleccionados = seleccionar_usuarios(contador_usuarios, config)
    del contador_usuarios  # ya no se necesita; puede ser grande (millones de claves)
    gc.collect()

    df_logs, diagnostico_subconjunto = extraer_historial_usuarios(
        usuarios_seleccionados, config
    )
    df_empleados = generar_empleados(usuarios_seleccionados, config)

    # merge() SIEMPRE produce un DataFrame nuevo (no es mutación in-place),
    # así que aquí sí se necesita memoria para la unión — pero justo
    # después liberamos las dos piezas de entrada, que ya no se usan.
    df_integrado = df_logs.merge(df_empleados, on="User ID", how="inner")
    del df_logs, df_empleados
    gc.collect()

    df_integrado, diagnostico_resolucion = resolver_ips(df_integrado, config)

    df_integrado, n_login_desconocidos = crear_features_temporales(df_integrado, config)
    df_integrado, diagnostico_centroides = crear_feature_impossible_travel(
        df_integrado, config
    )
    df_integrado = crear_feature_turnos(df_integrado)
    df_integrado = crear_features_negocio(df_integrado)

    validar_calidad_bloqueante(df_integrado, usuarios_seleccionados, config)

    df_final = exportar_dataset_final(df_integrado, config)

    metricas = generar_metricas_diagnosticas(
        df_integrado, usuarios_seleccionados, diagnostico_global,
        diagnostico_subconjunto, diagnostico_resolucion,
        diagnostico_centroides, n_login_desconocidos, config,
    )

    imprimir_checklist_final(df_final, metricas, config)

    return df_final


if __name__ == "__main__":
    main()
