"""
config.py
=========
Contenedor de configuración reproducible para la Fase 03 y catálogo de
constantes de dominio (roles hospitalarios, turnos, distribución de
países de residencia, centroides geográficos ISO2).

POR QUÉ EXISTE ESTE MÓDULO
--------------------------
En fase03_pipeline_v4.py (versión monolítica) estas constantes vivían
dispersas en el mismo archivo que la lógica que las consumía. Aislarlas
aquí permite que cualquier módulo (empleados.py, features.py) las
importe sin depender del resto del pipeline, y que cambiar una
ponderación no obligue a tocar lógica de negocio.

NO SE CAMBIA NINGÚN VALOR respecto a fase03_pipeline_v4.py — esto es
una reubicación (Etapa 1: refactor arquitectónico puro), no una
redefinición metodológica.
"""
from dataclasses import dataclass, field


@dataclass
class ConfiguracionPipeline:
    """Constantes reproducibles del pipeline. Equivalente tipado de la
    función configurar_entorno() del script monolítico.

    Todos los valores por defecto son idénticos a los de
    fase03_pipeline_v4.py. Se pueden sobreescribir por parámetro del
    constructor — por ejemplo, en pruebas, para apuntar a un fixture
    local en vez de /content (rutas de Google Colab).
    """

    RBA_PATH: str = "/content/rba_dataset.csv"
    IPINFO_PATH: str = "/content/country_asn.csv"
    OUT_RBA_2000: str = "/content/rba_2000_users.csv"
    OUT_EMPLEADOS: str = "/content/empleados.csv"
    OUT_DATASET_FINAL: str = "/content/dataset_final_modelo.csv"

    RANDOM_STATE: int = 42
    FAKER_SEED: int = 42

    MIN_EVENTOS_USUARIO: int = 15
    N_USUARIOS: int = 2000

    CHUNKSIZE_PASADA_1: int = 500_000
    CHUNKSIZE_PASADA_2: int = 250_000

    COLUMNAS_RBA_OBLIGATORIAS: list = field(default_factory=lambda: [
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
    ])

    VENTANA_CORTA: str = "15min"
    VENTANA_LARGA: str = "1h"

    UMBRAL_VELOCIDAD_KMH: float = 800.0
    VENTANA_MAX_HORAS: float = 12.0

    PESO_ASISTENCIAL_HOSPITALARIO: float = 0.80
    PROB_CUENTA_ACTIVA: float = 0.93

    # Ventana de recolección real del RBA Dataset, según su
    # documentación oficial. Se usa únicamente como verificación de
    # cordura no bloqueante sobre la unidad inferida del timestamp.
    VENTANA_FECHAS_RBA_CONOCIDA: tuple = ("2019-01-01", "2022-12-31")

    # Set de códigos ISO2 reconocidos por el pipeline (empleados +
    # centroides). Uso exclusivamente diagnóstico/informativo — nunca
    # se usa para inventar o corregir países no reconocidos.
    ISO2_RECONOCIDOS: set = field(default_factory=lambda: {
        "CO", "MX", "ES", "AR", "PE", "CL", "US", "EC",
        "BR", "VE", "DE", "FR", "GB", "CA", "CN", "IN", "RU", "JP",
    })
        # --- Etapa 2 (split / remuestreo / salidas de modelado) ---
    TEST_SIZE: float = 0.2
    RATIO_OVERSAMPLING: float = 1.0   # 1.0 = clases 1:1 en TRAIN (ver riesgo en resampling.py)
    OUT_TRAIN_PREPARED: str = "/content/dataset_train_prepared.csv"
    OUT_TEST_PREPARED: str = "/content/dataset_test_prepared.csv"
    OUT_PREPROCESSOR: str = "/content/preprocessor.joblib"


# ============================================================================
# CONSTANTES DE DOMINIO (idénticas a fase03_pipeline_v4.py — Etapa 1
# no introduce ningún cambio de valores ni de distribución)
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

# ISO2 canónico (corrección de la Versión 4: antes eran nombres en
# español, lo cual rompía la comparación contra ip_country_code).
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

# ISO2 canónico, alineado con el formato NATIVO de la columna
# 'Country' del RBA (que ya viene en ISO2, no en nombre de país).
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
