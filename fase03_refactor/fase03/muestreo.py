"""
muestreo.py
===========
Decide QUÉ usuarios entran al pipeline. OCP/DIP: PipelineFase03 depende de la
abstracción EstrategiaMuestreo, inyectada por constructor.

CONTRATO (Etapa 2): seleccionar(contador_usuarios, contador_eventos_ato=None).
 - MuestreoAleatorioSimple: ignora contador_eventos_ato (lógica sin cambios).
 - MuestreoEstratificadoPorTarget: lo requiere.

USAR EL TARGET AQUÍ NO ES LEAKAGE: decide qué USUARIOS entran al dataset,
nunca qué VALOR toma una feature (las features se calculan sin consultar el target,
que permanece asociado a cada evento). Sí es muestreo condicionado al
resultado: la prevalencia de la muestra NO representa la del RBA completo.
"""
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass, field

import numpy as np


@dataclass
class ResultadoMuestreo:
    """usuarios: IDs seleccionados. origen: {user_id: 'aleatorio' |
    'ato_elegible' | 'aleatorio_no_ato'} (trazabilidad académica)."""
    usuarios: list
    origen: dict = field(default_factory=dict)


class EstrategiaMuestreo(ABC):
    @abstractmethod
    def seleccionar(self, contador_usuarios: Counter,
                    contador_eventos_ato: Counter = None) -> ResultadoMuestreo:
        ...


class MuestreoAleatorioSimple(EstrategiaMuestreo):
    """Aleatorio, reproducible, sin reemplazo, sobre usuarios con
    >= MIN_EVENTOS_USUARIO eventos. Lógica IDÉNTICA a la Etapa 1."""

    def __init__(self, config):
        self.config = config

    def seleccionar(self, contador_usuarios, contador_eventos_ato=None):
        config = self.config
        print("=" * 60)
        print("[3/8] Seleccionando usuarios (muestreo aleatorio simple)...")
        print("=" * 60)

        poblacion_elegible = [
            uid for uid, freq in contador_usuarios.items()
            if freq >= config.MIN_EVENTOS_USUARIO
        ]
        poblacion_elegible.sort()

        print(f"  Usuarios con >= {config.MIN_EVENTOS_USUARIO} eventos: "
              f"{len(poblacion_elegible):,}")

        if len(poblacion_elegible) < config.N_USUARIOS:
            raise ValueError(
                "La población elegible es menor que N_USUARIOS. "
                "Revisa MIN_EVENTOS_USUARIO o el archivo de origen."
            )

        rng = np.random.default_rng(config.RANDOM_STATE)
        usuarios_seleccionados = rng.choice(
            poblacion_elegible, size=config.N_USUARIOS, replace=False
        )
        usuarios_seleccionados = sorted(int(u) for u in usuarios_seleccionados)

        if len(set(usuarios_seleccionados)) != config.N_USUARIOS:
            raise RuntimeError(
                "ERROR CRÍTICO: la selección de usuarios no produjo exactamente "
                f"{config.N_USUARIOS} usuarios únicos. Selección abortada."
            )
        for uid in usuarios_seleccionados:
            if contador_usuarios[uid] < config.MIN_EVENTOS_USUARIO:
                raise RuntimeError(
                    f"ERROR CRÍTICO: el usuario {uid} fue seleccionado pero no "
                    f"cumple MIN_EVENTOS_USUARIO. Selección abortada."
                )

        print(f"  Usuarios seleccionados: {len(usuarios_seleccionados):,} "
              f"(RANDOM_STATE={config.RANDOM_STATE})")
        print("  [OK] Verificado: exactamente N_USUARIOS únicos, todos con "
              "el mínimo de eventos requerido.\n")

        origen = {uid: "aleatorio" for uid in usuarios_seleccionados}
        return ResultadoMuestreo(usuarios=usuarios_seleccionados, origen=origen)


class MuestreoEstratificadoPorTarget(EstrategiaMuestreo):
    """Diseño caso-control a nivel de usuario:
      1. Positivos: TODOS los usuarios con >=1 evento ATO Y >= MIN_EVENTOS_USUARIO
         eventos (MIN_EVENTOS_USUARIO no se reduce).
      2. Negativos: el resto de la cuota (N_USUARIOS - n_positivos) sorteado
         (reproducible, sin reemplazo) entre usuarios con >= MIN_EVENTOS_USUARIO
         eventos y CERO eventos ATO (se excluye a TODO usuario con algún ATO,
         sea o no elegible).
    Los usuarios seleccionados conservan su historial COMPLETO (lo extrae
    AnalizadorRBA.segunda_pasada). No se inventan ni alteran etiquetas."""

    def __init__(self, config):
        self.config = config

    def seleccionar(self, contador_usuarios, contador_eventos_ato=None):
        config = self.config
        print("=" * 60)
        print("[3/8] Seleccionando usuarios (muestreo estratificado por target)...")
        print("=" * 60)

        if contador_eventos_ato is None:
            raise ValueError(
                "MuestreoEstratificadoPorTarget requiere contador_eventos_ato "
                "(lo entrega AnalizadorRBA.primera_pasada())."
            )

        usuarios_con_ato = set(contador_eventos_ato.keys())
        ato_elegibles = sorted(
            int(uid) for uid in usuarios_con_ato
            if contador_usuarios[uid] >= config.MIN_EVENTOS_USUARIO
        )
        n_ato = len(ato_elegibles)
        if n_ato == 0:
            raise ValueError("Ningún usuario ATO cumple MIN_EVENTOS_USUARIO.")
        if n_ato >= config.N_USUARIOS:
            raise ValueError(
                f"Usuarios ATO elegibles ({n_ato}) >= N_USUARIOS "
                f"({config.N_USUARIOS}): no queda cupo para negativos."
            )

        n_negativos = config.N_USUARIOS - n_ato
        pool_negativos = sorted(
            int(uid) for uid, n in contador_usuarios.items()
            if n >= config.MIN_EVENTOS_USUARIO and uid not in usuarios_con_ato
        )
        if len(pool_negativos) < n_negativos:
            raise ValueError(
                f"Pool no-ATO elegible ({len(pool_negativos)}) < cupo requerido "
                f"({n_negativos})."
            )

        rng = np.random.default_rng(config.RANDOM_STATE)
        negativos = sorted(
            int(u) for u in rng.choice(pool_negativos, size=n_negativos, replace=False)
        )
        usuarios = sorted(ato_elegibles + negativos)

        # --- validaciones bloqueantes ---
        if len(usuarios) != config.N_USUARIOS or len(set(usuarios)) != config.N_USUARIOS:
            raise RuntimeError("La selección no produjo exactamente N_USUARIOS únicos.")
        for uid in usuarios:
            if contador_usuarios[uid] < config.MIN_EVENTOS_USUARIO:
                raise RuntimeError(f"Usuario {uid} no cumple MIN_EVENTOS_USUARIO.")
        if any(uid in usuarios_con_ato for uid in negativos):
            raise RuntimeError("Un usuario 'negativo' tiene eventos ATO.")

        origen = {uid: "ato_elegible" for uid in ato_elegibles}
        origen.update({uid: "aleatorio_no_ato" for uid in negativos})

        print(f"  ATO usuarios en el RBA completo:      {len(usuarios_con_ato):,}")
        print(f"  ATO usuarios elegibles (>= {config.MIN_EVENTOS_USUARIO} eventos): {n_ato:,}")
        print(f"  ATO usuarios seleccionados:           {n_ato:,}")
        print(f"  ATO eventos seleccionados:            "
              f"{sum(contador_eventos_ato[u] for u in ato_elegibles):,}")
        print(f"  Usuarios negativos seleccionados:     {n_negativos:,}")
        print(f"  Eventos negativos (totales de esos usuarios): "
              f"{sum(contador_usuarios[u] for u in negativos):,}")
        print("  [NOTA] Muestra enriquecida: la prevalencia resultante NO "
              "representa la del RBA completo (muestreo condicionado al target).\n")

        return ResultadoMuestreo(usuarios=usuarios, origen=origen)